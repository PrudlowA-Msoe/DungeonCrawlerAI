from typing import Tuple, Optional
import random

from src.dungeon import Dungeon
from src.agent import Agent
from src.controllers import BaseController, RandomWalkerController, DecisionTreeController


MAX_STEPS_PER_EPISODE = 50


def run_episode(controller: BaseController, seed: Optional[int] = None) -> Tuple[bool, int]:
    """
    Run a single episode with the given controller on the basic 5x5 dungeon.

    Returns:
        (reached_exit: bool, steps_taken: int)
    """
    if seed is not None:
        random.seed(seed)

    dungeon = Dungeon()
    agent = Agent(dungeon.start_pos)

    for step in range(MAX_STEPS_PER_EPISODE):
        action = controller.select_action(agent, dungeon)
        agent.step(action, dungeon)
        if agent.at_exit(dungeon):
            return True, step + 1

    return False, MAX_STEPS_PER_EPISODE


def evaluate_controller(controller: BaseController, num_episodes: int = 10) -> float:
    """
    evaluates fitness, only movement for rn
    """
    total_reward = 0.0
    for ep in range(num_episodes):
        reached_exit, steps = run_episode(controller, seed=ep)
        if reached_exit:
            total_reward += 100.0 - steps
        else:
            total_reward -= 10.0

    return total_reward / num_episodes


if __name__ == "__main__":
    # random vs decision tree
    rw = RandomWalkerController()
    rw_fitness = evaluate_controller(rw)
    print(f"RandomWalkerController mean reward: {rw_fitness:.2f}")

    random_genome = DecisionTreeController.random_genome()
    dt = DecisionTreeController(genome=random_genome)
    dt_fitness = evaluate_controller(dt)
    print(f"Random DecisionTreeController mean reward: {dt_fitness:.2f}")
