"""
Main video compression pipeline with advanced features:
- Chroma subsampling (4:2:0)
- Aggressive quantization
- Huffman entropy coding
- Bit-level storage
- Parallel frame processing
"""
import numpy as np
from multiprocessing import Pool, cpu_count
from functools import partial
from video_utils import subsample_chroma_420, upsample_chroma_420, frames_to_yuv, frames_to_bgr
from video_dct import apply_dct_8x8, apply_idct_8x8, quantize_dct, dequantize_dct, get_chroma_quantization_matrix
from video_motion import block_matching, motion_compensation
from video_encoding import (zigzag_scan_8x8, run_length_encode, run_length_decode, 
                            huffman_encode, huffman_decode, pack_bits_to_bytes, 
                            unpack_bytes_to_bits, apply_threshold)


# Worker function for parallel processing (must be at module level)
def _compress_gop_worker(gop_task, i_frame_interval, quality):
    """
    Worker function to compress a GOP (Group of Pictures) in parallel.
    
    Args:
        gop_task: tuple of (gop_idx, start_idx, gop_frames)
        i_frame_interval: I-frame interval
        quality: compression quality
    
    Returns:
        tuple of (gop_idx, start_idx, compressed_frames)
    """
    gop_idx, start_idx, gop_frames = gop_task
    
    # Create a temporary compressor for this GOP
    compressor = VideoCompressor(i_frame_interval=i_frame_interval, 
                                quality=quality, 
                                parallel=False)  # Disable nested parallelism
    
    compressed_frames = []
    
    for local_idx, yuv_frame in enumerate(gop_frames):
        global_idx = start_idx + local_idx
        
        if global_idx % i_frame_interval == 0:
            # I-frame
            compressed = compressor.compress_i_frame(yuv_frame)
        else:
            # P-frame - reference is always the first frame in this GOP
            ref_frame = gop_frames[0]
            compressed = compressor.compress_p_frame(yuv_frame, ref_frame)
        
        compressed_frames.append(compressed)
    
    return (gop_idx, start_idx, compressed_frames)


class VideoCompressor:
    def __init__(self, i_frame_interval=10, quality=50, parallel=True, num_workers=None):
        """
        Initialize video compressor.
        
        Args:
            i_frame_interval: interval between I-frames (every Nth frame)
            quality: compression quality (1-100)
            parallel: enable parallel frame processing
            num_workers: number of worker processes (None = auto-detect)
        """
        self.i_frame_interval = i_frame_interval
        self.quality = quality
        self.parallel = parallel
        self.num_workers = num_workers if num_workers else max(1, cpu_count() - 1)
        self.compressed_data = []
        self.frame_shapes = []
    
    def compress_i_frame(self, yuv_frame):
        """
        Compress I-frame using DCT, quantization, and entropy coding.
        Uses 4:2:0 chroma subsampling for better compression.
        
        Returns:
            compressed data dictionary
        """
        # Chroma subsampling 4:2:0
        Y, U_sub, V_sub = subsample_chroma_420(yuv_frame)
        
        # Apply DCT
        dct_y = apply_dct_8x8(Y)
        dct_u = apply_dct_8x8(U_sub)
        dct_v = apply_dct_8x8(V_sub)
        
        # Quantize with aggressive high-frequency zeroing
        q_y, Q_luma = quantize_dct(dct_y, self.quality, aggressive=True)
        Q_chroma = get_chroma_quantization_matrix(self.quality)
        
        # Quantize chroma with more aggressive matrix
        h_u, w_u = dct_u.shape
        q_u = np.zeros_like(dct_u, dtype=np.int16)
        q_v = np.zeros_like(dct_v, dtype=np.int16)
        
        for i in range(0, h_u, 8):
            for j in range(0, w_u, 8):
                block_u = dct_u[i:i+8, j:j+8]
                block_v = dct_v[i:i+8, j:j+8]
                q_u[i:i+8, j:j+8] = np.round(block_u / Q_chroma).astype(np.int16)
                q_v[i:i+8, j:j+8] = np.round(block_v / Q_chroma).astype(np.int16)
        
        # Apply thresholding to create more zeros
        q_y = apply_threshold(q_y, threshold=1)
        q_u = apply_threshold(q_u, threshold=1)
        q_v = apply_threshold(q_v, threshold=1)
        
        # Zigzag scan and RLE for each channel
        y_rle = self._compress_channel(q_y)
        u_rle = self._compress_channel(q_u)
        v_rle = self._compress_channel(q_v)
        
        # Huffman encode the RLE data
        y_bits, y_codes = self._huffman_encode_rle(y_rle)
        u_bits, u_codes = self._huffman_encode_rle(u_rle)
        v_bits, v_codes = self._huffman_encode_rle(v_rle)
        
        # Pack bits to bytes
        y_bytes, y_padding = pack_bits_to_bytes(y_bits)
        u_bytes, u_padding = pack_bits_to_bytes(u_bits)
        v_bytes, v_padding = pack_bits_to_bytes(v_bits)
        
        return {
            'type': 'I',
            'Y_bytes': y_bytes,
            'Y_padding': y_padding,
            'Y_codes': y_codes,
            'U_bytes': u_bytes,
            'U_padding': u_padding,
            'U_codes': u_codes,
            'V_bytes': v_bytes,
            'V_padding': v_padding,
            'V_codes': v_codes,
            'Q_luma': Q_luma,
            'Q_chroma': Q_chroma,
            'Y_shape': Y.shape,
            'U_shape': U_sub.shape
        }
    
    def _compress_channel(self, quantized_channel):
        """Apply zigzag scan and RLE to a channel."""
        h, w = quantized_channel.shape
        rle_data = []
        
        for i in range(0, h, 8):
            for j in range(0, w, 8):
                block = quantized_channel[i:i+8, j:j+8]
                if block.shape == (8, 8):
                    zigzag = zigzag_scan_8x8(block)
                    rle_data.extend(zigzag)
        
        return run_length_encode(rle_data)
    
    def _huffman_encode_rle(self, rle_data):
        """Huffman encode RLE data (value, count) pairs."""
        if not rle_data:
            return '', {}
        
        # Flatten RLE data: [val1, count1, val2, count2, ...]
        flat_data = []
        for val, count in rle_data:
            flat_data.append(val)
            flat_data.append(count)
        
        return huffman_encode(flat_data)
    
    def compress_p_frame(self, yuv_frame, ref_yuv_frame):
        """
        Compress P-frame using motion estimation with improved residual compression.
        
        Returns:
            compressed data dictionary
        """
        # Chroma subsampling
        Y, U_sub, V_sub = subsample_chroma_420(yuv_frame)
        ref_Y, ref_U_sub, ref_V_sub = subsample_chroma_420(ref_yuv_frame)
        
        # Motion estimation on Y channel
        motion_vectors, residual = block_matching(ref_Y, Y)
        
        # Apply thresholding to residual (small values → 0)
        residual = apply_threshold(residual.astype(np.float32), threshold=2)
        
        # Compress residual using DCT
        dct_residual = apply_dct_8x8(residual)
        q_residual, Q_luma = quantize_dct(dct_residual, self.quality, aggressive=True)
        q_residual = apply_threshold(q_residual, threshold=1)
        
        # RLE + Huffman encode residual
        residual_rle = self._compress_channel(q_residual)
        residual_bits, residual_codes = self._huffman_encode_rle(residual_rle)
        residual_bytes, residual_padding = pack_bits_to_bytes(residual_bits)
        
        # Encode motion vectors
        mv_flat = motion_vectors.flatten()
        mv_bits, mv_codes = huffman_encode(mv_flat.tolist())
        mv_bytes, mv_padding = pack_bits_to_bytes(mv_bits)
        
        # For U and V channels, use simple difference with thresholding
        U_diff = U_sub.astype(np.int16) - ref_U_sub.astype(np.int16)
        V_diff = V_sub.astype(np.int16) - ref_V_sub.astype(np.int16)
        
        U_diff = apply_threshold(U_diff.astype(np.float32), threshold=2).astype(np.int16)
        V_diff = apply_threshold(V_diff.astype(np.float32), threshold=2).astype(np.int16)
        
        # RLE + Huffman for chroma differences
        u_rle = run_length_encode(U_diff.flatten())
        v_rle = run_length_encode(V_diff.flatten())
        
        u_bits, u_codes = self._huffman_encode_rle(u_rle)
        v_bits, v_codes = self._huffman_encode_rle(v_rle)
        
        u_bytes, u_padding = pack_bits_to_bytes(u_bits)
        v_bytes, v_padding = pack_bits_to_bytes(v_bits)
        
        return {
            'type': 'P',
            'mv_bytes': mv_bytes,
            'mv_padding': mv_padding,
            'mv_codes': mv_codes,
            'mv_shape': motion_vectors.shape,
            'residual_bytes': residual_bytes,
            'residual_padding': residual_padding,
            'residual_codes': residual_codes,
            'U_bytes': u_bytes,
            'U_padding': u_padding,
            'U_codes': u_codes,
            'V_bytes': v_bytes,
            'V_padding': v_padding,
            'V_codes': v_codes,
            'Q_luma': Q_luma,
            'Y_shape': Y.shape,
            'U_shape': U_sub.shape
        }
    
    def compress_frames(self, bgr_frames, progress_callback=None):
        """
        Compress all frames (with optional parallelization).
        
        Args:
            bgr_frames: list of BGR frames
            progress_callback: function(current, total, stage) for progress updates
        """
        yuv_frames = frames_to_yuv(bgr_frames)
        total_frames = len(yuv_frames)
        
        if self.parallel and total_frames > 4:
            # Parallel compression
            self.compressed_data = self._compress_frames_parallel(yuv_frames, progress_callback)
        else:
            # Sequential compression
            self.compressed_data = self._compress_frames_sequential(yuv_frames, progress_callback)
        
        return self.compressed_data
    
    def _compress_frames_sequential(self, yuv_frames, progress_callback=None):
        """Sequential frame compression (original method)."""
        compressed_data = []
        total_frames = len(yuv_frames)
        
        for idx, yuv_frame in enumerate(yuv_frames):
            if idx % self.i_frame_interval == 0:
                # I-frame
                compressed = self.compress_i_frame(yuv_frame)
                compressed_data.append(compressed)
                stage = f"Compressing I-frame {idx+1}/{total_frames}"
            else:
                # P-frame
                ref_idx = (idx // self.i_frame_interval) * self.i_frame_interval
                ref_frame = yuv_frames[ref_idx]
                compressed = self.compress_p_frame(yuv_frame, ref_frame)
                compressed_data.append(compressed)
                stage = f"Compressing P-frame {idx+1}/{total_frames}"
            
            if progress_callback:
                progress_callback(idx + 1, total_frames, stage)
        
        return compressed_data
    
    def _compress_frames_parallel(self, yuv_frames, progress_callback=None):
        """Parallel frame compression using multiprocessing."""
        total_frames = len(yuv_frames)
        compressed_data = [None] * total_frames
        
        # Group frames by GOP (Group of Pictures)
        gop_size = self.i_frame_interval
        num_gops = (total_frames + gop_size - 1) // gop_size
        
        # Process GOPs in parallel
        with Pool(processes=self.num_workers) as pool:
            # Prepare GOP data
            gop_tasks = []
            for gop_idx in range(num_gops):
                start_idx = gop_idx * gop_size
                end_idx = min(start_idx + gop_size, total_frames)
                gop_frames = yuv_frames[start_idx:end_idx]
                gop_tasks.append((gop_idx, start_idx, gop_frames))
            
            # Process GOPs in parallel
            compress_func = partial(_compress_gop_worker, 
                                   i_frame_interval=self.i_frame_interval,
                                   quality=self.quality)
            
            results = pool.map(compress_func, gop_tasks)
            
            # Collect results
            for gop_idx, start_idx, gop_compressed in results:
                for i, compressed in enumerate(gop_compressed):
                    compressed_data[start_idx + i] = compressed
                
                # Update progress
                if progress_callback:
                    frames_done = min((gop_idx + 1) * gop_size, total_frames)
                    stage = f"Compressed GOP {gop_idx+1}/{num_gops}"
                    progress_callback(frames_done, total_frames, stage)
        
        return compressed_data
    
    def decompress_i_frame(self, compressed):
        """Decompress I-frame with entropy decoding."""
        # Unpack bytes to bits
        y_bits = unpack_bytes_to_bits(compressed['Y_bytes'], compressed['Y_padding'])
        u_bits = unpack_bytes_to_bits(compressed['U_bytes'], compressed['U_padding'])
        v_bits = unpack_bytes_to_bits(compressed['V_bytes'], compressed['V_padding'])
        
        # Huffman decode
        y_flat = huffman_decode(y_bits, compressed['Y_codes'])
        u_flat = huffman_decode(u_bits, compressed['U_codes'])
        v_flat = huffman_decode(v_bits, compressed['V_codes'])
        
        # Decode RLE
        y_rle = self._decode_rle_flat(y_flat)
        u_rle = self._decode_rle_flat(u_flat)
        v_rle = self._decode_rle_flat(v_flat)
        
        y_data = run_length_decode(y_rle)
        u_data = run_length_decode(u_rle)
        v_data = run_length_decode(v_rle)
        
        # Reconstruct channels from zigzag data
        Y_shape = compressed['Y_shape']
        U_shape = compressed['U_shape']
        
        q_y = self._reconstruct_channel(y_data, Y_shape)
        q_u = self._reconstruct_channel(u_data, U_shape)
        q_v = self._reconstruct_channel(v_data, U_shape)
        
        # Dequantize
        Q_luma = compressed['Q_luma']
        Q_chroma = compressed['Q_chroma']
        
        dct_y = dequantize_dct(q_y, Q_luma)
        dct_u = dequantize_dct(q_u, Q_chroma)
        dct_v = dequantize_dct(q_v, Q_chroma)
        
        # Inverse DCT
        Y = apply_idct_8x8(dct_y, Y_shape)
        U_sub = apply_idct_8x8(dct_u, U_shape)
        V_sub = apply_idct_8x8(dct_v, U_shape)
        
        # Clip and convert to uint8
        Y = np.clip(Y, 0, 255).astype(np.uint8)
        U_sub = np.clip(U_sub, 0, 255).astype(np.uint8)
        V_sub = np.clip(V_sub, 0, 255).astype(np.uint8)
        
        # Upsample chroma from 4:2:0 to 4:4:4
        return upsample_chroma_420(Y, U_sub, V_sub)
    
    def _decode_rle_flat(self, flat_data):
        """Decode flat Huffman data back to RLE pairs."""
        rle = []
        for i in range(0, len(flat_data), 2):
            if i + 1 < len(flat_data):
                rle.append((flat_data[i], flat_data[i+1]))
        return rle
    
    def _reconstruct_channel(self, zigzag_data, shape):
        """Reconstruct channel from zigzag-scanned data."""
        h, w = shape
        channel = np.zeros((h, w), dtype=np.int16)
        
        block_idx = 0
        for i in range(0, h, 8):
            for j in range(0, w, 8):
                if block_idx * 64 + 64 <= len(zigzag_data):
                    block_data = zigzag_data[block_idx * 64:(block_idx + 1) * 64]
                    block = self._inverse_zigzag_8x8(block_data)
                    channel[i:i+8, j:j+8] = block
                    block_idx += 1
        
        return channel
    
    def _inverse_zigzag_8x8(self, data):
        """Inverse zigzag scan to reconstruct 8x8 block."""
        zigzag_indices = [
            (0,0), (0,1), (1,0), (2,0), (1,1), (0,2), (0,3), (1,2),
            (2,1), (3,0), (4,0), (3,1), (2,2), (1,3), (0,4), (0,5),
            (1,4), (2,3), (3,2), (4,1), (5,0), (6,0), (5,1), (4,2),
            (3,3), (2,4), (1,5), (0,6), (0,7), (1,6), (2,5), (3,4),
            (4,3), (5,2), (6,1), (7,0), (7,1), (6,2), (5,3), (4,4),
            (3,5), (2,6), (1,7), (2,7), (3,6), (4,5), (5,4), (6,3),
            (7,2), (7,3), (6,4), (5,5), (4,6), (3,7), (4,7), (5,6),
            (6,5), (7,4), (7,5), (6,6), (5,7), (6,7), (7,6), (7,7)
        ]
        
        block = np.zeros((8, 8), dtype=np.int16)
        for idx, (i, j) in enumerate(zigzag_indices):
            if idx < len(data):
                block[i, j] = data[idx]
        
        return block
    
    def decompress_p_frame(self, compressed, ref_yuv_frame):
        """Decompress P-frame with entropy decoding."""
        # Decode motion vectors
        mv_bits = unpack_bytes_to_bits(compressed['mv_bytes'], compressed['mv_padding'])
        mv_flat = huffman_decode(mv_bits, compressed['mv_codes'])
        motion_vectors = np.array(mv_flat).reshape(compressed['mv_shape'])
        
        # Decode residual
        residual_bits = unpack_bytes_to_bits(compressed['residual_bytes'], compressed['residual_padding'])
        residual_flat = huffman_decode(residual_bits, compressed['residual_codes'])
        residual_rle = self._decode_rle_flat(residual_flat)
        residual_data = run_length_decode(residual_rle)
        
        Y_shape = compressed['Y_shape']
        q_residual = self._reconstruct_channel(residual_data, Y_shape)
        
        # Dequantize and inverse DCT residual
        Q_luma = compressed['Q_luma']
        dct_residual = dequantize_dct(q_residual, Q_luma)
        residual = apply_idct_8x8(dct_residual, Y_shape).astype(np.int16)
        
        # Motion compensation
        ref_Y, ref_U_sub, ref_V_sub = subsample_chroma_420(ref_yuv_frame)
        Y = motion_compensation(ref_Y, motion_vectors, residual)
        
        # Decode U and V differences
        u_bits = unpack_bytes_to_bits(compressed['U_bytes'], compressed['U_padding'])
        v_bits = unpack_bytes_to_bits(compressed['V_bytes'], compressed['V_padding'])
        
        u_flat = huffman_decode(u_bits, compressed['U_codes'])
        v_flat = huffman_decode(v_bits, compressed['V_codes'])
        
        u_rle = self._decode_rle_flat(u_flat)
        v_rle = self._decode_rle_flat(v_flat)
        
        U_diff = run_length_decode(u_rle).reshape(compressed['U_shape'])
        V_diff = run_length_decode(v_rle).reshape(compressed['U_shape'])
        
        # Reconstruct U and V
        U_sub = ref_U_sub.astype(np.int16) + U_diff
        V_sub = ref_V_sub.astype(np.int16) + V_diff
        
        U_sub = np.clip(U_sub, 0, 255).astype(np.uint8)
        V_sub = np.clip(V_sub, 0, 255).astype(np.uint8)
        
        # Upsample chroma
        return upsample_chroma_420(Y, U_sub, V_sub)
    
    def decompress_frames(self, progress_callback=None):
        """
        Decompress all frames.
        
        Returns:
            list of BGR frames
        """
        yuv_frames = []
        total_frames = len(self.compressed_data)
        
        for idx, compressed in enumerate(self.compressed_data):
            if compressed['type'] == 'I':
                yuv_frame = self.decompress_i_frame(compressed)
                stage = f"Decompressing I-frame {idx+1}/{total_frames}"
            else:
                ref_idx = (idx // self.i_frame_interval) * self.i_frame_interval
                ref_frame = yuv_frames[ref_idx]
                yuv_frame = self.decompress_p_frame(compressed, ref_frame)
                stage = f"Decompressing P-frame {idx+1}/{total_frames}"
            
            yuv_frames.append(yuv_frame)
            
            if progress_callback:
                progress_callback(idx + 1, total_frames, stage)
        
        return frames_to_bgr(yuv_frames)
