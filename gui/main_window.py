# Aegis Swarm 2.0 - Main Graphical User Interface (Final Cleaned Version)
import sys, os, pygame
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QComboBox, QSplitter, QMessageBox)
from PyQt5.QtCore import QTimer, Qt, QObject, QThread, pyqtSignal
from core.battlefield import Battlefield
import config as config_module

class ExperimentWorker(QObject):
    finished = pyqtSignal(dict, str)
    def __init__(self, config_dict): super().__init__(); self.config = config_dict
    def run(self):
        print("Worker thread started...")
        from analysis.experiment_manager import ExperimentManager
        manager = ExperimentManager(self.config)
        blue_strats = ["bait_and_observe/wait_for_hva_and_strike"]
        red_strats = ["fearless_charge"]
        manager.run_experiments(blue_strats, red_strats, runs_per_matchup=10)
        payoff_matrix = manager.generate_payoff_matrix(blue_strats, red_strats)
        manager.save_results_to_json("gui_experiment_results.json")
        self.finished.emit(payoff_matrix, "Experiment run is complete.\nResults saved.")

class PygameCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.battlefield = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(1000 // config_module.full_config['GLOBAL_SIMULATION_SETTINGS']['FPS'])
        os.environ['SDL_WINDOWID'] = str(int(self.winId()))
        os.environ['SDL_VIDEODRIVER'] = 'windib'
        pygame.init()
        self.screen = pygame.display.set_mode((self.width(), self.height()))
    def update_simulation(self):
        if self.battlefield:
            dt = self.timer.interval() / 1000.0
            self.battlefield.update(dt)
            self.screen.fill(config_module.full_config['GLOBAL_SIMULATION_SETTINGS']['BG_COLOR'])
            self.battlefield.draw(self.screen)
            pygame.display.flip()
    def resizeEvent(self, event): self.screen = pygame.display.set_mode((event.size().width(), event.size().height()))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis Swarm 2.0 - Tactical AI Laboratory")
        self.setGeometry(100, 100, 1800, 1000)
        self.worker_thread = None
        self.experiment_worker = None
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)
        self.control_panel = QFrame()
        self.control_panel.setFrameShape(QFrame.StyledPanel)
        self.control_panel.setFixedWidth(250)
        self.control_layout = QVBoxLayout(self.control_panel)
        self.splitter.addWidget(self.control_panel)
        self.pygame_canvas = PygameCanvas()
        self.splitter.addWidget(self.pygame_canvas)
        self.splitter.setSizes([250, 1550])
        self.init_controls()
        self.reset_simulation()
    def init_controls(self):
        title = QLabel("CONTROLS"); title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;"); self.control_layout.addWidget(title)
        self.reset_button = QPushButton("Reset Simulation"); self.reset_button.clicked.connect(self.reset_simulation); self.control_layout.addWidget(self.reset_button)
        self.control_layout.addStretch(1)
        strat_title = QLabel("Strategy Matchup"); strat_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;"); self.control_layout.addWidget(strat_title)
        self.control_layout.addWidget(QLabel("Blue Team Strategy:"))
        self.blue_strategy_combo = QComboBox(); self.blue_strategy_combo.addItems(["bait_and_observe/wait_for_hva_and_strike"]); self.control_layout.addWidget(self.blue_strategy_combo)
        self.control_layout.addWidget(QLabel("Red Team Strategy:"))
        self.red_strategy_combo = QComboBox(); self.red_strategy_combo.addItems(["fearless_charge"]); self.control_layout.addWidget(self.red_strategy_combo)
        self.control_layout.addStretch(2)
        exp_title = QLabel("Analysis"); exp_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;"); self.control_layout.addWidget(exp_title)
        self.run_exp_button = QPushButton("Run Experiment Suite"); self.run_exp_button.setToolTip("Runs headless simulations. Check console."); self.run_exp_button.clicked.connect(self.run_experiments)
        self.control_layout.addWidget(self.run_exp_button)
        self.control_layout.addStretch(5)
        self.exit_button = QPushButton("Exit"); self.exit_button.clicked.connect(self.close); self.control_layout.addWidget(self.exit_button)
    def reset_simulation(self):
        self.pygame_canvas.battlefield = Battlefield(config_module.full_config)
    def run_experiments(self):
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Busy", "An experiment is already in progress. Please wait.")
            return
        self.run_exp_button.setEnabled(False)
        self.run_exp_button.setText("Running...")
        self.worker_thread = QThread()
        self.experiment_worker = ExperimentWorker(config_module.full_config)
        self.experiment_worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.experiment_worker.run)
        self.experiment_worker.finished.connect(self.on_experiment_finished)
        self.worker_thread.finished.connect(self.worker_thread.quit)
        self.experiment_worker.finished.connect(self.experiment_worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()
    def on_experiment_finished(self, payoff_matrix, status_message):
        print("Worker thread finished.")
        QMessageBox.information(self, "Experiment Finished", status_message)
        self.run_exp_button.setEnabled(True)
        self.run_exp_button.setText("Run Experiment Suite")
        self.worker_thread = None
        self.experiment_worker = None