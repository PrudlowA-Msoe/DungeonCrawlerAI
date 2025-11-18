import sys
from typing import Optional

import pygame

from config import GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, FPS, COLOR_BG
from dungeon import Dungeon
from agent import Agent, Action
from controllers import RandomWalkerController, DecisionTreeController

BEST_GENOME = [0, 0, 2, 1, 1, 1, 0, 0, 3]

def handle_keyboard_input() -> Optional[Action]:
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


def run_game() -> None:
    pygame.init()
    screen_size = (GRID_WIDTH * TILE_SIZE, GRID_HEIGHT * TILE_SIZE)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("5x5 Dungeon Prototype")

    clock = pygame.time.Clock()

    dungeon = Dungeon()
    agent = Agent(dungeon.start_pos)

    use_ai_controller = False
    ai_controller = DecisionTreeController(genome=BEST_GENOME)

    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Press 'r' to reset, 'a' to toggle AI, 'esc' to quit
                if event.key == pygame.K_r:
                    dungeon.reset()
                    agent = Agent(dungeon.start_pos)
                elif event.key == pygame.K_a:
                    use_ai_controller = not use_ai_controller
                    print(f"AI controller: {use_ai_controller}")
                elif event.key == pygame.K_ESCAPE:
                    running = False

        # Decide action (either from keyboard or from a controller)
        action: Optional[Action] = None
        if use_ai_controller:
            action = ai_controller.select_action(agent, dungeon)
        else:
            action = handle_keyboard_input()

        if action is not None:
            agent.step(action, dungeon)

        # Check for exit
        if agent.at_exit(dungeon):
            # For now just print, change floors later
            print("Reached exit! Press R to reset or A to watch the AI again.")

        # Draw
        screen.fill(COLOR_BG)
        dungeon.draw(screen)
        agent.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_game()
