"""
ga.py

Genetic algorithm for evolving DecisionTreeControllers on the dungeon task.

The GA operates over genomes that are:
    - Lists of integers, one per discrete state handled by DecisionTreeController.
    - Each gene indexes into the controller's ACTIONS list.

The algorithm uses:
    - Tournament selection
    - Uniform crossover (per-gene 50/50 from each parent)
    - Per-gene mutation (flip to random action with probability MUTATION_RATE)
    - Elitism (keep best ELITE_FRACTION of population each generation)

This module is the main entry point for training GA policies:
    - `run_ga()` drives the evolution loop and prints per-generation fitness.
    - The best genome can then be copied into main.py for visualization.
"""

from typing import List, Tuple
import random

from controllers import DecisionTreeController
from training import evaluate_controller

POP_SIZE = 100
NUM_GENERATIONS = 60
MUTATION_RATE = 0.1
TOURNAMENT_SIZE = 3
ELITE_FRACTION = 0.1   # keep top 10%
EPISODES_PER_EVAL = 5


Genome = List[int]


def make_random_genome() -> Genome:
    """return random genome"""
    return DecisionTreeController.random_genome()


def evaluate_genome(genome: Genome) -> float:
    """evaluate genome"""
    controller = DecisionTreeController(genome)
    return evaluate_controller(controller, num_episodes=EPISODES_PER_EVAL)


def tournament_select(pop: List[Genome], fitnesses: List[float]) -> Genome:
    """tournament selection"""
    best_idx = None
    for _ in range(TOURNAMENT_SIZE):
        idx = random.randrange(len(pop))
        if best_idx is None or fitnesses[idx] > fitnesses[best_idx]:
            best_idx = idx
    return pop[best_idx]


def crossover(parent1: Genome, parent2: Genome) -> Genome:
    """50 50 crossover"""
    child: Genome = []
    for g1, g2 in zip(parent1, parent2):
        child.append(g1 if random.random() < 0.5 else g2)
    return child


def mutate(genome: Genome) -> Genome:
    """per gene mutation"""
    num_actions = DecisionTreeController.num_actions()
    for i in range(len(genome)):
        if random.random() < MUTATION_RATE:
            genome[i] = random.randint(0, num_actions - 1)
    return genome


def run_ga(seed: int = 0) -> Tuple[Genome, float]:
    """Run the full GA loop and return the best genome discovered.

        Steps:
            1. Initialize a random population.
            2. For each generation:
                - Evaluate fitness of all genomes.
                - Track the best genome overall.
                - Build a new population via:
                    * Elitism
                    * Tournament selection
                    * Crossover
                    * Mutation
            3. Return the best genome and its fitness.

        Args:
            seed (int): Random seed for reproducibility.

        Returns:
            (Genome, float): Tuple of (best_genome, best_fitness).
        """
    random.seed(seed)

    #init pop
    population: List[Genome] = [make_random_genome() for _ in range(POP_SIZE)]

    best_overall_genome: Genome = population[0][:]
    best_overall_fitness: float = float("-inf")

    num_elites = max(1, int(ELITE_FRACTION * POP_SIZE))

    for gen in range(NUM_GENERATIONS):
        # eval pop
        fitnesses = [evaluate_genome(g) for g in population]

        # track best guy
        gen_best_idx = max(range(POP_SIZE), key=lambda i: fitnesses[i])
        gen_best_fitness = fitnesses[gen_best_idx]
        gen_best_genome = population[gen_best_idx]

        if gen_best_fitness > best_overall_fitness:
            best_overall_fitness = gen_best_fitness
            best_overall_genome = gen_best_genome[:]

        avg_fitness = sum(fitnesses) / len(fitnesses)
        print(
            f"Generation {gen:02d} | "
            f"best: {gen_best_fitness:.2f} | "
            f"avg: {avg_fitness:.2f}"
        )

        # sort by fitness and keep elites
        sorted_indices = sorted(range(POP_SIZE), key=lambda i: fitnesses[i], reverse=True)
        new_population: List[Genome] = [population[i][:] for i in sorted_indices[:num_elites]]

        # rest of population selection + crossover + mutation
        while len(new_population) < POP_SIZE:
            parent1 = tournament_select(population, fitnesses)
            parent2 = tournament_select(population, fitnesses)
            child = crossover(parent1, parent2)
            child = mutate(child)
            new_population.append(child)

        population = new_population

    print("\nBest overall genome:", best_overall_genome)
    print("Best overall fitness:", best_overall_fitness)
    return best_overall_genome, best_overall_fitness


if __name__ == "__main__":
    best_genome, best_fit = run_ga(seed=0)


