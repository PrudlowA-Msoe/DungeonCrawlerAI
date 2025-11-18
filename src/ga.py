"""
Genetic algorithm for evolving movement-only DecisionTreeControllers (for right now. later more will be added)
"""

from typing import List, Tuple
import random

from controllers import DecisionTreeController
from training import evaluate_controller


# hyperparams

POP_SIZE = 50
NUM_GENERATIONS = 40
MUTATION_RATE = 0.1      # per gene
TOURNAMENT_SIZE = 3
ELITE_FRACTION = 0.1 # keep these percentage
EPISODES_PER_EVAL = 20


Genome = List[int]


def make_random_genome() -> Genome:
    return DecisionTreeController.random_genome()


def evaluate_genome(genome: Genome) -> float:
    controller = DecisionTreeController(genome)
    return evaluate_controller(controller, num_episodes=EPISODES_PER_EVAL)


def tournament_select(pop: List[Genome], fitnesses: List[float]) -> Genome:
    """Tournament selection: pick the best among a few random individuals."""
    best_idx = None
    for _ in range(TOURNAMENT_SIZE):
        idx = random.randrange(len(pop))
        if best_idx is None or fitnesses[idx] > fitnesses[best_idx]:
            best_idx = idx
    return pop[best_idx]


def crossover(parent1: Genome, parent2: Genome) -> Genome:
    """Uniform crossover: choose each gene from either parent with 50/50 chance."""
    child: Genome = []
    for g1, g2 in zip(parent1, parent2):
        child.append(g1 if random.random() < 0.5 else g2)
    return child


def mutate(genome: Genome) -> Genome:
    """Per-gene mutation: with some probability, replace with a new random action index."""
    num_actions = DecisionTreeController.num_actions()
    for i in range(len(genome)):
        if random.random() < MUTATION_RATE:
            genome[i] = random.randint(0, num_actions - 1)
    return genome


def run_ga(seed: int = 0) -> Tuple[Genome, float]:
    random.seed(seed)

    # Initialize pop
    population: List[Genome] = [make_random_genome() for _ in range(POP_SIZE)]

    best_overall_genome: Genome = population[0][:]
    best_overall_fitness: float = float("-inf")

    num_elites = max(1, int(ELITE_FRACTION * POP_SIZE))

    for gen in range(NUM_GENERATIONS):
        fitnesses = [evaluate_genome(g) for g in population]

        # Track best
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

        # keep elites
        sorted_indices = sorted(range(POP_SIZE), key=lambda i: fitnesses[i], reverse=True)
        new_population: List[Genome] = [population[i][:] for i in sorted_indices[:num_elites]]

        # selection + crossover + mutation
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
    best_genome, best_fit = run_ga(seed=42)

    # If you want to try the best genome in your PyGame `main.py`,
    # you can copy-paste `best_genome` there and construct:
    #
    # from controllers import DecisionTreeController
    # ai_controller = DecisionTreeController(genome=best_genome)
