# ============================================================
# Mission 3: FFT Audio Spectrum Visualizer - WAV Player Module
# ============================================================
# This module provides WAV file parsing and sample streaming,
# plus a synthetic sine wave generator for testing without
# an actual audio file.
# ============================================================

import math
import struct


class WavReader:
    """
    Reads and streams samples from a WAV file.
    Supports 8-bit unsigned and 16-bit signed PCM mono audio.
    """
    
    def __init__(self, filepath):
        """
        Initialize WAV reader with a file path.
        
        Args:
            filepath: Path to WAV file on the device filesystem
        """
        self.filepath = filepath
        self.file = None
        self.sample_rate = 0
        self.num_channels = 0
        self.bits_per_sample = 0
        self.data_size = 0
        self.data_start = 0
        self.samples_read = 0
        self.total_samples = 0
        
        self._open_and_parse()
    
    def _open_and_parse(self):
        """Open the WAV file and parse its header."""
        self.file = open(self.filepath, 'rb')
        
        # Read RIFF header (12 bytes)
        riff_header = self.file.read(12)
        if len(riff_header) < 12:
            raise ValueError("File too short to be a valid WAV")
        
        # Validate RIFF/WAVE markers
        riff_id = riff_header[0:4]
        wave_id = riff_header[8:12]
        
        if riff_id != b'RIFF':
            raise ValueError(f"Not a RIFF file: {riff_id}")
        if wave_id != b'WAVE':
            raise ValueError(f"Not a WAVE file: {wave_id}")
        
        # Parse chunks until we find 'fmt ' and 'data'
        fmt_found = False
        data_found = False
        
        while not (fmt_found and data_found):
            chunk_header = self.file.read(8)
            if len(chunk_header) < 8:
                break
            
            chunk_id = chunk_header[0:4]
            chunk_size = struct.unpack('<I', chunk_header[4:8])[0]
            
            if chunk_id == b'fmt ':
                # Format chunk
                fmt_data = self.file.read(chunk_size)
                if len(fmt_data) < 16:
                    raise ValueError("Format chunk too short")
                
                audio_format = struct.unpack('<H', fmt_data[0:2])[0]
                self.num_channels = struct.unpack('<H', fmt_data[2:4])[0]
                self.sample_rate = struct.unpack('<I', fmt_data[4:8])[0]
                # byte_rate = struct.unpack('<I', fmt_data[8:12])[0]
                # block_align = struct.unpack('<H', fmt_data[12:14])[0]
                self.bits_per_sample = struct.unpack('<H', fmt_data[14:16])[0]
                
                if audio_format != 1:
                    raise ValueError(f"Unsupported audio format: {audio_format} (only PCM=1 supported)")
                
                if self.bits_per_sample not in (8, 16):
                    raise ValueError(f"Unsupported bits per sample: {self.bits_per_sample}")
                
                if self.num_channels > 2:
                    raise ValueError(f"Unsupported channel count: {self.num_channels}")
                
                fmt_found = True
                
            elif chunk_id == b'data':
                # Data chunk
                self.data_size = chunk_size
                self.data_start = self.file.tell()
                
                bytes_per_sample = self.bits_per_sample // 8
                self.total_samples = self.data_size // (bytes_per_sample * self.num_channels)
                
                data_found = True
                
            else:
                # Skip unknown chunk
                self.file.seek(chunk_size, 1)  # Seek relative to current position
        
        if not fmt_found:
            raise ValueError("No 'fmt ' chunk found in WAV file")
        if not data_found:
            raise ValueError("No 'data' chunk found in WAV file")
        
        print(f"[WAV] Opened: {self.filepath}")
        print(f"[WAV] Sample rate: {self.sample_rate} Hz")
        print(f"[WAV] Channels: {self.num_channels}")
        print(f"[WAV] Bits: {self.bits_per_sample}")
        print(f"[WAV] Total samples: {self.total_samples}")
    
    def fill_block(self, buffer):
        """
        Fill a preallocated buffer with samples from WAV file.
        Samples are normalized to [-1.0, 1.0] range.
        For stereo files, channels are averaged to mono.
        
        Args:
            buffer: Preallocated list/array to fill with samples
            
        Returns:
            Number of samples actually written (may be less at EOF)
        """
        n = len(buffer)
        bytes_per_sample = self.bits_per_sample // 8
        bytes_needed = n * bytes_per_sample * self.num_channels
        
        data = self.file.read(bytes_needed)
        if len(data) == 0:
            return 0
        
        # Calculate how many complete samples we got
        actual_samples = len(data) // (bytes_per_sample * self.num_channels)
        
        for i in range(actual_samples):
            offset = i * bytes_per_sample * self.num_channels
            
            if self.num_channels == 1:
                # Mono
                if self.bits_per_sample == 8:
                    value = data[offset]
                    buffer[i] = (value - 128) / 128.0
                else:
                    value = struct.unpack('<h', data[offset:offset+2])[0]
                    buffer[i] = value / 32768.0
            else:
                # Stereo - average channels
                if self.bits_per_sample == 8:
                    left = (data[offset] - 128) / 128.0
                    right = (data[offset + 1] - 128) / 128.0
                    buffer[i] = (left + right) / 2.0
                else:
                    left = struct.unpack('<h', data[offset:offset+2])[0] / 32768.0
                    right = struct.unpack('<h', data[offset+2:offset+4])[0] / 32768.0
                    buffer[i] = (left + right) / 2.0
        
        # Zero-fill remainder if we got fewer samples
        for i in range(actual_samples, n):
            buffer[i] = 0.0
        
        self.samples_read += actual_samples
        return actual_samples
    
    def read_block(self, n):
        """
        Read n samples from the WAV file (allocates new list).
        NOTE: Use fill_block() in main loop to avoid memory allocation.
        
        Args:
            n: Number of samples to read
            
        Returns:
            List of n float samples, or fewer if EOF reached
        """
        samples = [0.0] * n
        count = self.fill_block(samples)
        return samples[:count] if count < n else samples
    
    def reset(self):
        """Reset to the beginning of audio data."""
        self.file.seek(self.data_start)
        self.samples_read = 0
    
    def is_eof(self):
        """Check if we've reached the end of the audio data."""
        return self.samples_read >= self.total_samples
    
    def close(self):
        """Close the WAV file."""
        if self.file:
            self.file.close()
            self.file = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class SineGenerator:
    """
    Generates synthetic sine wave samples for testing.
    Supports frequency sweeping for spectrum visualization testing.
    """
    
    def __init__(self, sample_rate=8000, frequency=440.0, amplitude=0.8):
        """
        Initialize sine wave generator.
        
        Args:
            sample_rate: Sample rate in Hz
            frequency: Initial frequency in Hz
            amplitude: Amplitude (0.0 to 1.0)
        """
        self.sample_rate = sample_rate
        self.frequency = frequency
        self.amplitude = amplitude
        self.phase = 0.0
        
        # Sweep parameters
        self.sweep_enabled = False
        self.sweep_start_freq = 200
        self.sweep_end_freq = 3000
        self.sweep_duration = 5.0  # seconds
        self.sweep_samples = 0
        self.sweep_direction = 1  # 1 = up, -1 = down
        
        print(f"[SineGen] Initialized: {frequency} Hz @ {sample_rate} Hz sample rate")
    
    def enable_sweep(self, start_freq=200, end_freq=3000, duration=5.0):
        """
        Enable frequency sweeping mode.
        
        Args:
            start_freq: Starting frequency in Hz
            end_freq: Ending frequency in Hz
            duration: Time for one sweep in seconds
        """
        self.sweep_enabled = True
        self.sweep_start_freq = start_freq
        self.sweep_end_freq = end_freq
        self.sweep_duration = duration
        self.sweep_samples = 0
        self.sweep_direction = 1
        self.frequency = start_freq
        print(f"[SineGen] Sweep enabled: {start_freq} Hz -> {end_freq} Hz over {duration}s")
    
    def fill_block(self, buffer):
        """
        Fill a preallocated buffer with sine wave samples.
        Zero-allocation version for use in main loop.
        
        Args:
            buffer: Preallocated list/array to fill with samples
            
        Returns:
            Number of samples written (always len(buffer))
        """
        n = len(buffer)
        two_pi = 6.283185307179586  # 2 * pi precomputed
        phase_increment = two_pi * self.frequency / self.sample_rate
        
        # Cache instance variables for faster access
        phase = self.phase
        amplitude = self.amplitude
        sweep_enabled = self.sweep_enabled
        
        if sweep_enabled:
            # Sweep mode - frequency changes during block
            sweep_samples = self.sweep_samples
            total_sweep_samples = self.sweep_duration * self.sample_rate
            sweep_direction = self.sweep_direction
            sweep_start = self.sweep_start_freq
            sweep_range = self.sweep_end_freq - self.sweep_start_freq
            sample_rate = self.sample_rate
            
            for i in range(n):
                buffer[i] = amplitude * math.sin(phase)
                phase += phase_increment
                if phase > two_pi:
                    phase -= two_pi
                
                sweep_samples += 1
                if sweep_samples >= total_sweep_samples:
                    sweep_samples = 0
                    sweep_direction = -sweep_direction
                
                progress = sweep_samples / total_sweep_samples
                if sweep_direction > 0:
                    freq = sweep_start + progress * sweep_range
                else:
                    freq = sweep_start + sweep_range - progress * sweep_range
                phase_increment = two_pi * freq / sample_rate
            
            # Write back state
            self.sweep_samples = sweep_samples
            self.sweep_direction = sweep_direction
            self.frequency = freq
        else:
            # Fixed frequency - simpler loop
            for i in range(n):
                buffer[i] = amplitude * math.sin(phase)
                phase += phase_increment
                if phase > two_pi:
                    phase -= two_pi
        
        self.phase = phase
        return n
    
    def read_block(self, n):
        """
        Generate n samples of sine wave (allocates new list).
        NOTE: Use fill_block() in main loop to avoid memory allocation.
        
        Args:
            n: Number of samples to generate
            
        Returns:
            List of n float samples in [-amplitude, amplitude] range
        """
        samples = [0.0] * n
        self.fill_block(samples)
        return samples
    
    def reset(self):
        """Reset the generator state."""
        self.phase = 0.0
        self.sweep_samples = 0
        self.sweep_direction = 1
        if self.sweep_enabled:
            self.frequency = self.sweep_start_freq
    
    def is_eof(self):
        """Sine generator never reaches EOF (infinite stream)."""
        return False
    
    def close(self):
        """No resources to close for sine generator."""
        pass


class MultiToneGenerator:
    """
    Generates multiple simultaneous sine waves.
    Useful for testing multiple peaks in spectrum.
    """
    
    def __init__(self, sample_rate=8000, frequencies=None, amplitude=0.5):
        """
        Initialize multi-tone generator.
        
        Args:
            sample_rate: Sample rate in Hz
            frequencies: List of frequencies in Hz (default: [440, 880, 1320])
            amplitude: Amplitude per tone (divided among tones)
        """
        if frequencies is None:
            frequencies = [440, 880, 1320]  # Fundamental + harmonics
        
        self.sample_rate = sample_rate
        self.frequencies = frequencies
        self.amplitude = amplitude / len(frequencies)  # Prevent clipping
        self.phases = [0.0] * len(frequencies)
        
        print(f"[MultiTone] Frequencies: {frequencies} Hz")
    
    def fill_block(self, buffer):
        """
        Fill a preallocated buffer with mixed tone samples.
        Zero-allocation version for use in main loop.
        
        Args:
            buffer: Preallocated list/array to fill with samples
            
        Returns:
            Number of samples written (always len(buffer))
        """
        n = len(buffer)
        two_pi = 6.283185307179586
        num_tones = len(self.frequencies)
        amplitude = self.amplitude
        
        # Cache phase increments (computed once per block, not per sample)
        # Using local list to avoid repeated attribute lookups
        phases = self.phases
        sample_rate = self.sample_rate
        frequencies = self.frequencies
        
        for i in range(n):
            sample = 0.0
            for t in range(num_tones):
                sample += amplitude * math.sin(phases[t])
                phases[t] += two_pi * frequencies[t] / sample_rate
                if phases[t] > two_pi:
                    phases[t] -= two_pi
            buffer[i] = sample
        
        return n
    
    def read_block(self, n):
        """
        Generate n samples of mixed tones (allocates new list).
        NOTE: Use fill_block() in main loop to avoid memory allocation.
        
        Args:
            n: Number of samples to generate
            
        Returns:
            List of n float samples
        """
        samples = [0.0] * n
        self.fill_block(samples)
        return samples
    
    def reset(self):
        """Reset all phases."""
        for i in range(len(self.phases)):
            self.phases[i] = 0.0
    
    def is_eof(self):
        """Never reaches EOF."""
        return False
    
    def close(self):
        """No resources to close."""
        pass


def create_audio_source(config):
    """
    Factory function to create the appropriate audio source.
    
    Args:
        config: Configuration module with WAV_FILE, SELF_TEST, etc.
        
    Returns:
        Audio source object (WavReader or SineGenerator)
    """
    if config.SELF_TEST:
        print("[Audio] Self-test mode enabled")
        gen = SineGenerator(
            sample_rate=config.SAMPLE_RATE,
            frequency=config.TEST_FREQ_START,
            amplitude=0.8
        )
        gen.enable_sweep(
            start_freq=config.TEST_FREQ_START,
            end_freq=config.TEST_FREQ_END,
            duration=config.TEST_SWEEP_TIME
        )
        return gen
    
    try:
        reader = WavReader(config.WAV_FILE)
        return reader
    except OSError as e:
        print(f"[Audio] WAV file not found: {config.WAV_FILE}")
        print(f"[Audio] Error: {e}")
        print("[Audio] Falling back to self-test mode")
        gen = SineGenerator(
            sample_rate=config.SAMPLE_RATE,
            frequency=config.TEST_FREQ_START,
            amplitude=0.8
        )
        gen.enable_sweep(
            start_freq=config.TEST_FREQ_START,
            end_freq=config.TEST_FREQ_END,
            duration=config.TEST_SWEEP_TIME
        )
        return gen
    except ValueError as e:
        print(f"[Audio] Invalid WAV file: {e}")
        print("[Audio] Falling back to self-test mode")
        gen = SineGenerator(
            sample_rate=config.SAMPLE_RATE,
            frequency=config.TEST_FREQ_START,
            amplitude=0.8
        )
        gen.enable_sweep(
            start_freq=config.TEST_FREQ_START,
            end_freq=config.TEST_FREQ_END,
            duration=config.TEST_SWEEP_TIME
        )
        return gen

