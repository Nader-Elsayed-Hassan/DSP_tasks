# Installation Guide

## Quick Setup

### For Audio Processing Only

```bash
pip install librosa soundfile noisereduce numpy scipy matplotlib
python gui.py
```

### For Video Compression Only

```bash
pip install opencv-python numpy Pillow
python video_gui.py
```

### For Both Audio and Video

```bash
# Install all dependencies
pip install librosa soundfile noisereduce numpy scipy matplotlib opencv-python Pillow

# Run audio GUI
python gui.py

# Run video GUI (separate window)
python video_gui.py
```

## Detailed Installation

### Step 1: Check Python Version

```bash
python --version
```

You need **Python 3.8 or higher**.

### Step 2: Install Audio Dependencies

```bash
pip install librosa soundfile noisereduce numpy scipy matplotlib
```

**What each library does:**
- `librosa` - Audio loading and STFT operations
- `soundfile` - Save processed audio files
- `noisereduce` - Noise reduction algorithm
- `numpy` - Array operations
- `scipy` - Digital filters
- `matplotlib` - Waveform visualization

### Step 3: Install Video Dependencies

```bash
pip install opencv-python numpy Pillow
```

**What each library does:**
- `opencv-python` - Video I/O and processing
- `numpy` - Array operations (already installed if you did audio)
- `Pillow` - Image display in GUI

### Step 4: Verify Installation

#### Test Audio System

```bash
python gui.py
```

You should see the audio processing GUI window.

#### Test Video System

```bash
python test_video_compression.py
```

This will:
1. Create a test video
2. Compress it
3. Decompress it
4. Show metrics (PSNR, compression ratio)
5. Save the result

#### Run Video GUI

```bash
python video_gui.py
```

You should see the video compression GUI window.

## Troubleshooting

### Issue: "No module named 'cv2'"

**Solution:**
```bash
pip install opencv-python
```

### Issue: "No module named 'librosa'"

**Solution:**
```bash
pip install librosa
```

### Issue: "tkinter not found"

**Solution:**

**On Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**On macOS:**
```bash
brew install python-tk
```

**On Windows:**
Tkinter is included with Python by default. Reinstall Python from python.org if needed.

### Issue: Video GUI shows black screen

**Solution:**
Resize the window to trigger a canvas refresh, or restart the application.

### Issue: Compression is very slow

**Solution:**
- Use smaller videos (320x240 or 640x480)
- Increase I-frame interval (10 → 20)
- Reduce quality setting (50 → 30)

### Issue: "ImportError: DLL load failed" (Windows)

**Solution:**
Install Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

## System Requirements

### Minimum
- Python 3.8+
- 4 GB RAM
- 1 GB free disk space

### Recommended
- Python 3.9+
- 8 GB RAM
- 2 GB free disk space
- Multi-core CPU for faster compression

## Platform Support

| Platform | Audio | Video | Notes |
|----------|-------|-------|-------|
| Windows 10/11 | ✅ | ✅ | Fully supported |
| macOS 10.15+ | ✅ | ✅ | Fully supported |
| Linux (Ubuntu 20.04+) | ✅ | ✅ | May need python3-tk |

## Optional: Virtual Environment

It's recommended to use a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements_video.txt
pip install librosa soundfile noisereduce scipy matplotlib

# Run applications
python gui.py
python video_gui.py
```

## Uninstallation

```bash
pip uninstall librosa soundfile noisereduce numpy scipy matplotlib opencv-python Pillow
```

## Getting Help

If you encounter issues:

1. Check this troubleshooting guide
2. Verify all dependencies are installed: `pip list`
3. Check Python version: `python --version`
4. Try running the test script: `python test_video_compression.py`

## Next Steps

After installation:

1. **Audio Processing**: Read the main [README.md](README.md)
2. **Video Compression**: Read [VIDEO_README.md](VIDEO_README.md)
3. **Test the system**: Run `python test_video_compression.py`
4. **Try the GUIs**: Run `python gui.py` and `python video_gui.py`
