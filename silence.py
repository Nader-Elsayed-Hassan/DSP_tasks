import librosa
import soundfile as sf


def remove_silence_file(input_path: str, output_path: str = "no_silence.wav") -> str:
    """Load an audio file, trim leading/trailing silence, and save output.

    Args:
        input_path: path to input audio file.
        output_path: where to write the trimmed file (defaults to no_silence.wav).

    Returns:
        The path to the output file.
    """
    audio, sr = librosa.load(input_path, sr=None)
    audio_trimmed, _ = librosa.effects.trim(audio, top_db=20)
    sf.write(output_path, audio_trimmed, sr)
    print("Silence removed")
    return output_path


if __name__ == "__main__":
    # default behavior when executed as script
    remove_silence_file("clean_audio.wav")
