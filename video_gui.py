"""
Video Compression GUI - Separate from audio GUI.
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading

from video_utils import load_video, save_video
from video_compression import VideoCompressor
from video_metrics import calculate_psnr, calculate_compression_ratio, estimate_compressed_size, get_original_size


class VideoCompressionApp:
    def __init__(self, master):
        self.master = master
        master.title("Video Compression Tool")
        master.geometry("1000x700")
        
        self.filepath = None
        self.original_frames = None
        self.compressed_frames = None
        self.fps = 30
        self.size = (640, 480)
        self.compressor = None
        self.current_frame_idx = 0
        self.is_playing = False
        
        # ── Top panel: file selection and controls ──
        top_frame = tk.Frame(master)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        self.select_btn = tk.Button(top_frame, text="Select Video", width=15, command=self.select_video)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        self.file_label = tk.Label(top_frame, text="No video selected", fg="gray")
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # ── Middle panel: compression controls ──
        control_frame = tk.Frame(master)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(control_frame, text="I-frame Interval:").pack(side=tk.LEFT, padx=5)
        self.iframe_var = tk.IntVar(value=10)
        self.iframe_spin = tk.Spinbox(control_frame, from_=1, to=30, textvariable=self.iframe_var, width=5)
        self.iframe_spin.pack(side=tk.LEFT, padx=5)
        
        tk.Label(control_frame, text="Quality (1-100):").pack(side=tk.LEFT, padx=5)
        self.quality_var = tk.IntVar(value=50)
        self.quality_spin = tk.Spinbox(control_frame, from_=1, to=100, textvariable=self.quality_var, width=5)
        self.quality_spin.pack(side=tk.LEFT, padx=5)
        
        self.compress_btn = tk.Button(control_frame, text="Compress Video", width=15, 
                                      command=self.compress_video, state=tk.DISABLED)
        self.compress_btn.pack(side=tk.LEFT, padx=10)
        
        self.save_btn = tk.Button(control_frame, text="Save Compressed", width=15, 
                                  command=self.save_compressed, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # ── Progress bar ──
        progress_frame = tk.Frame(master)
        progress_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        self.progress_label = tk.Label(progress_frame, text="Ready", fg="blue")
        self.progress_label.pack(side=tk.TOP, anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        # ── Video display area ──
        display_frame = tk.Frame(master)
        display_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Original video
        left_frame = tk.Frame(display_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(left_frame, text="Original Video", font=("Arial", 10, "bold")).pack()
        self.original_canvas = tk.Canvas(left_frame, bg="black", width=400, height=300)
        self.original_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Compressed video
        right_frame = tk.Frame(display_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(right_frame, text="Compressed Video", font=("Arial", 10, "bold")).pack()
        self.compressed_canvas = tk.Canvas(right_frame, bg="black", width=400, height=300)
        self.compressed_canvas.pack(fill=tk.BOTH, expand=True)
        
        # ── Playback controls ──
        playback_frame = tk.Frame(master)
        playback_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        self.play_btn = tk.Button(playback_frame, text="▶ Play", width=10, 
                                  command=self.toggle_playback, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        self.frame_slider = tk.Scale(playback_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                     command=self.on_slider_change, state=tk.DISABLED)
        self.frame_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.frame_label = tk.Label(playback_frame, text="Frame: 0/0")
        self.frame_label.pack(side=tk.LEFT, padx=5)
        
        # ── Metrics display ──
        metrics_frame = tk.Frame(master)
        metrics_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.metrics_label = tk.Label(metrics_frame, text="", justify=tk.LEFT, fg="darkgreen")
        self.metrics_label.pack(side=tk.LEFT)
    
    def select_video(self):
        """Select video file."""
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4;*.avi;*.mov;*.mkv")]
        )
        if not path:
            return
        
        try:
            self.filepath = path
            self.original_frames, self.fps, self.size = load_video(path)
            
            short_name = path.split("/")[-1].split("\\")[-1]
            self.file_label.config(text=f"{short_name} ({len(self.original_frames)} frames)", fg="black")
            
            self.compress_btn.config(state=tk.NORMAL)
            self.play_btn.config(state=tk.NORMAL)
            self.frame_slider.config(state=tk.NORMAL, to=len(self.original_frames)-1)
            
            self.current_frame_idx = 0
            self.display_frame(0)
            
            messagebox.showinfo("Success", f"Loaded {len(self.original_frames)} frames at {self.fps:.1f} fps")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video: {str(e)}")
    
    def compress_video(self):
        """Compress video in background thread."""
        if self.original_frames is None:
            return
        
        self.compress_btn.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Starting compression...")
        
        def compress_thread():
            try:
                i_interval = self.iframe_var.get()
                quality = self.quality_var.get()
                
                self.compressor = VideoCompressor(i_frame_interval=i_interval, quality=quality)
                
                # Compress
                self.compressor.compress_frames(self.original_frames, progress_callback=self.update_progress)
                
                # Decompress
                self.master.after(0, lambda: self.progress_label.config(text="Decompressing..."))
                self.compressed_frames = self.compressor.decompress_frames(progress_callback=self.update_progress)
                
                # Calculate metrics
                self.master.after(0, self.show_metrics)
                self.master.after(0, lambda: self.save_btn.config(state=tk.NORMAL))
                self.master.after(0, lambda: self.compress_btn.config(state=tk.NORMAL))
                self.master.after(0, lambda: self.progress_label.config(text="Compression complete!"))
                
                # Display first frame
                self.master.after(0, lambda: self.display_frame(self.current_frame_idx))
                
            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Error", f"Compression failed: {str(e)}"))
                self.master.after(0, lambda: self.compress_btn.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=compress_thread, daemon=True)
        thread.start()
    
    def update_progress(self, current, total, stage):
        """Update progress bar and label."""
        progress = (current / total) * 100
        self.master.after(0, lambda: self.progress_bar.config(value=progress))
        self.master.after(0, lambda: self.progress_label.config(text=stage))
    
    def show_metrics(self):
        """Calculate and display compression metrics."""
        if self.original_frames is None or self.compressed_frames is None:
            return
        
        psnr = calculate_psnr(self.original_frames, self.compressed_frames)
        
        orig_size = get_original_size(self.original_frames)
        comp_size = estimate_compressed_size(self.compressor.compressed_data)
        ratio = calculate_compression_ratio(orig_size, comp_size)
        
        metrics_text = (f"PSNR: {psnr:.2f} dB  |  "
                       f"Original: {orig_size/(1024*1024):.2f} MB  |  "
                       f"Compressed: {comp_size/(1024*1024):.2f} MB  |  "
                       f"Ratio: {ratio:.2f}x")
        
        self.metrics_label.config(text=metrics_text)
    
    def display_frame(self, frame_idx):
        """Display frame on both canvases."""
        if self.original_frames is None:
            return
        
        frame_idx = max(0, min(frame_idx, len(self.original_frames) - 1))
        self.current_frame_idx = frame_idx
        
        # Display original
        orig_frame = cv2.cvtColor(self.original_frames[frame_idx], cv2.COLOR_BGR2RGB)
        self.show_on_canvas(self.original_canvas, orig_frame)
        
        # Display compressed if available
        if self.compressed_frames is not None:
            comp_frame = cv2.cvtColor(self.compressed_frames[frame_idx], cv2.COLOR_BGR2RGB)
            self.show_on_canvas(self.compressed_canvas, comp_frame)
        
        self.frame_label.config(text=f"Frame: {frame_idx+1}/{len(self.original_frames)}")
        self.frame_slider.set(frame_idx)
    
    def show_on_canvas(self, canvas, frame):
        """Display frame on canvas."""
        # Resize to fit canvas
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width, canvas_height = 400, 300
        
        h, w = frame.shape[:2]
        scale = min(canvas_width / w, canvas_height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        resized = cv2.resize(frame, (new_w, new_h))
        img = Image.fromarray(resized)
        photo = ImageTk.PhotoImage(image=img)
        
        canvas.delete("all")
        canvas.create_image(canvas_width//2, canvas_height//2, image=photo)
        canvas.image = photo  # Keep reference
    
    def toggle_playback(self):
        """Toggle video playback."""
        if self.original_frames is None:
            return
        
        self.is_playing = not self.is_playing
        
        if self.is_playing:
            self.play_btn.config(text="⏸ Pause")
            self.play_video()
        else:
            self.play_btn.config(text="▶ Play")
    
    def play_video(self):
        """Play video frames."""
        if not self.is_playing or self.original_frames is None:
            return
        
        self.current_frame_idx += 1
        
        if self.current_frame_idx >= len(self.original_frames):
            self.current_frame_idx = 0
        
        self.display_frame(self.current_frame_idx)
        
        delay = int(1000 / self.fps)
        self.master.after(delay, self.play_video)
    
    def on_slider_change(self, value):
        """Handle slider change."""
        if not self.is_playing:
            self.display_frame(int(value))
    
    def save_compressed(self):
        """Save compressed video."""
        if self.compressed_frames is None:
            return
        
        output = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("AVI files", "*.avi")]
        )
        
        if not output:
            return
        
        try:
            save_video(output, self.compressed_frames, self.fps, self.size)
            messagebox.showinfo("Success", f"Video saved to {output}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save video: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCompressionApp(root)
    root.mainloop()
