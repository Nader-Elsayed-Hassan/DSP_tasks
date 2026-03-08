import librosa
import noisereduce as nr
import soundfile as sf


def reduce_noise_file(input_path: str, output_path: str = "clean_audio.wav") -> str:
    """Read an audio file, reduce noise, and write result to output_path.

    Args:
        input_path: path to the input audio file.
        output_path: where to save the processed audio (defaults to clean_audio.wav).

    Returns:
        The path to the output file.
    """
    audio, sr = librosa.load(input_path, sr=None)
    reduced_noise = nr.reduce_noise(y=audio, sr=sr)
    sf.write(output_path, reduced_noise, sr)
    print("Noise removed successfully")
    return output_path


if __name__ == "__main__":
    # When run directly, operate on a file named input.wav and save result to clean_audio.wav
    reduce_noise_file("input.wav")
