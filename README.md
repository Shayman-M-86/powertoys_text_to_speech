# PowerToys OCR → Natural SAPI TTS

This tool connects **[Microsoft PowerToys](https://learn.microsoft.com/en-us/windows/powertoys/)** with the Windows text-to-speech system. It lets you quickly grab text from anywhere on your screen and have it spoken aloud using a **Natural voice** — even though those voices normally aren’t exposed to SAPI.

## How it works

1. **Text Extraction with PowerToys**  
   - PowerToys includes a *Text Extractor* tool (default shortcut: `Win`+`Shift`+`T`).  
   - You draw a box on your screen and PowerToys performs OCR.  
   - The recognized text is automatically copied to your clipboard.  

2. **SAPI Natural Voice Playback**  
   - Normally, SAPI only exposes the legacy desktop voices (George, David, Zira, Hazel, etc.).  
   - To work around this, I use **NaturalVoiceSAPIAdapter**, which makes Windows register the modern **Narrator “Natural” voices** so they appear in the SAPI voice list.  
   - My Python script then:
     - Listens for the PowerToys hotkey.  
     - Waits for new text on the clipboard.  
     - Cleans it up (removes extra whitespace/newlines).  
     - Sends it to SAPI, *forcing selection of the Natural voice*.  

The result is a seamless loop:  
👉 Press `Win`+`Shift`+`T` → draw a box → hear the extracted text read aloud with a Natural-sounding voice.

---

## Why the adapter is needed

Windows ships high-quality voices like **Aria**, **Jenny**, **Sonia**, and **Natasha** as part of its Narrator / OneCore speech system. But Python’s `win32com.client.Dispatch("SAPI.SpVoice")` can’t access them directly.  

The **NaturalVoiceSAPIAdapter** bridges that gap by exposing those voices through the old SAPI interface. That way, you can keep using the simple, fast SAPI COM API in Python while still enjoying the improved voice quality.

---

✨ With this setup, you get the best of both worlds:  

- **Fast OCR** via PowerToys.  
- **Modern, natural TTS** via SAPI, without rewriting your whole project for WinRT APIs.  
