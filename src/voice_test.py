import win32com.client

speaker = win32com.client.Dispatch("SAPI.SpVoice")
tokens = speaker.GetVoices()

print("Available SAPI voices:\n")
chosen = None
for i in range(tokens.Count):
    voice = tokens.Item(i)
    desc = voice.GetDescription()
    print(f"{i}: {desc}")
    if "natural" in desc.lower():
        chosen = voice

if chosen:
    speaker.Voice = chosen
    print("\nSelected Natural voice:", speaker.Voice.GetDescription())
else:
    print("\nNo Natural voice found, using default voice.")

speaker.Speak("Hello, this is a test of the selected voice.")
