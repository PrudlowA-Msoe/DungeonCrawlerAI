"""
Human-like Handmade Controller
A purely reactive controller that mimics human decision-making using only immediate perceptions.
No pathfinding, no memory, no complex algorithms - just if-then rules based on what the agent can see.
"""

import random
from typing import List, Tuple, Optional
from agent import Action, Agent
from dungeon import Dungeon, TileType
from controllers import BaseController


class HumanLikeHandmadeController(BaseController):
    """
    A controller that mimics human decision-making:
    - Only uses information the agent can immediately perceive
    - Makes decisions based on simple if-then rules
    - Focuses on survival, item collection, and reaching the exit
    - No memory, no pathfinding, no complex algorithms
    """
    
    def __init__(self):
        super().__init__()
        # No internal state - humans make decisions based on current situation only
        
    def reset_episode(self) -> None:
        """Reset for new episode - humans don't really 'reset' but we need to match interface"""
        pass
        
    def _what_can_i_see(self, agent: Agent, dungeon: Dungeon) -> dict:
        """
        Simulate what a human player can see immediately around them.
        Returns a dictionary of immediate perceptions.
        """
        perceptions = {
            'current_tile': dungeon.get_tile(agent.x, agent.y),
            'adjacent_tiles': {},
            'my_health': agent.health,
            'my_mana': agent.mana,
            'my_health_potions': agent.health_potions,
            'my_mana_potions': agent.mana_potions,
            'exit_direction': self._get_exit_direction(agent, dungeon),
            'immediate_danger': False,
            'items_nearby': False,
            'monsters_nearby': False
        }
        
        # Check all adjacent tiles (including current position)
        for dx, dy, direction in [
            (0, 0, "here"),
            (-1, 0, "left"),
            (1, 0, "right"),
            (0, -1, "up"),
            (0, 1, "down")
        ]:
            x, y = agent.x + dx, agent.y + dy
            if dungeon.in_bounds(x, y):
                tile = dungeon.get_tile(x, y)
                perceptions['adjacent_tiles'][direction] = tile
                
                # Update danger and item flags
                if tile in [TileType.MONSTER_MELEE, TileType.MONSTER_MAGIC]:
                    perceptions['monsters_nearby'] = True
                    if dx == 0 and dy == 0:  # Monster is on my tile!
                        perceptions['immediate_danger'] = True
                        
                if tile in [TileType.HEALTH_POTION, TileType.MANA_POTION, TileType.COIN]:
                    perceptions['items_nearby'] = True
                    
        return perceptions
    
    def _get_exit_direction(self, agent: Agent, dungeon: Dungeon) -> str:
        """
        Simple direction to exit - just tells which way to go.
        Humans don't calculate complex paths, just "exit is that way".
        """
        exit_x, exit_y = dungeon.exit_pos
        
        if exit_x > agent.x:
            x_dir = "right"
        elif exit_x < agent.x:
            x_dir = "left"
        else:
            x_dir = None
            
        if exit_y > agent.y:
            y_dir = "down"
        elif exit_y < agent.y:
            y_dir = "up"
        else:
            y_dir = None
            
        # Simple priority: if exit is in same row/col, go directly
        if x_dir and y_dir:
            return random.choice([x_dir, y_dir])  # Human would pick one
        elif x_dir:
            return x_dir
        elif y_dir:
            return y_dir
        else:
            return "here"  # At exit!
    
    def _check_emergency(self, perceptions: dict) -> Optional[Action]:
        """
        Check for emergency situations that require immediate action.
        Human thinking: "Oh no, I'm about to die!"
        """
        # Emergency: Very low health
        if perceptions['my_health'] < 25:
            # If I have a health potion, DRINK IT NOW!
            if perceptions['my_health_potions'] > 0:
                return Action.DRINK_HEALTH
                
            # If monster is on my tile and I'm this low, try to kill it
            if perceptions['immediate_danger']:
                monster_on_me = perceptions['adjacent_tiles']["here"]
                if monster_on_me == TileType.MONSTER_MELEE:
                    return Action.MELEE
                elif monster_on_me == TileType.MONSTER_MAGIC and perceptions['my_mana'] > 0:
                    return Action.MAGIC_BLAST
                    
        # Emergency: Monster attacking me right now
        if perceptions['immediate_danger']:
            monster_on_me = perceptions['adjacent_tiles']["here"]
            if monster_on_me == TileType.MONSTER_MELEE:
                return Action.MELEE
            elif monster_on_me == TileType.MONSTER_MAGIC and perceptions['my_mana'] > 0:
                return Action.MAGIC_BLAST
                
        return None
    
    def _check_items_to_collect(self, perceptions: dict, dungeon: Dungeon, agent: Agent) -> Optional[Action]:
        """
        Human thinking: "Ooh, shiny! Let me grab that."
        """
        # Check current tile first (if I'm standing on something)
        current_tile = perceptions['current_tile']
        if current_tile in [TileType.HEALTH_POTION, TileType.MANA_POTION, TileType.COIN]:
            # Just wait a moment to ensure collection
            return Action.STAY
            
        # Check adjacent tiles for items
        for direction, tile in perceptions['adjacent_tiles'].items():
            if direction == "here":
                continue
                
            if tile in [TileType.HEALTH_POTION, TileType.MANA_POTION, TileType.COIN]:
                # Move toward the item
                if direction == "up":
                    return Action.UP
                elif direction == "down":
                    return Action.DOWN
                elif direction == "left":
                    return Action.LEFT
                elif direction == "right":
                    return Action.RIGHT
                    
        return None
    
    def _check_monsters_to_attack(self, perceptions: dict) -> Optional[Action]:
        """
        Human thinking: "That monster looks dangerous. Should I kill it?"
        """
        # Don't attack if health is too low
        if perceptions['my_health'] < 40:
            return None
            
        # Check for melee monsters first (easier to kill)
        for direction, tile in perceptions['adjacent_tiles'].items():
            if tile == TileType.MONSTER_MELEE:
                return Action.MELEE
                
        # Check for magic monsters (need mana)
        for direction, tile in perceptions['adjacent_tiles'].items():
            if tile == TileType.MONSTER_MAGIC and perceptions['my_mana'] > 0:
                return Action.MAGIC_BLAST
                
        return None
    
    def _check_potions_to_drink(self, perceptions: dict) -> Optional[Action]:
        """
        Human thinking: "I could use a boost..."
        """
        # Drink health potion if health is medium-low and we have potions
        if perceptions['my_health'] < 60 and perceptions['my_health_potions'] > 0:
            return Action.DRINK_HEALTH
                
        # Drink mana potion if we need mana for magic monsters
        if perceptions['my_mana'] == 0 and perceptions['my_mana_potions'] > 0:
            # Check if there are magic monsters nearby
            for tile in perceptions['adjacent_tiles'].values():
                if tile == TileType.MONSTER_MAGIC:
                    return Action.DRINK_MANA
                    
        return None
    
    def _move_toward_exit(self, perceptions: dict, dungeon: Dungeon, agent: Agent) -> Action:
        """
        Human thinking: "The exit is that way... let's go!"
        Simple movement toward exit without pathfinding.
        """
        exit_dir = perceptions['exit_direction']
        
        if exit_dir == "here":
            return Action.STAY  # We're at the exit!
            
        # Try to move in the direction of the exit
        if exit_dir == "up":
            new_x, new_y = agent.x, agent.y - 1
            if dungeon.is_walkable(new_x, new_y):
                return Action.UP
        elif exit_dir == "down":
            new_x, new_y = agent.x, agent.y + 1
            if dungeon.is_walkable(new_x, new_y):
                return Action.DOWN
        elif exit_dir == "left":
            new_x, new_y = agent.x - 1, agent.y
            if dungeon.is_walkable(new_x, new_y):
                return Action.LEFT
        elif exit_dir == "right":
            new_x, new_y = agent.x + 1, agent.y
            if dungeon.is_walkable(new_x, new_y):
                return Action.RIGHT
                
        # If we can't move toward exit, try a random safe direction
        return self._try_random_safe_move(dungeon, agent)
    
    def _try_random_safe_move(self, dungeon: Dungeon, agent: Agent) -> Action:
        """
        Human thinking: "Hmm, can't go that way... let's try another direction."
        """
        possible_moves = []
        
        # Check each direction
        for action, (dx, dy) in [
            (Action.UP, (0, -1)),
            (Action.DOWN, (0, 1)),
            (Action.LEFT, (-1, 0)),
            (Action.RIGHT, (1, 0))
        ]:
            new_x, new_y = agent.x + dx, agent.y + dy
            if dungeon.is_walkable(new_x, new_y):
                possible_moves.append(action)
                
        if possible_moves:
            return random.choice(possible_moves)
        else:
            return Action.STAY
    
    def select_action(self, agent: Agent, dungeon: Dungeon) -> Action:
        """
        Main decision function - mimics human thought process.
        Priority:
        1. Emergency situations (about to die)
        2. Collect nearby items
        3. Attack monsters when safe
        4. Drink potions when helpful
        5. Move toward exit
        """
        # What can I see right now?
        perceptions = self._what_can_i_see(agent, dungeon)
        
        # 1. Check for emergencies
        emergency_action = self._check_emergency(perceptions)
        if emergency_action:
            return emergency_action
            
        # 2. Check for items to collect (humans love loot!)
        item_action = self._check_items_to_collect(perceptions, dungeon, agent)
        if item_action:
            return item_action
            
        # 3. Check for monsters to attack (if we're feeling brave)
        if perceptions['my_health'] > 40:
            attack_action = self._check_monsters_to_attack(perceptions)
            if attack_action:
                return attack_action
                
        # 4. Check for potions to drink
        potion_action = self._check_potions_to_drink(perceptions)
        if potion_action:
            return potion_action
            
        # 5. Otherwise, try to move toward exit
        return self._move_toward_exit(perceptions, dungeon, agent)