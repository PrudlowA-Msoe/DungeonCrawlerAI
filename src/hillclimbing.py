"""
hillclimbing.py

Implements a simple hill-climbing optimizer over a parameterized
hand-designed controller.

Workflow:
    - Start from initial weights that define a handmade heuristic policy
      (e.g., weights on distance-to-exit, monster danger, item value).
    - At each iteration:
        * Propose a small random change to the weights.
        * Evaluate the modified controller over several random floors.
        * If performance improves, accept the new weights.
    - After many iterations, keep the best set of weights found.

This provides a non-GA baseline that still uses optimization, making it
useful for algorithm comparison against the GA-evolved controller.
"""
import random
from typing import List, Tuple, Dict, Set, Optional
from collections import deque

from agent import Action, Agent, Pos
from dungeon import Dungeon, TileType
from controllers import BaseController


class HillClimbingHandmadeController(BaseController):
    """
    Handmade controller that uses Hill Climbing algorithm:
    1. Generate candidate actions (neighbors in action space)
    2. Evaluate each candidate using a heuristic function
    3. Select the action with highest immediate reward
    4. Use memory to avoid getting stuck in local optima
    """
    
    def __init__(self, exploration_rate: float = 0.1):
        """
        Initialize the hill climbing controller.
        
        Args:
            exploration_rate: Probability of taking a random action to explore
        """
        super().__init__()
        self.exploration_rate = exploration_rate
        self.memory: List[Pos] = []  # Remember recent positions
        self.visited_positions: Set[Pos] = set()
        self.last_action: Optional[Action] = None
        self.stuck_counter: int = 0
        
    def reset_episode(self) -> None:
        """Reset internal state for new episode"""
        self.memory.clear()
        self.visited_positions.clear()
        self.last_action = None
        self.stuck_counter = 0
        
    def _generate_candidate_actions(self, agent: Agent, dungeon: Dungeon) -> List[Action]:
        """Generate all possible candidate actions (neighbors in action space)"""
        candidates = []
        
        # Always consider movement actions
        for move in [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]:
            dx, dy = 0, 0
            if move == Action.UP:
                dy = -1
            elif move == Action.DOWN:
                dy = 1
            elif move == Action.LEFT:
                dx = -1
            elif move == Action.RIGHT:
                dx = 1
                
            new_x, new_y = agent.x + dx, agent.y + dy
            if dungeon.is_walkable(new_x, new_y):
                candidates.append(move)
                
        # Consider staying in place
        candidates.append(Action.STAY)
        
        # Consider combat actions if appropriate
        melee_monster_nearby = False
        magic_monster_nearby = False
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
            x, y = agent.x + dx, agent.y + dy
            if dungeon.in_bounds(x, y):
                tile = dungeon.get_tile(x, y)
                if tile == TileType.MONSTER_MELEE:
                    melee_monster_nearby = True
                elif tile == TileType.MONSTER_MAGIC:
                    magic_monster_nearby = True
        
        if melee_monster_nearby:
            candidates.append(Action.MELEE)
            
        if magic_monster_nearby:
            candidates.append(Action.MAGIC_BLAST)
            
        # Consider potion actions
        if agent.health_potions > 0:
            candidates.append(Action.DRINK_HEALTH)
            
        if agent.mana_potions > 0:
            candidates.append(Action.DRINK_MANA)
            
        return candidates
    
    def _evaluate_position_heuristic(self, x: int, y: int, agent: Agent, dungeon: Dungeon) -> float:
        """
        Evaluate a position using multiple factors (higher is better).
        This is the heuristic function for hill climbing.
        
        Args:
            x, y: Position to evaluate
            agent: Current agent state
            dungeon: Current dungeon state
            
        Returns:
            Heuristic score (higher is better)
        """
        if not dungeon.in_bounds(x, y):
            return -float('inf')
        
        if not dungeon.is_walkable(x, y):
            return -float('inf')
            
        score = 0.0
        
        # 1. Distance to exit (negative because closer is better)
        exit_x, exit_y = dungeon.exit_pos
        dist_to_exit = abs(exit_x - x) + abs(exit_y - y)
        score -= dist_to_exit * 2.0
        
        # 2. Check for items on the tile
        tile = dungeon.get_tile(x, y)
        if tile == TileType.HEALTH_POTION:
            score += 50  # High value for health potions
        elif tile == TileType.MANA_POTION:
            score += 40  # High value for mana potions
        elif tile == TileType.COIN:
            score += 30  # Value for coins
            
        # 3. Check adjacent items (can collect next turn)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if dungeon.in_bounds(nx, ny):
                adj_tile = dungeon.get_tile(nx, ny)
                if adj_tile == TileType.HEALTH_POTION:
                    score += 25
                elif adj_tile == TileType.MANA_POTION:
                    score += 20
                elif adj_tile == TileType.COIN:
                    score += 15
                    
        # 4. Avoid monsters (negative score for being adjacent to monsters)
        monster_penalty = 0
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
            nx, ny = x + dx, y + dy
            if dungeon.in_bounds(nx, ny):
                adj_tile = dungeon.get_tile(nx, ny)
                if adj_tile == TileType.MONSTER_MELEE:
                    monster_penalty += 30  # High penalty for melee monsters
                elif adj_tile == TileType.MONSTER_MAGIC:
                    monster_penalty += 25  # Penalty for magic monsters
        score -= monster_penalty
        
        # 5. Exploration bonus for unvisited positions
        if (x, y) not in self.visited_positions:
            score += 10
            
        # 6. Penalize backtracking (positions visited recently)
        if (x, y) in self.memory[-3:]:
            score -= 5
            
        # 7. Prefer positions that are farther from monsters
        monster_dist_sum = 0
        monster_count = 0
        for my in range(dungeon.height):
            for mx in range(dungeon.width):
                tile_type = dungeon.get_tile(mx, my)
                if tile_type in [TileType.MONSTER_MELEE, TileType.MONSTER_MAGIC]:
                    monster_dist = abs(mx - x) + abs(my - y)
                    monster_dist_sum += monster_dist
                    monster_count += 1
                    
        if monster_count > 0:
            avg_monster_dist = monster_dist_sum / monster_count
            score += avg_monster_dist * 0.5  # Prefer being farther from monsters
            
        # 8. If low health, strongly prefer moving away from monsters
        if agent.health < 40:
            # Find closest monster
            closest_monster_dist = float('inf')
            for my in range(dungeon.height):
                for mx in range(dungeon.width):
                    tile_type = dungeon.get_tile(mx, my)
                    if tile_type in [TileType.MONSTER_MELEE, TileType.MONSTER_MAGIC]:
                        dist = abs(mx - x) + abs(my - y)
                        if dist < closest_monster_dist:
                            closest_monster_dist = dist
                            
            if closest_monster_dist < 3:  # Monster is nearby
                score += closest_monster_dist * 5  # Strongly prefer moving away
                
        return score
    
    def _evaluate_action_heuristic(self, action: Action, agent: Agent, dungeon: Dungeon) -> float:
        """
        Evaluate an action using heuristic function (higher score is better).
        
        Args:
            action: Action to evaluate
            agent: Current agent state
            dungeon: Current dungeon state
            
        Returns:
            Heuristic score for the action
        """
        score = 0.0
        
        # Movement actions
        if action in [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT, Action.STAY]:
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
                score = self._evaluate_position_heuristic(new_x, new_y, agent, dungeon)
            else:
                return -float('inf')  # Invalid move
                
        # Combat actions
        elif action == Action.MELEE:
            # Check if there's a melee monster to attack
            has_melee_monster = False
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
                x, y = agent.x + dx, agent.y + dy
                if dungeon.in_bounds(x, y) and dungeon.get_tile(x, y) == TileType.MONSTER_MELEE:
                    has_melee_monster = True
                    break
                    
            if has_melee_monster:
                score = 60  # Good to kill a monster
                # Bonus if low health and monster is adjacent
                if agent.health < 50:
                    score += 20
            else:
                score = -20  # Wasted action
                
        elif action == Action.MAGIC_BLAST:
            if agent.mana <= 0:
                return -30  # No mana for magic
                
            # Check if there's a magic monster to attack
            has_magic_monster = False
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
                x, y = agent.x + dx, agent.y + dy
                if dungeon.in_bounds(x, y) and dungeon.get_tile(x, y) == TileType.MONSTER_MAGIC:
                    has_magic_monster = True
                    break
                    
            if has_magic_monster:
                score = 55  # Good to kill magic monster (slightly less than melee due to mana cost)
                # Bonus if low on mana but have potions
                if agent.mana == 1 and agent.mana_potions > 0:
                    score += 10
            else:
                score = -25  # Wasted mana
                
        # Potion actions
        elif action == Action.DRINK_HEALTH:
            if agent.health_potions > 0:
                health_needed = 100 - agent.health
                if health_needed > 0:
                    # Score based on how much health we need
                    score = min(health_needed, 40) * 1.5
                    # Bonus if health is critical
                    if agent.health < 30:
                        score += 30
                else:
                    score = -10  # Don't need health
            else:
                score = -15  # No health potions
                
        elif action == Action.DRINK_MANA:
            if agent.mana_potions > 0:
                mana_needed = 3 - agent.mana
                if mana_needed > 0:
                    # Check if there are magic monsters nearby
                    magic_monsters_nearby = False
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
                        x, y = agent.x + dx, agent.y + dy
                        if dungeon.in_bounds(x, y) and dungeon.get_tile(x, y) == TileType.MONSTER_MAGIC:
                            magic_monsters_nearby = True
                            break
                            
                    if magic_monsters_nearby:
                        score = mana_needed * 20  # Very valuable to have mana against magic monsters
                    else:
                        score = mana_needed * 10  # Some value for future use
                else:
                    score = -10  # Don't need mana
            else:
                score = -15  # No mana potions
        
        # Adjust score based on agent state
        if agent.health < 30:
            # Prioritize survival when health is critical
            if action in [Action.DRINK_HEALTH, Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]:
                score += 25
            elif action == Action.MELEE:
                score -= 15  # Avoid combat when very low health
                
        # Penalize repeated actions (to encourage variety)
        if action == self.last_action:
            score -= 5
            
        return score
    
    def _check_emergency_situation(self, agent: Agent, dungeon: Dungeon) -> Optional[Action]:
        """
        Check for emergency situations that override normal hill climbing.
        
        Args:
            agent: Current agent state
            dungeon: Current dungeon state
            
        Returns:
            Emergency action if needed, None otherwise
        """
        # Emergency: Very low health and adjacent to monster
        if agent.health < 20:
            # Check if monster is adjacent
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
                x, y = agent.x + dx, agent.y + dy
                if dungeon.in_bounds(x, y):
                    tile = dungeon.get_tile(x, y)
                    if tile in [TileType.MONSTER_MELEE, TileType.MONSTER_MAGIC]:
                        # Try to move away
                        safe_moves = []
                        for move in [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]:
                            mdx, mdy = 0, 0
                            if move == Action.UP:
                                mdy = -1
                            elif move == Action.DOWN:
                                mdy = 1
                            elif move == Action.LEFT:
                                mdx = -1
                            elif move == Action.RIGHT:
                                mdx = 1
                                
                            nx, ny = agent.x + mdx, agent.y + mdy
                            if dungeon.is_walkable(nx, ny):
                                # Check if this move takes us away from monsters
                                monster_near = False
                                for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                    mx, my = nx + ddx, ny + ddy
                                    if dungeon.in_bounds(mx, my):
                                        if dungeon.get_tile(mx, my) in [TileType.MONSTER_MELEE, TileType.MONSTER_MAGIC]:
                                            monster_near = True
                                            break
                                            
                                if not monster_near:
                                    safe_moves.append(move)
                                    
                        if safe_moves:
                            return random.choice(safe_moves)
                            
                        # If no safe moves, try to attack or drink potion
                        if agent.health_potions > 0:
                            return Action.DRINK_HEALTH
                        elif tile == TileType.MONSTER_MELEE:
                            return Action.MELEE
                        elif tile == TileType.MONSTER_MAGIC and agent.mana > 0:
                            return Action.MAGIC_BLAST
                            
        # Emergency: No mana but magic monster adjacent and we have mana potion
        if agent.mana == 0:
            magic_monster_adjacent = False
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
                x, y = agent.x + dx, agent.y + dy
                if dungeon.in_bounds(x, y) and dungeon.get_tile(x, y) == TileType.MONSTER_MAGIC:
                    magic_monster_adjacent = True
                    break
                    
            if magic_monster_adjacent and agent.mana_potions > 0:
                return Action.DRINK_MANA
                
        return None
    
    def _detect_stuck_in_local_optima(self) -> bool:
        """
        Detect if agent is stuck in a local optima (repeating patterns).
        
        Returns:
            True if stuck, False otherwise
        """
        if len(self.memory) < 6:
            return False
            
        # Check for repeating position patterns
        recent_positions = self.memory[-6:]
        
        # Check for 3-position cycle
        if (recent_positions[0] == recent_positions[2] == recent_positions[4] and
            recent_positions[1] == recent_positions[3] == recent_positions[5]):
            return True
            
        # Check for staying in same area
        unique_positions = set(recent_positions)
        if len(unique_positions) <= 2:
            return True
            
        return False
    
    def _get_exploratory_move(self, agent: Agent, dungeon: Dungeon) -> Action:
        """
        Get an exploratory move when stuck in local optima.
        
        Args:
            agent: Current agent state
            dungeon: Current dungeon state
            
        Returns:
            Exploratory action
        """
        # Try to move to an unvisited position
        unvisited_moves = []
        for move in [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]:
            dx, dy = 0, 0
            if move == Action.UP:
                dy = -1
            elif move == Action.DOWN:
                dy = 1
            elif move == Action.LEFT:
                dx = -1
            elif move == Action.RIGHT:
                dx = 1
                
            new_x, new_y = agent.x + dx, agent.y + dy
            if dungeon.is_walkable(new_x, new_y) and (new_x, new_y) not in self.visited_positions:
                unvisited_moves.append(move)
                
        if unvisited_moves:
            return random.choice(unvisited_moves)
            
        # If no unvisited moves, try any safe move
        safe_moves = []
        for move in [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]:
            dx, dy = 0, 0
            if move == Action.UP:
                dy = -1
            elif move == Action.DOWN:
                dy = 1
            elif move == Action.LEFT:
                dx = -1
            elif move == Action.RIGHT:
                dx = 1
                
            new_x, new_y = agent.x + dx, agent.y + dy
            if dungeon.is_walkable(new_x, new_y):
                safe_moves.append(move)
                
        if safe_moves:
            return random.choice(safe_moves)
            
        return Action.STAY
    
    def select_action(self, agent: Agent, dungeon: Dungeon) -> Action:
        """
        Main decision function using Hill Climbing algorithm.
        
        Args:
            agent: Current agent state
            dungeon: Current dungeon state
            
        Returns:
            Selected action
        """
        # Update memory and visited positions
        self.memory.append(agent.pos)
        if len(self.memory) > 10:
            self.memory.pop(0)
            
        self.visited_positions.add(agent.pos)
        
        # Check for emergency situations first
        emergency_action = self._check_emergency_situation(agent, dungeon)
        if emergency_action is not None:
            self.last_action = emergency_action
            return emergency_action
            
        # Check if stuck in local optima
        if self._detect_stuck_in_local_optima():
            self.stuck_counter += 1
            if self.stuck_counter >= 2:
                # Try exploratory move
                exploratory_action = self._get_exploratory_move(agent, dungeon)
                self.last_action = exploratory_action
                self.stuck_counter = 0
                return exploratory_action
        else:
            self.stuck_counter = 0
            
        # Occasionally explore randomly (epsilon-greedy)
        if random.random() < self.exploration_rate:
            candidates = self._generate_candidate_actions(agent, dungeon)
            if candidates:
                exploratory_action = random.choice(candidates)
                self.last_action = exploratory_action
                return exploratory_action
        
        # Generate candidate actions
        candidates = self._generate_candidate_actions(agent, dungeon)
        
        if not candidates:
            self.last_action = Action.STAY
            return Action.STAY
            
        # Evaluate all candidates using heuristic
        scored_candidates = []
        for action in candidates:
            score = self._evaluate_action_heuristic(action, agent, dungeon)
            scored_candidates.append((action, score))
            
        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Return the best action
        best_action, best_score = scored_candidates[0]
        
        # If all scores are very low, try exploratory move
        if best_score < -50:
            exploratory_action = self._get_exploratory_move(agent, dungeon)
            self.last_action = exploratory_action
            return exploratory_action
                
        self.last_action = best_action
        return best_action