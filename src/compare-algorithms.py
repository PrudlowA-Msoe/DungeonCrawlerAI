"""
compare_algorithms.py

Runs three controllers across 200 randomized 5x5 floors:
- HillClimbingHandmadeController
- GA-evolved DecisionTreeController (uses BEST_GENOME from main.py if available)
- HumanLikeHandmadeController

Prints average floor-score + extra metrics for comparison.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import statistics

from training import run_episode, MAX_STEPS_PER_EPISODE
from controllers import DecisionTreeController

# Optional imports (kept resilient to naming/location changes)
try:
    from hillclimbing import HillClimbingHandmadeController
except Exception:
    HillClimbingHandmadeController = None  # type: ignore

try:
    from human import HumanLikeHandmadeController
except Exception:
    HumanLikeHandmadeController = None  # type: ignore

# Try to pull the GA best genome you already paste into main.py
try:
    from main import BEST_GENOME
except Exception:
    BEST_GENOME = None  # type: ignore


def compute_floor_score_from_stats(
    steps: int,
    damage_taken: int,
    monsters_killed: int,
    potions_collected: int,
    coins_collected: int,
) -> float:
    """
    Mirrors main.compute_floor_score(agent, steps).
    """
    score = 200.0 - 2.0 * steps
    score += 10.0 * monsters_killed
    score += 5.0 * potions_collected
    score += 8.0 * coins_collected
    score -= 0.3 * damage_taken
    return score


@dataclass
class Summary:
    name: str
    avg_score_all: float
    avg_score_success_only: float
    success_rate: float
    avg_steps_success: float
    avg_damage_all: float
    avg_monsters_all: float
    avg_potions_all: float
    avg_coins_all: float


def simulate_controller(
    controller,
    name: str,
    num_floors: int = 200,
    seed_base: int = 0,
) -> Summary:
    """
    Runs the controller through num_floors randomized dungeons.
    Uses deterministic seeds so each controller sees the same sequence.
    """
    scores_all: List[float] = []
    scores_success: List[float] = []

    steps_success: List[int] = []

    damages: List[int] = []
    kills: List[int] = []
    potions: List[int] = []
    coins: List[int] = []

    successes = 0

    for i in range(num_floors):
        seed = seed_base + i

        (
            reached_exit,
            steps,
            damage_taken,
            monsters_killed,
            potions_collected,
            coins_collected,
            _initial_dist,
            _final_dist,
            _best_dist,
        ) = run_episode(controller, seed=seed)

        # Track raw stats
        damages.append(damage_taken)
        kills.append(monsters_killed)
        potions.append(potions_collected)
        coins.append(coins_collected)

        # "Floor score" is defined in main only when you reach the exit.
        # For comparison across many floors, we report:
        # 1) avg_score_all where failures count as 0
        # 2) avg_score_success_only for successful floors
        if reached_exit:
            successes += 1
            score = compute_floor_score_from_stats(
                steps, damage_taken, monsters_killed, potions_collected, coins_collected
            )
            scores_all.append(score)
            scores_success.append(score)
            steps_success.append(steps)
        else:
            scores_all.append(0.0)

    success_rate = successes / float(num_floors)

    avg_score_all = statistics.mean(scores_all) if scores_all else 0.0
    avg_score_success_only = (
        statistics.mean(scores_success) if scores_success else 0.0
    )
    avg_steps_success = statistics.mean(steps_success) if steps_success else float("inf")

    return Summary(
        name=name,
        avg_score_all=avg_score_all,
        avg_score_success_only=avg_score_success_only,
        success_rate=success_rate,
        avg_steps_success=avg_steps_success,
        avg_damage_all=statistics.mean(damages) if damages else 0.0,
        avg_monsters_all=statistics.mean(kills) if kills else 0.0,
        avg_potions_all=statistics.mean(potions) if potions else 0.0,
        avg_coins_all=statistics.mean(coins) if coins else 0.0,
    )


def make_ga_controller() -> DecisionTreeController:
    """
    Builds a DecisionTreeController from BEST_GENOME if available,
    otherwise falls back to a random genome.
    """
    if BEST_GENOME is not None:
        return DecisionTreeController(genome=BEST_GENOME)

    # Fallback if someone runs this before copying in a genome
    print("[WARN] BEST_GENOME not found in main.py. Using a random genome.")
    return DecisionTreeController(genome=DecisionTreeController.random_genome())


def print_summary_table(summaries: List[Summary]) -> None:
    # Simple console table (no external deps)
    headers = [
        "Controller",
        "Avg Score (all)",
        "Avg Score (success only)",
        "Success Rate",
        "Avg Steps (success)",
        "Avg Dmg",
        "Avg Kills",
        "Avg Potions",
        "Avg Coins",
    ]

    rows = []
    for s in summaries:
        rows.append([
            s.name,
            f"{s.avg_score_all:8.2f}",
            f"{s.avg_score_success_only:8.2f}",
            f"{100.0 * s.success_rate:6.1f}%",
            f"{s.avg_steps_success:8.2f}" if s.avg_steps_success != float("inf") else "   n/a  ",
            f"{s.avg_damage_all:7.2f}",
            f"{s.avg_monsters_all:9.2f}",
            f"{s.avg_potions_all:11.2f}",
            f"{s.avg_coins_all:9.2f}",
        ])

    # compute col widths
    col_widths = [len(h) for h in headers]
    for r in rows:
        for j, cell in enumerate(r):
            col_widths[j] = max(col_widths[j], len(str(cell)))

    def fmt_row(items):
        return " | ".join(str(items[i]).ljust(col_widths[i]) for i in range(len(items)))

    print("\n" + fmt_row(headers))
    print("-+-".join("-" * w for w in col_widths))
    for r in rows:
        print(fmt_row(r))
    print()


def main() -> None:
    controllers_to_test = []

    # Hillclimber baseline
    if HillClimbingHandmadeController is not None:
        controllers_to_test.append(("HillClimber Handmade", HillClimbingHandmadeController()))
    else:
        print("[WARN] Could not import HillClimbingHandmadeController from hillclimbing.py")

    # Human-like handmade baseline (non-interactive)
    if HumanLikeHandmadeController is not None:
        controllers_to_test.append(("Human-like Handmade", HumanLikeHandmadeController()))
    else:
        print("[WARN] Could not import HumanLikeHandmadeController from human.py")

    # GA-evolved decision tree
    ga_ctrl = make_ga_controller()
    controllers_to_test.append(("Genetic Algorithm DT", ga_ctrl))

    if not controllers_to_test:
        print("No controllers available to test.")
        return

    summaries: List[Summary] = []
    num_floors = 200

    # Use the same seeds across all controllers for fairness
    for name, ctrl in controllers_to_test:
        summaries.append(simulate_controller(ctrl, name=name, num_floors=num_floors, seed_base=0))

    # Sort by avg_score_all descending for a nice readout
    summaries.sort(key=lambda s: s.avg_score_all, reverse=True)

    print_summary_table(summaries)

    # Optional: quick narrative
    best = summaries[0]
    print(
        f"Top performer by Avg Score (all floors): {best.name} "
        f"(Avg={best.avg_score_all:.2f}, Success={best.success_rate*100:.1f}%)."
    )


if __name__ == "__main__":
    main()
