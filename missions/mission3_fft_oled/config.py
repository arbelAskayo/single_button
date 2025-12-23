# ============================================================
# Mission 3: FFT Audio Spectrum Visualizer - Configuration
# ============================================================
# This file contains all configurable parameters for the
# FFT spectrum visualizer. Adjust these values to match your
# hardware setup and preferences.
# ============================================================

# ------------------------------------------------------------
# I2C Configuration (for SSD1306 OLED)
# ------------------------------------------------------------
SCL_PIN = 22          # I2C clock pin
SDA_PIN = 21          # I2C data pin
I2C_FREQ = 400000     # I2C frequency in Hz (400kHz is standard for SSD1306)

# ------------------------------------------------------------
# OLED Display Configuration
# ------------------------------------------------------------
OLED_WIDTH = 128      # Display width in pixels
OLED_HEIGHT = 64      # Display height in pixels
OLED_ADDR = 0x3C      # Default I2C address (0x3C or 0x3D)

# ------------------------------------------------------------
# FFT Configuration
# ------------------------------------------------------------
FFT_SIZE = 128        # Number of samples per FFT frame (must be power of 2)
SAMPLE_RATE = 8000    # Expected sample rate in Hz

# ------------------------------------------------------------
# Visualization Configuration
# ------------------------------------------------------------
NUM_BARS = 16         # Number of frequency bars to display
BAR_WIDTH = 3         # Width of each bar in pixels (128/32 = 4, minus 1 for gap)
BAR_GAP = 1           # Gap between bars in pixels
EMA_ALPHA = 0.3       # Exponential moving average smoothing (0.0-1.0, higher = less smooth)
LOG_SCALE = True      # Use logarithmic scaling for magnitudes
MIN_DB = -60          # Minimum dB level to display (for log scaling)
MAX_DB = 0            # Maximum dB level to display (for log scaling)

# ------------------------------------------------------------
# Audio Source Configuration
# ------------------------------------------------------------
WAV_FILE = "/audio.wav"   # Path to WAV file on device
LOOP_AUDIO = True         # Loop audio file when reaching end

# ------------------------------------------------------------
# Self-Test Mode
# ------------------------------------------------------------
# When True, generates a synthetic sine wave instead of reading WAV file.
# Also activates automatically if WAV file is not found.
SELF_TEST = True

# Self-test parameters
TEST_FREQ_START = 200     # Starting frequency for sweep (Hz)
TEST_FREQ_END = 3000      # Ending frequency for sweep (Hz)
TEST_SWEEP_TIME = 5.0     # Time for one complete sweep (seconds)

# ------------------------------------------------------------
# Optional Hardware (from your setup)
# ------------------------------------------------------------
BUTTON_PIN = 4        # Button for pause/resume (optional, not used in basic Mission 3)
BUZZER_PIN = 23       # Buzzer pin (not used in Mission 3)

# ------------------------------------------------------------
# Performance Tuning
# ------------------------------------------------------------
FRAME_DELAY_MS = 0    # Additional delay between frames (0 for max speed)

