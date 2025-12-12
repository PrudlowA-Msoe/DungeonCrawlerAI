"""
hyperparam_sweep_mutation.py

Runs small GA experiments to study the effect of different hyperparameter
choices on final performance.

This script:
    - Defines a baseline configuration mirroring ga.py.
    - Sweeps one hyperparameter at a time (mutation_rate, pop_size,
      num_generations, tournament_size, elite_fraction, episodes_per_eval),
      while keeping the others fixed.
    - For each setting, runs several GA trials and records the best fitness.
    - Produces matplotlib plots and console logs summarizing the trends.

Outputs:
    - Printed mean best fitness (and standard deviation) for each setting.
    - A PNG figure (e.g., hyperparam_sweep_<param>.png) visualizing how
      fitness depends on the hyperparameter value.
"""

from __future__ import annotations

import random
from typing import List, Dict, Any

import matplotlib.pyplot as plt

from controllers import DecisionTreeController
from training import evaluate_controller


def run_ga_once(
    *,
    mutation_rate: float,
    pop_size: int,
    num_generations: int,
    tournament_size: int,
    elite_fraction: float,
    episodes_per_eval: int,
    seed: int = 0,
) -> float:
    """
    A small self-contained GA run with configurable hyperparameters.
    Returns the best fitness found.
    """
    random.seed(seed)

    num_actions = DecisionTreeController.num_actions()

    def eval_genome(genome: List[int]) -> float:
        ctrl = DecisionTreeController(genome)
        return evaluate_controller(ctrl, num_episodes=episodes_per_eval)

    # Initialize population
    population: List[List[int]] = [
        DecisionTreeController.random_genome()
        for _ in range(pop_size)
    ]

    best_overall_fitness = float("-inf")

    # At least 1 elite so we always keep the best so far
    num_elites = max(1, int(elite_fraction * pop_size)) if elite_fraction > 0.0 else 1

    for _gen in range(num_generations):
        fitnesses = [eval_genome(g) for g in population]

        # Track best this generation
        gen_best_idx = max(range(pop_size), key=lambda i: fitnesses[i])
        gen_best = fitnesses[gen_best_idx]
        if gen_best > best_overall_fitness:
            best_overall_fitness = gen_best

        # --- selection + reproduction ---

        # Elitism: keep top num_elites genomes
        sorted_idx = sorted(
            range(pop_size),
            key=lambda i: fitnesses[i],
            reverse=True,
        )
        new_pop: List[List[int]] = [population[i][:] for i in sorted_idx[:num_elites]]

        # Tournament selection helper
        def tournament_select() -> List[int]:
            best = None
            best_idx = None
            for _ in range(tournament_size):
                idx = random.randrange(pop_size)
                if best is None or fitnesses[idx] > best:
                    best = fitnesses[idx]
                    best_idx = idx
            return population[best_idx][:]

        # Crossover + mutation helpers
        def crossover(p1: List[int], p2: List[int]) -> List[int]:
            return [
                (g1 if random.random() < 0.5 else g2)
                for g1, g2 in zip(p1, p2)
            ]

        def mutate(genome: List[int]) -> List[int]:
            for i in range(len(genome)):
                if random.random() < mutation_rate:
                    genome[i] = random.randint(0, num_actions - 1)
            return genome

        # Fill the rest of the population
        while len(new_pop) < pop_size:
            parent1 = tournament_select()
            parent2 = tournament_select()
            child = crossover(parent1, parent2)
            child = mutate(child)
            new_pop.append(child)

        population = new_pop

    return best_overall_fitness


def main():
    # Baseline hyperparameters (roughly matching ga.py)
    baseline: Dict[str, Any] = {
        "mutation_rate": 0.2,
        "pop_size": 100,
        "num_generations": 40,
        "tournament_size": 3,
        "elite_fraction": 0.1,
        "episodes_per_eval": 10,
    }

    # Values to sweep for each hyperparameter
    sweep_values: Dict[str, List[Any]] = {
        "mutation_rate": [0.05, 0.10, 0.20, 0.30],
        "pop_size": [50, 100, 150],
        "num_generations": [20, 40, 60],
        "tournament_size": [2, 3, 5],
        "elite_fraction": [0.0, 0.1, 0.2],
        "episodes_per_eval": [5, 10, 20],
    }

    runs_per_setting = 3  # increase if you want smoother averages

    for param_name, values in sweep_values.items():
        print(f"\n=== Sweeping {param_name} ===")
        avg_best_per_value = []

        for value in values:
            bests = []
            print(f"  Testing {param_name} = {value!r}")
            for r in range(runs_per_setting):
                params = baseline.copy()
                params[param_name] = value
                seed = 1234 + r
                best_fit = run_ga_once(
                    mutation_rate=params["mutation_rate"],
                    pop_size=params["pop_size"],
                    num_generations=params["num_generations"],
                    tournament_size=params["tournament_size"],
                    elite_fraction=params["elite_fraction"],
                    episodes_per_eval=params["episodes_per_eval"],
                    seed=seed,
                )
                print(f"    Run {r}: best fitness = {best_fit:.2f}")
                bests.append(best_fit)

            avg_best = sum(bests) / len(bests)
            avg_best_per_value.append(avg_best)
            print(f"  -> Avg best fitness for {param_name}={value!r}: {avg_best:.2f}")

        # Plot for this hyperparameter
        plt.figure()
        plt.plot(values, avg_best_per_value, marker="o")
        plt.xlabel(param_name)
        plt.ylabel("Mean best fitness")
        plt.title(f"Hyperparameter sweep: {param_name}")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"ga_sweep_{param_name}.png", dpi=150)
        # Comment out show() if you only want image files
        plt.show()


if __name__ == "__main__":
    main()
