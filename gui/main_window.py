# Aegis Swarm 3.1 - Main GUI (Patch 3.1.2)
# PATCH: Restored the call to save_results_to_json in the worker thread.

import sys, os, copy, subprocess
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, 
                             QComboBox, QSplitter, QMessageBox, QSlider, QFormLayout, QTextEdit, 
                             QApplication, QFileDialog, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QFont

import config as config_module

class ExperimentWorker(QObject):
    finished = pyqtSignal(str)
    def __init__(self, config_dict):
        super().__init__()
        self.config = config_dict
    
    def run(self):
        from analysis.experiment_manager import ExperimentManager
        manager = ExperimentManager(self.config)
        
        blue_strat_name = self.config['TEAM_BLUE_CONFIG']['strategy_name']
        red_strat_profile = self.config['TEAM_RED_CONFIG'].get('active_strategy_profile', {})
        red_strat_name = red_strat_profile.get('display_name', 'Unknown Red Strategy')
        
        manager.run_experiments([blue_strat_name], [red_strat_name], runs_per_matchup=10)
        payoff_matrix = manager.generate_payoff_matrix([blue_strat_name], [red_strat_name])
        
        # --- [THE FIX] This line was missing! ---
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis Swarm 3.1 - Athena Console (Red Dawn Edition)")
        self.setGeometry(100, 100, 800, 600)
        
        self.worker_thread = None; self.experiment_worker = None
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        
        self.control_panel = QFrame(); self.control_panel.setFrameShape(QFrame.StyledPanel)
        self.control_layout = QVBoxLayout(self.control_panel)
        
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
        sim_title = QLabel("TACTICAL CONFIGURATION"); sim_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;"); self.control_layout.addWidget(sim_title)
        
        blue_title = QLabel("BLUE TEAM"); blue_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;"); self.control_layout.addWidget(blue_title)
        blue_form = QFormLayout()
        self.blue_strategy_label = QLabel("Market-Based AI (Unified)")
        self.scout_slider = QSlider(Qt.Horizontal)
        blue_comp = config_module.TEAM_BLUE_CONFIG['swarm_composition']
        self.total_blue_drones = blue_comp['scouts']['count'] + blue_comp['strikers']['count']
        self.scout_slider.setRange(0, self.total_blue_drones); self.scout_slider.setValue(blue_comp['scouts']['count'])
        self.scout_slider_label = QLabel(); self.scout_slider.valueChanged.connect(self.update_blue_composition_labels)
        blue_form.addRow("AI Strategy:", self.blue_strategy_label)
        blue_form.addRow("Composition:", self.scout_slider)
        blue_form.addRow("", self.scout_slider_label)
        self.control_layout.addLayout(blue_form)
        self.update_blue_composition_labels(self.scout_slider.value())

        red_title = QLabel("RED TEAM"); red_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;"); self.control_layout.addWidget(red_title)
        red_form = QFormLayout()
        self.red_strategy_combo = QComboBox()
        
        red_profiles = config_module.TEAM_RED_CONFIG['strategy_profiles']
        for key, profile in red_profiles.items():
            self.red_strategy_combo.addItem(profile['display_name'], key)
        
        default_key = config_module.TEAM_RED_CONFIG['default_strategy']
        default_index = self.red_strategy_combo.findData(default_key)
        if default_index != -1: self.red_strategy_combo.setCurrentIndex(default_index)

        red_form.addRow("Strategy:", self.red_strategy_combo)
        self.control_layout.addLayout(red_form)
        self.control_layout.addStretch(1)

        self.run_exp_button = QPushButton("Run Experiment Suite"); self.run_exp_button.clicked.connect(self.run_experiments)
        self.control_layout.addWidget(self.run_exp_button)

        results_title = QLabel("ANALYSIS & REPLAY"); results_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;"); self.results_layout.addWidget(results_title)
        self.results_box = QTextEdit(); self.results_box.setReadOnly(True); self.results_box.setFont(QFont("Courier New", 10)); self.results_box.setText("Experiment results will be shown here.")
        self.results_box.setFixedHeight(200)
        self.results_layout.addWidget(self.results_box)
        replay_title = QLabel("Available Replays"); replay_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;"); self.results_layout.addWidget(replay_title)
        self.replay_list = QListWidget(); self.replay_list.itemDoubleClicked.connect(self.launch_replay)
        self.results_layout.addWidget(self.replay_list)
        refresh_button = QPushButton("Refresh Replay List"); refresh_button.clicked.connect(self.populate_replays)
        self.results_layout.addWidget(refresh_button)

    def populate_replays(self):
        self.replay_list.clear()
        replays_dir = "replays"
        if os.path.exists(replays_dir):
            files = sorted([f for f in os.listdir(replays_dir) if f.endswith(".json")], reverse=True)
            self.replay_list.addItems(files)
        else:
            self.replay_list.addItem("No 'replays' directory found.")

    def launch_replay(self, item):
        replay_file = os.path.join("replays", item.text())
        if not os.path.exists(replay_file): return
        try:
            subprocess.Popen([sys.executable, "replay.py", replay_file])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch replay: {e}")
            
    def update_blue_composition_labels(self, value): 
        self.scout_slider_label.setText(f"{value} Scouts / {self.total_blue_drones - value} Strikers")

    def _get_config_from_gui(self):
        new_config = copy.deepcopy(config_module.full_config)
        
        scout_count = self.scout_slider.value()
        new_config['TEAM_BLUE_CONFIG']['swarm_composition']['scouts']['count'] = scout_count
        new_config['TEAM_BLUE_CONFIG']['swarm_composition']['strikers']['count'] = self.total_blue_drones - scout_count
        
        selected_key = self.red_strategy_combo.currentData()
        red_profiles = new_config['TEAM_RED_CONFIG']['strategy_profiles']
        if selected_key in red_profiles:
            new_config['TEAM_RED_CONFIG']['active_strategy_profile'] = red_profiles[selected_key]
        else:
            default_key = new_config['TEAM_RED_CONFIG']['default_strategy']
            new_config['TEAM_RED_CONFIG']['active_strategy_profile'] = red_profiles[default_key]
            
        return new_config

    def run_experiments(self):
        if self.worker_thread and self.worker_thread.isRunning(): return
        
        self.run_exp_button.setEnabled(False); self.run_exp_button.setText("Running...")
        self.results_box.setText("Running experiment...\nPlease wait.")
        
        current_config = self._get_config_from_gui()
        self.worker_thread = QThread()
        self.experiment_worker = ExperimentWorker(current_config)
        self.experiment_worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.experiment_worker.run)
        self.experiment_worker.finished.connect(self.on_experiment_finished)
        self.worker_thread.start()

    def on_experiment_finished(self, result_string):
        self.results_box.setText(result_string)
        self.run_exp_button.setEnabled(True); self.run_exp_button.setText("Run Experiment Suite")
        self.populate_replays()
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.worker_thread = None; self.experiment_worker = None