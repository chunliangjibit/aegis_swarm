# Aegis Swarm 2.0 - Main Graphical User Interface (Final Import Fix)

import sys, os, pygame, copy
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, 
                             QComboBox, QSplitter, QMessageBox, QSlider, QFormLayout, QApplication) # 【核心修正】: 导入 QApplication
from PyQt5.QtCore import QTimer, Qt, QObject, QThread, pyqtSignal

from core.battlefield import Battlefield
import config as config_module
import strategies.blue_strategies as blue_strat_module
import strategies.red_strategies as red_strat_module

# --- Worker Thread Class (No changes) ---
class ExperimentWorker(QObject):
    finished = pyqtSignal(dict, str)
    def __init__(self, config_dict): super().__init__(); self.config = config_dict
    def run(self):
        print("Worker thread started...")
        from analysis.experiment_manager import ExperimentManager
        manager = ExperimentManager(self.config)
        blue_strats = [self.config['TEAM_BLUE_CONFIG'].get('strategy_name', 'default_blue_strategy')]
        red_strats = [self.config['TEAM_RED_CONFIG'].get('strategy_name', 'default_red_strategy')]
        manager.run_experiments(blue_strats, red_strats, runs_per_matchup=10)
        payoff_matrix = manager.generate_payoff_matrix(blue_strats, red_strats)
        manager.save_results_to_json("gui_experiment_results.json")
        self.finished.emit(payoff_matrix, "Experiment run is complete.\nResults saved.")

# --- Pygame Canvas Class (No changes) ---
class PygameCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.battlefield = None
        self.timer = QTimer(self); self.timer.timeout.connect(self.update_simulation)
        self.timer.start(1000 // config_module.full_config['GLOBAL_SIMULATION_SETTINGS']['FPS'])
        os.environ['SDL_WINDOWID'] = str(int(self.winId())); os.environ['SDL_VIDEODRIVER'] = 'windib'
        pygame.init(); self.screen = pygame.display.set_mode((self.width(), self.height()))
    def update_simulation(self):
        if self.battlefield:
            dt = self.timer.interval() / 1000.0; self.battlefield.update(dt)
            self.screen.fill(config_module.full_config['GLOBAL_SIMULATION_SETTINGS']['BG_COLOR'])
            self.battlefield.draw(self.screen); pygame.display.flip()
    def resizeEvent(self, event): self.screen = pygame.display.set_mode((event.size().width(), event.size().height()))

# --- Main Window (No other changes) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis Swarm 2.0 - Interactive Tactical Laboratory")
        self.setGeometry(100, 100, 1800, 1000)
        self.worker_thread = None; self.experiment_worker = None
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.splitter = QSplitter(Qt.Horizontal); self.main_layout.addWidget(self.splitter)
        self.control_panel = QFrame(); self.control_panel.setFrameShape(QFrame.StyledPanel); self.control_panel.setFixedWidth(300)
        self.control_layout = QVBoxLayout(self.control_panel); self.splitter.addWidget(self.control_panel)
        self.pygame_canvas = PygameCanvas(); self.splitter.addWidget(self.pygame_canvas)
        self.splitter.setSizes([300, 1500])
        self.init_controls()
        self.reset_simulation()

    def init_controls(self):
        sim_title = QLabel("SIMULATION CONTROL"); sim_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        self.control_layout.addWidget(sim_title)
        self.reset_button = QPushButton("Reset & Apply Changes"); self.reset_button.clicked.connect(self.reset_simulation)
        self.control_layout.addWidget(self.reset_button)
        blue_title = QLabel("BLUE TEAM CONFIGURATION"); blue_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;")
        self.control_layout.addWidget(blue_title)
        form_layout = QFormLayout()
        self.blue_strategy_combo = QComboBox()
        # This logic is a bit complex, let's find a better way to represent combined strategies
        self.blue_strategy_combo.addItems(["fortified_scouts_with_strikers"])
        form_layout.addRow("Overall Strategy:", self.blue_strategy_combo)
        self.total_blue_drones = sum(role['count'] for role in config_module.TEAM_BLUE_CONFIG['swarm_composition'].values())
        self.scout_slider = QSlider(Qt.Horizontal)
        self.scout_slider.setRange(0, self.total_blue_drones)
        initial_scout_count = config_module.TEAM_BLUE_CONFIG['swarm_composition']['fortified_scouts']['count']
        self.scout_slider.setValue(initial_scout_count)
        self.scout_slider_label = QLabel(f"{initial_scout_count} Scouts / {self.total_blue_drones - initial_scout_count} Strikers")
        self.scout_slider.valueChanged.connect(self.update_blue_composition_labels)
        form_layout.addRow("Composition:", self.scout_slider)
        form_layout.addRow("", self.scout_slider_label)
        self.control_layout.addLayout(form_layout)
        red_title = QLabel("RED TEAM CONFIGURATION"); red_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;")
        self.control_layout.addWidget(red_title)
        red_form_layout = QFormLayout()
        self.red_strategy_combo = QComboBox()
        red_strats = [s.replace("_strategy", "") for s in dir(red_strat_module) if s.endswith("_strategy")]
        self.red_strategy_combo.addItems(red_strats)
        red_form_layout.addRow("Strategy:", self.red_strategy_combo)
        self.control_layout.addLayout(red_form_layout)
        self.control_layout.addStretch(1)
        analysis_title = QLabel("ANALYSIS"); analysis_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 15px;")
        self.control_layout.addWidget(analysis_title)
        self.run_exp_button = QPushButton("Run Experiment Suite"); self.run_exp_button.setToolTip("Runs headless simulations with current settings."); self.run_exp_button.clicked.connect(self.run_experiments)
        self.control_layout.addWidget(self.run_exp_button)
        self.control_layout.addStretch(2)
        self.exit_button = QPushButton("Exit"); self.exit_button.clicked.connect(self.close); self.control_layout.addWidget(self.exit_button)

    def update_blue_composition_labels(self, value):
        scout_count = value
        striker_count = self.total_blue_drones - scout_count
        self.scout_slider_label.setText(f"{scout_count} Scouts / {striker_count} Strikers")

    def _get_config_from_gui(self):
        new_config = copy.deepcopy(config_module.full_config)
        scout_count = self.scout_slider.value()
        striker_count = self.total_blue_drones - scout_count
        new_config['TEAM_BLUE_CONFIG']['swarm_composition']['fortified_scouts']['count'] = scout_count
        new_config['TEAM_BLUE_CONFIG']['swarm_composition']['strikers']['count'] = striker_count
        # Simplified strategy naming for clarity
        new_config['TEAM_BLUE_CONFIG']['strategy_name'] = self.blue_strategy_combo.currentText()
        new_config['TEAM_RED_CONFIG']['strategy_name'] = self.red_strategy_combo.currentText() + "_strategy"
        # The logic to assign strategies per role remains in the config/strategy files
        # The experiment manager will just use the overall name for reporting.
        return new_config

    def reset_simulation(self):
        current_config = self._get_config_from_gui()
        self.pygame_canvas.battlefield = Battlefield(current_config)
    
    def run_experiments(self):
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Busy", "An experiment is already in progress."); return
        self.run_exp_button.setEnabled(False); self.run_exp_button.setText("Running...")
        current_config = self._get_config_from_gui()
        self.worker_thread = QThread()
        self.experiment_worker = ExperimentWorker(current_config)
        self.experiment_worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.experiment_worker.run)
        self.experiment_worker.finished.connect(self.on_experiment_finished)
        self.worker_thread.finished.connect(self.worker_thread.quit); self.experiment_worker.finished.connect(self.experiment_worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def on_experiment_finished(self, payoff_matrix, status_message):
        print("Worker thread finished.")
        QMessageBox.information(self, "Experiment Finished", status_message)
        self.run_exp_button.setEnabled(True); self.run_exp_button.setText("Run Experiment Suite")
        self.worker_thread = None; self.experiment_worker = None

# We keep this block for independent testing of the GUI file
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())