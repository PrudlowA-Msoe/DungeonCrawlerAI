import random
from typing import Any, List, Sequence

from agent import Action, Agent
from dungeon import Dungeon


class BaseController:
    """common interface for all controllers"""

    def select_action(self, agent: Agent, dungeon: Dungeon) -> Action:
        raise NotImplementedError


class RandomWalkerController(BaseController):
    """
    choose random valid move each step
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
    GA-trainable, movement-only, decision-tree-style controller.
    """

    # Movement-only action space for this controller
    ACTIONS: List[Action] = [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]

    def __init__(self, genome: Sequence[int]):
        if len(genome) != 9:
            raise ValueError(f"DecisionTreeController genome must have length 9, got {len(genome)}")
        # store as list[int]
        self.genome: List[int] = list(genome)

    # genetic helpers

    @classmethod
    def random_genome(cls) -> List[int]:
        """Create a random movement only genome."""
        return [random.randint(0, len(cls.ACTIONS) - 1) for _ in range(9)]

    @classmethod
    def num_genes(cls) -> int:
        return 9

    @classmethod
    def num_actions(cls) -> int:
        return len(cls.ACTIONS)

    # controller logic

    def _state_index_from_agent_and_exit(self, agent: Agent, dungeon: Dungeon) -> int:
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

        # Map (sx, sy) into [0 to 8]
        idx = (sx + 1) * 3 + (sy + 1)
        return idx

    def select_action(self, agent: Agent, dungeon: Dungeon) -> Action:
        """
        Map the relative exit direction (dx, dy) to an action via the genome.
        """
        idx = self._state_index_from_agent_and_exit(agent, dungeon)
        gene_value = self.genome[idx]
        # in case of bad mutate
        gene_value = gene_value % len(self.ACTIONS)
        action = self.ACTIONS[gene_value]

        return action
