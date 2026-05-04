import tkinter as tk
from tkinter import filedialog, messagebox

import librosa
import librosa.display
import matplotlib.pyplot as plt
import soundfile as sf

from audio_noise import reduce_noise_file
from audio_silence import remove_silence_file
from audio_compression import (
    apply_stft,
    quantize,
    run_length_encode,
    dequantize,
    reconstruct_audio,
    calculate_snr
)


class AudioApp:
    def __init__(self, master):
        self.master = master
        master.title("Audio Cleaner & Viewer")
        master.geometry("300x260")

        self.filepath = None

        self.select_btn = tk.Button(master, text="Select Audio", width=25, command=self.select_file)
        self.select_btn.pack(pady=5)

        self.noise_btn = tk.Button(master, text="Remove Noise", width=25, command=self.remove_noise, state=tk.DISABLED)
        self.noise_btn.pack(pady=5)

        self.silence_btn = tk.Button(master, text="Remove Silence", width=25, command=self.remove_silence, state=tk.DISABLED)
        self.silence_btn.pack(pady=5)

        self.wave_btn = tk.Button(master, text="Show Waveform", width=25, command=self.show_waveform, state=tk.DISABLED)
        self.wave_btn.pack(pady=5)

        self.compress_btn = tk.Button(master, text="Compress Audio", width=25, command=self.compress_audio, state=tk.DISABLED)
        self.compress_btn.pack(pady=5)

    def select_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Audio files", "*.wav;*.mp3;*.flac;*.ogg;*.m4a")]
        )
        if path:
            self.filepath = path
            self.noise_btn.config(state=tk.NORMAL)
            self.silence_btn.config(state=tk.NORMAL)
            self.wave_btn.config(state=tk.NORMAL)
            self.compress_btn.config(state=tk.NORMAL)
            messagebox.showinfo("Selected", f"Selected file:\n{path}")

    def remove_noise(self):
        output = filedialog.asksaveasfilename(defaultextension=".wav")
        if output:
            try:
                reduce_noise_file(self.filepath, output)
                messagebox.showinfo("Done", "Noise removed successfully")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def remove_silence(self):
        output = filedialog.asksaveasfilename(defaultextension=".wav")
        if output:
            try:
                remove_silence_file(self.filepath, output)
                messagebox.showinfo("Done", "Silence removed successfully")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def show_waveform(self):
        try:
            audio, sr = librosa.load(self.filepath, sr=None)
            plt.figure(figsize=(8, 3))
            librosa.display.waveshow(audio, sr=sr)
            plt.title("Waveform")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def compress_audio(self):
        try:
            audio, sr = librosa.load(self.filepath, sr=None)

            mag, phase = apply_stft(audio)
            q_mag, step = quantize(mag)

            _ = run_length_encode(q_mag)

            decoded_mag = dequantize(q_mag, step)
            reconstructed = reconstruct_audio(decoded_mag, phase, length=len(audio))

            output = filedialog.asksaveasfilename(defaultextension=".wav")
            if output:
                sf.write(output, reconstructed, sr)

            snr = calculate_snr(audio, reconstructed)
            messagebox.showinfo("Done", f"Compression finished\nSNR: {snr:.2f} dB")

        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()
