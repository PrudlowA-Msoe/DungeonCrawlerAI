"""
sprites.py

Utility module for loading and scaling sprite images for the dungeon tiles.

Responsibilities:
    - Locate sprite assets relative to the project directory.
    - Load PNG files using pygame.image.load.
    - Scale them to TILE_SIZE so they fit exactly one grid cell.
    - Expose named constants for each sprite:
        * SPRITE_WALL, SPRITE_PLAYER, SPRITE_MONSTER_MELEE, ...
"""
import os
import pygame
from config import TILE_SIZE

BASE_DIR = os.path.dirname(__file__)

def asset(path: str) -> str:
    """Build path"""
    return os.path.join(BASE_DIR, "..", "sprites", path)


def load_sprite(filename: str) -> pygame.Surface:
    """Load and scale sprite to one tile"""
    image = pygame.image.load(asset(filename))
    image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
    return image


SPRITE_WALL          = load_sprite("rock1.png")
SPRITE_PLAYER        = load_sprite("player.png")
SPRITE_MONSTER_MELEE = load_sprite("monster2.png")
SPRITE_MONSTER_MAGIC = load_sprite("monster1.png")
SPRITE_HEALTH        = load_sprite("health.png")
SPRITE_MANA          = load_sprite("bluepot.png")
SPRITE_EXIT          = load_sprite("exit.png")
SPRITE_COIN          = load_sprite("coin.png")

