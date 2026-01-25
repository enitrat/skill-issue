#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pocket-tts", "pygame>=2.6.1", "scipy"]
# ///
"""
Stop hook that converts Claude's final response to speech using Kyutai Pocket TTS.

When Claude finishes responding (Stop event), this hook reads the transcript,
extracts Claude's last response, and plays it as audio.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional

import scipy.io.wavfile


def get_cache_dir() -> Path:
    """Get or create cache directory for TTS model and audio files."""
    cache_dir = Path.home() / ".cache" / "claude-tts-notify"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def clean_text_for_tts(text: str) -> str:
    """Clean text for better TTS pronunciation."""
    # Remove markdown formatting
    text = re.sub(r"`([^`]+)`", r"\1", text)  # Remove backticks
    text = re.sub(r"```[\s\S]*?```", "", text)  # Remove code blocks
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)  # Remove bold
    text = re.sub(r"\*([^*]+)\*", r"\1", text)  # Remove italic
    text = re.sub(r"_([^_]+)_", r"\1", text)  # Remove underscores
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # Remove links
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)  # Remove headers

    # Replace underscores with spaces
    text = text.replace("_", " ")

    # Clean up extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def truncate_for_tts(text: str, max_chars: int = 500) -> str:
    """Truncate text to reasonable length for TTS, ending at sentence boundary."""
    if len(text) <= max_chars:
        return text

    # Find last sentence boundary before max_chars
    truncated = text[:max_chars]
    last_period = truncated.rfind(". ")
    last_exclaim = truncated.rfind("! ")
    last_question = truncated.rfind("? ")

    # Find the latest sentence boundary
    last_boundary = max(last_period, last_exclaim, last_question)

    if last_boundary > max_chars // 2:
        return truncated[: last_boundary + 1]

    return truncated + "..."


def extract_claude_response(transcript_path: str) -> Optional[str]:
    """
    Extract Claude's last response from the transcript JSONL file.

    Args:
        transcript_path: Path to the JSONL transcript file

    Returns:
        Claude's last text response, or None if not found
    """
    try:
        path = Path(transcript_path)
        if not path.exists():
            print(f"Transcript not found: {transcript_path}", file=sys.stderr)
            return None

        # Read last N lines (transcript can be large)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Search backwards for the last assistant message
        for line in reversed(lines[-100:]):  # Check last 100 entries
            try:
                entry = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            # Look for assistant messages
            if entry.get("type") != "assistant":
                continue

            message = entry.get("message", {})
            content = message.get("content")

            if not content:
                continue

            # Handle string content
            if isinstance(content, str):
                return content.strip()

            # Handle array content (Claude Code format)
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        if text:
                            text_parts.append(text.strip())
                if text_parts:
                    return " ".join(text_parts)

        return None

    except Exception as e:
        print(f"Error reading transcript: {e}", file=sys.stderr)
        return None


def speak_text(text: str):
    """Generate audio from text using Pocket TTS and play it."""
    import pygame

    try:
        from pocket_tts import TTSModel

        # Initialize pygame mixer
        pygame.mixer.init()

        # Load model (cached after first load)
        model = TTSModel.load_model()

        # Use default voice
        voice_state = model.get_state_for_audio_prompt(
            "hf://kyutai/tts-voices/alba-mackenna/casual.wav"
        )

        # Generate audio
        audio = model.generate_audio(voice_state, text)

        # Save to temp file
        cache_dir = get_cache_dir()
        temp_wav = cache_dir / "temp_output.wav"
        scipy.io.wavfile.write(str(temp_wav), model.sample_rate, audio.numpy())

        # Play with pygame
        pygame.mixer.music.load(str(temp_wav))
        pygame.mixer.music.set_volume(0.7)
        pygame.mixer.music.play()

        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)

        # Cleanup
        pygame.mixer.quit()

        # Remove temp file
        try:
            temp_wav.unlink()
        except:
            pass

    except ImportError as e:
        print(f"TTS dependencies not available: {e}", file=sys.stderr)
        print("Install with: uv sync", file=sys.stderr)
    except Exception as e:
        print(f"TTS error: {e}", file=sys.stderr)
        # Ensure pygame is cleaned up on error
        try:
            pygame.mixer.quit()
        except:
            pass


def main():
    """Main hook entry point."""
    # Read input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return

    hook_event = input_data.get("hook_event_name", "")

    # Only process Stop events
    if hook_event != "Stop":
        print("{}")
        return

    # Get transcript path
    transcript_path = input_data.get("transcript_path")
    if not transcript_path:
        print("{}")
        return

    # Extract Claude's last response
    response = extract_claude_response(transcript_path)
    if not response:
        print("{}")
        return

    # Clean and truncate for TTS
    cleaned = clean_text_for_tts(response)
    if not cleaned:
        print("{}")
        return

    # Truncate to reasonable length
    text_to_speak = truncate_for_tts(cleaned, max_chars=500)

    # Speak the response
    speak_text(text_to_speak)

    # Return empty JSON to indicate success
    print("{}")


if __name__ == "__main__":
    main()
