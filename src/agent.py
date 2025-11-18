from enum import Enum, auto
from typing import Tuple

import pygame

from config import TILE_SIZE, COLOR_AGENT
from dungeon import Dungeon


Pos = Tuple[int, int]


class Action(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    STAY = auto()


class Agent:
    """
    The controlled agent.

    for now just position + basic movement.
    later we will add health, mana, inventory, combat, etc.
    """

    def __init__(self, start_pos: Pos):
        self.start_pos: Pos = start_pos
        self.x, self.y = start_pos
        self.health: int = 100
        self.mana: int = 0

    @property
    def pos(self) -> Pos:
        return (self.x, self.y)

    def reset(self) -> None:
        """Reset agent to start of the current floor"""
        self.x, self.y = self.start_pos
        self.health = 100
        self.mana = 0

    def step(self, action: Action, dungeon: Dungeon) -> None:
        """move if tile is walkable"""
        dx, dy = 0, 0
        if action == Action.UP:
            dy = -1
        elif action == Action.DOWN:
            dy = 1
        elif action == Action.LEFT:
            dx = -1
        elif action == Action.RIGHT:
            dx = 1
        elif action == Action.STAY:
            dx = dy = 0

        new_x = self.x + dx
        new_y = self.y + dy

        if dungeon.is_walkable(new_x, new_y):
            self.x = new_x
            self.y = new_y
        # after train handle stepping onto monsters / items, taking damage, etc.

    def at_exit(self, dungeon: Dungeon) -> bool:
        return (self.x, self.y) == dungeon.exit_pos

    # render pygame

    def draw(self, surface: pygame.Surface) -> None:
        rect = pygame.Rect(
            self.x * TILE_SIZE + 8,
            self.y * TILE_SIZE + 8,
            TILE_SIZE - 16,
            TILE_SIZE - 16,
        )
        pygame.draw.rect(surface, COLOR_AGENT, rect)
