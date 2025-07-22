# Aegis Swarm 2.0 - Main Graphical User Interface (Phoenix Upgrade: Athena Console)
# UPGRADED: Removed the embedded Pygame canvas. The GUI is now a pure control console
# for launching headless simulations and selecting replays.

import sys, os, copy, subprocess
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, 
                             QComboBox, QSplitter, QMessageBox, QSlider, QFormLayout, QTextEdit, 
                             QApplication, QFileDialog, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QFont

import config as config_module
import strategies.blue_strategies as blue_strat_module
import strategies.red_strategies as red_strat_module

# --- Worker Thread Class (No changes) ---
class ExperimentWorker(QObject):
    finished = pyqtSignal(str)
    def __init__(self, config_dict): super().__init__(); self.config = config_dict
    def run(self):
        print("Worker thread started...")
        from analysis.experiment_manager import ExperimentManager
        manager = ExperimentManager(self.config)
        blue_strat_name = self.config['TEAM_BLUE_CONFIG']['strategy_name']
        red_strat_name = self.config['TEAM_RED_CONFIG']['strategy_name']
        manager.run_experiments([blue_strat_name], [red_strat_name], runs_per_matchup=10)
        payoff_matrix = manager.generate_payoff_matrix([blue_strat_name], [red_strat_name])
        manager.save_results_to_json("experiment_summary.json")
        result_string = f"--- Matchup Result ---\n"
        result_string += f"Blue Strategy: {blue_strat_name}\n"
        result_string += f"Red Strategy: {red_strat_name}\n"
        result_string += "-"*25 + "\n"
        payoff = payoff_matrix[blue_strat_name][red_strat_name]
        result_string += f"Average Payoff: {payoff:.2f}\n"
        result_string += "-"*25 + "\n"
        if payoff > 0: result_string += "Outcome: Blue Team Tactical Advantage"
        elif payoff < 0: result_string += "Outcome: Red Team Tactical Advantage"
        else: result_string += "Outcome: Stalemate"
        self.finished.emit(result_string)

# --- Main Window (Major Re-architecture) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis Swarm 2.0 - Athena Console")
        self.setGeometry(100, 100, 800, 600) # Smaller, more focused window
        
        self.worker_thread = None; self.experiment_worker = None
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # --- Left Panel: Controls ---
        self.control_panel = QFrame(); self.control_panel.setFrameShape(QFrame.StyledPanel)
        self.control_layout = QVBoxLayout(self.control_panel)
        
        # --- Right Panel: Replay & Results ---
        self.results_panel = QFrame(); self.results_panel.setFrameShape(QFrame.StyledPanel)
        self.results_layout = QVBoxLayout(self.results_panel)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.control_panel)
        self.splitter.addWidget(self.results_panel)
        self.main_layout.addWidget(self.splitter)
        self.splitter.setSizes([350, 450])

        self.init_controls()
        self.populate_replays()

    def init_controls(self):
        # === LEFT PANEL: CONTROLS ===
        sim_title = QLabel("TACTICAL CONFIGURATION"); sim_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;"); self.control_layout.addWidget(sim_title)
        
        blue_title = QLabel("BLUE TEAM"); blue_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;"); self.control_layout.addWidget(blue_title)
        blue_form = QFormLayout()
        self.scout_strategy_combo = QComboBox(); self.scout_strategy_combo.addItems(["bait_and_observe_strategy", "passive_scan_strategy"])
        self.striker_strategy_combo = QComboBox(); self.striker_strategy_combo.addItems(["mission_focus_strategy", "self_defense_priority_strategy", "hva_only_strategy"])
        self.striker_strategy_combo.setCurrentText("mission_focus_strategy")
        self.scout_slider = QSlider(Qt.Horizontal); self.total_blue_drones = sum(r['count'] for r in config_module.TEAM_BLUE_CONFIG['swarm_composition'].values())
        self.scout_slider.setRange(0, self.total_blue_drones); self.scout_slider.setValue(config_module.TEAM_BLUE_CONFIG['swarm_composition']['scouts']['count'])
        self.scout_slider_label = QLabel(); self.scout_slider.valueChanged.connect(self.update_blue_composition_labels)
        self.defense_radius_slider = QSlider(Qt.Horizontal); self.defense_radius_slider.setRange(0, 200); self.defense_radius_slider.setValue(75)
        self.defense_radius_label = QLabel(); self.defense_radius_slider.valueChanged.connect(self.update_defense_radius_label)
        blue_form.addRow("Scout Strategy:", self.scout_strategy_combo); blue_form.addRow("Striker Strategy:", self.striker_strategy_combo)
        blue_form.addRow("Composition:", self.scout_slider); blue_form.addRow("", self.scout_slider_label)
        blue_form.addRow("Defense Radius:", self.defense_radius_slider); blue_form.addRow("", self.defense_radius_label)
        self.control_layout.addLayout(blue_form); self.update_blue_composition_labels(self.scout_slider.value()); self.update_defense_radius_label(self.defense_radius_slider.value())

        red_title = QLabel("RED TEAM"); red_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;"); self.control_layout.addWidget(red_title)
        red_form = QFormLayout()
        self.red_strategy_combo = QComboBox(); red_strats = [s for s in dir(red_strat_module) if s.endswith("_strategy")]
        self.red_strategy_combo.addItems(red_strats); self.red_strategy_combo.setCurrentText("fearless_charge_strategy")
        red_form.addRow("Strategy:", self.red_strategy_combo)
        self.control_layout.addLayout(red_form)
        self.control_layout.addStretch(1)

        self.run_exp_button = QPushButton("Run Experiment Suite"); self.run_exp_button.setToolTip("Runs headless simulations with current settings."); self.run_exp_button.clicked.connect(self.run_experiments)
        self.control_layout.addWidget(self.run_exp_button)

        # === RIGHT PANEL: REPLAYS & RESULTS ===
        results_title = QLabel("ANALYSIS & REPLAY"); results_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;"); self.results_layout.addWidget(results_title)
        
        self.results_box = QTextEdit(); self.results_box.setReadOnly(True); self.results_box.setFont(QFont("Courier New", 10)); self.results_box.setText("Experiment results will be shown here.")
        self.results_box.setFixedHeight(200) # Fixed height for summary
        self.results_layout.addWidget(self.results_box)

        replay_title = QLabel("Available Replays"); replay_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;"); self.results_layout.addWidget(replay_title)
        self.replay_list = QListWidget()
        self.replay_list.itemDoubleClicked.connect(self.launch_replay)
        self.results_layout.addWidget(self.replay_list)

        refresh_button = QPushButton("Refresh Replay List")
        refresh_button.clicked.connect(self.populate_replays)
        self.results_layout.addWidget(refresh_button)

    def populate_replays(self):
        """Scans the 'replays' directory and populates the list widget."""
        self.replay_list.clear()
        replays_dir = "replays"
        if os.path.exists(replays_dir):
            files = [f for f in os.listdir(replays_dir) if f.endswith(".json")]
            self.replay_list.addItems(sorted(files, reverse=True))
        else:
            self.replay_list.addItem("No 'replays' directory found.")

    def launch_replay(self, item):
        """Launches the replay script with the selected file."""
        replay_file = os.path.join("replays", item.text())
        if not os.path.exists(replay_file):
            QMessageBox.warning(self, "Error", "Replay file not found.")
            return
        
        print(f"Launching replay for: {replay_file}")
        # Use subprocess to launch replay.py as a separate process
        # This is more robust than trying to embed it.
        try:
            # Assumes 'python' is in the system's PATH
            subprocess.Popen(["python", "replay.py", replay_file])
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Could not find 'replay.py'. Make sure it is in the project's root directory.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch replay: {e}")
            
    # ... (the rest of the methods are the same, just removed reset_simulation) ...
    def update_blue_composition_labels(self, value): self.scout_slider_label.setText(f"{value} Scouts / {self.total_blue_drones - value} Strikers")
    def update_defense_radius_label(self, value): self.defense_radius_label.setText(f"{value} pixels")
    def _get_config_from_gui(self):
        new_config = copy.deepcopy(config_module.full_config)
        new_config['TEAM_BLUE_CONFIG']['swarm_composition']['scouts']['count'] = self.scout_slider.value()
        new_config['TEAM_BLUE_CONFIG']['swarm_composition']['strikers']['count'] = self.total_blue_drones - self.scout_slider.value()
        new_config['TEAM_BLUE_CONFIG']['swarm_composition']['scouts']['strategy'] = self.scout_strategy_combo.currentText()
        new_config['TEAM_BLUE_CONFIG']['swarm_composition']['strikers']['strategy'] = self.striker_strategy_combo.currentText()
        new_config['TEAM_BLUE_CONFIG']['self_defense_radius'] = self.defense_radius_slider.value()
        new_config['TEAM_BLUE_CONFIG']['strategy_name'] = f"Scouts({self.scout_strategy_combo.currentText()})_Strikers({self.striker_strategy_combo.currentText()})"
        red_strat = self.red_strategy_combo.currentText()
        new_config['TEAM_RED_CONFIG']['strategy_name'] = red_strat
        for role_cfg in new_config['TEAM_RED_CONFIG']['swarm_composition'].values(): role_cfg['strategy'] = red_strat
        return new_config
    def run_experiments(self):
        if self.worker_thread and self.worker_thread.isRunning(): QMessageBox.warning(self, "Busy", "An experiment is already in progress."); return
        self.run_exp_button.setEnabled(False); self.run_exp_button.setText("Running..."); self.results_box.setText("Running experiment...\nPlease wait.")
        current_config = self._get_config_from_gui()
        self.worker_thread = QThread()
        self.experiment_worker = ExperimentWorker(current_config)
        self.experiment_worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.experiment_worker.run); self.experiment_worker.finished.connect(self.on_experiment_finished)
        self.worker_thread.finished.connect(self.worker_thread.quit); self.experiment_worker.finished.connect(self.experiment_worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()
    def on_experiment_finished(self, result_string):
        print("Worker thread finished.")
        self.results_box.setText(result_string)
        self.run_exp_button.setEnabled(True); self.run_exp_button.setText("Run Experiment Suite")
        self.worker_thread = None; self.experiment_worker = None
        self.populate_replays() # Automatically refresh the list after experiments

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())