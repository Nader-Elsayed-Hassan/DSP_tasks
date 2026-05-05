"""
Video quality metrics: PSNR and compression ratio.
"""
import numpy as np


def calculate_psnr(original_frames, compressed_frames):
    """
    Calculate Peak Signal-to-Noise Ratio (PSNR).
    
    Args:
        original_frames: list of original BGR frames
        compressed_frames: list of compressed/decompressed BGR frames
    
    Returns:
        average PSNR in dB
    """
    if len(original_frames) != len(compressed_frames):
        raise ValueError("Frame count mismatch")
    
    psnr_values = []
    
    for orig, comp in zip(original_frames, compressed_frames):
        mse = np.mean((orig.astype(np.float64) - comp.astype(np.float64)) ** 2)
        
        if mse == 0:
            psnr = float('inf')
        else:
            max_pixel = 255.0
            psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
        
        psnr_values.append(psnr)
    
    return np.mean(psnr_values)


def calculate_compression_ratio(original_size, compressed_size):
    """
    Calculate compression ratio.
    
    Args:
        original_size: size in bytes
        compressed_size: size in bytes
    
    Returns:
        compression ratio
    """
    return original_size / compressed_size if compressed_size > 0 else 0


def estimate_compressed_size(compressed_data):
    """
    Estimate compressed data size in bytes (actual bit-packed storage).
    
    Args:
        compressed_data: list of compressed frame dictionaries
    
    Returns:
        estimated size in bytes
    """
    total_size = 0
    
    for frame_data in compressed_data:
        if frame_data['type'] == 'I':
            # I-frame: packed bytes for Y, U, V
            total_size += len(frame_data['Y_bytes'])
            total_size += len(frame_data['U_bytes'])
            total_size += len(frame_data['V_bytes'])
            
            # Huffman code tables (estimate)
            total_size += len(str(frame_data['Y_codes']))
            total_size += len(str(frame_data['U_codes']))
            total_size += len(str(frame_data['V_codes']))
            
            # Quantization matrices
            total_size += frame_data['Q_luma'].nbytes
            total_size += frame_data['Q_chroma'].nbytes
            
        else:
            # P-frame: motion vectors, residual, U/V diffs (all packed)
            total_size += len(frame_data['mv_bytes'])
            total_size += len(frame_data['residual_bytes'])
            total_size += len(frame_data['U_bytes'])
            total_size += len(frame_data['V_bytes'])
            
            # Huffman code tables (estimate)
            total_size += len(str(frame_data['mv_codes']))
            total_size += len(str(frame_data['residual_codes']))
            total_size += len(str(frame_data['U_codes']))
            total_size += len(str(frame_data['V_codes']))
            
            # Quantization matrix
            total_size += frame_data['Q_luma'].nbytes
    
    return total_size


def get_original_size(frames):
    """Get original video size in bytes."""
    total_size = sum(frame.nbytes for frame in frames)
    return total_size
