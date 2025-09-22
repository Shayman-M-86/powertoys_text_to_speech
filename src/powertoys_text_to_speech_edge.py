import time
import threading
import re
from queue import Queue, Empty
from typing import Optional

import keyboard
import win32clipboard
import win32con

# ---------- Config ----------
POWEROCR_HOTKEY = "windows+shift+t"   # PowerToys Text Extractor default
CLIPBOARD_WAIT_SECONDS = 15
POLL_INTERVAL_SECONDS = 0.10
MIN_CHARS_TO_SPEAK = 3

# Match your SAPI-registered “Natural” voice. We’ll pick the first SAPI token
# whose description contains this substring (case-insensitive).
NATURAL_MATCH_SUBSTR = "natural"

# Optional SAPI tuning (range: Rate -10..+10, Volume 0..100)
SAPI_RATE = 0
SAPI_VOLUME = 100
# ----------------------------


def get_clipboard_text() -> Optional[str]:
    """Safely read text from Windows clipboard."""
    text = None
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            if isinstance(data, str):
                text = data
    except Exception:
        text = None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass
    return text


def tidy_text(s: str) -> str:
    """Basic cleanup to make OCR text nicer to read aloud."""
    if not s:
        return ""
    s = s.strip()
    # replace newlines with spaces and collapse multiples
    s = s.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


def wait_for_clip_change(baseline: str, timeout_s: float) -> Optional[str]:
    """Poll the clipboard until it differs from baseline or we time out."""
    start = time.time()
    while time.time() - start < timeout_s:
        current = get_clipboard_text()
        if current and current != baseline:
            return current
        time.sleep(POLL_INTERVAL_SECONDS)
    return None


class SapiNaturalSpeaker:
    """
    SAPI-only speaker that *forces* a 'Natural' voice (as exposed in SAPI on your system).
    Runs SAPI on its own COM STA thread and speaks texts sequentially.
    """
    def __init__(self, natural_match_substr: str = NATURAL_MATCH_SUBSTR):
        self._q: "Queue[str]" = Queue()
        self._match = (natural_match_substr or "").lower()
        self._thr = threading.Thread(target=self._run, daemon=True)
        self._thr.start()

    def speak(self, text: str):
        if text and len(text) >= MIN_CHARS_TO_SPEAK:
            self._q.put(text)

    def _run(self):
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        try:
            voice = win32com.client.Dispatch("SAPI.SpVoice")

            # Pick the first SAPI token whose description contains "natural"
            selected = None
            tokens = voice.GetVoices()
            for i in range(tokens.Count):
                token = tokens.Item(i)
                desc = token.GetDescription()
                if self._match and self._match in desc.lower():
                    selected = token
                    break

            if selected:
                voice.Voice = selected
                print(f"[SAPI] Selected Natural voice: {voice.Voice.GetDescription()}")
            else:
                print("[SAPI] No 'Natural' voice found in SAPI tokens; using default SAPI voice.")

            # Optional tuning
            try:
                voice.Rate = SAPI_RATE
                voice.Volume = SAPI_VOLUME
            except Exception:
                pass

            # Worker loop
            while True:
                try:
                    txt = self._q.get(timeout=0.1)
                except Empty:
                    continue
                try:
                    voice.Speak(txt)
                except Exception:
                    # keep loop alive on TTS errors
                    pass
        finally:
            pythoncom.CoUninitialize()


def main():
    print("PowerToys Text Extractor → TTS (SAPI Natural voice only).")
    print(f"Press {POWEROCR_HOTKEY}, draw your OCR box; I’ll speak what’s copied.")
    print("Ctrl+C to quit.")

    speaker = SapiNaturalSpeaker()

    def on_hotkey():
        baseline = get_clipboard_text() or ""
        new_text = wait_for_clip_change(baseline, CLIPBOARD_WAIT_SECONDS)
        if new_text:
            cleaned = tidy_text(new_text)
            if cleaned and len(cleaned) >= MIN_CHARS_TO_SPEAK:
                print("\n[Spoken text]\n" + cleaned + "\n")
                speaker.speak(cleaned)

    keyboard.add_hotkey(
        POWEROCR_HOTKEY,
        on_hotkey,
        suppress=False,           # don't steal the hotkey; let PowerToys see it
        trigger_on_release=True
    )

    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\nExiting…")


if __name__ == "__main__":
    main()
