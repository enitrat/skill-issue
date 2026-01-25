# TTS Notify Hook

Converts Claude's responses to speech using [Kyutai Pocket TTS](https://github.com/kyutai-labs/pocket-tts).

When Claude finishes responding (Stop event), this hook reads the transcript, extracts Claude's last response, and plays it as audio.

## Features

- Triggers on **Stop** event (when Claude finishes responding)
- Extracts Claude's last response from the transcript
- Uses Kyutai Pocket TTS (runs on CPU, no GPU required)
- Cross-platform audio playback with pygame
- Automatic markdown cleanup for cleaner speech
- Truncates long responses to ~500 characters

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Audio output device
- SDL2 library (for pygame audio)

## System Dependencies

On Ubuntu/Debian:
```bash
sudo apt install libsdl2-mixer-2.0-0
```

On macOS:
```bash
brew install sdl2 sdl2_mixer
```

## Configuration

### Changing the Voice

Edit `hook.py` and modify the voice path in `speak_text()`:

```python
voice_state = model.get_state_for_audio_prompt(
    "hf://kyutai/tts-voices/<voice-name>/<style>.wav"
)
```

Available voices: `alba-mackenna`, `marius`, `javert` (each with casual/formal styles)
