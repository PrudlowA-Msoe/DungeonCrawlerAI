from enum import Enum, auto
from typing import List, Tuple, Optional
import random

import pygame

from config import GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, COLOR_GRID, COLOR_WALL, COLOR_EXIT


class TileType(Enum):
    EMPTY = auto()
    WALL = auto()
    EXIT = auto()
    # after train we will add: MONSTER_A, MONSTER_B, COIN, MANA_POTION, HEALTH_POTION, etc.


Grid = List[List[TileType]]
Pos = Tuple[int, int]


class Dungeon:
    """
    Represents a single dungeon floor.

    Currently: static 5x5 with a central obstacle and an exit in a corner.
    Later: extend to multiple floors and randomized layouts.
    """

    def __init__(self, width: int = GRID_WIDTH, height: int = GRID_HEIGHT):
        self.width = width
        self.height = height
        self.grid: Grid = [[TileType.EMPTY for _ in range(width)] for _ in range(height)]
        self.start_pos: Pos = (0, 0)
        self.exit_pos: Pos = (self.width - 1, self.height - 1)
        self._create_basic_layout()

    def _create_basic_layout(self) -> None:
        """Create the basic 5x5 with thing in middle"""
        # empty grid
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y][x] = TileType.EMPTY

        # central block in middle for training
        if self.width >= 3 and self.height >= 3:
            cx = self.width // 2
            cy = self.height // 2
            self.grid[cy][cx] = TileType.WALL

        # Start and exit pos
        self.start_pos = (0, 0)
        self.exit_pos = (self.width - 1, self.height - 1)
        self.grid[self.exit_pos[1]][self.exit_pos[0]] = TileType.EXIT

    def generate_random_layout(self, seed: Optional[int] = None) -> None:
        """
        For now just uses the basic layout but I will randomize walls,
        exit, monsters, items, etc later
        """
        if seed is not None:
            random.seed(seed)
        self._create_basic_layout()

    def reset(self) -> None:
        """Reset dungeon to its initial layout"""
        self._create_basic_layout()

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, x: int, y: int) -> TileType:
        return self.grid[y][x]

    def is_walkable(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        tile = self.get_tile(x, y)
        return tile != TileType.WALL  # later also exclude monsters

    # render in pygame

    def draw(self, surface: pygame.Surface) -> None:
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(
                    x * TILE_SIZE,
                    y * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                # lines for grid
                pygame.draw.rect(surface, COLOR_GRID, rect, width=1)

                tile = self.grid[y][x]
                if tile == TileType.WALL:
                    pygame.draw.rect(surface, COLOR_WALL, rect)
                elif tile == TileType.EXIT:
                    pygame.draw.rect(surface, COLOR_EXIT, rect)
