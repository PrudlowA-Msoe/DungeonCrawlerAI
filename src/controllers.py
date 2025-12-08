import random
from typing import List, Sequence, Tuple

from agent import Action, Agent
from dungeon import Dungeon, TileType


class BaseController:
    """interface for controllers"""

    def select_action(self, agent: Agent, dungeon: Dungeon) -> Action:
        raise NotImplementedError

    def reset_episode(self) -> None:
        """reset internal state"""
        pass


class RandomWalkerController(BaseController):
    """
    avoid combat
    """

    def select_action(self, agent: Agent, dungeon: Dungeon) -> Action:
        candidate_actions = [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]
        valid_actions = []

        for action in candidate_actions:
            dx, dy = 0, 0
            if action == Action.UP:
                dy = -1
            elif action == Action.DOWN:
                dy = 1
            elif action == Action.LEFT:
                dx = -1
            elif action == Action.RIGHT:
                dx = 1

            new_x = agent.x + dx
            new_y = agent.y + dy
            if dungeon.is_walkable(new_x, new_y):
                valid_actions.append(action)

        if not valid_actions:
            return Action.STAY
        return random.choice(valid_actions)


class DecisionTreeController(BaseController):
    """
    GA-trainable decision-tree-style controller

    State features:
      - Exit sector: (sign(dx), sign(dy)) E {-1,0,1}^2  has 9 values
      - Adjacent enemy type: none / melee / magic / both has 4 values
      - Potion adjacent 0/1
      - Has mana 0/1
      - Front (toward exit) blocked by a wall 0/1

    Total states: 9 * 4 * 2 * 2 * 2 = 288
    Genome: length-288 list of action indices into ACTIONS
    """

    ACTIONS: List[Action] = [
        Action.UP,
        Action.DOWN,
        Action.LEFT,
        Action.RIGHT,
        Action.MELEE,
        Action.MAGIC_BLAST,
        Action.DRINK_HEALTH,
        Action.DRINK_MANA,
    ]

    @classmethod
    def num_actions(cls) -> int:
        return len(cls.ACTIONS)

    @classmethod
    def num_genes(cls) -> int:
        # exit sector * enemy_adj_type * potion_adj * has_mana * front_blocked
        return 9 * 4 * 2 * 2 * 2

    @classmethod
    def random_genome(cls) -> List[int]:
        """Create a random genome over the expanded action set"""
        return [random.randint(0, cls.num_actions() - 1) for _ in range(cls.num_genes())]

    def __init__(self, genome: Sequence[int]):
        genome = list(genome)
        if len(genome) != self.num_genes():
            raise ValueError(f"DecisionTreeController genome must have length {self.num_genes()}, got {len(genome)}")
        self.genome: List[int] = genome

        # mem for loops
        self.prev_positions: List[Tuple[int, int]] = []


    def reset_episode(self) -> None:
        self.prev_positions.clear()


    def _get_enemy_adj_type(self, agent: Agent, dungeon: Dungeon) -> int:
        """
        Return:
            0 = no adj monsters
            1 = meleeweak monsters only
            2 = magicweak monsters only
            3 = both types adj
        """
        has_melee = False
        has_magic = False

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
            x, y = agent.x + dx, agent.y + dy
            if dungeon.in_bounds(x, y):
                tile = dungeon.get_tile(x, y)
                if tile == TileType.MONSTER_MELEE:
                    has_melee = True
                elif tile == TileType.MONSTER_MAGIC:
                    has_magic = True

        if has_melee and has_magic:
            return 3
        if has_melee:
            return 1
        if has_magic:
            return 2
        return 0

    def _has_adjacent_potion(self, agent: Agent, dungeon: Dungeon) -> int:
        """Return 1 if any adj cell has a potion else 0."""
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
            x, y = agent.x + dx, agent.y + dy
            if dungeon.in_bounds(x, y):
                tile = dungeon.get_tile(x, y)
                if tile in (TileType.HEALTH_POTION, TileType.MANA_POTION):
                    return 1
        return 0

    def _exit_sector(self, agent: Agent, dungeon: Dungeon) -> int:
        """Return 0 to 8 encoding (sign(dx), sign(dy))"""
        exit_x, exit_y = dungeon.exit_pos
        dx = exit_x - agent.x
        dy = exit_y - agent.y

        def sign(v: int) -> int:
            if v < 0:
                return -1
            elif v > 0:
                return 1
            return 0

        sx = sign(dx)  # -1, 0, 1
        sy = sign(dy)  # -1, 0, 1
        return (sx + 1) * 3 + (sy + 1)  # 0..8

    def _front_blocked(self, agent: Agent, dungeon: Dungeon) -> int:
        """
        get a front direction that minmizes distance to the exit
        then check if that tile is walkable If it's blocked
        return 1; else 0
        """
        exit_x, exit_y = dungeon.exit_pos
        dx = exit_x - agent.x
        dy = exit_y - agent.y

        # Already at exit so front doesn't really matter
        if dx == 0 and dy == 0:
            return 0

        # Choose axis with larger |delta| as "front"
        if abs(dx) >= abs(dy) and dx != 0:
            step = (1, 0) if dx > 0 else (-1, 0)
        else:
            step = (0, 1) if dy > 0 else (0, -1)

        fx = agent.x + step[0]
        fy = agent.y + step[1]

        if not dungeon.is_walkable(fx, fy):
            return 1
        return 0

    def _state_index(self, agent: Agent, dungeon: Dungeon) -> int:
        exit_index = self._exit_sector(agent, dungeon)              # 0 to 8
        enemy_type = self._get_enemy_adj_type(agent, dungeon)       # 0 ti 3
        potion_adj = self._has_adjacent_potion(agent, dungeon)      # 0/1
        has_mana = 1 if agent.mana > 0 else 0                       # 0/1
        front_blocked = self._front_blocked(agent, dungeon)         # 0/1

        # ((((exit * 4 + enemy) * 2 + potion) * 2 + has_mana) * 2 + front_blocked)
        idx = exit_index
        idx = idx * 4 + enemy_type
        idx = idx * 2 + potion_adj
        idx = idx * 2 + has_mana
        idx = idx * 2 + front_blocked
        return idx

    @staticmethod
    def _manhattan_to_exit(x: int, y: int, dungeon: Dungeon) -> int:
        ex, ey = dungeon.exit_pos
        return abs(ex - x) + abs(ey - y)

    def _has_adjacent_monster_type(self, agent: Agent, dungeon: Dungeon, monster_type: TileType) -> bool:
        """True if any monster of given type exists adj or next to"""
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
            x, y = agent.x + dx, agent.y + dy
            if dungeon.in_bounds(x, y) and dungeon.get_tile(x, y) == monster_type:
                return True
        return False

    def _best_walkable_move(self, agent: Agent, dungeon: Dungeon) -> Action:
        """
        Choose move that minimizes distance to exit
        """
        candidates: List[Tuple[Action, int]] = []
        for move in (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT):
            dx, dy = 0, 0
            if move == Action.UP:
                dy = -1
            elif move == Action.DOWN:
                dy = 1
            elif move == Action.LEFT:
                dx = -1
            elif move == Action.RIGHT:
                dx = 1
            nx = agent.x + dx
            ny = agent.y + dy
            if dungeon.is_walkable(nx, ny):
                dist = self._manhattan_to_exit(nx, ny, dungeon)
                candidates.append((move, dist))

        if not candidates:
            return Action.STAY

        min_dist = min(d for _, d in candidates)
        best = [a for a, d in candidates if d == min_dist]
        return random.choice(best)

    def _fix_blocked_move(self, agent: Agent, dungeon: Dungeon, action: Action) -> Action:
        """
        If the action is a move into a wall pick another walkable
        movement action that gives the smallest Manhattan dist to exit
        """
        if action not in (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT):
            return action

        dx, dy = 0, 0
        if action == Action.UP:
            dy = -1
        elif action == Action.DOWN:
            dy = 1
        elif action == Action.LEFT:
            dx = -1
        elif action == Action.RIGHT:
            dx = 1

        new_x = agent.x + dx
        new_y = agent.y + dy

        if dungeon.is_walkable(new_x, new_y):
            return action

        return self._best_walkable_move(agent, dungeon)

    def _sanitize_action(self, agent: Agent, dungeon: Dungeon, action: Action) -> Action:
        """
        Make obviously bad actions more sensible without changing genome
          - Avoid spamming DRINK when no potion / already full
          - Avoid MAGIC_BLAST with no mana
          - Switch between MELEE / MAGIC_BLAST when the "wrong" attack is chosen
        """

        # 1) Drinking health when we have no potions or are full move instead
        if action == Action.DRINK_HEALTH:
            if agent.health_potions <= 0 or agent.health >= agent.max_health:
                return self._best_walkable_move(agent, dungeon)
            return action

        if action == Action.DRINK_MANA:
            if agent.mana_potions <= 0 or agent.mana >= agent.max_mana:
                return self._best_walkable_move(agent, dungeon)
            return action

        if action == Action.MAGIC_BLAST:
            if agent.mana <= 0:
                if agent.mana_potions > 0 and agent.mana < agent.max_mana:
                    return Action.DRINK_MANA
                return self._best_walkable_move(agent, dungeon)

            if not self._has_adjacent_monster_type(agent, dungeon, TileType.MONSTER_MAGIC):
                if self._has_adjacent_monster_type(agent, dungeon, TileType.MONSTER_MELEE):
                    return Action.MELEE
                return self._best_walkable_move(agent, dungeon)

            return action

        if action == Action.MELEE:
            has_melee = self._has_adjacent_monster_type(agent, dungeon, TileType.MONSTER_MELEE)
            has_magic = self._has_adjacent_monster_type(agent, dungeon, TileType.MONSTER_MAGIC)

            if has_melee:
                return action

            if has_magic:
                if agent.mana > 0:
                    return Action.MAGIC_BLAST
                if agent.mana_potions > 0 and agent.mana < agent.max_mana:
                    return Action.DRINK_MANA
                return self._best_walkable_move(agent, dungeon)

            return self._best_walkable_move(agent, dungeon)

        return action

    def _explore_move(self, agent: Agent, dungeon: Dungeon, avoid: Action) -> Action:
        """
        choose different movement if stuck
        """
        moves = [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]
        candidates: List[Action] = []

        for move in moves:
            if move == avoid:
                continue
            dx, dy = 0, 0
            if move == Action.UP:
                dy = -1
            elif move == Action.DOWN:
                dy = 1
            elif move == Action.LEFT:
                dx = -1
            elif move == Action.RIGHT:
                dx = 1
            nx = agent.x + dx
            ny = agent.y + dy
            if dungeon.is_walkable(nx, ny):
                candidates.append(move)

        if candidates:
            return random.choice(candidates)
        return avoid

    def _is_stuck_loop(self) -> bool:
        """
        movement loop detector
        """
        if len(self.prev_positions) < 3:
            return False
        if self.prev_positions[-1] == self.prev_positions[-3]:
            return True
        if len(self.prev_positions) >= 4:
            a, b, c, d = self.prev_positions[-4:]
            if a == c and b == d:
                return True
        return False


    def select_action(self, agent: Agent, dungeon: Dungeon) -> Action:
        self.prev_positions.append(agent.pos)
        if len(self.prev_positions) > 8:
            self.prev_positions.pop(0)

        stuck = self._is_stuck_loop()

        idx = self._state_index(agent, dungeon)
        gene_value = self.genome[idx] % self.num_actions()
        action = self.ACTIONS[gene_value]

        action = self._sanitize_action(agent, dungeon, action)
        # avoid wall
        action = self._fix_blocked_move(agent, dungeon, action)

        # if looping force a diff move
        if stuck and action in (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT):
            action = self._explore_move(agent, dungeon, avoid=action)

        return action


