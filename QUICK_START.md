# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies

```bash
pip install opencv-python numpy Pillow
```

### Step 2: Test the System

```bash
python test_video_compression.py
```

This creates a test video, compresses it, and shows the results.

### Step 3: Run the GUI

```bash
python video_gui.py
```

## 📺 Using the Video Compression GUI

### 1. Load a Video

Click **"Select Video"** → Choose MP4, AVI, MOV, or MKV file

### 2. Configure Settings

- **I-frame Interval**: 10 (every 10th frame is an I-frame)
- **Quality**: 50 (1=lowest, 100=highest)

### 3. Compress

Click **"Compress Video"** → Watch the progress bar

### 4. View Results

- **Left panel**: Original video
- **Right panel**: Compressed video
- **Bottom**: PSNR and compression ratio

### 5. Playback

- Click **▶ Play** to watch both videos
- Use the **slider** to navigate frames
- Click **⏸ Pause** to stop

### 6. Save

Click **"Save Compressed"** → Choose output location

## 🎯 Quick Tips

### For Better Quality
- Increase **Quality** to 75-90
- Decrease **I-frame Interval** to 5

### For Smaller Files
- Decrease **Quality** to 20-40
- Increase **I-frame Interval** to 15-20

### For Faster Compression
- Use smaller videos (320x240 or 640x480)
- Increase **I-frame Interval**

## 📊 Understanding the Metrics

### PSNR (Peak Signal-to-Noise Ratio)
- **> 35 dB**: Excellent quality
- **30-35 dB**: Good quality
- **25-30 dB**: Acceptable quality
- **< 25 dB**: Poor quality

### Compression Ratio
- **2x**: Moderate compression
- **3-4x**: Good compression
- **5x+**: High compression

## 🎬 Video Compression Stages

Watch the progress label to see each stage:

1. **Compressing I-frame X/Y** - Full frame compression
2. **Compressing P-frame X/Y** - Motion-based compression
3. **Decompressing I-frame X/Y** - Reconstructing full frames
4. **Decompressing P-frame X/Y** - Reconstructing predicted frames

## 🔧 Troubleshooting

### Video won't load
- Check file format (MP4, AVI, MOV, MKV)
- Try a different video file
- Check file isn't corrupted

### Compression is slow
- Use smaller video resolution
- Increase I-frame interval
- Close other applications

### Black screen in canvas
- Resize the window
- Restart the application
- Check video loaded successfully

### Low PSNR
- Increase quality setting
- Decrease I-frame interval
- Use less compression

## 📁 File Locations

### Input
- Any MP4, AVI, MOV, or MKV file

### Output
- Saved wherever you choose
- Recommended: Same folder as input

### Test Files
- `test_video.mp4` - Generated test video
- `test_video_decompressed.mp4` - Compressed result

## 🎓 Learning Path

### Beginner
1. Run `test_video_compression.py`
2. Open `video_gui.py`
3. Load a small video (< 10 seconds)
4. Try different quality settings

### Intermediate
1. Read `VIDEO_README.md`
2. Experiment with I-frame intervals
3. Compare PSNR at different qualities
4. Try different video types

### Advanced
1. Read the source code
2. Modify compression parameters
3. Implement custom features
4. Optimize performance

## 📚 Documentation

- **README.md** - Main project overview
- **VIDEO_README.md** - Detailed video compression guide
- **INSTALL.md** - Installation instructions
- **PROJECT_SUMMARY.md** - Technical summary
- **QUICK_START.md** - This file

## 🎵 Audio Processing

This project also includes audio processing!

```bash
python gui.py
```

Features:
- Noise reduction
- Silence removal
- Audio compression
- Waveform visualization

## 💡 Example Workflow

### Compress a Video

```bash
# 1. Start the GUI
python video_gui.py

# 2. Click "Select Video"
# 3. Choose your video file
# 4. Set Quality to 50
# 5. Set I-frame Interval to 10
# 6. Click "Compress Video"
# 7. Wait for compression to complete
# 8. Click "Play" to compare
# 9. Click "Save Compressed" to export
```

### Test Different Settings

```bash
# High quality, large file
Quality: 80, I-frame: 5

# Balanced
Quality: 50, I-frame: 10

# High compression, smaller file
Quality: 30, I-frame: 20
```

## 🔍 What to Look For

### During Compression
- Progress bar moving smoothly
- Stage labels updating
- No error messages

### After Compression
- Both videos displayed
- Metrics shown at bottom
- Videos play synchronously

### Quality Check
- Compare original vs compressed
- Check PSNR value
- Look for visual artifacts
- Verify compression ratio

## ⚡ Performance Tips

### For Slow Computers
- Use 320x240 resolution
- Quality: 30-40
- I-frame interval: 15-20

### For Fast Computers
- Use 1280x720 resolution
- Quality: 60-80
- I-frame interval: 5-10

### For Best Quality
- Quality: 90-100
- I-frame interval: 3-5
- Accept slower compression

### For Smallest Files
- Quality: 20-30
- I-frame interval: 20-30
- Accept lower quality

## 🎉 You're Ready!

Start with `python video_gui.py` and experiment with different videos and settings.

For detailed information, see [VIDEO_README.md](VIDEO_README.md)
