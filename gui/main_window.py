# Aegis Swarm 3.2 - Main GUI (Video Export Edition)
# UPGRADED:
# - Added an "Export Selected to MP4" button to the GUI.
# - The button is only enabled when a replay is selected.
# - Video export runs in a non-blocking background thread (QThread).
# - Provides GUI feedback during and after the export process.

import sys, os, copy, subprocess
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, 
                             QComboBox, QSplitter, QMessageBox, QSlider, QFormLayout, QTextEdit, 
                             QApplication, QFileDialog, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QFont

import config as config_module

class ExperimentWorker(QObject):
    """Worker thread for running the simulation experiment suite."""
    finished = pyqtSignal(str)
    def __init__(self, config_dict):
        super().__init__()
        self.config = config_dict
    
    def run(self):
        # This part remains unchanged
        from analysis.experiment_manager import ExperimentManager # Assuming the folder name is 'analysis'
        manager = ExperimentManager(self.config)
        blue_strat_name = self.config['TEAM_BLUE_CONFIG']['strategy_name']
        red_strat_profile = self.config['TEAM_RED_CONFIG'].get('active_strategy_profile', {})
        red_strat_name = red_strat_profile.get('display_name', 'Unknown Red Strategy')
        manager.run_experiments([blue_strat_name], [red_strat_name], runs_per_matchup=10)
        payoff_matrix = manager.generate_payoff_matrix([blue_strat_name], [red_strat_name])
        manager.save_results_to_json("experiment_summary.json")
        result_string = f"--- Matchup Result ---\n"
        result_string += f"Blue Strategy: {blue_strat_name}\nRed Strategy: {red_strat_name}\n"
        result_string += "-"*25 + "\n"
        payoff = payoff_matrix[blue_strat_name][red_strat_name]
        result_string += f"Average Payoff: {payoff:.2f}\n"
        result_string += "-"*25 + "\n"
        if payoff > 0: result_string += "Outcome: Blue Team Tactical Advantage"
        elif payoff < 0: result_string += "Outcome: Red Team Tactical Advantage"
        else: result_string += "Outcome: Stalemate"
        self.finished.emit(result_string)

# --- [NEW] Worker for Video Export ---
class VideoExportWorker(QObject):
    """Worker thread for exporting a replay to MP4 to avoid freezing the GUI."""
    finished = pyqtSignal(str) # Emits a status message when done
    
    def __init__(self, replay_filepath):
        super().__init__()
        self.replay_filepath = replay_filepath

    def run(self):
        try:
            command = [sys.executable, "replay.py", self.replay_filepath, "--export-video"]
            # Using subprocess.run to wait for the process to complete and capture output
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            self.finished.emit(f"SUCCESS: Video exported for\n{os.path.basename(self.replay_filepath)}")
        except subprocess.CalledProcessError as e:
            error_message = f"ERROR exporting video:\n{e.stderr}"
            self.finished.emit(error_message)
        except Exception as e:
            self.finished.emit(f"An unexpected error occurred: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis Swarm 3.2 - Athena Console")
        self.setGeometry(100, 100, 800, 600)
        
        self.experiment_worker_thread = None; self.experiment_worker = None
        self.video_worker_thread = None; self.video_exporter = None # For video export

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
        # ... (rest of the controls setup is the same)
        sim_title = QLabel("TACTICAL CONFIGURATION"); sim_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;"); self.control_layout.addWidget(sim_title)
        blue_title = QLabel("BLUE TEAM"); blue_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;"); self.control_layout.addWidget(blue_title)
        blue_form = QFormLayout()
        self.blue_strategy_label = QLabel("Market-Based AI (Unified)")
        self.scout_slider = QSlider(Qt.Horizontal)
        blue_comp = config_module.TEAM_BLUE_CONFIG['swarm_composition']
        self.total_blue_drones = blue_comp['scouts']['count'] + blue_comp['strikers']['count']
        self.scout_slider.setRange(0, self.total_blue_drones); self.scout_slider.setValue(blue_comp['scouts']['count'])
        self.scout_slider_label = QLabel(); self.scout_slider.valueChanged.connect(self.update_blue_composition_labels)
        blue_form.addRow("AI Strategy:", self.blue_strategy_label); blue_form.addRow("Composition:", self.scout_slider); blue_form.addRow("", self.scout_slider_label)
        self.control_layout.addLayout(blue_form)
        self.update_blue_composition_labels(self.scout_slider.value())
        red_title = QLabel("RED TEAM"); red_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;"); self.control_layout.addWidget(red_title)
        red_form = QFormLayout()
        self.red_strategy_combo = QComboBox()
        red_profiles = config_module.TEAM_RED_CONFIG['strategy_profiles']
        for key, profile in red_profiles.items(): self.red_strategy_combo.addItem(profile['display_name'], key)
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
        
        self.replay_list = QListWidget()
        self.replay_list.itemDoubleClicked.connect(self.launch_interactive_replay)
        self.replay_list.itemSelectionChanged.connect(self.on_replay_selection_changed) # <-- [NEW] Connect signal
        self.results_layout.addWidget(self.replay_list)
        
        # --- [NEW] Button layout for replay controls ---
        replay_button_layout = QHBoxLayout()
        self.refresh_replays_button = QPushButton("Refresh Replay List")
        self.refresh_replays_button.clicked.connect(self.populate_replays)
        self.export_video_button = QPushButton("Export Selected to MP4")
        self.export_video_button.clicked.connect(self.launch_video_export)
        self.export_video_button.setEnabled(False) # Disabled by default
        
        replay_button_layout.addWidget(self.refresh_replays_button)
        replay_button_layout.addWidget(self.export_video_button)
        self.results_layout.addLayout(replay_button_layout)

    def populate_replays(self):
        self.replay_list.clear()
        replays_dir = "replays"
        if os.path.exists(replays_dir):
            files = sorted([f for f in os.listdir(replays_dir) if f.endswith(".json")], key=lambda f: os.path.getmtime(os.path.join(replays_dir, f)), reverse=True)
            self.replay_list.addItems(files)
        else:
            self.replay_list.addItem("No 'replays' directory found.")

    def launch_interactive_replay(self, item):
        replay_file = os.path.join("replays", item.text())
        if not os.path.exists(replay_file): return
        try:
            # Use Popen for non-blocking interactive replay
            subprocess.Popen([sys.executable, "replay.py", replay_file])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch replay: {e}")
            
    # --- [ALL NEW METHODS FOR VIDEO EXPORT] ---

    def on_replay_selection_changed(self):
        """Enables or disables the export button based on selection."""
        if self.replay_list.currentItem() and self.export_video_button.text() == "Export Selected to MP4":
            self.export_video_button.setEnabled(True)
        else:
            self.export_video_button.setEnabled(False)

    def launch_video_export(self):
        """Starts the video export process in a background thread."""
        if self.video_worker_thread and self.video_worker_thread.isRunning():
            return
        
        selected_item = self.replay_list.currentItem()
        if not selected_item:
            self.results_box.setText("Please select a replay from the list to export.")
            return

        replay_file_path = os.path.join("replays", selected_item.text())
        
        self.export_video_button.setEnabled(False)
        self.export_video_button.setText("Exporting...")
        self.results_box.setText(f"Starting video export for:\n{selected_item.text()}\n\nThis may take a moment...")
        QApplication.processEvents() # Force GUI update

        self.video_worker_thread = QThread()
        self.video_exporter = VideoExportWorker(replay_file_path)
        self.video_exporter.moveToThread(self.video_worker_thread)
        self.video_worker_thread.started.connect(self.video_exporter.run)
        self.video_exporter.finished.connect(self.on_video_export_finished)
        self.video_worker_thread.start()
        
    def on_video_export_finished(self, message):
        """Handles the completion of the video export thread."""
        self.results_box.setText(message)
        self.export_video_button.setText("Export Selected to MP4")
        self.on_replay_selection_changed() # Re-evaluate if button should be enabled
        
        if self.video_worker_thread:
            self.video_worker_thread.quit()
            self.video_worker_thread.wait()
        self.video_worker_thread = None
        self.video_exporter = None
        
    # --- [END OF NEW METHODS] ---

    def update_blue_composition_labels(self, value): 
        self.scout_slider_label.setText(f"{value} Scouts / {self.total_blue_drones - value} Strikers")

    def _get_config_from_gui(self):
        # This part remains unchanged
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
        if self.experiment_worker_thread and self.experiment_worker_thread.isRunning(): return
        self.run_exp_button.setEnabled(False); self.run_exp_button.setText("Running...")
        self.results_box.setText("Running experiment...\nPlease wait.")
        current_config = self._get_config_from_gui()
        self.experiment_worker_thread = QThread()
        self.experiment_worker = ExperimentWorker(current_config)
        self.experiment_worker.moveToThread(self.experiment_worker_thread)
        self.experiment_worker_thread.started.connect(self.experiment_worker.run)
        self.experiment_worker.finished.connect(self.on_experiment_finished)
        self.experiment_worker_thread.start()

    def on_experiment_finished(self, result_string):
        self.results_box.setText(result_string)
        self.run_exp_button.setEnabled(True); self.run_exp_button.setText("Run Experiment Suite")
        self.populate_replays()
        if self.experiment_worker_thread:
            self.experiment_worker_thread.quit()
            self.experiment_worker_thread.wait()
        self.experiment_worker_thread = None; self.experiment_worker = None

# Main application entry point remains the same
if __name__ == '__main__':
    # This block is typically in a separate main.py, but including here for completeness
    # if this file were to be run directly.
    try:
        from gui.main_window import MainWindow # Assumes standard project structure
    except ImportError:
        pass # Allow running this file directly for testing

    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())