# Mission 4: Mario-Like Endless Runner Game

## Overview

This mission implements a retro-style side-scrolling endless runner game that:
1. Uses only the OLED display (3 wires) and built-in BOOT button
2. Features jump physics with gravity
3. Spawns random obstacles to avoid
4. Tracks score and high score

## Architecture

```
main.py
├── Button          # Debounced input with short/long press detection
├── Player          # Character with jump physics
├── Obstacle        # Single obstacle entity
├── ObstacleManager # Pool-based obstacle spawning
└── Game            # State machine (START, PLAY, GAME_OVER)
```

## Quick Start

### For Deployment (Thonny/Windows)

Use the files in `deploy/mission4/` - they are ready to copy directly to the ESP32.

Upload to ESP32:
1. `ssd1306.py`
2. `main.py`

Press BOOT button to play!

## Controls

| Input | Action |
|-------|--------|
| Short press (<200ms) | Small jump |
| Long press (>200ms) | High jump |

## Game Mechanics

### Player Physics
- Fixed horizontal position (x=20)
- Gravity pulls player down each frame
- Jump applies upward velocity
- Ground collision stops fall

### Obstacles
- Spawn from right edge
- Move left at constant speed
- Multiple types (tall pipes, short blocks)
- Pooled for memory efficiency (max 5 active)

### Collision
- AABB (Axis-Aligned Bounding Box)
- Player hitbox vs obstacle hitbox
- Collision triggers Game Over

### Scoring
- Score increments every 3 frames
- High score persists during session

## Performance

- Target: 30 FPS
- Preallocated obstacle pool
- Periodic garbage collection
- No allocations in main loop

## File Structure

```
missions/mission4_mario_runner/
├── main.py     # Complete game in single file
└── README.md   # This file

deploy/mission4/
├── ssd1306.py  # OLED driver
├── main.py     # Game (copy of above)
└── README.md   # Deployment instructions
```

