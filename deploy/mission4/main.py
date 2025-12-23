# ============================================================
# Mission 4: Mario-Like Endless Runner Game
# ============================================================
#
# FILES REQUIRED ON ESP32:
# ------------------------
# 1. ssd1306.py  - OLED display driver
# 2. main.py     - This file (the game)
#
# HARDWARE:
# ---------
# - OLED SSD1306 128x64 I2C (SDA=GPIO21, SCL=GPIO22)
# - BOOT button (GPIO0) - built-in on ESP32
# - No other wiring needed!
#
# HOW TO PLAY:
# ------------
# - Press BOOT to start
# - Short press = small jump
# - Long press (hold) = high jump
# - Avoid obstacles, get high score!
#
# DEPLOYMENT VIA THONNY:
# ----------------------
# 1. Copy ssd1306.py to ESP32 root (/)
# 2. Copy main.py to ESP32 root (/)
# 3. Reset ESP32 or press F5 to run
#
# ============================================================

import gc
import time
from machine import Pin, I2C
import ssd1306

# ============================================================
# GAME CONSTANTS
# ============================================================

# Display
SCREEN_W = 128
SCREEN_H = 64

# I2C Pins
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 400000

# Ground
GROUND_Y = 54  # Y position of ground line (from top)

# Player
PLAYER_X = 20      # Fixed horizontal position
PLAYER_W = 8       # Width
PLAYER_H = 12      # Height
GRAVITY = 1.0      # Gravity acceleration (pixels/frame^2)
JUMP_VEL = -9      # Short jump velocity
JUMP_VEL_HIGH = -13  # Long press jump velocity

# Obstacles
OBSTACLE_SPEED = 3     # Pixels per frame
MAX_OBSTACLES = 5      # Maximum active obstacles
MIN_SPAWN_FRAMES = 35  # Minimum frames between spawns
MAX_SPAWN_FRAMES = 70  # Maximum frames between spawns

# Obstacle types: (width, height)
OBSTACLE_TYPES = [
    (8, 16),   # Tall pipe
    (12, 10),  # Short wide block
    (6, 20),   # Very tall pipe
    (10, 8),   # Low block (need to jump)
]

# Button timing
DEBOUNCE_MS = 30
LONG_PRESS_MS = 200

# Frame timing
TARGET_FPS = 30
FRAME_MS = 1000 // TARGET_FPS

# Game states
STATE_START = 0
STATE_PLAY = 1
STATE_GAME_OVER = 2


# ============================================================
# BUTTON HANDLER
# ============================================================

class Button:
    """
    Handles BOOT button (GPIO0) with debounce and short/long press detection.
    BOOT button is active LOW with internal pull-up.
    """
    
    PRESS_NONE = 0
    PRESS_SHORT = 1
    PRESS_LONG = 2
    
    def __init__(self, pin_num=0):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self.last_state = 1  # Released (pulled high)
        self.press_start = 0
        self.last_check = 0
        self.pending_release = False
        self.press_duration = 0
    
    def update(self):
        """
        Call this every frame. Returns press type when button is released.
        Returns: PRESS_NONE, PRESS_SHORT, or PRESS_LONG
        """
        now = time.ticks_ms()
        current = self.pin.value()
        result = self.PRESS_NONE
        
        # Debounce: ignore changes within DEBOUNCE_MS
        if time.ticks_diff(now, self.last_check) < DEBOUNCE_MS:
            return result
        
        # Detect press (falling edge: 1 -> 0)
        if self.last_state == 1 and current == 0:
            self.press_start = now
            self.pending_release = True
        
        # Detect release (rising edge: 0 -> 1)
        elif self.last_state == 0 and current == 1 and self.pending_release:
            duration = time.ticks_diff(now, self.press_start)
            self.pending_release = False
            if duration >= LONG_PRESS_MS:
                result = self.PRESS_LONG
            else:
                result = self.PRESS_SHORT
        
        self.last_state = current
        self.last_check = now
        return result
    
    def is_pressed(self):
        """Check if button is currently held down."""
        return self.pin.value() == 0
    
    def get_hold_duration(self):
        """Get how long button has been held (0 if not pressed)."""
        if self.pending_release:
            return time.ticks_diff(time.ticks_ms(), self.press_start)
        return 0


# ============================================================
# PLAYER CLASS
# ============================================================

class Player:
    """
    Player character with jump physics.
    Uses fixed-point integers for velocity to avoid float allocations.
    """
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset player to starting state."""
        self.x = PLAYER_X
        self.y = GROUND_Y  # Bottom of player sprite
        self.vy = 0.0      # Vertical velocity
        self.on_ground = True
        self.jumping = False
    
    def jump(self, high=False):
        """Initiate a jump if on ground."""
        if self.on_ground:
            self.vy = JUMP_VEL_HIGH if high else JUMP_VEL
            self.on_ground = False
            self.jumping = True
    
    def update(self):
        """Update physics each frame."""
        if not self.on_ground:
            # Apply gravity
            self.vy += GRAVITY
            self.y += self.vy
            
            # Check ground collision
            if self.y >= GROUND_Y:
                self.y = GROUND_Y
                self.vy = 0.0
                self.on_ground = True
                self.jumping = False
    
    def get_top(self):
        """Get Y coordinate of player's top edge."""
        return int(self.y) - PLAYER_H
    
    def draw(self, display):
        """Draw player sprite."""
        top = self.get_top()
        # Simple rectangle player
        display.fill_rect(self.x, top, PLAYER_W, PLAYER_H, 1)
        # Add "eyes" to make it look like a character
        display.pixel(self.x + 2, top + 2, 0)
        display.pixel(self.x + 5, top + 2, 0)


# ============================================================
# OBSTACLE SYSTEM
# ============================================================

class Obstacle:
    """Single obstacle with position and dimensions."""
    
    def __init__(self):
        self.active = False
        self.x = 0
        self.width = 0
        self.height = 0
    
    def spawn(self, obstacle_type):
        """Activate obstacle at right edge of screen."""
        self.width, self.height = OBSTACLE_TYPES[obstacle_type]
        self.x = SCREEN_W
        self.active = True
    
    def update(self):
        """Move obstacle left."""
        if self.active:
            self.x -= OBSTACLE_SPEED
            # Deactivate when fully off screen
            if self.x < -self.width:
                self.active = False
    
    def get_top(self):
        """Get Y coordinate of obstacle's top edge."""
        return GROUND_Y - self.height
    
    def draw(self, display):
        """Draw obstacle."""
        if self.active:
            top = self.get_top()
            display.fill_rect(int(self.x), top, self.width, self.height, 1)


class ObstacleManager:
    """Manages spawning and updating all obstacles."""
    
    def __init__(self):
        # Preallocate obstacle pool
        self.obstacles = [Obstacle() for _ in range(MAX_OBSTACLES)]
        self.reset()
    
    def reset(self):
        """Reset all obstacles."""
        for obs in self.obstacles:
            obs.active = False
        self.spawn_timer = MIN_SPAWN_FRAMES
        self.spawn_counter = 0
    
    def update(self, difficulty=1.0):
        """Update all obstacles and spawn new ones."""
        # Update existing obstacles
        for obs in self.obstacles:
            obs.update()
        
        # Spawn timer
        self.spawn_counter += 1
        if self.spawn_counter >= self.spawn_timer:
            self._spawn_obstacle()
            # Randomize next spawn time (pseudo-random using time)
            t = time.ticks_ms() & 0xFF
            self.spawn_timer = MIN_SPAWN_FRAMES + (t % (MAX_SPAWN_FRAMES - MIN_SPAWN_FRAMES))
            self.spawn_counter = 0
    
    def _spawn_obstacle(self):
        """Spawn a new obstacle if slot available."""
        for obs in self.obstacles:
            if not obs.active:
                # Pick random obstacle type based on time
                t = time.ticks_ms()
                obstacle_type = t % len(OBSTACLE_TYPES)
                obs.spawn(obstacle_type)
                break
    
    def check_collision(self, player):
        """Check if player collides with any active obstacle."""
        px = player.x
        py = player.get_top()
        pw = PLAYER_W
        ph = PLAYER_H
        
        for obs in self.obstacles:
            if not obs.active:
                continue
            
            ox = int(obs.x)
            oy = obs.get_top()
            ow = obs.width
            oh = obs.height
            
            # AABB collision
            if (px < ox + ow and px + pw > ox and
                py < oy + oh and py + ph > oy):
                return True
        
        return False
    
    def draw(self, display):
        """Draw all active obstacles."""
        for obs in self.obstacles:
            obs.draw(display)


# ============================================================
# GAME CLASS
# ============================================================

class Game:
    """Main game controller."""
    
    def __init__(self, display):
        self.display = display
        self.button = Button(0)  # BOOT button
        self.player = Player()
        self.obstacles = ObstacleManager()
        self.state = STATE_START
        self.score = 0
        self.high_score = 0
        self.frame_count = 0
    
    def reset(self):
        """Reset game for new round."""
        self.player.reset()
        self.obstacles.reset()
        self.score = 0
        self.frame_count = 0
    
    def update(self):
        """Main update loop - call once per frame."""
        press = self.button.update()
        
        if self.state == STATE_START:
            self._update_start(press)
        elif self.state == STATE_PLAY:
            self._update_play(press)
        elif self.state == STATE_GAME_OVER:
            self._update_game_over(press)
    
    def _update_start(self, press):
        """Update start screen."""
        if press != Button.PRESS_NONE:
            self.reset()
            self.state = STATE_PLAY
            gc.collect()  # Clean memory before game starts
    
    def _update_play(self, press):
        """Update gameplay."""
        # Handle jump input
        if press == Button.PRESS_SHORT:
            self.player.jump(high=False)
        elif press == Button.PRESS_LONG:
            self.player.jump(high=True)
        
        # Check if button is being held for variable jump
        # (Jump higher if held longer while in air)
        
        # Update game objects
        self.player.update()
        self.obstacles.update()
        
        # Check collision
        if self.obstacles.check_collision(self.player):
            self.state = STATE_GAME_OVER
            if self.score > self.high_score:
                self.high_score = self.score
            return
        
        # Increment score
        self.frame_count += 1
        self.score = self.frame_count // 3  # Score increments every 3 frames
    
    def _update_game_over(self, press):
        """Update game over screen."""
        if press != Button.PRESS_NONE:
            self.state = STATE_START
            gc.collect()
    
    def render(self):
        """Render current game state."""
        self.display.fill(0)
        
        if self.state == STATE_START:
            self._render_start()
        elif self.state == STATE_PLAY:
            self._render_play()
        elif self.state == STATE_GAME_OVER:
            self._render_game_over()
        
        self.display.show()
    
    def _render_start(self):
        """Render start screen."""
        # Title
        self.display.text("MARIO RUNNER", 16, 10, 1)
        
        # Decorative line
        self.display.hline(10, 24, 108, 1)
        
        # Instructions
        self.display.text("Press BOOT", 24, 32, 1)
        self.display.text("to Start!", 28, 42, 1)
        
        # High score if exists
        if self.high_score > 0:
            self.display.text("Best:" + str(self.high_score), 36, 54, 1)
    
    def _render_play(self):
        """Render gameplay."""
        # Draw ground
        self.display.hline(0, GROUND_Y + 1, SCREEN_W, 1)
        # Ground texture (small marks)
        for x in range(0, SCREEN_W, 8):
            self.display.pixel(x, GROUND_Y + 2, 1)
        
        # Draw obstacles
        self.obstacles.draw(self.display)
        
        # Draw player
        self.player.draw(self.display)
        
        # Draw score (top right)
        score_str = str(self.score)
        self.display.text(score_str, SCREEN_W - len(score_str) * 8 - 2, 2, 1)
    
    def _render_game_over(self):
        """Render game over screen."""
        # Game Over text
        self.display.text("GAME OVER", 28, 12, 1)
        
        # Score
        self.display.text("Score:", 20, 28, 1)
        self.display.text(str(self.score), 68, 28, 1)
        
        # High score
        if self.score >= self.high_score:
            self.display.text("NEW BEST!", 28, 38, 1)
        else:
            self.display.text("Best:" + str(self.high_score), 28, 38, 1)
        
        # Restart instruction
        self.display.text("BOOT=Retry", 24, 52, 1)


# ============================================================
# OLED INITIALIZATION
# ============================================================

def init_oled():
    """Initialize I2C and OLED display with error handling."""
    print("[OLED] Initializing I2C...")
    
    try:
        i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
        
        # Scan for devices
        devices = i2c.scan()
        print(f"[OLED] I2C scan found: {[hex(d) for d in devices]}")
        
        if not devices:
            print("[OLED] ERROR: No I2C devices found!")
            return None
        
        # Look for OLED at 0x3C or 0x3D
        oled_addr = None
        for addr in devices:
            if addr in (0x3C, 0x3D):
                oled_addr = addr
                break
        
        if oled_addr is None:
            oled_addr = devices[0]  # Use first device as fallback
            print(f"[OLED] Using fallback address: 0x{oled_addr:02X}")
        else:
            print(f"[OLED] Found OLED at 0x{oled_addr:02X}")
        
        # Create display
        display = ssd1306.SSD1306_I2C(SCREEN_W, SCREEN_H, i2c, addr=oled_addr)
        print("[OLED] Display initialized successfully")
        return display
        
    except Exception as e:
        print(f"[OLED] ERROR: {e}")
        return None


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    """Main game entry point."""
    print("\n" + "=" * 40)
    print("Mission 4: Mario Runner")
    print("=" * 40)
    
    gc.collect()
    print(f"[Main] Free memory: {gc.mem_free()} bytes")
    
    # Initialize display
    display = init_oled()
    if display is None:
        print("[Main] FATAL: Could not initialize display")
        return
    
    # Show loading message
    display.fill(0)
    display.text("Loading...", 30, 28, 1)
    display.show()
    time.sleep_ms(500)
    
    # Create game
    game = Game(display)
    
    gc.collect()
    print(f"[Main] Free memory after init: {gc.mem_free()} bytes")
    print("[Main] Starting game loop...")
    print("[Main] Press BOOT button to play!\n")
    
    # Main game loop
    frame_count = 0
    last_gc = 0
    
    try:
        while True:
            frame_start = time.ticks_ms()
            
            # Update game
            game.update()
            
            # Render
            game.render()
            
            # Frame timing
            elapsed = time.ticks_diff(time.ticks_ms(), frame_start)
            sleep_time = FRAME_MS - elapsed
            if sleep_time > 0:
                time.sleep_ms(sleep_time)
            
            # Periodic garbage collection (every ~5 seconds)
            frame_count += 1
            if frame_count - last_gc > TARGET_FPS * 5:
                gc.collect()
                last_gc = frame_count
    
    except KeyboardInterrupt:
        print("\n[Main] Game stopped by user")
        display.fill(0)
        display.text("Goodbye!", 36, 28, 1)
        display.show()


# Run the game
if __name__ == "__main__":
    main()

