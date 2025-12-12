# Multi-Objective Dungeon Controller Evolution

# GitHub Repo link: https://github.com/PrudlowA-Msoe/DungeonCrawlerAI

**Group members:**  
- Andrew Prudlow  
- Nihal Majjiga  

This project evolves an AI controller for a 5×5 dungeon game using a **genetic algorithm (GA)** over a **decision-tree–style policy**.  
The dungeon contains walls, melee-weak and magic-weak monsters, health/mana potions, coins, and an exit.  
The agent must reach the exit while balancing multiple objectives: avoid damage, kill monsters efficiently, use potions intelligently, collect coins, and finish quickly.

The codebase also includes:
- A hand crafted controller,
- A hill-climbing optimizer for a controller,
- A GA-evolved decision-tree-like controller,
- Scripts for visualizing training, hyperparameter sweeps, and algorithm comparisons.

---

## Project Structure

Every file/folder and its purpos:

- **`agent.py`** – Defines the `Agent` class, action enum, combat rules, inventory (potions/coins), and how the agent steps and draws itself in the dungeon.
- **`compare-algorithms.py`** – Runs batches of random dungeons with multiple controllers (GA DT, hill-climber, human-like) and prints aggregate performance statistics.
- **`config.py`** – Central configuration for grid size, tile size, colors, reward weights, and key hyperparameters (population size, mutation rate, etc.).
- **`controllers.py`** – Implements controller classes, including the GA `DecisionTreeController`, random/walker baselines, and helpers for mapping discrete state features to genome indices. 
- **`dungeon.py`** – Defines the `Dungeon` environment, tile types (walls, monsters, potions, coins, exit), random layout generation, connectivity checks, and rendering. 
- **`ga.py`** – Core genetic algorithm loop: initializes a population of genomes, evaluates them in the dungeon, performs selection, crossover, mutation, and prints fitness over generations. 
- **`hillclimbing.py`** – Hill-climbing optimization over parameters of a hand-made controller to produce a strong baseline.
- **`human.py`** – Human controller that maps keyboard input (movement / attacks / potion use) into actions, used as a baseline or for demos.
- **`hyperparam_sweep_mutation.py`** – Runs multiple GA trainings across different hyperparameter combinations (population, mutation rate, episodes per eval, etc.), logging summary stats and saving plots comparing settings.
- **`main.py`** – PyGame front-end that loads a chosen “best” genome, runs through 5 random floors, lets you toggle between AI and keyboard control, and logs floor scores plus the AI’s last few actions.
- **`plot_ga_fitness_over_time.py`** – Convenience script to run GA training and save a matplotlib figure of best vs. average fitness per generation.  
- **`sprites.py`** – Loads and scales sprite images (player, monsters, potions, coin, wall, exit) from the `sprites/` folder for use in the PyGame renderer.
- **`training.py`** – Shared training utilities: runs episodes for a given controller over randomized dungeons, computes the multi-objective fitness, and returns evaluation metrics. 
- **`sprites/`** – Folder of PNG sprites: `player.png`, `monster1.png`, `monster2.png`, `health.png`, `mana.png`, `coin.png`, `exit.png`, `rock1.png`, etc., used for visual rendering. 

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
```

## How to Run the Project

This section basically explains how to run the project

---

### 1. Visual Demo: move around or watch the AI in the Dungeon

```bash
python main.py
```

**What this does**

- Opens a PyGame window and spawns **5 random dungeon floors**.
- Uses the hard-coded `BEST_GENOME` at the top of `main.py` as the AI’s policy.
- Lets you switch between **AI control** and **keyboard control**.

**Controls**

- **Arrow keys** – Move the agent when human control is active.
- **A** – Toggle AI controller ON/OFF.
- **R** – Restart at floor 1 with a new set of random floors.
- **Esc** – Quit the game window.

**Console output (terminal)**

Every time the agent reaches the exit of a floor, the program prints:

- Floor number  
- Steps taken on that floor  
- Damage taken  
- Monsters killed  
- Coins collected  
- Potions collected  
- The **floor score** computed by `compute_floor_score(...)`

**On-screen HUD in the game window**

- Current floor / total floors  
- Whether AI control is ON or OFF  
- The last **three AI actions** chosen (to help understand its decisions)

---

### 2. Train the Genetic Algorithm (Decision-Tree Controller)

```bash
python ga.py
```

**What you’ll see**

During training, the script prints lines like:

```text
Generation 12 | best: 144.45 | avg: 91.22
```

- `best` = best fitness in that generation  
- `avg` = average fitness over the whole population

At the end, it prints:

- The **best overall genome** (a list of integers, one per discrete state)  
- The **best overall fitness** value found

**Reusing a trained genome**

To visualize a trained controller in the PyGame demo:

1. Copy the final printed genome from `ga.py`’s output.
2. Paste it into the `BEST_GENOME` constant near the top of `main.py`.
3. Run `python main.py` again to watch that evolved controller play.

**Tuning the GA**

- Hyperparameters (population size, number of generations, mutation rate, etc.) are defined in `ga.py` and/or `config.py`.
- You can edit those values and re-run `ga.py` to see how training behavior changes.

---

### 3. Plot Fitness Over Time

```bash
python plot_ga_fitness_over_time.py
```

**What this script does**

- Runs a full GA training run using the same core training code.
- Logs fitness at each generation.
- Creates a matplotlib figure with:
  - X-axis: generation number  
  - Y-axis: **best fitness** and **average fitness**  

- Saves the figure as something like:

```text
ga_fitness_over_generations.png
```

in the current working directory.

**How to interpret the plot**

- A **steep early increase** means the GA quickly finds much better controllers.
- A **plateau** indicates the population is converging; you may need to change
  hyperparameters or the representation to get further improvements.

---

### 4. Hyperparameter Sweep

```bash
python hyperparam_sweep_mutation.py
```

**What it does**

- Defines a grid of GA hyperparameters, such as:
  - Population sizes
  - Mutation rates
  - Number of episodes per fitness evaluation
- For each hyperparameter combination, it:
  - Runs several GA training trials
  - Collects the **final best fitness** from each trial
  - Prints lines like:

    ```text
    pop=100, mut=0.2, episodes=5 -> mean_best=..., stdev=...
    ```

- Generates a matplotlib bar chart or line plot summarizing which settings
  produced the highest mean best fitness, saved as e.g.:

```text
ga_sweep_<param_name>.png
```

in the working directory.

**How to interpret the plots**

- Compare bars/points to see which:
  - Population sizes
  - Mutation rates
  - Evaluation episode counts

  lead to the strongest controllers.

- A **high standard deviation** suggests training is unstable for that setting;
  high mean with **low** standard deviation is usually best.

---

### 5. Compare Controllers (GA vs Human-like vs Hill-Climber)

```bash
python compare-algorithms.py
```

**What this script does**

- Runs each controller type on many random dungeon floors, for example:
  - Human handmade controller
  - GA-evolved decision-tree controller
  - Hill-climber–optimized handmade controller
- Uses the same scoring function as the rest of the project:

```text
score = 200
        - 2 * steps
        + 10 * monsters_killed
        + 5 * potions_collected
        + 8 * coins_collected
        - 0.3 * damage_taken
```

- At the end, prints a comparison table summarizing:

  - **Average score (all runs)**  
  - **Average score (successful runs only)** – where the agent reached the exit  
  - **Success rate** (% of floors completed)  
  - **Average steps** on successful runs  
  - **Average damage**, **kills**, **potions**, and **coins**

**How to interpret**

- The higher the **Avg Score (all)**, the stronger the controller across the full distribution of floors.
- Comparing **Success Rate** and **Avg Damage** reveals trade-offs:
  - Some controllers win more often but take more damage.
  - Others are more cautious but may time out or fail more often.
- You can use these numbers directly in reports, tables, or slides to discuss performance.

---

### 6. Hill-Climbing on Handmade Controller

```bash
python hillclimbing.py
```

**What it does**

- Starts from a parameterized **hand-designed** controller (with weights for things like distance to exit, monster risk, etc.).
- Repeatedly overwrites those parameters and **keeps the changes** that improve the average fitness on sampled dungeons.
- Prints:
  - The parameter changes over time
  - The final performance achieved by the hill-climbed controller

This provides a strong, explainable baseline to compare against the GA-evolved controller.

---

## Outputs and How to Interpret Them

### Console Logs

- **`ga.py`** – Shows per-generation fitness
  - Use this to see whether training is improving or has plateaued.
- **`main.py`** – Prints per-floor stats whenever an exit is reached:
  - **Steps:** lower is better.
  - **Damage:** lower is better.
  - **Monsters / coins / potions:** higher is better.
  - **Score:** single scalar combining all objectives; values around ~180+ are very good given the spawn caps.
- **`compare-algorithms.py`** – Prints a summary table across controllers; ideal for performance comparison in your writeup or presentation.

### Saved Figures

- **`ga_fitness_over_generations.png`** (from `plot_ga_fitness_over_time.py`):
  - Shows how the GA’s best and average fitness change over generations.
- **`ga_sweep_*.png`** (from `hyperparam_sweep_mutation.py`):
  - Show how changing hyperparameters (population, mutation, episodes per eval, etc.) affects final performance.

### Game Window

- Visual animation of the agent moving through multiple random floors.
- Useful to:
  - Point to the HUD’s last-three-actions display and explain how the controller chooses moves (fo example when it decides to drink potions vs attack vs move).

---

## Typical Workflow

To recreate what we did in the project:

1. **Train a GA controller**

   ```bash
   python ga.py
   ```

   - Note the printed final best genome.

2. **Plug that genome into the demo**

   - Open `main.py` and set `BEST_GENOME` to the list printed by `ga.py`.

3. **Visualize behavior in PyGame**

   ```bash
   python main.py
   ```

   - Watch 5 random floors and observe:
     - How often the AI reaches the exit
     - How it fights monsters
     - When it uses health/mana potions
     - Whether it goes out of its way to pick up coins

4. **Analyze training behavior and hyperparameters**

   ```bash
   python plot_ga_fitness_over_time.py
   python hyperparam_sweep_mutation.py
   ```

   - Use the generated plots to understand:
     - How quickly fitness improves
     - Which hyperparameters work best

5. **Compare algorithms for analysis**

   ```bash
   python compare-algorithms.py
   ```

   - Use the table to directly compare:
     - GA decision-tree controller
     - Human-like handmade controller
     - Hill-climber–optimized controller
