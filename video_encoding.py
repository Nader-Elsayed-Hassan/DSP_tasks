"""
Encoding utilities: zigzag scan, run-length encoding, and Huffman coding.
"""
import numpy as np
from collections import Counter
import heapq


def zigzag_scan_8x8(block):
    """
    Perform zigzag scan on 8x8 block.
    
    Returns:
        1D array of coefficients in zigzag order
    """
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
    return np.array([block[i, j] for i, j in zigzag_indices])


def apply_threshold(data, threshold=1):
    """
    Apply thresholding: small values become zero.
    This improves compression by creating more zeros.
    
    Args:
        data: input array
        threshold: values with abs < threshold become 0
    
    Returns:
        thresholded array
    """
    result = data.copy()
    result[np.abs(result) < threshold] = 0
    return result


def run_length_encode(data):
    """
    Run-length encoding for quantized coefficients.
    Optimized for sequences with many zeros.
    
    Returns:
        list of (value, count) tuples
    """
    if len(data) == 0:
        return []
    
    # Flatten if needed
    if isinstance(data, np.ndarray):
        data = data.flatten()
    
    encoded = []
    current_val = data[0]
    count = 1
    
    for val in data[1:]:
        if val == current_val and count < 255:  # Limit count to fit in byte
            count += 1
        else:
            encoded.append((int(current_val), count))
            current_val = val
            count = 1
    
    encoded.append((int(current_val), count))
    return encoded


def run_length_decode(encoded):
    """Decode run-length encoded data."""
    decoded = []
    for val, count in encoded:
        decoded.extend([val] * count)
    return np.array(decoded)


class HuffmanNode:
    def __init__(self, value, freq):
        self.value = value
        self.freq = freq
        self.left = None
        self.right = None
    
    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree(data):
    """Build Huffman tree from data."""
    if len(data) == 0:
        return None
    
    freq = Counter(data)
    heap = [HuffmanNode(val, count) for val, count in freq.items()]
    heapq.heapify(heap)
    
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        
        parent = HuffmanNode(None, left.freq + right.freq)
        parent.left = left
        parent.right = right
        
        heapq.heappush(heap, parent)
    
    return heap[0] if heap else None


def generate_huffman_codes(root):
    """Generate Huffman codes from tree."""
    if root is None:
        return {}
    
    codes = {}
    
    def traverse(node, code):
        if node.value is not None:
            codes[node.value] = code
            return
        
        if node.left:
            traverse(node.left, code + '0')
        if node.right:
            traverse(node.right, code + '1')
    
    traverse(root, '')
    return codes


def huffman_encode(data):
    """
    Encode data using Huffman coding.
    
    Returns:
        encoded bitstring, huffman codes dictionary
    """
    if len(data) == 0:
        return '', {}
    
    root = build_huffman_tree(data)
    if root is None:
        return '', {}
    
    codes = generate_huffman_codes(root)
    
    # Handle single unique value case
    if len(codes) == 1:
        val = list(codes.keys())[0]
        codes[val] = '0'
    
    encoded = ''.join(codes.get(val, '0') for val in data)
    
    return encoded, codes


def huffman_decode(encoded_bits, codes):
    """
    Decode Huffman encoded bitstring.
    
    Args:
        encoded_bits: bitstring
        codes: huffman codes dictionary {value: code}
    
    Returns:
        decoded data list
    """
    if not encoded_bits or not codes:
        return []
    
    # Reverse the codes dictionary
    reverse_codes = {code: val for val, code in codes.items()}
    
    decoded = []
    current_code = ''
    
    for bit in encoded_bits:
        current_code += bit
        if current_code in reverse_codes:
            decoded.append(reverse_codes[current_code])
            current_code = ''
    
    return decoded


def pack_bits_to_bytes(bitstring):
    """
    Pack bitstring into bytes for efficient storage.
    
    Args:
        bitstring: string of '0' and '1'
    
    Returns:
        bytes object, number of padding bits
    """
    # Pad to multiple of 8
    padding = (8 - len(bitstring) % 8) % 8
    bitstring_padded = bitstring + '0' * padding
    
    # Convert to bytes
    byte_array = bytearray()
    for i in range(0, len(bitstring_padded), 8):
        byte = bitstring_padded[i:i+8]
        byte_array.append(int(byte, 2))
    
    return bytes(byte_array), padding


def unpack_bytes_to_bits(byte_data, padding):
    """
    Unpack bytes back to bitstring.
    
    Args:
        byte_data: bytes object
        padding: number of padding bits to remove
    
    Returns:
        bitstring
    """
    bitstring = ''.join(format(byte, '08b') for byte in byte_data)
    
    # Remove padding
    if padding > 0:
        bitstring = bitstring[:-padding]
    
    return bitstring
