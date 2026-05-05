import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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

BG          = "#1e1e2e"
SIDEBAR_BG  = "#181825"
CARD_BG     = "#313244"
ACCENT      = "#cba6f7"
ACCENT2     = "#89b4fa"
SUCCESS     = "#a6e3a1"
WARNING     = "#fab387"
TEXT        = "#cdd6f4"
SUBTEXT     = "#6c7086"
PLOT_BG     = "#1e1e2e"
PLOT_GRID   = "#313244"
BORDER      = "#45475a"


class ModernButton(tk.Frame):
    def __init__(self, parent, text, command, state=tk.NORMAL, icon="", **kwargs):
        super().__init__(parent, bg=SIDEBAR_BG, cursor="hand2")
        self._command = command
        self._enabled = state == tk.NORMAL

        self._btn = tk.Label(
            self,
            text=f"  {icon}  {text}" if icon else f"  {text}",
            bg=CARD_BG if self._enabled else SIDEBAR_BG,
            fg=TEXT if self._enabled else SUBTEXT,
            font=("Segoe UI", 10, "bold"),
            padx=12, pady=10,
            anchor="w",
            cursor="hand2",
            relief=tk.FLAT,
            width=22
        )
        self._btn.pack(fill=tk.X)

        self._btn.bind("<Enter>", self._on_enter)
        self._btn.bind("<Leave>", self._on_leave)
        self._btn.bind("<Button-1>", self._on_click)

    def _on_enter(self, e):
        if self._enabled:
            self._btn.config(bg=ACCENT, fg="#1e1e2e")

    def _on_leave(self, e):
        if self._enabled:
            self._btn.config(bg=CARD_BG, fg=TEXT)
        else:
            self._btn.config(bg=SIDEBAR_BG, fg=SUBTEXT)

    def _on_click(self, e):
        if self._enabled:
            self._command()

    def config(self, **kwargs):
        if "state" in kwargs:
            self._enabled = kwargs["state"] == tk.NORMAL
            if self._enabled:
                self._btn.config(bg=CARD_BG, fg=TEXT)
            else:
                self._btn.config(bg=SIDEBAR_BG, fg=SUBTEXT)


class AudioApp:
    def __init__(self, master):
        self.master = master
        master.title("Audio DSP Studio")
        master.geometry("1050x640")
        master.configure(bg=BG)
        master.resizable(True, True)

        self.filepath = None
        self._build_ui()

    def _build_ui(self):
        sidebar = tk.Frame(self.master, bg=SIDEBAR_BG, width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        title_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(24, 4))

        tk.Label(title_frame, text="🎵", bg=SIDEBAR_BG, fg=ACCENT,
                 font=("Segoe UI", 22)).pack(anchor="w")
        tk.Label(title_frame, text="Audio DSP", bg=SIDEBAR_BG, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(title_frame, text="Studio", bg=SIDEBAR_BG, fg=ACCENT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill=tk.X, padx=16, pady=16)

        tk.Label(sidebar, text="ACTIONS", bg=SIDEBAR_BG, fg=SUBTEXT,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(0, 8))

        self.select_btn = ModernButton(sidebar, "Select Audio", self.select_file, icon="📂")
        self.select_btn.pack(fill=tk.X, padx=10, pady=3)

        self.noise_btn = ModernButton(sidebar, "Remove Noise", self.remove_noise,
                                      state=tk.DISABLED, icon="🔇")
        self.noise_btn.pack(fill=tk.X, padx=10, pady=3)

        self.silence_btn = ModernButton(sidebar, "Remove Silence", self.remove_silence,
                                        state=tk.DISABLED, icon="✂️")
        self.silence_btn.pack(fill=tk.X, padx=10, pady=3)

        self.compress_btn = ModernButton(sidebar, "Compress Audio", self.compress_audio,
                                         state=tk.DISABLED, icon="📦")
        self.compress_btn.pack(fill=tk.X, padx=10, pady=3)

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill=tk.X, padx=16, pady=16)

        tk.Label(sidebar, text="FILE", bg=SIDEBAR_BG, fg=SUBTEXT,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(0, 4))

        self.file_label = tk.Label(sidebar, text="No file selected", wraplength=180,
                                   justify=tk.LEFT, fg=SUBTEXT, bg=SIDEBAR_BG,
                                   font=("Segoe UI", 9))
        self.file_label.pack(anchor="w", padx=16)

        main_area = tk.Frame(self.master, bg=BG)
        main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        header = tk.Frame(main_area, bg=BG, height=56)
        header.pack(fill=tk.X, padx=24, pady=(20, 0))
        header.pack_propagate(False)

        tk.Label(header, text="Waveform Viewer", bg=BG, fg=TEXT,
                 font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT, anchor="w")

        self.status_dot = tk.Label(header, text="●", bg=BG, fg=SUBTEXT,
                                   font=("Segoe UI", 10))
        self.status_dot.pack(side=tk.RIGHT, anchor="e", padx=(0, 4))
        self.status_label = tk.Label(header, text="Idle", bg=BG, fg=SUBTEXT,
                                     font=("Segoe UI", 9))
        self.status_label.pack(side=tk.RIGHT, anchor="e")

        plot_card = tk.Frame(main_area, bg=CARD_BG, bd=0,
                             highlightbackground=BORDER, highlightthickness=1)
        plot_card.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        self.fig, self.axes = plt.subplots(2, 1, figsize=(8, 5.2))
        self.fig.patch.set_facecolor(CARD_BG)
        self.fig.subplots_adjust(hspace=0.45)
        self._clear_plots("Select an audio file to see its waveform.")

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_card)
        self.canvas.get_tk_widget().configure(bg=CARD_BG, highlightthickness=0)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    def _set_status(self, text, color=SUBTEXT):
        self.status_label.config(text=text, fg=color)
        self.status_dot.config(fg=color)

    def _style_ax(self, ax):
        ax.set_facecolor(PLOT_BG)
        ax.tick_params(colors=TEXT, labelsize=7)
        ax.xaxis.label.set_color(SUBTEXT)
        ax.yaxis.label.set_color(SUBTEXT)
        ax.title.set_color(TEXT)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)
        ax.grid(True, color=PLOT_GRID, linewidth=0.5, linestyle="--", alpha=0.6)

    def _clear_plots(self, message=""):
        for ax in self.axes:
            ax.clear()
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_facecolor(PLOT_BG)
            for spine in ax.spines.values():
                spine.set_edgecolor(BORDER)
        if message:
            self.axes[0].text(0.5, 0.5, message,
                              ha="center", va="center",
                              transform=self.axes[0].transAxes,
                              fontsize=11, color=SUBTEXT,
                              fontfamily="Segoe UI")
        self.fig.tight_layout()

    def _plot_waveform(self, ax, audio, sr, title, color=ACCENT):
        ax.clear()
        times = np.linspace(0, len(audio) / sr, num=len(audio))
        ax.plot(times, audio, color=color, linewidth=0.7, alpha=0.9)
        ax.fill_between(times, audio, alpha=0.08, color=color)
        ax.set_title(title, fontsize=10, pad=8, fontfamily="Segoe UI")
        ax.set_xlabel("Time (s)", fontsize=8)
        ax.set_ylabel("Amplitude", fontsize=8)
        self._style_ax(ax)

    def _refresh_canvas(self):
        self.fig.tight_layout()
        self.canvas.draw()

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

        short = path.split("/")[-1]
        self.file_label.config(text=short, fg=ACCENT)
        self._set_status("File loaded", ACCENT)

        try:
            audio, sr = librosa.load(path, sr=None)
            self._plot_waveform(self.axes[0], audio, sr, "Original Waveform", color=ACCENT)
            self.axes[1].clear()
            self.axes[1].set_xticks([])
            self.axes[1].set_yticks([])
            self.axes[1].set_facecolor(PLOT_BG)
            for spine in self.axes[1].spines.values():
                spine.set_edgecolor(BORDER)
            self.axes[1].text(0.5, 0.5, "Run an operation to see before / after comparison",
                              ha="center", va="center",
                              transform=self.axes[1].transAxes,
                              fontsize=10, color=SUBTEXT)
            self._refresh_canvas()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def remove_noise(self):
        output = filedialog.asksaveasfilename(defaultextension=".wav",
                                              filetypes=[("WAV files", "*.wav")])
        if not output:
            return
        try:
            self._set_status("Processing…", WARNING)
            self.master.update()

            audio_before, sr = librosa.load(self.filepath, sr=None)
            reduce_noise_file(self.filepath, output)
            audio_after, sr_after = librosa.load(output, sr=None)

            self._plot_waveform(self.axes[0], audio_before, sr,
                                "Before — Noise Removal", color=ACCENT2)
            self._plot_waveform(self.axes[1], audio_after, sr_after,
                                "After — Noise Removal", color=SUCCESS)
            self._refresh_canvas()
            self._set_status("Noise removed", SUCCESS)
            messagebox.showinfo("Done", "Noise removed successfully")
        except Exception as e:
            self._set_status("Error", "#f38ba8")
            messagebox.showerror("Error", str(e))

    def remove_silence(self):
        output = filedialog.asksaveasfilename(defaultextension=".wav",
                                              filetypes=[("WAV files", "*.wav")])
        if not output:
            return
        try:
            self._set_status("Processing…", WARNING)
            self.master.update()

            audio_before, sr = librosa.load(self.filepath, sr=None)
            remove_silence_file(self.filepath, output)
            audio_after, sr_after = librosa.load(output, sr=None)

            self._plot_waveform(self.axes[0], audio_before, sr,
                                "Before — Silence Removal", color=ACCENT2)
            self._plot_waveform(self.axes[1], audio_after, sr_after,
                                "After — Silence Removal", color=WARNING)
            self._refresh_canvas()
            self._set_status("Silence removed", SUCCESS)
            messagebox.showinfo("Done", "Silence removed successfully")
        except Exception as e:
            self._set_status("Error", "#f38ba8")
            messagebox.showerror("Error", str(e))

    def compress_audio(self):
        try:
            self._set_status("Processing…", WARNING)
            self.master.update()

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
                                    "Before — Compression", color=ACCENT2)
                self._plot_waveform(self.axes[1], reconstructed, sr,
                                    "After — Compression (Reconstructed)", color=ACCENT)
                self._refresh_canvas()

            snr = calculate_snr(audio, reconstructed)
            self._set_status(f"SNR: {snr:.1f} dB", SUCCESS)
            messagebox.showinfo("Done", f"Compression finished\nSNR: {snr:.2f} dB")

        except Exception as e:
            self._set_status("Error", "#f38ba8")
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()
