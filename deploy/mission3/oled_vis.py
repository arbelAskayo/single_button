# ============================================================
# Mission 3: FFT Audio Spectrum Visualizer - OLED Visualization
# ============================================================
# This module handles OLED display initialization, I2C scanning,
# and efficient spectrum bar rendering with smoothing.
# ============================================================

from machine import Pin, I2C
import math

# Import the SSD1306 driver (will be copied to device)
try:
    import ssd1306
except ImportError:
    print("[OLED] ERROR: ssd1306.py not found!")
    print("[OLED] Please copy ssd1306.py to the device.")
    raise


def scan_i2c(scl_pin, sda_pin, freq=400000):
    """
    Scan the I2C bus for devices and return found addresses.
    
    Args:
        scl_pin: GPIO pin number for SCL
        sda_pin: GPIO pin number for SDA
        freq: I2C frequency in Hz
        
    Returns:
        Tuple of (I2C object, list of found addresses)
    """
    print(f"[I2C] Scanning on SCL={scl_pin}, SDA={sda_pin}...")
    
    i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=freq)
    addresses = i2c.scan()
    
    if addresses:
        print(f"[I2C] Found {len(addresses)} device(s):")
        for addr in addresses:
            print(f"[I2C]   - 0x{addr:02X}")
    else:
        print("[I2C] No devices found!")
    
    return i2c, addresses


def init_display(config):
    """
    Initialize the OLED display with I2C scanning.
    
    Args:
        config: Configuration module with pin definitions
        
    Returns:
        SSD1306_I2C display object
    """
    i2c, addresses = scan_i2c(config.SCL_PIN, config.SDA_PIN, config.I2C_FREQ)
    
    # Find OLED address (typically 0x3C or 0x3D)
    oled_addr = None
    for addr in addresses:
        if addr in (0x3C, 0x3D):
            oled_addr = addr
            break
    
    if oled_addr is None:
        if addresses:
            # Use first found address as fallback
            oled_addr = addresses[0]
            print(f"[OLED] Using address 0x{oled_addr:02X} (fallback)")
        else:
            # Use configured default
            oled_addr = config.OLED_ADDR
            print(f"[OLED] No device found, trying default 0x{oled_addr:02X}")
    else:
        print(f"[OLED] Using address 0x{oled_addr:02X}")
    
    try:
        display = ssd1306.SSD1306_I2C(
            config.OLED_WIDTH, 
            config.OLED_HEIGHT, 
            i2c, 
            addr=oled_addr
        )
        print(f"[OLED] Display initialized: {config.OLED_WIDTH}x{config.OLED_HEIGHT}")
        return display
    except Exception as e:
        print(f"[OLED] Failed to initialize display: {e}")
        raise


def show_message(display, lines, clear=True):
    """
    Display a multi-line text message on the OLED.
    
    Args:
        display: SSD1306 display object
        lines: List of strings to display
        clear: Whether to clear the display first
    """
    if clear:
        display.fill(0)
    
    y = 0
    for line in lines:
        display.text(line, 0, y, 1)
        y += 10
    
    display.show()


def show_error(display, title, message):
    """
    Display an error message on the OLED.
    
    Args:
        display: SSD1306 display object
        title: Error title
        message: Error message (can be multi-line string)
    """
    display.fill(0)
    display.text("ERROR", 0, 0, 1)
    display.text("-" * 16, 0, 10, 1)
    display.text(title[:16], 0, 20, 1)
    
    # Split message into lines
    y = 32
    words = message.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= 16:
            line += (" " if line else "") + word
        else:
            display.text(line[:16], 0, y, 1)
            y += 10
            line = word
            if y > 54:
                break
    if line and y <= 54:
        display.text(line[:16], 0, y, 1)
    
    display.show()


class SpectrumVisualizer:
    """
    Efficient spectrum bar visualization with smoothing and scaling.
    """
    
    def __init__(self, display, config):
        """
        Initialize the spectrum visualizer.
        
        Args:
            display: SSD1306 display object
            config: Configuration module
        """
        self.display = display
        self.config = config
        
        self.width = config.OLED_WIDTH
        self.height = config.OLED_HEIGHT
        self.num_bars = config.NUM_BARS
        self.bar_width = config.BAR_WIDTH
        self.bar_gap = config.BAR_GAP
        self.ema_alpha = config.EMA_ALPHA
        
        # Calculate bar positions
        total_bar_space = self.bar_width + self.bar_gap
        self.bar_x_positions = [i * total_bar_space for i in range(self.num_bars)]
        
        # Pre-allocate smoothed values
        self.smoothed_heights = [0.0] * self.num_bars
        self.prev_heights = [0] * self.num_bars
        
        # Scaling parameters
        self.log_scale = config.LOG_SCALE
        self.min_db = config.MIN_DB
        self.max_db = config.MAX_DB
        
        # Peak hold (optional visual enhancement)
        self.peak_heights = [0] * self.num_bars
        self.peak_decay = 0.95  # How fast peaks fall
        
        print(f"[Vis] Initialized: {self.num_bars} bars, {self.bar_width}px wide")
    
    def map_bins_to_bars(self, magnitudes):
        """
        Map FFT magnitude bins to visualization bars.
        Groups multiple FFT bins into each bar.
        
        Args:
            magnitudes: List of FFT magnitude values (N/2 bins)
            
        Returns:
            List of bar values (num_bars values)
        """
        num_bins = len(magnitudes)
        bins_per_bar = num_bins // self.num_bars
        
        if bins_per_bar < 1:
            bins_per_bar = 1
        
        bar_values = []
        for i in range(self.num_bars):
            start_bin = i * bins_per_bar
            end_bin = min(start_bin + bins_per_bar, num_bins)
            
            if start_bin < num_bins:
                # Average the magnitudes in this range
                bin_sum = sum(magnitudes[start_bin:end_bin])
                bin_count = end_bin - start_bin
                avg_mag = bin_sum / bin_count if bin_count > 0 else 0
                bar_values.append(avg_mag)
            else:
                bar_values.append(0)
        
        return bar_values
    
    def scale_to_pixels(self, magnitudes):
        """
        Scale magnitude values to pixel heights (0 to height-1).
        
        Args:
            magnitudes: List of magnitude values
            
        Returns:
            List of pixel heights (integers)
        """
        heights = []
        
        # Find max for normalization (with smoothing to avoid flicker)
        max_mag = max(magnitudes) if magnitudes else 1.0
        if max_mag < 0.001:
            max_mag = 0.001
        
        for mag in magnitudes:
            if self.log_scale:
                # Logarithmic scaling
                if mag < 1e-10:
                    db = self.min_db
                else:
                    db = 20 * math.log10(mag / max_mag)
                    db = max(db, self.min_db)
                
                # Map dB range to pixels
                normalized = (db - self.min_db) / (self.max_db - self.min_db)
            else:
                # Linear scaling
                normalized = mag / max_mag
            
            # Clamp and convert to pixels
            normalized = max(0.0, min(1.0, normalized))
            pixel_height = int(normalized * (self.height - 1))
            heights.append(pixel_height)
        
        return heights
    
    def apply_smoothing(self, heights):
        """
        Apply exponential moving average smoothing.
        
        Args:
            heights: List of new height values
            
        Returns:
            List of smoothed height values (integers)
        """
        result = []
        for i, h in enumerate(heights):
            # EMA: new_value = alpha * new + (1 - alpha) * old
            self.smoothed_heights[i] = (
                self.ema_alpha * h + 
                (1 - self.ema_alpha) * self.smoothed_heights[i]
            )
            result.append(int(self.smoothed_heights[i]))
        return result
    
    def draw_bars(self, heights):
        """
        Draw spectrum bars efficiently.
        Only updates changed regions for better performance.
        
        Args:
            heights: List of bar heights (0 to height-1)
        """
        # Clear only the visualization area (not the whole screen)
        # Actually, for simplicity and reliability, clear and redraw
        self.display.fill(0)
        
        for i, height in enumerate(heights):
            x = self.bar_x_positions[i]
            
            if height > 0:
                # Draw bar from bottom up
                # OLED coordinates: (0,0) is top-left, y increases downward
                y_top = self.height - height
                y_bottom = self.height - 1
                
                self.display.fill_rect(x, y_top, self.bar_width, height, 1)
            
            # Update peak (optional)
            if height > self.peak_heights[i]:
                self.peak_heights[i] = height
            else:
                self.peak_heights[i] = int(self.peak_heights[i] * self.peak_decay)
            
            # Draw peak marker (single pixel line above bar)
            if self.peak_heights[i] > height and self.peak_heights[i] > 0:
                peak_y = self.height - self.peak_heights[i] - 1
                if peak_y >= 0:
                    self.display.hline(x, peak_y, self.bar_width, 1)
        
        self.prev_heights = heights[:]
    
    def draw_bars_optimized(self, heights):
        """
        Optimized bar drawing that only updates changed bars.
        May be faster on some displays but can cause artifacts.
        
        Args:
            heights: List of bar heights
        """
        for i, height in enumerate(heights):
            prev_height = self.prev_heights[i]
            
            if height == prev_height:
                continue
            
            x = self.bar_x_positions[i]
            
            if height > prev_height:
                # Bar grew - add pixels at top
                y_top = self.height - height
                y_bottom = self.height - prev_height
                h = y_bottom - y_top
                if h > 0:
                    self.display.fill_rect(x, y_top, self.bar_width, h, 1)
            else:
                # Bar shrank - clear pixels at top
                y_top = self.height - prev_height
                y_bottom = self.height - height
                h = y_bottom - y_top
                if h > 0:
                    self.display.fill_rect(x, y_top, self.bar_width, h, 0)
        
        self.prev_heights = heights[:]
    
    def update(self, magnitudes):
        """
        Full update cycle: map bins, scale, smooth, and draw.
        
        Args:
            magnitudes: FFT magnitude values
        """
        # Map FFT bins to bars
        bar_values = self.map_bins_to_bars(magnitudes)
        
        # Scale to pixel heights
        heights = self.scale_to_pixels(bar_values)
        
        # Apply smoothing
        heights = self.apply_smoothing(heights)
        
        # Draw bars
        self.draw_bars(heights)
        
        # Update display
        self.display.show()
    
    def show_info(self, text, y_pos=0):
        """
        Show info text at top of display (useful for debugging).
        
        Args:
            text: Text to display
            y_pos: Y position
        """
        self.display.text(text[:16], 0, y_pos, 1)

