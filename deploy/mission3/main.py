# ============================================================
# Mission 3: FFT Audio Spectrum Visualizer
# ============================================================
# 
# FILES REQUIRED ON ESP32:
# ------------------------
# 1. ssd1306.py     - OLED display driver (from Upload_these_to_device/)
# 2. config.py      - Configuration parameters
# 3. fft.py         - FFT implementation
# 4. wav_player.py  - WAV file parser and sine generator
# 5. oled_vis.py    - OLED visualization
# 6. main.py        - This file (entry point)
# 7. audio.wav      - (Optional) WAV file to visualize
#
# DEPLOYMENT:
# -----------
# 1. Copy all .py files to ESP32 root using Thonny
# 2. (Optional) Copy a mono WAV file as /audio.wav
# 3. Reset ESP32 or run main.py
#
# SELF-TEST MODE:
# ---------------
# If audio.wav is not found, the visualizer automatically
# switches to self-test mode with a sweeping sine wave.
# You can also force self-test by setting SELF_TEST=True in config.py
#
# ============================================================

import gc
import time

# Import our modules
import config
from fft import fft, get_hann_window, apply_window_inplace
from wav_player import create_audio_source
from oled_vis import init_display, show_message, show_error, SpectrumVisualizer


def run_visualizer():
    """
    Main visualization loop.
    """
    print("\n" + "=" * 50)
    print("Mission 3: FFT Audio Spectrum Visualizer")
    print("=" * 50)
    
    # Force garbage collection before starting
    gc.collect()
    print(f"[Main] Free memory: {gc.mem_free()} bytes")
    
    # ------------------------------------------------------------
    # Initialize OLED Display
    # ------------------------------------------------------------
    print("\n[Main] Initializing OLED display...")
    try:
        display = init_display(config)
    except Exception as e:
        print(f"[Main] FATAL: Could not initialize display: {e}")
        return
    
    # Show startup message
    show_message(display, [
        "FFT Spectrum",
        "Visualizer",
        "",
        "Initializing..."
    ])
    time.sleep(1)
    
    # ------------------------------------------------------------
    # Initialize Audio Source
    # ------------------------------------------------------------
    print("\n[Main] Initializing audio source...")
    audio_source = create_audio_source(config)
    
    # Check if we got a valid source
    if audio_source is None:
        show_error(display, "Audio Error", "No audio source available")
        return
    
    # Update display with source info
    source_type = type(audio_source).__name__
    show_message(display, [
        "Audio Source:",
        source_type[:16],
        "",
        "Starting..."
    ])
    time.sleep(1)
    
    # ------------------------------------------------------------
    # Initialize Visualizer
    # ------------------------------------------------------------
    print("\n[Main] Initializing visualizer...")
    visualizer = SpectrumVisualizer(display, config)
    
    # ------------------------------------------------------------
    # Pre-allocate Buffers (CRITICAL for avoiding MemoryError)
    # ------------------------------------------------------------
    print("\n[Main] Pre-allocating buffers...")
    
    # Get the Hann window (cached, allocated once)
    window = get_hann_window(config.FFT_SIZE)
    
    # Pre-allocate sample buffer - reused every frame
    samples = [0.0] * config.FFT_SIZE
    
    # Pre-allocate FFT result buffer - list of (real, imag) tuples
    fft_result = [(0.0, 0.0)] * config.FFT_SIZE
    
    # Pre-allocate magnitude buffer
    num_bins = config.FFT_SIZE // 2
    magnitudes = [0.0] * num_bins
    
    gc.collect()
    print(f"[Main] Free memory after init: {gc.mem_free()} bytes")
    
    # ------------------------------------------------------------
    # Main Visualization Loop
    # ------------------------------------------------------------
    print("\n[Main] Starting visualization loop...")
    print("[Main] Press Ctrl+C to stop\n")
    
    frame_count = 0
    start_time = time.ticks_ms()
    fps_update_interval = 100  # Update FPS every N frames
    
    try:
        while True:
            # Fill sample buffer in-place (no allocation)
            samples_read = audio_source.fill_block(samples)
            
            # Check for end of file (WAV files only)
            if samples_read < config.FFT_SIZE:
                if audio_source.is_eof():
                    if config.LOOP_AUDIO:
                        print("[Main] End of audio, looping...")
                        audio_source.reset()
                        # Buffer already zero-filled by fill_block
                    else:
                        print("[Main] End of audio, stopping...")
                        show_message(display, [
                            "",
                            "  Playback",
                            "  Complete",
                            ""
                        ])
                        break
            
            # Apply window function in-place (no allocation)
            apply_window_inplace(samples, window)
            
            # Compute FFT (still allocates internally, but less than before)
            fft_out = fft(samples)
            
            # Copy FFT result to preallocated buffer
            for i in range(len(fft_out)):
                fft_result[i] = fft_out[i]
            
            # Compute magnitudes into preallocated buffer
            for i in range(num_bins):
                real, imag = fft_result[i]
                magnitudes[i] = (real * real + imag * imag) ** 0.5
            
            # Update visualization
            visualizer.update(magnitudes)
            
            # Frame rate limiting (optional)
            if config.FRAME_DELAY_MS > 0:
                time.sleep_ms(config.FRAME_DELAY_MS)
            
            # FPS calculation and periodic GC
            frame_count += 1
            if frame_count % fps_update_interval == 0:
                elapsed = time.ticks_diff(time.ticks_ms(), start_time)
                fps = (fps_update_interval * 1000) / elapsed if elapsed > 0 else 0
                print(f"[Main] FPS: {fps:.1f}, Free mem: {gc.mem_free()}")
                start_time = time.ticks_ms()
                gc.collect()
    
    except KeyboardInterrupt:
        print("\n[Main] Stopped by user")
    
    finally:
        # Cleanup
        print("[Main] Cleaning up...")
        audio_source.close()
        
        show_message(display, [
            "",
            "  Visualizer",
            "   Stopped",
            ""
        ])
        
        gc.collect()
        print(f"[Main] Final free memory: {gc.mem_free()} bytes")
        print("[Main] Done.")


# Entry point
if __name__ == "__main__":
    run_visualizer()
