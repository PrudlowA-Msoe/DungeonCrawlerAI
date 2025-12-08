from enum import Enum, auto
from typing import List, Tuple, Optional
from collections import deque
import random

import pygame

from config import (
    GRID_WIDTH,
    GRID_HEIGHT,
    TILE_SIZE,
    COLOR_GRID,
    COLOR_WALL,
    COLOR_EXIT,
    COLOR_MONSTER_MELEE,
    COLOR_MONSTER_MAGIC,
    COLOR_HEALTH_POTION,
    COLOR_MANA_POTION,
)

from sprites import (
    SPRITE_WALL,
    SPRITE_MONSTER_MELEE,
    SPRITE_MONSTER_MAGIC,
    SPRITE_HEALTH,
    SPRITE_MANA,
    SPRITE_EXIT,
    SPRITE_COIN,
)


class TileType(Enum):
    EMPTY = auto()
    WALL = auto()
    EXIT = auto()
    MONSTER_MELEE = auto()
    MONSTER_MAGIC = auto()
    HEALTH_POTION = auto()
    MANA_POTION = auto()


Grid = List[List[TileType]]
Pos = Tuple[int, int]


class Dungeon:
    """
    dungeon floor on a 5x5 grid
    """

    def __init__(self, width: int = GRID_WIDTH, height: int = GRID_HEIGHT):
        self.width = width
        self.height = height
        self.grid: Grid = [[TileType.EMPTY for _ in range(width)] for _ in range(height)]
        self.start_pos: Pos = (0, 0)
        self.exit_pos: Pos = (self.width - 1, self.height - 1)
        self._create_basic_layout()

    def _create_basic_layout(self) -> None:
        """Simple"""
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y][x] = TileType.EMPTY

        # Central wall
        if self.width >= 3 and self.height >= 3:
            cx = self.width // 2
            cy = self.height // 2
            self.grid[cy][cx] = TileType.WALL

        self.start_pos = (0, 0)
        self.exit_pos = (self.width - 1, self.height - 1)
        self.grid[self.exit_pos[1]][self.exit_pos[0]] = TileType.EXIT

    def _has_path_start_to_exit(self) -> bool:
        """Check that there's a path from start to exit"""
        sx, sy = self.start_pos
        ex, ey = self.exit_pos
        q = deque([(sx, sy)])
        visited = {(sx, sy)}

        while q:
            x, y = q.popleft()
            if (x, y) == (ex, ey):
                return True
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if self.in_bounds(nx, ny) and self.grid[ny][nx] != TileType.WALL and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    q.append((nx, ny))

        return False

    def generate_random_layout(self, seed: Optional[int] = None) -> None:
        """
        Randomized layout
        - Random walls (but always a path from start to exit)
        - Random monsters and potions on empty cells
        """
        if seed is not None:
            random.seed(seed)

        # randomize walls but enforce connectivity via BFS
        attempts = 0
        while True:
            attempts += 1

            # Clear grid
            for y in range(self.height):
                for x in range(self.width):
                    self.grid[y][x] = TileType.EMPTY

            self.start_pos = (0, 0)
            self.exit_pos = (self.width - 1, self.height - 1)

            for y in range(self.height):
                for x in range(self.width):
                    if (x, y) in (self.start_pos, self.exit_pos):
                        continue
                    if random.random() < 0.2:
                        self.grid[y][x] = TileType.WALL

            self.grid[self.start_pos[1]][self.start_pos[0]] = TileType.EMPTY
            self.grid[self.exit_pos[1]][self.exit_pos[0]] = TileType.EXIT

            if self._has_path_start_to_exit():
                break

            if attempts > 100:
                self._create_basic_layout()
                return

        empty_cells = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.grid[y][x] == TileType.EMPTY and (x, y) not in (self.start_pos, self.exit_pos)
        ]
        random.shuffle(empty_cells)

        max_monsters = 2
        num_monsters = min(random.randint(0, max_monsters), len(empty_cells))
        for i in range(num_monsters):
            x, y = empty_cells.pop()
            if i % 2 == 0:
                self.grid[y][x] = TileType.MONSTER_MELEE
            else:
                self.grid[y][x] = TileType.MONSTER_MAGIC

        max_potions = 2
        num_potions = min(random.randint(0, max_potions), len(empty_cells))
        for j in range(num_potions):
            x, y = empty_cells.pop()
            if j % 2 == 0:
                self.grid[y][x] = TileType.HEALTH_POTION
            else:
                self.grid[y][x] = TileType.MANA_POTION

    def reset(self) -> None:
        """Reset dungeon to simple layout"""
        self._create_basic_layout()


    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, x: int, y: int) -> TileType:
        return self.grid[y][x]

    def set_tile(self, x: int, y: int, tile_type: TileType) -> None:
        self.grid[y][x] = tile_type

    def clear_tile(self, x: int, y: int) -> None:
        self.grid[y][x] = TileType.EMPTY

    def is_walkable(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        tile = self.get_tile(x, y)
        return tile != TileType.WALL

    def apply_monster_damage(self, agent: "Agent") -> None:
        """
        Apply melee damage from monsters
        """
        from agent import Agent
        assert isinstance(agent, Agent)

        damage = 0
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
            x, y = agent.x + dx, agent.y + dy
            if self.in_bounds(x, y) and self.grid[y][x] in (
                TileType.MONSTER_MELEE,
                TileType.MONSTER_MAGIC,
            ):
                damage += 5

        if damage > 0:
            agent.take_damage(damage)


    def draw(self, surface: pygame.Surface) -> None:
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(
                    x * TILE_SIZE,
                    y * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )

                pygame.draw.rect(surface, COLOR_GRID, rect, width=1)

                tile = self.grid[y][x]
                pos = rect.topleft

                if tile == TileType.WALL:
                    surface.blit(SPRITE_WALL, pos)
                elif tile == TileType.EXIT:
                    surface.blit(SPRITE_EXIT, pos)
                elif tile == TileType.MONSTER_MELEE:
                    surface.blit(SPRITE_MONSTER_MELEE, pos)
                elif tile == TileType.MONSTER_MAGIC:
                    surface.blit(SPRITE_MONSTER_MAGIC, pos)
                elif tile == TileType.HEALTH_POTION:
                    surface.blit(SPRITE_HEALTH, pos)
                elif tile == TileType.MANA_POTION:
                    surface.blit(SPRITE_MANA, pos)
                # if/when you add coins:
                # elif tile == TileType.COIN:
                #     surface.blit(SPRITE_COIN, pos)


