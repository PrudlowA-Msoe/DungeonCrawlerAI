"""
main.py

Interactive PyGame front-end for visualizing the dungeon and controllers.

Features:
    - Spawns a sequence of random dungeon floors (MAX_FLOORS).
    - Creates an Agent and a DecisionTreeController using BEST_GENOME.
    - Allows toggling between human keyboard control and AI control.
    - Draws the dungeon, agent, HUD text, and tracks last few AI actions.
    - Logs per-floor statistics (steps, damage, kills, coins, potions, score).

Controls:
    - Arrow keys: Move the agent (when human control is active).
    - A: Toggle AI controller on/off.
    - R: Restart from floor 1 with freshly randomized floors.
    - ESC / window close: Quit.
"""
import sys
from typing import Optional, Tuple, List

import pygame

from config import GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, FPS, COLOR_BG
from dungeon import Dungeon
from agent import Agent, Action
from controllers import DecisionTreeController

# Best genome from GA
BEST_GENOME = [5, 0, 7, 7, 5, 1, 2, 7, 4, 7, 5, 5, 6, 4, 4, 4, 2, 2, 4, 1, 7, 3, 2, 3, 3, 1, 7, 2, 6, 1, 1, 2, 1, 0, 0, 1, 6, 5, 4, 0, 7, 3, 6, 7, 2, 6, 7, 6, 1, 4, 7, 6, 5, 1, 4, 1, 4, 5, 2, 3, 1, 0, 3, 4, 1, 6, 7, 4, 2, 3, 6, 0, 0, 3, 4, 4, 0, 7, 3, 6, 2, 3, 1, 0, 0, 2, 6, 4, 7, 5, 7, 1, 1, 0, 5, 0, 6, 2, 1, 0, 5, 0, 7, 3, 2, 6, 6, 0, 5, 1, 7, 7, 5, 1, 5, 4, 3, 0, 0, 3, 5, 5, 3, 7, 1, 2, 4, 5, 6, 6, 3, 1, 3, 7, 2, 7, 0, 1, 3, 2, 2, 6, 6, 6, 1, 5, 6, 4, 2, 0, 2, 5, 6, 1, 1, 2, 1, 1, 2, 6, 7, 0, 7, 7, 3, 4, 4, 5, 7, 6, 2, 5, 6, 3, 4, 2, 4, 4, 3, 6, 5, 3, 2, 0, 3, 0, 0, 5, 5, 2, 5, 0, 3, 0, 5, 4, 0, 4, 3, 4, 3, 5, 0, 2, 2, 6, 4, 7, 5, 5, 6, 0, 4, 4, 7, 7, 0, 6, 7, 6, 5, 3, 5, 7, 1, 5, 1, 1, 4, 6, 1, 7, 1, 6, 2, 6, 6, 3, 3, 2, 7, 5, 1, 6, 1, 7, 6, 1, 2, 4, 3, 4, 5, 7, 6, 6, 0, 4, 5, 2, 7, 0, 6, 7, 2, 6, 5, 3, 7, 4, 5, 7, 6, 0, 0, 7, 6, 0, 0, 1, 5, 6, 4, 2, 2, 1, 2, 0, 0, 5, 7, 4, 3, 2, 4, 4, 4, 3, 6, 7, 5, 4, 6, 4, 5, 6, 7, 4, 2, 7, 0, 0, 4, 7, 3, 5, 4, 4, 2, 7, 4, 5, 7, 2, 6, 5, 7, 7, 5, 7, 4, 1, 0, 3, 5, 6, 7, 5, 4, 4, 4, 6, 7, 5, 7, 5, 5, 4, 3, 5, 1, 5, 3, 1, 5, 3, 7, 1, 1, 1, 2, 1, 4, 5, 4, 0, 0, 6, 0, 5, 5, 1, 2, 7, 6, 2, 7, 3, 6, 4, 3, 7, 7, 7, 2, 1, 4, 6, 0, 0, 3, 6, 7, 5, 1, 2, 6, 4, 1, 2, 5, 7, 0, 0, 4, 6, 7, 0, 0, 7, 1, 3, 2, 6, 6, 1, 3, 4, 7, 7, 2, 7, 2, 2, 3, 2, 4, 0, 5, 1, 3, 3, 2, 5, 3, 4, 3, 4, 2, 6, 2, 1, 2, 7, 3, 3, 4, 7, 0, 3, 3, 1, 3, 2, 7, 7, 6, 1, 2, 6, 5, 0, 7, 5, 5, 1, 4, 1, 3, 2, 2, 7, 7, 7, 1, 2, 2, 5, 5, 6, 4, 6, 1, 5, 2, 6, 7, 5, 6, 4, 5, 6, 7, 7, 1, 7, 3, 1, 4, 5, 7, 1, 2, 0, 2, 4, 7, 7, 5, 4, 7, 6, 1, 1, 5, 4, 1, 1, 3, 7, 0, 6, 7, 4, 0, 2, 6, 5, 7, 5, 5, 4, 1, 5, 6, 2, 7, 3, 4, 1, 1, 1, 5, 5, 3, 5, 4, 4, 6, 4, 5, 2, 7, 3, 1, 3, 5, 1, 3, 6, 5, 7, 7, 3, 4, 7, 5, 2, 1, 5, 5, 0, 4, 3, 7, 2]


MAX_FLOORS = 5


def handle_keyboard_input() -> Optional[Action]:
    """Map raw keyboard input to an Action for human control.

        Returns:
            Action | None: Concrete action if a movement key is pressed,
            or None if no relevant key is held down.
        """
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        return Action.UP
    if keys[pygame.K_DOWN]:
        return Action.DOWN
    if keys[pygame.K_LEFT]:
        return Action.LEFT
    if keys[pygame.K_RIGHT]:
        return Action.RIGHT
    return None


def make_floor() -> Tuple[Dungeon, Agent]:
    """
    Create a new randomized dungeon floor
    """
    dungeon = Dungeon()
    dungeon.generate_random_layout()
    agent = Agent(dungeon.start_pos)
    return dungeon, agent


def compute_floor_score(agent: Agent, steps: int) -> float:
    """
    Compute a per floor score
    """
    score = 200.0 - 2.0 * steps
    score += 10.0 * agent.monsters_killed
    score += 5.0 * agent.potions_collected
    score += 8.0 * agent.coins_collected
    score -= 0.3 * agent.damage_taken
    return score


def run_game() -> None:
    pygame.init()
    screen_size = (GRID_WIDTH * TILE_SIZE, GRID_HEIGHT * TILE_SIZE)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption(f"5x5 Dungeon - Floor 1/{MAX_FLOORS}")

    clock = pygame.time.Clock()

    current_floor = 1
    dungeon, agent = make_floor()

    use_ai_controller = False
    ai_controller = DecisionTreeController(genome=BEST_GENOME)
    ai_controller.reset_episode()

    font = pygame.font.SysFont(None, 24)

    last_actions: List[Action] = []
    floor_steps: int = 0

    running = True
    while running:
        _dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Press 'r' to restart from floor 1 with new random floors
                # 'a' to toggle AI, 'esc' to quit
                if event.key == pygame.K_r:
                    current_floor = 1
                    dungeon, agent = make_floor()
                    use_ai_controller = False
                    ai_controller.reset_episode()
                    last_actions.clear()
                    floor_steps = 0
                    pygame.display.set_caption(f"5x5 Dungeon - Floor {current_floor}/{MAX_FLOORS}")
                    print("Restarted run at floor 1.")
                elif event.key == pygame.K_a:
                    use_ai_controller = not use_ai_controller
                    print(f"AI controller: {use_ai_controller}")
                    if use_ai_controller:
                        last_actions.clear()
                elif event.key == pygame.K_ESCAPE:
                    running = False

        if use_ai_controller:
            action = ai_controller.select_action(agent, dungeon)
            last_actions.append(action)
            if len(last_actions) > 3:
                last_actions.pop(0)
        else:
            action = handle_keyboard_input()

        if action is not None:
            floor_steps += 1
            agent.step(action, dungeon)

        if agent.at_exit(dungeon):
            floor_score = compute_floor_score(agent, floor_steps)
            print(
                f"Reached exit on floor {current_floor}! "
                f"Steps: {floor_steps}, Damage: {agent.damage_taken}, "
                f"Monsters killed: {agent.monsters_killed}, "
                f"Coins: {agent.coins_collected}, "
                f"Potions: {agent.potions_collected}, "
                f"Score: {floor_score:.2f}"
            )

            if current_floor < MAX_FLOORS:
                current_floor += 1
                dungeon, agent = make_floor()
                ai_controller.reset_episode()
                last_actions.clear()
                floor_steps = 0
                pygame.display.set_caption(f"5x5 Dungeon - Floor {current_floor}/{MAX_FLOORS}")
                print(f"Advancing to floor {current_floor}...")
            else:
                print("Completed all 5 floors! Starting a new run at floor 1.")
                current_floor = 1
                dungeon, agent = make_floor()
                ai_controller.reset_episode()
                last_actions.clear()
                floor_steps = 0
                pygame.display.set_caption(f"5x5 Dungeon - Floor {current_floor}/{MAX_FLOORS}")

        # Draw
        screen.fill(COLOR_BG)
        dungeon.draw(screen)
        agent.draw(screen)

        # floor + AI status
        hud_text = (
            f"Floor {current_floor}/{MAX_FLOORS}  "
            f"AI: {'ON' if use_ai_controller else 'OFF'}  (A toggle, R restart)"
        )
        text_surface = font.render(hud_text, True, (255, 255, 255))
        screen.blit(text_surface, (5, 5))

        # last 3 AI decisions
        if use_ai_controller:
            if last_actions:
                names = [a.name for a in last_actions]
                decisions_text = "Last AI actions: " + ", ".join(names)
            else:
                decisions_text = "Last AI actions: (none yet)"
            text_surface2 = font.render(decisions_text, True, (200, 200, 200))
            screen.blit(text_surface2, (5, 5 + 22))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_game()

