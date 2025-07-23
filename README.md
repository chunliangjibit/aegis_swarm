# Aegis Swarm 3.2 - Advanced Tactical Laboratory

**Aegis Swarm** is an advanced, agent-based 2D simulation platform for Unmanned Aerial Vehicle (UAV) swarm confrontations. It is designed to explore, validate, and quantify the effectiveness of complex swarm intelligence tactics through rigorous, data-driven experimentation.

This version (v3.2) introduces a revolutionary **Market-Based AI** for the Blue Team and a modular **Mission-Driven AI** for the Red Team, creating a high-fidelity environment for sophisticated tactical wargaming.

---

## Core Features

- **High-Fidelity Agent Modeling**: Each UAV is an independent agent (`Agent`) with its own physical attributes, state, and decision-making logic, now featuring distinct visual identification for different roles.

- **Blue Team: Intelligent Marketplace AI**:
  - **Decentralized Decision-Making**: The Blue team's task allocation is governed by a decentralized **Marketplace**. An auction mechanism efficiently assigns tasks to the agent that can execute them at the lowest "cost," a dynamic value combining travel distance and perceived risk.
  - **Dynamic Task Valuation**: Targets are no longer static points. Their "bounty" value dynamically changes based on threat level, intelligence freshness, and cross-validation from multiple scouts.
  - **Automatic Task Bundling**: The market AI automatically groups spatially and temporally close targets into high-value "bundle" tasks, encouraging strikers to perform coordinated, multi-target strikes instead of "one-by-one" attacks.
  - **Role Specialization & Visual ID**: The swarm is divided into **Scouts** (light blue) and **Strikers** (dark blue).
    - **Scouts** proactively search the battlefield and publish discovered enemies as "bounty" tasks to the market.
    - **Strikers** act as rational "bounty hunters," assessing risk and bidding on tasks to execute attacks.

- **Red Team: Modular Mission-Driven AI**:
  - **Mission + ROE Framework**: The Red Team's AI is no longer a monolithic script. It combines high-level **Missions** (the strategic goal) with low-level **Rules of Engagement (ROE)** (the tactical reaction).
  - **Diverse Tactical Profiles**: This framework allows for the creation of numerous, distinct enemy behaviors selectable in the GUI, including:
    - **Armed Assault**: Aggressively advances towards a key point, engaging any target of opportunity en route.
    - **Stealth Infiltration**: Prioritizes reaching a key point by actively evading combat unless absolutely necessary.
    - **Area Sweep Force**: Patrols a designated zone with the express purpose of seeking and destroying all hostile units.
    - **Zombie Charge (Legacy)**: The original, predictable direct-attack strategy, retained for baseline comparisons.

- **Scientific Experimentation Framework**:
  - **Parallelized Simulation**: Leverages Python's `multiprocessing` module to run numerous independent simulation instances in parallel, enabling rapid generation of statistically significant results.
  - **Quantitative Evaluation**: Automatically generates a **Payoff Matrix** to scientifically measure the performance of different tactical matchups.
  - **Comprehensive Logging**: Generates a detailed `experiment_summary.json` for each experiment suite, logging all configurations, parameters, and run-by-run results for full reproducibility.

- **Visual Replay & Analysis**:
  - **Apollo Replayer**: A standalone viewer (`replay.py`) provides perfect visual playback of every engagement.
  - **Advanced Visualization**: The replayer visualizes market tasks, highlights high-value targets, renders bundle tasks as distinct strategic objectives, and uses unique colors for different agent roles, providing deep tactical insight at a glance.

---

## Tech Stack

- **Simulation Core**: Python 3.9+, NumPy, Numba (for performance acceleration)
- **GUI & Visualization**:
  - **Main Control Panel (Athena Console)**: PyQt5
  - **Replay Viewer (Apollo Replayer)**: Pygame
- **Data Format**: JSON

---

## How to Run

1.  **Environment Setup**:
    It is highly recommended to use a virtual environment.
    ```bash
    # Using Conda
    conda create -n swarm python=3.9
    conda activate swarm

    # Or using venv
    python -m venv swarm_env
    source swarm_env/bin/activate  # On Windows: swarm_env\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install numpy numba pygame PyQt5
    ```

3.  **Launch the Athena Console**:
    This is the main entry point of the application. It provides a GUI to configure and launch experiments.
    ```bash
    python main.py
    ```

4.  **Run an Experiment**:
    - In the **Athena Console** GUI, you can now select a sophisticated strategy for the Red Team from the dropdown menu (e.g., "Armed Assault," "Stealth Infiltration").
    - You can adjust the Blue Team's force composition (Scouts vs. Strikers) using the slider.
    - Click the **"Run Experiment Suite"** button. The application will run 10 headless simulations in the background.
    - After completion, the resulting Payoff Matrix will be displayed in the results text box, and a detailed `experiment_summary.json` will be saved to the root directory.

5.  **Watch a Replay**:
    - Detailed log files (`.json`) are automatically saved to the `replays/` directory after an experiment.
    - In the console GUI, click **"Refresh Replay List"**. The new log files will appear.
    - **Double-click** any log file in the list to launch the Apollo Replayer.
    - In the replay, you can now clearly distinguish light blue Scouts from dark blue Strikers and observe the complex market dynamics.

---

## Future Roadmap

- [ ] **Advanced AI Behaviors**: Implement more complex market mechanisms, such as multi-task bundle auctions and peer-to-peer task trading between agents.
- [ ] **Enhanced Physics Engine**: Introduce more realistic physical constraints, such as terrain occlusion (Line of Sight) and fuel consumption.
- [ ] **3D Visualization**: Migrate the simulation and replay systems to a 3D engine to explore tactical behaviors in three-dimensional space.