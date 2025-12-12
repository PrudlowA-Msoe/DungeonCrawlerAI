# Multi-Objective Dungeon Controller Evolution

**Group members:**  
- Andrew Prudlow  
- Nihal Majjiga  

This project evolves an AI controller for a tiny 5×5 dungeon game using a **genetic algorithm (GA)** over a **decision-tree–style policy**.  
The dungeon contains walls, melee-weak and magic-weak monsters, health/mana potions, coins, and an exit.  
The agent must reach the exit while balancing multiple objectives: avoid damage, kill monsters efficiently, use potions intelligently, collect coins, and finish quickly.

The codebase also includes:
- A hand-crafted “human-like” controller,
- A hill-climbing optimizer for a handmade controller,
- A GA-evolved decision-tree controller,
- Scripts for visualizing training, hyperparameter sweeps, and algorithm comparisons.

---

## Project Structure

Every file/folder and its purpose in one sentence:

- **`agent.py`** – Defines the `Agent` class, action enum, combat rules, inventory (potions/coins), and how the agent steps and draws itself in the dungeon. :contentReference[oaicite:0]{index=0}  
- **`compare-algorithms.py`** – Runs batches of random dungeons with multiple controllers (GA DT, hill-climber, human-like) and prints aggregate performance statistics.
- **`config.py`** – Central configuration for grid size, tile size, colors, reward weights, and key hyperparameters (population size, mutation rate, etc.).
- **`controllers.py`** – Implements controller classes, including the GA `DecisionTreeController`, random/walker baselines, and helpers for mapping discrete state features to genome indices. :contentReference[oaicite:1]{index=1}  
- **`dungeon.py`** – Defines the `Dungeon` environment, tile types (walls, monsters, potions, coins, exit), random layout generation, connectivity checks, and rendering. :contentReference[oaicite:2]{index=2}  
- **`ga.py`** – Core genetic algorithm loop: initializes a population of genomes, evaluates them in the dungeon, performs selection, crossover, mutation, and prints fitness over generations. :contentReference[oaicite:3]{index=3}  
- **`hillclimbing.py`** – Hill-climbing optimization over parameters of a hand-made controller to produce a strong baseline.
- **`human.py`** – Human-controlled policy that maps keyboard input (movement / attacks / potion use) into actions, used as a baseline or for demos.
- **`hyperparam_sweep_mutation.py`** – Runs multiple GA trainings across different hyperparameter combinations (population, mutation rate, episodes per eval, etc.), logging summary stats and saving plots comparing settings. :contentReference[oaicite:4]{index=4}  
- **`main.py`** – PyGame front-end that loads a chosen “best” genome, runs through 5 random floors, lets you toggle between AI and keyboard control, and logs floor scores plus the AI’s last few actions. :contentReference[oaicite:5]{index=5}  
- **`plot_ga_fitness_over_time.py`** – Convenience script to run GA training and save a matplotlib figure of best vs. average fitness per generation. :contentReference[oaicite:6]{index=6}  
- **`sprites.py`** – Loads and scales sprite images (player, monsters, potions, coin, wall, exit) from the `sprites/` folder for use in the PyGame renderer. :contentReference[oaicite:7]{index=7}  
- **`training.py`** – Shared training utilities: runs episodes for a given controller over randomized dungeons, computes the multi-objective fitness, and returns evaluation metrics. :contentReference[oaicite:8]{index=8}  
- **`sprites/`** – Folder of PNG sprites: `player.png`, `monster1.png`, `monster2.png`, `health.png`, `mana.png`, `coin.png`, `exit.png`, `rock1.png`, etc., used for visual rendering. :contentReference[oaicite:9]{index=9}  

(If you add new scripts or assets, give them a one-line description here.)

---

## Requirements & Installation

**Python version:** 3.9+ recommended.

**Required libraries (beyond the standard library):**

- [pygame](https://www.pygame.org/) – for graphics and real-time interaction.
- [matplotlib](https://matplotlib.org/) – for plotting fitness curves and hyperparameter sweeps.

Install via:

```bash
pip install pygame matplotlib

