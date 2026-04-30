import librosa
import soundfile as sf


def remove_silence_file(input_path: str, output_path: str, top_db: int = 20) -> str:
    audio, sr = librosa.load(input_path, sr=None)

    if len(audio) == 0:
        raise ValueError("Empty audio file")

    trimmed, _ = librosa.effects.trim(audio, top_db=top_db)

    if len(trimmed) == 0:
        raise ValueError("Audio became empty after trimming")

    sf.write(output_path, trimmed, sr)
    return output_path