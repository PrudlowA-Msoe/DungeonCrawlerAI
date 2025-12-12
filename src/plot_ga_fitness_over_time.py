"""
plot_ga_fitness_over_time.py

Utility script to visualize GA training dynamics.

Behavior:
    - Runs GA training (or reuses logged fitness values, depending on
      implementation).
    - Records best and average fitness per generation.
    - Plots both curves using matplotlib.
    - Saves the figure as `ga_fitness_over_generations.png`.

This script is primarily for analysis and presentation: it demonstrates
that the GA actually learns better policies over time and where it
eventually plateaus.
"""

import random

import matplotlib.pyplot as plt

from ga import (
    make_random_genome,
    evaluate_genome,
    tournament_select,
    crossover,
    mutate,
    POP_SIZE,
    NUM_GENERATIONS,
    ELITE_FRACTION,
)


def run_ga_with_history(seed: int = 0):
    random.seed(seed)

    population = [make_random_genome() for _ in range(POP_SIZE)]

    best_overall_genome = population[0][:]
    best_overall_fitness = float("-inf")

    history_best = []
    history_avg = []

    num_elites = max(1, int(ELITE_FRACTION * POP_SIZE))

    for gen in range(NUM_GENERATIONS):
        # Evaluate population
        fitnesses = [evaluate_genome(g) for g in population]

        gen_best_idx = max(range(POP_SIZE), key=lambda i: fitnesses[i])
        gen_best_fitness = fitnesses[gen_best_idx]
        gen_avg_fitness = sum(fitnesses) / len(fitnesses)

        history_best.append(gen_best_fitness)
        history_avg.append(gen_avg_fitness)

        if gen_best_fitness > best_overall_fitness:
            best_overall_fitness = gen_best_fitness
            best_overall_genome = population[gen_best_idx][:]

        print(
            f"Generation {gen:02d} | "
            f"best: {gen_best_fitness:.2f} | "
            f"avg: {gen_avg_fitness:.2f}"
        )

        # Elitism
        sorted_indices = sorted(
            range(POP_SIZE),
            key=lambda i: fitnesses[i],
            reverse=True,
        )
        new_population = [population[i][:] for i in sorted_indices[:num_elites]]

        # Fill rest of population with offspring
        while len(new_population) < POP_SIZE:
            parent1 = tournament_select(population, fitnesses)
            parent2 = tournament_select(population, fitnesses)
            child = crossover(parent1, parent2)
            child = mutate(child)
            new_population.append(child)

        population = new_population

    return best_overall_genome, best_overall_fitness, history_best, history_avg


def main():
    genome, best_fit, hist_best, hist_avg = run_ga_with_history(seed=0)
    print("\nBest overall fitness:", best_fit)
    print("Best genome length:", len(genome))

    generations = list(range(len(hist_best)))

    plt.plot(generations, hist_best, label="Best of generation")
    plt.plot(generations, hist_avg, label="Average of generation")
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    plt.title("GA Fitness Over Generations")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("ga_fitness_over_generations.png", dpi=150)
    plt.show()


if __name__ == "__main__":
    main()
