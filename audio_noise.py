import librosa
import noisereduce as nr
import soundfile as sf
import numpy as np
import scipy.signal as sps


def reduce_noise_file(input_path: str, output_path: str) -> str:
    """Simple noise reduction — wrapper used by the GUI."""
    audio, sr = librosa.load(input_path, sr=None)

    if len(audio) == 0:
        raise ValueError("Empty audio file")

    # Use first 0.5s as noise profile if available, else stationary mode
    noise_profile = audio[:int(0.5 * sr)] if len(audio) > int(0.5 * sr) else None

    if noise_profile is not None and len(noise_profile) > 0:
        reduced = nr.reduce_noise(y=audio, sr=sr, y_noise=noise_profile, prop_decrease=0.9)
    else:
        reduced = nr.reduce_noise(y=audio, sr=sr, prop_decrease=0.9)

    if len(reduced) == 0:
        raise ValueError("Noise reduction produced empty audio")

    sf.write(output_path, reduced, sr)
    return output_path


def enhance_voice(input_path: str, output_path: str = "enhanced_audio.wav") -> str:
    """Full voice enhancement pipeline with filtering and normalization."""
    audio, sr = librosa.load(input_path, sr=None)

    noise_profile = audio[:int(0.5 * sr)]
    reduced = nr.reduce_noise(
        y=audio,
        sr=sr,
        y_noise=noise_profile,
        prop_decrease=0.9,
        time_mask_smooth_ms=50,
        freq_mask_smooth_hz=200
    )

    # Normalize RMS
    rms = np.sqrt(np.mean(reduced ** 2))
    target_rms = 0.03
    reduced = reduced * (target_rms / (rms + 1e-6))

    # Presence boost at 1kHz
    b, a = sps.iirpeak(1000 / (sr / 2), Q=1.5)
    reduced = sps.filtfilt(b, a, reduced)

    # High-pass filter to remove rumble
    b, a = sps.butter(4, 80 / (sr / 2), btype='highpass')
    reduced = sps.filtfilt(b, a, reduced)

    # De-esser
    b, a = sps.iirpeak(7000 / (sr / 2), Q=10)
    de_essed = reduced - 0.3 * sps.filtfilt(b, a, reduced)

    # Soft clip
    enhanced = np.tanh(de_essed * 2.5)

    sf.write(output_path, enhanced, sr)
    return output_path
