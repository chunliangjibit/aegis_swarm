# Aegis Swarm 2.5 - Tactical AI Laboratory (Intelligent Marketplace Edition)

**Aegis Swarm** is an advanced, agent-based 2D simulation platform for Unmanned Aerial Vehicle (UAV) swarm confrontations. It is designed to explore, validate, and quantify the effectiveness of complex swarm intelligence tactics through rigorous, data-driven experimentation.

The core feature of the current version (v2.5) is a **decentralized, "intelligent marketplace" AI for task allocation**, which replaces traditional centralized command-and-control models.

---

## Core Features

- **High-Fidelity Agent Modeling**: Each UAV is an independent agent (`Agent`) with its own physical attributes, state, and decision-making logic.
- **Emergent Swarm Intelligence**: Built upon the classic Boids model, the swarm exhibits fluid and organized flocking behaviors.
- **Revolutionary Marketplace AI**:
  - **Decentralized Decision-Making**: The Blue team's task allocation is no longer dependent on a central authority. A **decentralized marketplace (`Marketplace`)** uses an auction mechanism to efficiently assign tasks to the agent that can perform them at the lowest cost.
  - **Role Specialization**: The swarm is divided into **Scouts** and **Strikers**.
    - **Scouts** proactively search the battlefield and publish discovered enemies as high-value "bounty" tasks to the market.
    - **Strikers** act as rational "bounty hunters," bidding on these tasks to execute attacks.
  - **Resilient Intelligence Network**: Embodying the "Every Platform is a Sensor" concept, all agents—including Strikers—contribute to situational awareness by publishing new intelligence, creating a robust network with no single point of failure.
- **Configurable Adversary AI**: The Red team possesses multiple configurable strategies (e.g., distributed attack), providing a challenging and intelligent opponent for testing the Blue AI.
- **Scientific Experimentation Framework**:
  - **Parallelized Simulation**: Leverages Python's `multiprocessing` module to run numerous independent simulation instances in parallel, enabling rapid generation of statistically significant results.
  - **Quantitative Evaluation**: Automatically generates a **Payoff Matrix** to scientifically measure the performance of different tactical matchups.
- **Visual Replay & Analysis**: Every simulation run is logged to a detailed `.json` file. A standalone **Apollo Replayer** (`replay.py`) provides perfect visual playback of the engagement, including real-time agent status and the dynamic state of market tasks.

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
    It is recommended to use a virtual environment like Conda or venv.
    ```bash
    conda create -n swarm python=3.9
    conda activate swarm
    ```

2.  **Install Dependencies**:
    ```bash
    pip install numpy numba pygame PyQt5
    ```

3.  **Launch the Athena Console**:
    This is the main entry point of the application. It provides a GUI to configure and launch experiments.
    ```bash
    python main_window.py
    ```

4.  **Run an Experiment**:
    - In the console GUI, you can select the Red team's strategy and adjust the Blue team's force composition.
    - Click the **"Run Experiment Suite"** button. The application will run 10 headless simulations in the background (this can be configured in `analysis/experiment_manager.py`).
    - After completion, the resulting Payoff Matrix will be displayed in the results text box.

5.  **Watch a Replay**:
    - Detailed log files are automatically saved to the `replays/` directory after an experiment.
    - In the console GUI, click **"Refresh Replay List"**. The new log files will appear.
    - **Double-click** any log file in the list to launch the Apollo Replayer and watch a full visual playback of that specific simulation run.

---

## Future Roadmap

- [ ] **Advanced AI Behaviors**: Implement more complex market mechanisms, such as multi-task bundle auctions and peer-to-peer task trading between agents.
- [ ] **Enhanced Physics Engine**: Introduce more realistic physical constraints, such as terrain occlusion (Line of Sight) and fuel consumption.
- [ ] **3D Visualization**: Migrate the simulation and replay systems to a 3D engine to explore tactical behaviors in three-dimensional space.