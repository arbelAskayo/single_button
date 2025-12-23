# Mission 4: Mario-Like Endless Runner Game

A retro-style side-scrolling endless runner game for ESP32 with SSD1306 OLED display.
Uses only **3 wires** (OLED) + the built-in **BOOT button** for input!

## Features

- Side-scrolling endless runner gameplay
- Jump physics with gravity
- Short press = small jump, Long press = high jump
- Multiple obstacle types (pipes, blocks)
- Score tracking with high score
- Smooth 30 FPS gameplay
- No extra wiring needed (uses built-in BOOT button)

## Hardware Requirements

- ESP32 DevKit (ESP-WROOM-32)
- SSD1306 OLED 128x64 I2C display
- 3 jumper wires (VCC, SDA, SCL - GND shared via breadboard)

### Wiring

| OLED Pin | ESP32 Pin | Notes |
|----------|-----------|-------|
| GND      | GND       | Shared via breadboard row |
| VCC      | 3.3V      | Power |
| SCL      | GPIO 22   | I2C Clock |
| SDA      | GPIO 21   | I2C Data |

### Button

The game uses the **built-in BOOT button** (GPIO0) on the ESP32 board.
No additional wiring required!

## Files to Deploy

Copy these files to the ESP32 root directory (`/`):

1. `ssd1306.py` - OLED display driver
2. `main.py` - The game

## Deployment via Thonny (Windows)

### Step 1: Connect to ESP32

1. Open Thonny
2. Go to **Tools > Options > Interpreter**
3. Select **MicroPython (ESP32)**
4. Select the correct COM port
5. Click **OK**

### Step 2: Upload Files

1. In Thonny, go to **View > Files** to show the file browser
2. Navigate to this `deploy/mission4/` folder on your PC
3. Right-click `ssd1306.py` and select **Upload to /**
4. Right-click `main.py` and select **Upload to /**

### Step 3: Run

Option A - Run directly:
1. Open `main.py` on the device
2. Press **F5** or click **Run**

Option B - Auto-run on boot:
1. The file is already named `main.py`, so it runs automatically on reset
2. Press the **EN** (reset) button on your ESP32

## How to Play

1. **Start Screen**: Press BOOT button to begin
2. **Gameplay**:
   - **Short press** (tap): Small jump
   - **Long press** (hold ~200ms+): High jump
3. **Avoid obstacles** moving from right to left
4. **Score** increases as you survive
5. **Game Over**: Press BOOT to restart

## Game Controls

| Action | Button Input |
|--------|--------------|
| Start game | Any press |
| Small jump | Short press (<200ms) |
| High jump | Long press (>200ms) |
| Restart | Any press (from Game Over) |

## Troubleshooting

### "No I2C devices found"
- Check wiring connections
- Ensure OLED VCC is connected to 3.3V (not 5V!)
- Verify GND connection

### Game runs slowly
- This should not happen at 30 FPS target
- Check for other processes running on ESP32

### Button not responding
- The BOOT button is GPIO0
- Some ESP32 boards have different button layouts
- Ensure you're pressing the BOOT button (not EN/reset)

### OLED display garbled
- Try pressing EN (reset) button
- Re-upload both files
- Check I2C connections

## Game Constants (Tuning)

Edit `main.py` to adjust gameplay:

```python
# Physics
GRAVITY = 1.0        # Higher = faster fall
JUMP_VEL = -9        # Short jump power (negative = up)
JUMP_VEL_HIGH = -13  # Long jump power

# Difficulty
OBSTACLE_SPEED = 3       # Pixels per frame
MIN_SPAWN_FRAMES = 35    # Minimum time between obstacles
MAX_SPAWN_FRAMES = 70    # Maximum time between obstacles

# Timing
TARGET_FPS = 30          # Frame rate
LONG_PRESS_MS = 200      # Threshold for long press
```

## Technical Details

- **Display**: 128x64 monochrome OLED (SSD1306)
- **Frame Rate**: 30 FPS (33ms per frame)
- **Memory**: Preallocated obstacle pool, periodic GC
- **Input**: Debounced button with edge detection

## License

Educational use - part of the Single Button learning project.

