# ============================================================
# Mission 3: FFT Audio Spectrum Visualizer - FFT Module
# ============================================================
# This module provides FFT (Fast Fourier Transform) functionality.
# It attempts to use ulab (MicroPython's numpy-like library) if
# available, otherwise falls back to a pure Python implementation.
# ============================================================

import math

# Try to import ulab for hardware-accelerated FFT
_USE_ULAB = False
try:
    from ulab import numpy as np
    from ulab.scipy import signal as ulab_signal
    _USE_ULAB = True
    print("[FFT] Using ulab for accelerated FFT")
except ImportError:
    try:
        # Older ulab versions
        import ulab as np
        _USE_ULAB = True
        print("[FFT] Using ulab (legacy import) for accelerated FFT")
    except ImportError:
        print("[FFT] ulab not available, using pure Python FFT")


def is_power_of_two(n):
    """Check if n is a power of 2."""
    return n > 0 and (n & (n - 1)) == 0


def generate_hann_window(n):
    """
    Generate a Hann window of size n.
    Pre-computed once to avoid runtime allocations.
    
    Args:
        n: Window size
        
    Returns:
        List of n float values representing the Hann window
    """
    if _USE_ULAB:
        # Use ulab's efficient array operations
        indices = np.arange(n)
        window = 0.5 * (1 - np.cos(2 * math.pi * indices / (n - 1)))
        return list(window)
    else:
        # Pure Python implementation
        window = []
        for i in range(n):
            value = 0.5 * (1 - math.cos(2 * math.pi * i / (n - 1)))
            window.append(value)
        return window


def apply_window(samples, window):
    """
    Apply a window function to samples (element-wise multiplication).
    NOTE: This allocates a new list. Use apply_window_inplace() in main loop.
    
    Args:
        samples: List of sample values
        window: List of window coefficients (same length as samples)
        
    Returns:
        List of windowed samples
    """
    return [s * w for s, w in zip(samples, window)]


def apply_window_inplace(samples, window):
    """
    Apply a window function to samples in-place (zero allocation).
    Modifies the samples buffer directly.
    
    Args:
        samples: List of sample values (modified in-place)
        window: List of window coefficients (same length as samples)
    """
    n = len(samples)
    for i in range(n):
        samples[i] = samples[i] * window[i]


def _bit_reverse(n, bits):
    """Reverse the bits of n using 'bits' number of bits."""
    result = 0
    for _ in range(bits):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result


def _fft_pure_python(samples):
    """
    Pure Python implementation of Cooley-Tukey radix-2 FFT.
    
    Args:
        samples: List of real sample values (length must be power of 2)
        
    Returns:
        List of tuples (real, imag) representing complex FFT result
    """
    n = len(samples)
    
    if not is_power_of_two(n):
        raise ValueError(f"FFT size must be power of 2, got {n}")
    
    # Number of bits needed to represent indices
    bits = int(math.log2(n))
    
    # Bit-reversal permutation - initialize with real samples, imag = 0
    result = [(0.0, 0.0)] * n
    for i in range(n):
        j = _bit_reverse(i, bits)
        result[j] = (float(samples[i]), 0.0)
    
    # Cooley-Tukey iterative FFT
    size = 2
    while size <= n:
        half_size = size // 2
        # Twiddle factor angle step
        angle_step = -2 * math.pi / size
        
        for start in range(0, n, size):
            angle = 0.0
            for k in range(half_size):
                # Twiddle factor: W = e^(-j * angle)
                w_real = math.cos(angle)
                w_imag = math.sin(angle)
                
                idx1 = start + k
                idx2 = start + k + half_size
                
                # Get values
                a_real, a_imag = result[idx1]
                b_real, b_imag = result[idx2]
                
                # Complex multiplication: (b_real + j*b_imag) * (w_real + j*w_imag)
                t_real = b_real * w_real - b_imag * w_imag
                t_imag = b_real * w_imag + b_imag * w_real
                
                # Butterfly
                result[idx1] = (a_real + t_real, a_imag + t_imag)
                result[idx2] = (a_real - t_real, a_imag - t_imag)
                
                angle += angle_step
        
        size *= 2
    
    return result


def fft(samples):
    """
    Compute the FFT of real-valued samples.
    
    Args:
        samples: List of real sample values (length must be power of 2)
        
    Returns:
        List of tuples (real, imag) representing complex FFT result
    """
    if _USE_ULAB:
        # Use ulab's FFT
        arr = np.array(samples)
        result = np.fft.fft(arr)
        # Convert to list of tuples for consistent interface
        return [(float(result[i].real), float(result[i].imag)) for i in range(len(result))]
    else:
        return _fft_pure_python(samples)


def magnitude(fft_result, num_bins=None):
    """
    Compute magnitude spectrum from FFT result.
    Only returns first half (positive frequencies).
    
    Args:
        fft_result: List of (real, imag) tuples from fft()
        num_bins: Number of bins to return (default: N/2)
        
    Returns:
        List of magnitude values
    """
    n = len(fft_result)
    half_n = n // 2
    
    if num_bins is None:
        num_bins = half_n
    else:
        num_bins = min(num_bins, half_n)
    
    mags = []
    for i in range(num_bins):
        real, imag = fft_result[i]
        mag = math.sqrt(real * real + imag * imag)
        mags.append(mag)
    
    return mags


def magnitude_db(fft_result, num_bins=None, ref=1.0, min_db=-60):
    """
    Compute magnitude spectrum in decibels.
    
    Args:
        fft_result: List of (real, imag) tuples from fft()
        num_bins: Number of bins to return (default: N/2)
        ref: Reference value for 0 dB
        min_db: Minimum dB value (to avoid -infinity for zero values)
        
    Returns:
        List of magnitude values in dB
    """
    mags = magnitude(fft_result, num_bins)
    
    db_values = []
    for mag in mags:
        if mag < 1e-10:
            db_values.append(min_db)
        else:
            db = 20 * math.log10(mag / ref)
            db_values.append(max(db, min_db))
    
    return db_values


def bin_frequencies(sample_rate, fft_size, num_bins=None):
    """
    Calculate the center frequency of each FFT bin.
    
    Args:
        sample_rate: Sample rate in Hz
        fft_size: FFT size
        num_bins: Number of bins (default: fft_size/2)
        
    Returns:
        List of frequencies in Hz
    """
    if num_bins is None:
        num_bins = fft_size // 2
    
    freq_resolution = sample_rate / fft_size
    return [i * freq_resolution for i in range(num_bins)]


# Pre-computed window cache
_window_cache = {}


def get_hann_window(n):
    """
    Get a cached Hann window of size n.
    Avoids recomputing the window each frame.
    """
    if n not in _window_cache:
        _window_cache[n] = generate_hann_window(n)
    return _window_cache[n]

