from typing import Tuple, Optional
import random

from dungeon import Dungeon
from agent import Agent
from controllers import BaseController, RandomWalkerController, DecisionTreeController


MAX_STEPS_PER_EPISODE = 50


def manhattan(a, b) -> int:
    (x1, y1), (x2, y2) = a, b
    return abs(x1 - x2) + abs(y1 - y2)


def run_episode(
    controller: BaseController, seed: Optional[int] = None
) -> Tuple[bool, int, int, int, int, int, int, int]:
    """
    Run a single episode with the controller on a randomized 5x5 dungeon
    Returns:
        reached_exit: bool
        steps_taken: int
        total_damage_taken: int
        monsters_killed: int
        potions_collected: int
        initial_distance_to_exit: int
        final_distance_to_exit: int
        best_distance_to_exit: int
    """
    if seed is not None:
        random.seed(seed)

    controller.reset_episode()

    dungeon = Dungeon()
    dungeon.generate_random_layout(seed)

    agent = Agent(dungeon.start_pos)

    initial_dist = manhattan(agent.pos, dungeon.exit_pos)
    best_dist = initial_dist

    for step in range(MAX_STEPS_PER_EPISODE):
        action = controller.select_action(agent, dungeon)
        agent.step(action, dungeon)

        current_dist = manhattan(agent.pos, dungeon.exit_pos)
        if current_dist < best_dist:
            best_dist = current_dist

        # death
        if agent.health <= 0:
            final_dist = current_dist
            return (
                False,
                step + 1,
                agent.damage_taken,
                agent.monsters_killed,
                agent.potions_collected,
                initial_dist,
                final_dist,
                best_dist,
            )

        # success
        if agent.at_exit(dungeon):
            final_dist = 0
            best_dist = 0
            return (
                True,
                step + 1,
                agent.damage_taken,
                agent.monsters_killed,
                agent.potions_collected,
                initial_dist,
                final_dist,
                best_dist,
            )

    # timeout
    final_dist = manhattan(agent.pos, dungeon.exit_pos)
    return (
        False,
        MAX_STEPS_PER_EPISODE,
        agent.damage_taken,
        agent.monsters_killed,
        agent.potions_collected,
        initial_dist,
        final_dist,
        best_dist,
    )


def evaluate_controller(controller: BaseController, num_episodes: int = 10) -> float:
    """
    Fitness combining:
      + Big reward for reaching exit
      + Reward for the closest distance to exit reached in the episode
      + Reward for killing monsters and collecting potions
      - Penalty for damage
    """
    total_reward = 0.0

    for ep in range(num_episodes):
        (
            reached_exit,
            steps,
            damage_taken,
            monsters_killed,
            potions_collected,
            initial_dist,
            final_dist,
            best_dist,
        ) = run_episode(controller, seed=ep)

        dist_improvement = max(0, initial_dist - best_dist)

        if reached_exit:
            reward = 200.0 - 2.0 * steps
        else:
            reward = -30.0

        reward += 8.0 * dist_improvement

        # Reward combat
        reward += 10.0 * monsters_killed
        reward += 5.0 * potions_collected

        # Penalize damage
        reward -= 0.3 * damage_taken

        total_reward += reward

    return total_reward / num_episodes


if __name__ == "__main__":
    rw = RandomWalkerController()
    rw_fitness = evaluate_controller(rw)
    print(f"RandomWalkerController mean reward: {rw_fitness:.2f}")

    random_genome = DecisionTreeController.random_genome()
    dt = DecisionTreeController(genome=random_genome)
    dt_fitness = evaluate_controller(dt)
    print(f"Random DecisionTreeController mean reward: {dt_fitness:.2f}")


