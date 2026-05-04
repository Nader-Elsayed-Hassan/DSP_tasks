import tkinter as tk
from tkinter import filedialog, messagebox

import librosa
import librosa.display
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
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
        master.geometry("900x560")

        self.filepath = None

        # ── Left panel: buttons ──────────────────────────────────────────────
        btn_frame = tk.Frame(master)
        btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.select_btn = tk.Button(btn_frame, text="Select Audio", width=22, command=self.select_file)
        self.select_btn.pack(pady=5)

        self.noise_btn = tk.Button(btn_frame, text="Remove Noise", width=22, command=self.remove_noise, state=tk.DISABLED)
        self.noise_btn.pack(pady=5)

        self.silence_btn = tk.Button(btn_frame, text="Remove Silence", width=22, command=self.remove_silence, state=tk.DISABLED)
        self.silence_btn.pack(pady=5)

        self.compress_btn = tk.Button(btn_frame, text="Compress Audio", width=22, command=self.compress_audio, state=tk.DISABLED)
        self.compress_btn.pack(pady=5)

        self.file_label = tk.Label(btn_frame, text="No file selected", wraplength=160,
                                   justify=tk.LEFT, fg="gray")
        self.file_label.pack(pady=10)

        # ── Right panel: matplotlib canvas ───────────────────────────────────
        plot_frame = tk.Frame(master)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=10)

        self.fig, self.axes = plt.subplots(2, 1, figsize=(7, 5))
        self.fig.patch.set_facecolor("#f0f0f0")
        self._clear_plots("Select an audio file to see its waveform.")

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _clear_plots(self, message=""):
        """Reset both axes to a blank state with an optional message."""
        for ax in self.axes:
            ax.clear()
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_facecolor("#f8f8f8")
        if message:
            self.axes[0].text(0.5, 0.5, message,
                              ha="center", va="center",
                              transform=self.axes[0].transAxes,
                              fontsize=11, color="gray")
        self.fig.tight_layout()

    def _plot_waveform(self, ax, audio, sr, title, color="steelblue"):
        """Draw a waveform on the given axes."""
        ax.clear()
        times = np.linspace(0, len(audio) / sr, num=len(audio))
        ax.plot(times, audio, color=color, linewidth=0.6)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("Time (s)", fontsize=8)
        ax.set_ylabel("Amplitude", fontsize=8)
        ax.set_facecolor("#f8f8f8")
        ax.tick_params(labelsize=7)

    def _refresh_canvas(self):
        self.fig.tight_layout()
        self.canvas.draw()

    # ── button callbacks ─────────────────────────────────────────────────────

    def select_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Audio files", "*.wav;*.mp3;*.flac;*.ogg;*.m4a")]
        )
        if not path:
            return

        self.filepath = path
        self.noise_btn.config(state=tk.NORMAL)
        self.silence_btn.config(state=tk.NORMAL)
        self.compress_btn.config(state=tk.NORMAL)

        # Show filename (truncated) in label
        short = path.split("/")[-1]
        self.file_label.config(text=short, fg="black")

        # Plot original waveform in top axes; clear bottom
        try:
            audio, sr = librosa.load(path, sr=None)
            self._plot_waveform(self.axes[0], audio, sr, "Original Waveform", color="steelblue")
            self.axes[1].clear()
            self.axes[1].set_xticks([])
            self.axes[1].set_yticks([])
            self.axes[1].set_facecolor("#f8f8f8")
            self.axes[1].text(0.5, 0.5, "Run 'Remove Noise' to see before/after comparison",
                              ha="center", va="center",
                              transform=self.axes[1].transAxes,
                              fontsize=10, color="gray")
            self._refresh_canvas()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def remove_noise(self):
        output = filedialog.asksaveasfilename(defaultextension=".wav",
                                              filetypes=[("WAV files", "*.wav")])
        if not output:
            return
        try:
            # Load original for plotting
            audio_before, sr = librosa.load(self.filepath, sr=None)

            # Run noise reduction
            reduce_noise_file(self.filepath, output)

            # Load processed audio
            audio_after, sr_after = librosa.load(output, sr=None)

            # Plot before (top) and after (bottom)
            self._plot_waveform(self.axes[0], audio_before, sr,
                                "Before Noise Removal", color="steelblue")
            self._plot_waveform(self.axes[1], audio_after, sr_after,
                                "After Noise Removal", color="seagreen")
            self._refresh_canvas()

            messagebox.showinfo("Done", "Noise removed successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def remove_silence(self):
        output = filedialog.asksaveasfilename(defaultextension=".wav",
                                              filetypes=[("WAV files", "*.wav")])
        if not output:
            return
        try:
            audio_before, sr = librosa.load(self.filepath, sr=None)

            remove_silence_file(self.filepath, output)

            audio_after, sr_after = librosa.load(output, sr=None)

            self._plot_waveform(self.axes[0], audio_before, sr,
                                "Before Silence Removal", color="steelblue")
            self._plot_waveform(self.axes[1], audio_after, sr_after,
                                "After Silence Removal", color="darkorange")
            self._refresh_canvas()

            messagebox.showinfo("Done", "Silence removed successfully")
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

            output = filedialog.asksaveasfilename(defaultextension=".wav",
                                                  filetypes=[("WAV files", "*.wav")])
            if output:
                sf.write(output, reconstructed, sr)

                self._plot_waveform(self.axes[0], audio, sr,
                                    "Before Compression", color="steelblue")
                self._plot_waveform(self.axes[1], reconstructed, sr,
                                    "After Compression (Reconstructed)", color="mediumpurple")
                self._refresh_canvas()

            snr = calculate_snr(audio, reconstructed)
            messagebox.showinfo("Done", f"Compression finished\nSNR: {snr:.2f} dB")

        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()
