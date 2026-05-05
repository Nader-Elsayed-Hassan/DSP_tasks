"""
Video utility functions for loading and color space conversion.
"""
import cv2
import numpy as np


def load_video(filepath):
    """
    Load video file and extract frames.
    
    Returns:
        frames: list of BGR frames
        fps: frames per second
        size: (width, height)
    """
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {filepath}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    
    cap.release()
    return frames, fps, (width, height)


def bgr_to_yuv(frame):
    """Convert BGR frame to YUV color space."""
    return cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)


def yuv_to_bgr(frame):
    """Convert YUV frame back to BGR color space."""
    return cv2.cvtColor(frame, cv2.COLOR_YUV2BGR)


def subsample_chroma_420(yuv_frame):
    """
    Convert YUV 4:4:4 to YUV 4:2:0 (chroma subsampling).
    U and V channels are downsampled to half resolution.
    
    Args:
        yuv_frame: YUV frame with full resolution U and V
    
    Returns:
        Y (full res), U (half res), V (half res)
    """
    Y = yuv_frame[:, :, 0]
    U = yuv_frame[:, :, 1]
    V = yuv_frame[:, :, 2]
    
    # Downsample U and V by 2x2 (average 2x2 blocks)
    U_sub = cv2.resize(U, (U.shape[1] // 2, U.shape[0] // 2), interpolation=cv2.INTER_LINEAR)
    V_sub = cv2.resize(V, (V.shape[1] // 2, V.shape[0] // 2), interpolation=cv2.INTER_LINEAR)
    
    return Y, U_sub, V_sub


def upsample_chroma_420(Y, U_sub, V_sub):
    """
    Convert YUV 4:2:0 back to YUV 4:4:4.
    Upsample U and V to match Y resolution.
    
    Args:
        Y: full resolution Y channel
        U_sub: half resolution U channel
        V_sub: half resolution V channel
    
    Returns:
        YUV frame with full resolution
    """
    h, w = Y.shape
    
    # Upsample U and V to full resolution
    U = cv2.resize(U_sub, (w, h), interpolation=cv2.INTER_LINEAR)
    V = cv2.resize(V_sub, (w, h), interpolation=cv2.INTER_LINEAR)
    
    return np.stack([Y, U, V], axis=2)


def save_video(filepath, frames, fps, size):
    """
    Save frames to video file.
    
    Args:
        filepath: output video path
        frames: list of BGR frames
        fps: frames per second
        size: (width, height)
    """
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filepath, fourcc, fps, size)
    
    for frame in frames:
        out.write(frame)
    
    out.release()


def frames_to_yuv(frames):
    """Convert list of BGR frames to YUV."""
    return [bgr_to_yuv(frame) for frame in frames]


def frames_to_bgr(yuv_frames):
    """Convert list of YUV frames to BGR."""
    return [yuv_to_bgr(frame) for frame in yuv_frames]
