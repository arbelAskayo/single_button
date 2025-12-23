# Mission 3: FFT Audio Spectrum Visualizer

## Overview

This mission implements a real-time FFT spectrum visualizer that:
1. Reads audio samples from a WAV file (or generates synthetic tones)
2. Computes FFT to get frequency spectrum
3. Renders animated spectrum bars on the OLED display

## Architecture

```
main.py          Entry point and main loop
    ├── config.py       Configuration parameters
    ├── fft.py          FFT computation (ulab or pure Python)
    ├── wav_player.py   WAV file parsing and sample streaming
    └── oled_vis.py     OLED initialization and bar rendering
```

## Quick Start

### For Development (Cursor/macOS)

Files are organized here for development and version control.
Edit these files, then copy the deploy version to your ESP32.

### For Deployment (Thonny/Windows)

Use the files in `deploy/mission3/` - they are ready to copy directly to the ESP32.

See `deploy/mission3/README.md` for detailed deployment instructions.

## Module Descriptions

### config.py
All configurable parameters in one place:
- I2C pins (SCL=22, SDA=21)
- FFT size (256 samples)
- Visualization settings (32 bars, smoothing, log scale)
- Audio source settings

### fft.py
FFT implementation with two modes:
- **ulab mode**: Uses MicroPython's ulab library if available (faster)
- **Pure Python mode**: Cooley-Tukey radix-2 FFT implementation

Also includes:
- Hann window generation
- Magnitude calculation
- Window caching

### wav_player.py
Audio source management:
- `WavReader`: Parses and streams samples from WAV files
- `SineGenerator`: Generates synthetic sine waves for testing
- `MultiToneGenerator`: Multiple simultaneous tones
- `create_audio_source()`: Factory function with automatic fallback

### oled_vis.py
OLED display handling:
- I2C bus scanning and device detection
- Display initialization with error handling
- `SpectrumVisualizer` class with:
  - Bin-to-bar mapping
  - Logarithmic/linear scaling
  - EMA smoothing
  - Peak hold effect
  - Efficient bar rendering

### main.py
Main application flow:
1. Initialize display with splash screen
2. Create audio source (WAV or synthetic)
3. Pre-allocate buffers for performance
4. Run visualization loop:
   - Read samples
   - Apply window
   - Compute FFT
   - Update visualization
5. Handle EOF and keyboard interrupt

## Self-Test Mode

The self-test mode runs automatically if:
- No `audio.wav` file is found
- `SELF_TEST = True` in config.py

It generates a sweeping sine wave that moves from low to high frequencies,
allowing you to verify the FFT and visualization are working correctly.

## Performance Notes

- Pure Python FFT for N=256 takes ~80-120ms on ESP32
- With ulab, FFT takes ~5-10ms
- OLED update takes ~10-15ms at 400kHz I2C
- Expected frame rate: 8-15 FPS depending on configuration

