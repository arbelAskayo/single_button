# Mission 3: FFT Audio Spectrum Visualizer

A real-time FFT spectrum visualizer for ESP32 with SSD1306 OLED display.

## Features

- Reads WAV files from the ESP32 filesystem
- Real-time FFT computation (pure Python or ulab-accelerated)
- Animated spectrum bars with peak hold
- EMA smoothing for stable visualization
- Logarithmic or linear scaling
- Self-test mode with sweeping sine wave

## Hardware Requirements

- ESP32 development board with MicroPython v1.20.0
- SSD1306 OLED display (128x64, I2C)

### Wiring

| OLED Pin | ESP32 Pin |
|----------|-----------|
| GND      | GND       |
| VCC      | 3.3V      |
| SCL      | GPIO 22   |
| SDA      | GPIO 21   |

## Files to Deploy

Copy ALL these files to the ESP32 root directory (`/`):

1. `ssd1306.py` - OLED display driver
2. `config.py` - Configuration parameters
3. `fft.py` - FFT implementation
4. `wav_player.py` - WAV file parser
5. `oled_vis.py` - Visualization module
6. `main.py` - Entry point

Optional:
- `audio.wav` - Your WAV file to visualize (8-bit or 16-bit PCM, mono or stereo)

## Deployment via Thonny (Windows)

### Step 1: Connect to ESP32

1. Open Thonny
2. Go to **Tools > Options > Interpreter**
3. Select **MicroPython (ESP32)**
4. Select the correct COM port
5. Click **OK**

### Step 2: Upload Files

1. In Thonny, go to **View > Files** to show the file browser
2. Navigate to this `deploy/mission3/` folder on your PC
3. For each file, right-click and select **Upload to /**
4. Upload all 6 `.py` files

### Step 3: Upload WAV File (Optional)

1. Prepare a WAV file (8kHz sample rate recommended, mono, 8 or 16-bit PCM)
2. Rename it to `audio.wav`
3. Right-click and **Upload to /** in Thonny

### Step 4: Run

Option A - Run directly:
1. Open `main.py` on the device
2. Press **F5** or click **Run**

Option B - Auto-run on boot:
1. The file is already named `main.py`, so it runs automatically on reset
2. Press the **EN** (reset) button on your ESP32

## Self-Test Mode

If no `audio.wav` file is found, the visualizer automatically switches to
self-test mode, which displays a sweeping sine wave moving across the spectrum.

You can also force self-test mode by editing `config.py`:

```python
SELF_TEST = True
```

## Configuration

Edit `config.py` to customize:

```python
# I2C pins (match your wiring)
SCL_PIN = 22
SDA_PIN = 21

# FFT settings
FFT_SIZE = 256       # Power of 2 (128, 256, 512)
SAMPLE_RATE = 8000   # Hz

# Visualization
NUM_BARS = 32        # Number of frequency bars
EMA_ALPHA = 0.3      # Smoothing (0.1 = smooth, 0.9 = responsive)
LOG_SCALE = True     # Use logarithmic scaling

# Audio
WAV_FILE = "/audio.wav"
LOOP_AUDIO = True    # Loop when reaching end
```

## Troubleshooting

### "ssd1306.py not found"
Make sure you uploaded `ssd1306.py` to the ESP32 root directory.

### OLED not displaying
1. Check wiring (VCC to 3.3V, not 5V!)
2. The console should show I2C scan results
3. Try address 0x3D if 0x3C doesn't work

### Low frame rate
- The pure Python FFT is slower than ulab
- Try reducing `FFT_SIZE` to 128
- Reduce `NUM_BARS` to 16

### "No audio source" error
- The WAV file must be named exactly `audio.wav`
- The file must be in the root directory (`/audio.wav`)
- Only PCM format is supported (not compressed)

## Creating a WAV File

Use Audacity or any audio editor:

1. Open your audio file
2. Convert to mono: **Tracks > Mix > Mix Stereo Down to Mono**
3. Set sample rate: **Tracks > Resample > 8000 Hz**
4. Export: **File > Export > Export as WAV**
   - Encoding: **Signed 16-bit PCM** or **Unsigned 8-bit PCM**
5. Rename to `audio.wav`

## Performance

Expected frame rates on ESP32:

| FFT Size | Bars | Approx FPS |
|----------|------|------------|
| 128      | 16   | ~15-20     |
| 256      | 32   | ~8-12      |
| 512      | 32   | ~4-6       |

With ulab (if available), expect 2-3x faster FFT computation.

## License

Educational use - part of the Single Button learning project.

