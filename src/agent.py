from enum import Enum, auto
from typing import Tuple

import pygame

from config import TILE_SIZE, COLOR_AGENT
from dungeon import Dungeon, TileType
from sprites import SPRITE_PLAYER


Pos = Tuple[int, int]


class Action(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    STAY = auto()
    MELEE = auto()
    MAGIC_BLAST = auto()
    DRINK_HEALTH = auto()
    DRINK_MANA = auto()


class Agent:
    """
    The controlled agent
    - Position
    - Health n mana
    - Health/mana potions
    - Melee and magic attacks
    - Tracks damage, monsters killed, potions collected, coins collected
    """

    def __init__(self, start_pos: Pos):
        self.start_pos: Pos = start_pos
        self.x, self.y = start_pos

        self.max_health: int = 100
        self.health: int = self.max_health

        self.max_mana: int = 3
        self.mana: int = self.max_mana

        self.health_potions: int = 0
        self.mana_potions: int = 0

        # fitness trackers
        self.damage_taken: int = 0
        self.monsters_killed: int = 0
        self.potions_collected: int = 0
        self.coins_collected: int = 0  # NEW

    @property
    def pos(self) -> Pos:
        return (self.x, self.y)

    def reset(self) -> None:
        """Reset agent to start of the current floor"""
        self.x, self.y = self.start_pos
        self.health = self.max_health
        self.mana = self.max_mana
        self.health_potions = 0
        self.mana_potions = 0
        self.damage_taken = 0
        self.monsters_killed = 0
        self.potions_collected = 0
        self.coins_collected = 0

    def take_damage(self, amount: int) -> None:
        if amount <= 0:
            return
        self.health -= amount
        self.damage_taken += amount

    def melee_attack(self, dungeon: Dungeon) -> None:
        """Sword attack kills melee-weak monster"""
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
            x, y = self.x + dx, self.y + dy
            if dungeon.in_bounds(x, y) and dungeon.get_tile(x, y) == TileType.MONSTER_MELEE:
                dungeon.clear_tile(x, y)
                self.monsters_killed += 1
                break

    def magic_blast(self, dungeon: Dungeon) -> None:
        """Magic blast consumes 1 mana, kills magic-weak monster"""
        if self.mana <= 0:
            return
        self.mana -= 1

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
            x, y = self.x + dx, self.y + dy
            if dungeon.in_bounds(x, y) and dungeon.get_tile(x, y) == TileType.MONSTER_MAGIC:
                dungeon.clear_tile(x, y)
                self.monsters_killed += 1
                break

    def drink_health_potion(self) -> None:
        if self.health_potions > 0 and self.health < self.max_health:
            self.health_potions -= 1
            self.health = min(self.max_health, self.health + 40)

    def drink_mana_potion(self) -> None:
        if self.mana_potions > 0 and self.mana < self.max_mana:
            self.mana_potions -= 1
            self.mana = self.max_mana

    def _pickup_tile(self, dungeon: Dungeon) -> None:
        """Pick up items by moving over them"""
        tile = dungeon.get_tile(self.x, self.y)

        if tile == TileType.HEALTH_POTION:
            self.health_potions += 1
            self.potions_collected += 1
            dungeon.clear_tile(self.x, self.y)

        elif tile == TileType.MANA_POTION:
            self.mana_potions += 1
            self.potions_collected += 1
            dungeon.clear_tile(self.x, self.y)

        elif tile == TileType.COIN:
            self.coins_collected += 1
            dungeon.clear_tile(self.x, self.y)

    def step(self, action: Action, dungeon: Dungeon) -> None:
        """Apply an action"""
        dx, dy = 0, 0

        # Movement
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
        elif action == Action.MELEE:
            self.melee_attack(dungeon)
        elif action == Action.MAGIC_BLAST:
            self.magic_blast(dungeon)
        elif action == Action.DRINK_HEALTH:
            self.drink_health_potion()
        elif action == Action.DRINK_MANA:
            self.drink_mana_potion()

        # Actually move
        if action in (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT, Action.STAY):
            new_x = self.x + dx
            new_y = self.y + dy
            if dungeon.is_walkable(new_x, new_y):
                self.x = new_x
                self.y = new_y

        # Pickup items and then take monster damage
        self._pickup_tile(dungeon)
        dungeon.apply_monster_damage(self)

    def at_exit(self, dungeon: Dungeon) -> bool:
        return (self.x, self.y) == dungeon.exit_pos

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(
            SPRITE_PLAYER,
            (self.x * TILE_SIZE, self.y * TILE_SIZE),
        )



