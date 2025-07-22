# Aegis Swarm 2.0 - Main Graphical User Interface (Final Import Fix)
import sys, os, pygame, copy
# 【核心修正】: 在这个导入列表中，重新加入 QApplication
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, 
                             QComboBox, QSplitter, QMessageBox, QSlider, QFormLayout, QTextEdit, QApplication)
from PyQt5.QtCore import QTimer, Qt, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from core.battlefield import Battlefield
import config as config_module
import strategies.blue_strategies as blue_strat_module
import strategies.red_strategies as red_strat_module

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
        manager.save_results_to_json("gui_experiment_results.json")
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

class PygameCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setMinimumSize(800, 600); self.battlefield = None
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis Swarm 2.0 - Ultimate Tactical Laboratory"); self.setGeometry(100, 100, 1800, 1000)
        self.worker_thread = None; self.experiment_worker = None
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.splitter = QSplitter(Qt.Horizontal); self.main_layout.addWidget(self.splitter)
        self.control_panel = QFrame(); self.control_panel.setFrameShape(QFrame.StyledPanel); self.control_panel.setFixedWidth(350)
        self.control_layout = QVBoxLayout(self.control_panel); self.splitter.addWidget(self.control_panel)
        self.pygame_canvas = PygameCanvas(); self.splitter.addWidget(self.pygame_canvas)
        self.splitter.setSizes([350, 1450]); self.init_controls(); self.reset_simulation()
        
    def init_controls(self):
        sim_title = QLabel("SIMULATION CONTROL"); sim_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;"); self.control_layout.addWidget(sim_title)
        self.reset_button = QPushButton("Reset & Apply Changes"); self.reset_button.clicked.connect(self.reset_simulation); self.control_layout.addWidget(self.reset_button)
        blue_title = QLabel("BLUE TEAM CONFIGURATION"); blue_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;"); self.control_layout.addWidget(blue_title)
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
        red_title = QLabel("RED TEAM CONFIGURATION"); red_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;"); self.control_layout.addWidget(red_title)
        red_form = QFormLayout()
        self.red_strategy_combo = QComboBox(); red_strats = [s for s in dir(red_strat_module) if s.endswith("_strategy")]
        self.red_strategy_combo.addItems(red_strats); self.red_strategy_combo.setCurrentText("fearless_charge_strategy")
        red_form.addRow("Strategy:", self.red_strategy_combo)
        self.control_layout.addLayout(red_form)
        self.control_layout.addStretch(1)
        analysis_title = QLabel("ANALYSIS"); analysis_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 15px;"); self.control_layout.addWidget(analysis_title)
        self.run_exp_button = QPushButton("Run Experiment Suite"); self.run_exp_button.setToolTip("Runs headless simulations with current settings."); self.run_exp_button.clicked.connect(self.run_experiments)
        self.control_layout.addWidget(self.run_exp_button)
        self.results_box = QTextEdit(); self.results_box.setReadOnly(True); self.results_box.setFont(QFont("Courier New", 10)); self.results_box.setText("Experiment results will be shown here.")
        self.control_layout.addWidget(self.results_box)
        self.exit_button = QPushButton("Exit"); self.exit_button.clicked.connect(self.close); self.control_layout.addWidget(self.exit_button)

    def update_blue_composition_labels(self, value): self.scout_slider_label.setText(f"{value} Scouts / {self.total_blue_drones - value} Strikers")
    def update_defense_radius_label(self, value): self.defense_radius_label.setText(f"{value} pixels")
    
    def _get_config_from_gui(self):
        new_config = copy.deepcopy(config_module.full_config)
        new_config['TEAM_BLUE_CONFIG']['swarm_composition']['scouts']['count'] = self.scout_slider.value()
        new_config['TEAM_BLUE_CONFIG']['swarm_composition']['strikers']['count'] = self.total_blue_drones - self.scout_slider.value()
        new_config['TEAM_BLUE_CONFIG']['swarm_composition']['scouts']['strategy'] = self.scout_strategy_combo.currentText()
        new_config['TEAM_BLUE_CONFIG']['swarm_composition']['strikers']['strategy'] = self.striker_strategy_combo.currentText()
        new_config['TEAM_BLUE_CONFIG']['self_defense_radius'] = self.defense_radius_slider.value()
        new_config['TEAM_BLUE_CONFIG']['strategy_name'] = f"Scouts({self.scout_strategy_combo.currentText()}) + Strikers({self.striker_strategy_combo.currentText()})"
        red_strat = self.red_strategy_combo.currentText()
        new_config['TEAM_RED_CONFIG']['strategy_name'] = red_strat
        for role_cfg in new_config['TEAM_RED_CONFIG']['swarm_composition'].values(): role_cfg['strategy'] = red_strat
        return new_config

    def reset_simulation(self): self.pygame_canvas.battlefield = Battlefield(self._get_config_from_gui())
    
    def run_experiments(self):
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Busy", "An experiment is already in progress."); return
        self.run_exp_button.setEnabled(False); self.run_exp_button.setText("Running..."); self.results_box.setText("Running experiment...\nPlease wait.")
        current_config = self._get_config_from_gui()
        self.worker_thread = QThread()
        self.experiment_worker = ExperimentWorker(current_config)
        self.experiment_worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.experiment_worker.run)
        self.experiment_worker.finished.connect(self.on_experiment_finished)
        self.worker_thread.finished.connect(self.worker_thread.quit); self.experiment_worker.finished.connect(self.experiment_worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def on_experiment_finished(self, result_string):
        print("Worker thread finished.")
        self.results_box.setText(result_string)
        self.run_exp_button.setEnabled(True); self.run_exp_button.setText("Run Experiment Suite")
        self.worker_thread = None; self.experiment_worker = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())