import numpy as np
import librosa


def apply_stft(audio):
    stft = librosa.stft(audio, n_fft=1024, hop_length=512)
    return np.abs(stft), np.angle(stft)


def quantize(magnitude, levels=256):
    """Uniform scalar quantization. Higher levels = better quality."""
    max_val = np.max(magnitude)
    if max_val == 0:
        return magnitude, 1.0

    step = max(max_val / levels, 1e-8)
    quantized = np.floor(magnitude / step).astype(np.float32)
    return quantized, step


def run_length_encode(data):
    """Run-length encoding on flattened quantized data."""
    flat = data.flatten().astype(int)
    encoded = []
    count = 1

    for i in range(1, len(flat)):
        if flat[i] == flat[i - 1]:
            count += 1
        else:
            encoded.append((int(flat[i - 1]), count))
            count = 1

    encoded.append((int(flat[-1]), count))
    return encoded


def run_length_decode(encoded, shape):
    """Decode run-length encoded data back to original shape."""
    flat = []
    for value, count in encoded:
        flat.extend([value] * count)
    return np.array(flat, dtype=np.float32).reshape(shape)


def dequantize(quantized, step):
    """Reconstruct magnitude from quantized values."""
    return (quantized + 0.5) * step  # mid-tread reconstruction


def reconstruct_audio(magnitude, phase, length=None):
    """Reconstruct time-domain audio from magnitude and phase."""
    stft = magnitude * np.exp(1j * phase)
    audio = librosa.istft(stft, hop_length=512, length=length)
    return audio


def calculate_snr(original, reconstructed):
    """Signal-to-Noise Ratio in dB. Higher is better."""
    min_len = min(len(original), len(reconstructed))
    original = original[:min_len]
    reconstructed = reconstructed[:min_len]

    noise = original - reconstructed
    signal_power = np.sum(original ** 2)
    noise_power = np.sum(noise ** 2)

    if noise_power == 0:
        return float("inf")
    if signal_power == 0:
        return float("-inf")

    return 10 * np.log10(signal_power / noise_power)
