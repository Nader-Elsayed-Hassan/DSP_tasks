"""
Test script for video compression system.
Creates a simple test video and compresses it.
"""
import numpy as np
import cv2
from video_utils import save_video, load_video
from video_compression import VideoCompressor
from video_metrics import calculate_psnr, calculate_compression_ratio, estimate_compressed_size, get_original_size


def create_test_video(filename="test_video.mp4", num_frames=30, width=320, height=240):
    """Create a simple test video with moving shapes."""
    print(f"Creating test video: {filename}")
    
    frames = []
    for i in range(num_frames):
        # Create frame with gradient background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :, 0] = (i * 255 // num_frames)  # Blue channel
        frame[:, :, 1] = 128  # Green channel
        frame[:, :, 2] = (255 - i * 255 // num_frames)  # Red channel
        
        # Add moving circle
        center_x = int(width * (i / num_frames))
        center_y = height // 2
        cv2.circle(frame, (center_x, center_y), 30, (255, 255, 255), -1)
        
        # Add moving rectangle
        rect_x = int(width * (1 - i / num_frames))
        cv2.rectangle(frame, (rect_x - 20, 50), (rect_x + 20, 100), (0, 255, 0), -1)
        
        frames.append(frame)
    
    save_video(filename, frames, fps=10, size=(width, height))
    print(f"✓ Created {num_frames} frames")
    return filename


def test_compression():
    """Test the video compression pipeline."""
    print("\n" + "="*60)
    print("VIDEO COMPRESSION TEST")
    print("="*60)
    
    # Create test video
    test_file = create_test_video()
    
    # Load video
    print("\n1. Loading video...")
    frames, fps, size = load_video(test_file)
    print(f"   ✓ Loaded {len(frames)} frames at {fps} fps, size {size}")
    
    # Compress video
    print("\n2. Compressing video...")
    compressor = VideoCompressor(i_frame_interval=10, quality=50)
    
    def progress_callback(current, total, stage):
        if current % 5 == 0 or current == total:
            print(f"   {stage} ({current}/{total})")
    
    compressed_data = compressor.compress_frames(frames, progress_callback)
    print(f"   ✓ Compressed {len(compressed_data)} frames")
    
    # Count frame types
    i_frames = sum(1 for f in compressed_data if f['type'] == 'I')
    p_frames = sum(1 for f in compressed_data if f['type'] == 'P')
    print(f"   ✓ I-frames: {i_frames}, P-frames: {p_frames}")
    
    # Decompress video
    print("\n3. Decompressing video...")
    decompressed_frames = compressor.decompress_frames(progress_callback)
    print(f"   ✓ Decompressed {len(decompressed_frames)} frames")
    
    # Calculate metrics
    print("\n4. Calculating metrics...")
    psnr = calculate_psnr(frames, decompressed_frames)
    orig_size = get_original_size(frames)
    comp_size = estimate_compressed_size(compressed_data)
    ratio = calculate_compression_ratio(orig_size, comp_size)
    
    print(f"   ✓ PSNR: {psnr:.2f} dB")
    print(f"   ✓ Original size: {orig_size / 1024:.2f} KB")
    print(f"   ✓ Compressed size: {comp_size / 1024:.2f} KB")
    print(f"   ✓ Compression ratio: {ratio:.2f}x")
    
    # Save decompressed video
    print("\n5. Saving decompressed video...")
    output_file = "test_video_decompressed.mp4"
    save_video(output_file, decompressed_frames, fps, size)
    print(f"   ✓ Saved to {output_file}")
    
    print("\n" + "="*60)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"\nYou can now compare:")
    print(f"  - Original: {test_file}")
    print(f"  - Decompressed: {output_file}")
    print(f"\nRun 'python video_gui.py' to use the GUI interface.")


if __name__ == "__main__":
    try:
        test_compression()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
