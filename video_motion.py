"""
Motion estimation and compensation for P-frames.
"""
import numpy as np
import cv2


def block_matching(ref_frame, curr_frame, block_size=16, search_range=2):
    """
    Perform block matching motion estimation.
    
    Args:
        ref_frame: reference frame (Y channel)
        curr_frame: current frame (Y channel)
        block_size: size of blocks for matching
        search_range: search window radius (default: 2 for faster compression)
    
    Returns:
        motion_vectors: (h/block_size, w/block_size, 2) array of motion vectors
        residual: difference between predicted and actual frame
    """
    h, w = curr_frame.shape
    mv_h = h // block_size
    mv_w = w // block_size
    
    motion_vectors = np.zeros((mv_h, mv_w, 2), dtype=np.int16)
    predicted_frame = np.zeros_like(curr_frame)
    
    for i in range(mv_h):
        for j in range(mv_w):
            y = i * block_size
            x = j * block_size
            
            curr_block = curr_frame[y:y+block_size, x:x+block_size]
            
            min_sad = float('inf')
            best_mv = (0, 0)
            
            # Search in reference frame
            for dy in range(-search_range, search_range + 1):
                for dx in range(-search_range, search_range + 1):
                    ref_y = y + dy
                    ref_x = x + dx
                    
                    # Check bounds
                    if (ref_y >= 0 and ref_y + block_size <= h and
                        ref_x >= 0 and ref_x + block_size <= w):
                        
                        ref_block = ref_frame[ref_y:ref_y+block_size, 
                                             ref_x:ref_x+block_size]
                        
                        # Calculate SAD (Sum of Absolute Differences)
                        sad = np.sum(np.abs(curr_block.astype(np.int16) - 
                                           ref_block.astype(np.int16)))
                        
                        if sad < min_sad:
                            min_sad = sad
                            best_mv = (dy, dx)
            
            motion_vectors[i, j] = best_mv
            
            # Build predicted frame
            ref_y = y + best_mv[0]
            ref_x = x + best_mv[1]
            if (ref_y >= 0 and ref_y + block_size <= h and
                ref_x >= 0 and ref_x + block_size <= w):
                predicted_frame[y:y+block_size, x:x+block_size] = \
                    ref_frame[ref_y:ref_y+block_size, ref_x:ref_x+block_size]
    
    # Calculate residual
    residual = curr_frame.astype(np.int16) - predicted_frame.astype(np.int16)
    
    return motion_vectors, residual


def motion_compensation(ref_frame, motion_vectors, residual, block_size=16):
    """
    Reconstruct frame using motion vectors and residual.
    
    Args:
        ref_frame: reference frame (Y channel)
        motion_vectors: motion vectors from block matching
        residual: residual frame
        block_size: block size used in motion estimation
    
    Returns:
        reconstructed frame
    """
    h, w = ref_frame.shape
    reconstructed = np.zeros_like(ref_frame)
    
    mv_h, mv_w = motion_vectors.shape[:2]
    
    for i in range(mv_h):
        for j in range(mv_w):
            y = i * block_size
            x = j * block_size
            
            dy, dx = motion_vectors[i, j]
            ref_y = y + dy
            ref_x = x + dx
            
            # Copy block from reference frame
            if (ref_y >= 0 and ref_y + block_size <= h and
                ref_x >= 0 and ref_x + block_size <= w):
                reconstructed[y:y+block_size, x:x+block_size] = \
                    ref_frame[ref_y:ref_y+block_size, ref_x:ref_x+block_size]
    
    # Add residual
    reconstructed = reconstructed.astype(np.int16) + residual
    reconstructed = np.clip(reconstructed, 0, 255).astype(np.uint8)
    
    return reconstructed
