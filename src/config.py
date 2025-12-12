"""
config.py

Central configuration for the dungeon project.

Contains:
    - Grid and rendering settings:
        * GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, FPS
        * Colors for background and tile types

    - Spawn parameters for random dungeon generation:
        * Max number of monsters, potions, coins per floor

    - Any other global constants used across multiple modules.

Changing values here lets you quickly adjust the difficulty or visuals
without touching the core logic in dungeon.py, agent.py, or controllers.py.
"""
GRID_WIDTH = 5
GRID_HEIGHT = 5
TILE_SIZE = 96  # pixels, so window is 480x480
FPS = 1

# Colors (R, G, B)
COLOR_BG = (25, 25, 35)
COLOR_GRID = (60, 60, 80)
COLOR_WALL = (90, 90, 90)
COLOR_EXIT = (50, 200, 70)
COLOR_AGENT = (230, 220, 80)
COLOR_MONSTER_MELEE = (200, 80, 80)
COLOR_MONSTER_MAGIC = (80, 80, 200)
COLOR_HEALTH_POTION = (200, 0, 200)
COLOR_MANA_POTION = (0, 200, 200)
COLOR_COIN = (240, 200, 60)

