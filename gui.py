import tkinter as tk
from tkinter import filedialog, messagebox

# library imports may fail if packages are not installed; we will notify the user
try:
    import librosa
    import librosa.display
    import matplotlib.pyplot as plt
except ModuleNotFoundError as e:
    missing = e.name
    tk.Tk().withdraw()  # hide main window
    messagebox.showerror(
        "Missing Dependency",
        f"The required Python package '{missing}' is not installed.\n"
        "Please install dependencies with:\n"
        "pip install librosa noisereduce soundfile matplotlib"
    )
    raise

from noise import reduce_noise_file
from silence import remove_silence_file


class AudioApp:
    def __init__(self, master):
        self.master = master
        master.title("Audio Cleaner & Viewer")
        master.geometry("300x220")

        self.filepath = None

        self.select_btn = tk.Button(master, text="Select Audio", width=25, command=self.select_file)
        self.select_btn.pack(pady=5)

        self.noise_btn = tk.Button(master, text="Remove Noise", width=25, command=self.remove_noise, state=tk.DISABLED)
        self.noise_btn.pack(pady=5)

        self.silence_btn = tk.Button(master, text="Remove Silence", width=25, command=self.remove_silence, state=tk.DISABLED)
        self.silence_btn.pack(pady=5)

        self.wave_btn = tk.Button(master, text="Show Waveform", width=25, command=self.show_waveform, state=tk.DISABLED)
        self.wave_btn.pack(pady=5)

    def select_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Audio files", "*.wav;*.mp3;*.flac;*.ogg;*.m4a")]
        )
        if path:
            self.filepath = path
            self.noise_btn.config(state=tk.NORMAL)
            self.silence_btn.config(state=tk.NORMAL)
            self.wave_btn.config(state=tk.NORMAL)
            messagebox.showinfo("Selected", f"Selected file:\n{path}")

    def remove_noise(self):
        if not self.filepath:
            return
        output = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav")],
            title="Save noise reduced file as"
        )
        if output:
            try:
                reduce_noise_file(self.filepath, output)
                messagebox.showinfo("Done", f"Noise reduced\nSaved to {output}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove noise:\n{e}")

    def remove_silence(self):
        if not self.filepath:
            return
        output = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav")],
            title="Save silence removed file as"
        )
        if output:
            try:
                remove_silence_file(self.filepath, output)
                messagebox.showinfo("Done", f"Silence removed\nSaved to {output}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove silence:\n{e}")

    def show_waveform(self):
        if not self.filepath:
            return
        try:
            audio, sr = librosa.load(self.filepath, sr=None)
            plt.figure(figsize=(8, 3))
            librosa.display.waveshow(audio, sr=sr)
            plt.title("Waveform")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Error", f"Unable to load waveform:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()
