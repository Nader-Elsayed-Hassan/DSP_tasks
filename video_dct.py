"""
DCT (Discrete Cosine Transform) operations for video compression.
"""
import numpy as np
import cv2


def apply_dct_8x8(channel):
    """
    Apply DCT on 8x8 blocks of a single channel (vectorized).
    
    Args:
        channel: 2D numpy array (single channel, e.g., Y, U, or V)
    
    Returns:
        dct_blocks: DCT coefficients
    """
    h, w = channel.shape
    # Pad to make dimensions divisible by 8
    pad_h = (8 - h % 8) % 8
    pad_w = (8 - w % 8) % 8
    padded = np.pad(channel, ((0, pad_h), (0, pad_w)), mode='constant').astype(np.float32)
    
    # Get dimensions
    h_padded, w_padded = padded.shape
    n_blocks_h = h_padded // 8
    n_blocks_w = w_padded // 8
    
    # Reshape into blocks: (n_blocks_h, n_blocks_w, 8, 8)
    blocks = padded.reshape(n_blocks_h, 8, n_blocks_w, 8).transpose(0, 2, 1, 3)
    
    # Apply DCT to all blocks at once
    dct_blocks = np.zeros_like(blocks)
    for i in range(n_blocks_h):
        for j in range(n_blocks_w):
            dct_blocks[i, j] = cv2.dct(blocks[i, j])
    
    # Reshape back to original layout
    dct_result = dct_blocks.transpose(0, 2, 1, 3).reshape(h_padded, w_padded)
    
    return dct_result


def apply_idct_8x8(dct_channel, original_shape):
    """
    Apply inverse DCT on 8x8 blocks (vectorized).
    
    Args:
        dct_channel: DCT coefficients
        original_shape: (height, width) of original channel
    
    Returns:
        reconstructed channel
    """
    h_padded, w_padded = dct_channel.shape
    n_blocks_h = h_padded // 8
    n_blocks_w = w_padded // 8
    
    # Reshape into blocks: (n_blocks_h, n_blocks_w, 8, 8)
    blocks = dct_channel.reshape(n_blocks_h, 8, n_blocks_w, 8).transpose(0, 2, 1, 3)
    
    # Apply IDCT to all blocks
    idct_blocks = np.zeros_like(blocks)
    for i in range(n_blocks_h):
        for j in range(n_blocks_w):
            idct_blocks[i, j] = cv2.idct(blocks[i, j])
    
    # Reshape back to original layout
    reconstructed = idct_blocks.transpose(0, 2, 1, 3).reshape(h_padded, w_padded)
    
    # Remove padding
    h, w = original_shape
    return reconstructed[:h, :w]


def quantize_dct(dct_coeffs, quality=50, aggressive=True):
    """
    Quantize DCT coefficients using JPEG quantization matrix (vectorized).
    Aggressively zeros out high frequencies for better compression.
    
    Args:
        dct_coeffs: DCT coefficients
        quality: quality factor (1-100, higher = better quality)
        aggressive: if True, zero out high frequencies more aggressively
    
    Returns:
        quantized coefficients, quantization matrix
    """
    # Standard JPEG quantization matrix for luminance
    Q_luma = np.array([
        [16, 11, 10, 16, 24, 40, 51, 61],
        [12, 12, 14, 19, 26, 58, 60, 55],
        [14, 13, 16, 24, 40, 57, 69, 56],
        [14, 17, 22, 29, 51, 87, 80, 62],
        [18, 22, 37, 56, 68, 109, 103, 77],
        [24, 35, 55, 64, 81, 104, 113, 92],
        [49, 64, 78, 87, 103, 121, 120, 101],
        [72, 92, 95, 98, 112, 100, 103, 99]
    ], dtype=np.float32)
    
    # Scale quantization matrix based on quality
    if quality < 50:
        scale = 5000 / quality
    else:
        scale = 200 - 2 * quality
    
    Q_scaled = np.floor((Q_luma * scale + 50) / 100)
    Q_scaled[Q_scaled == 0] = 1
    
    # Aggressive high-frequency zeroing
    freq_mask = np.ones((8, 8), dtype=np.float32)
    if aggressive:
        if quality < 30:
            # Very aggressive - keep only 4x4 low frequencies
            freq_mask[4:, :] = 0
            freq_mask[:, 4:] = 0
        elif quality < 50:
            # Aggressive - keep 6x6
            freq_mask[6:, :] = 0
            freq_mask[:, 6:] = 0
        else:
            # Moderate - keep 7x7
            freq_mask[7:, :] = 0
            freq_mask[:, 7:] = 0
    
    # Vectorized quantization
    h, w = dct_coeffs.shape
    n_blocks_h = h // 8
    n_blocks_w = w // 8
    
    # Reshape into blocks
    blocks = dct_coeffs.reshape(n_blocks_h, 8, n_blocks_w, 8).transpose(0, 2, 1, 3)
    
    # Apply quantization and mask to all blocks at once
    Q_scaled_broadcast = Q_scaled[np.newaxis, np.newaxis, :, :]
    freq_mask_broadcast = freq_mask[np.newaxis, np.newaxis, :, :]
    
    quantized_blocks = np.round(blocks / Q_scaled_broadcast).astype(np.int16)
    
    if aggressive:
        quantized_blocks = quantized_blocks * freq_mask_broadcast.astype(np.int16)
    
    # Reshape back
    quantized = quantized_blocks.transpose(0, 2, 1, 3).reshape(h, w)
    
    return quantized, Q_scaled


def get_chroma_quantization_matrix(quality=50):
    """Get chrominance quantization matrix (more aggressive than luma)."""
    Q_chroma = np.array([
        [17, 18, 24, 47, 99, 99, 99, 99],
        [18, 21, 26, 66, 99, 99, 99, 99],
        [24, 26, 56, 99, 99, 99, 99, 99],
        [47, 66, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99]
    ], dtype=np.float32)
    
    if quality < 50:
        scale = 5000 / quality
    else:
        scale = 200 - 2 * quality
    
    Q_scaled = np.floor((Q_chroma * scale + 50) / 100)
    Q_scaled[Q_scaled == 0] = 1
    
    return Q_scaled


def dequantize_dct(quantized, Q_matrix):
    """Reverse quantization (vectorized)."""
    h, w = quantized.shape
    n_blocks_h = h // 8
    n_blocks_w = w // 8
    
    # Reshape into blocks
    blocks = quantized.reshape(n_blocks_h, 8, n_blocks_w, 8).transpose(0, 2, 1, 3)
    
    # Apply dequantization to all blocks at once
    Q_broadcast = Q_matrix[np.newaxis, np.newaxis, :, :]
    dequantized_blocks = blocks.astype(np.float32) * Q_broadcast
    
    # Reshape back
    dequantized = dequantized_blocks.transpose(0, 2, 1, 3).reshape(h, w)
    
    return dequantized
