# Aegis Swarm：Tactical AI Laboratory

Aegis Swarm is a high-performance，configurable 2D simulation platform designed for UAV（Unmanned Aerial Vehicle）swarm tactics and multi-agent AI research。It provides a laboratory environment to develop，visualize，and analyze complex confrontation scenarios between two opposing forces（Blue vs. Red）。

The platform features a graphical user interface for real-time visualization and an automated experiment manager for running large-scale batch simulations to evaluate strategy effectiveness。

## Key Features 🚀

*   **Hybrid GUI System**：Combines a **PyQt5**-based main window for application controls with an embedded **Pygame** viewport for efficient，real-time rendering of the simulation battlefield。
*   **High-Performance Simulation Core**：Utilizes **Numba**'s JIT（Just-In-Time）compilation to accelerate critical，computationally-intensive calculations（e.g.，Boids model，combat damage，perception checks），enabling smooth simulation of large-scale swarms。
*   **Advanced Agent Modeling**：Agents are modeled with detailed attributes including flight physics，health，perception radius，and weapon systems。Their movement can be governed by a customizable Boids flocking model combined with tactical objectives。
*   **Modular Strategy Framework**：Agent behavior is defined in easily editable strategy modules（`blue_strategies.py`，`red_strategies.py`）。This allows for the rapid development and testing of new tactical logic without altering the core simulation engine。
*   **Intelligence and Fog of War**：The platform models situational awareness through a “Shared Situational Picture”（SSP）module。This allows agents to share perception data，simulating a team-level intelligence network and the effects of incomplete information。
*   **Automated Experiment Manager**：A powerful tool（`analysis/experiment_manager.py`）to run headless，parallelized simulations using Python's `multiprocessing` library。It can systematically test different strategy matchups over many runs，generate statistical results，and output a strategic payoff matrix。
*   **Deeply Configurable**：Nearly every aspect of the simulation—from agent performance and weapon characteristics to UI colors and AI model weights—is controlled through a centralized configuration file（`config.py`）。

## Architecture Overview 🏗️

The platform's architecture is designed to separate concerns，making it modular and extensible。

1.  **Application Entry Point（`main.py`）**：Initializes the PyQt5 `QApplication` and launches the `MainWindow`。
2.  **Main Window（`gui/main_window.py`）**：The primary GUI window。It contains controls and embeds a `BattlefieldWidget` where the simulation is rendered。
3.  **Battlefield Orchestrator（`core/battlefield.py`）**：The heart of a single simulation run。It manages the game loop，updates the state of all agents，orchestrates model calculations，and uses Pygame to draw the scene。
4.  **Core Models（`core/models.py`）**：This is the performance-critical computation layer。It contains functions decorated with `@njit` from the Numba library to perform high-speed calculations for agent movement（Boids），combat outcomes，and perception。
5.  **Agent Definition（`core/agent.py`）**：Defines the `Agent` class，which encapsulates the state and physics of a single UAV。
6.  **Experiment Manager（`analysis/experiment_manager.py`）**：Operates at a higher level than the GUI。It can spawn multiple `Battlefield` instances in separate processes to conduct large-scale，automated experiments without the need for graphical output。

## Installation & Setup 🛠️

Follow these steps to get the simulation environment running on your local machine。

1.  **Clone the repository：**
    ```bash
    git clone [https://github.com/your-username/aegis_swarm.git](https://github.com/your-username/aegis_swarm.git)
    cd aegis_swarm
    ```

2.  **（Recommended）Create a Python virtual environment：**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies from `requirements.txt`：**
    The project's dependencies are listed in `requirements.txt`。Install them using pip：
    ```bash
    pip install -r requirements.txt
    ```

## How to Use 📖

### Running a Single Simulation with GUI

To launch the visual simulation and observe strategies in real-time，run the `main.py` script：

```bash
python main.py
```

This will open the main application window where you can start，pause，and reset the simulation。

### Running Automated Experiments (Headless)

For rigorous testing of AI strategies，you can use the `ExperimentManager`。This script runs simulations in the background much faster than real-time。

1.  Create a new Python script in the root directory（e.g.，`run_experiments.py`）。

2.  Add the following code to the script to configure and run an experiment：

    ```python
    from analysis.experiment_manager import ExperimentManager
    from config import get_config

    if __name__ == '__main__':
        # Define which strategies to test against each other
        blue_strats_to_test = ["bait_and_observe/wait_for_hva_and_strike"]
        red_strats_to_test = ["fearless_charge"]

        # Load the base configuration
        base_config = get_config()

        # Initialize and run the manager
        manager = ExperimentManager(base_config)
        results = manager.run_experiments(
            blue_strategies=blue_strats_to_test,
            red_strategies=red_strats_to_test,
            runs_per_matchup=100  # Number of simulations for each matchup
        )

        # Generate and print the results
        manager.generate_payoff_matrix(blue_strats_to_test, red_strats_to_test)
        manager.save_results_to_json("my_experiment_results.json")

    ```

3.  Execute the script from your terminal：

    ```bash
    python run_experiments.py
    ```

4.  The results，including a payoff matrix and raw scores，will be printed to the console and saved in a JSON file。

## Configuration ⚙️

All simulation parameters are centralized in `config.py`。Modifying this file is the primary way to alter the simulation's behavior。

Key configuration sections include：

*   **`TEAM_BLUE_CONFIG` / `TEAM_RED_CONFIG`**：Define team properties，swarm composition，and default strategies。
*   **`ROLE_TEMPLATES`**：Define the performance characteristics of different agent types（e.g.，speed，health，sensor range）。
*   **`WEAPON_TEMPLATES`**：Define weapon parameters like damage，area of effect，and kill probability。
*   **`GLOBAL_SIMULATION_SETTINGS`**：Control global parameters like screen size and boundary behavior。

## Dependencies

*   **PyQt5**：Powers the main application window，menus，and controls。
*   **Pygame**：Used for 2D rendering of the battlefield，agents，and projectiles。
*   **NumPy**：The backbone for all numerical operations，especially vector and matrix calculations。
*   **Numba**：Dramatically accelerates performance by JIT-compiling computation-heavy Python and NumPy code。
*   **PyYAML**：Used for loading and parsing the `.yaml` configuration files（though the final version uses a `.py` config，this dependency might exist from a previous iteration and is good practice for config management）。