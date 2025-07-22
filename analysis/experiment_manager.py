# Aegis Swarm 2.0 - Experiment Manager (with Organized Logging)
# UPGRADED: All detailed simulation logs are now saved into a dedicated 'replays' folder.

import copy, time, json, multiprocessing, uuid, os # 【新增】: 导入 os 模块

from core.battlefield import Battlefield

def run_single_sim_task(config_and_id):
    config, sim_id = config_and_id
    import pygame
    pygame.init()
    battlefield = Battlefield(config)
    start_time = time.time(); max_duration_seconds = 60
    simulation_log = {"metadata": {}, "timestamps": []}
    blue_id, red_id = config['TEAM_BLUE_CONFIG']['id'], config['TEAM_RED_CONFIG']['id']
    initial_blue_value, initial_red_value = _calculate_team_value(battlefield, blue_id), _calculate_team_value(battlefield, red_id)
    current_time, dt = 0.0, 0.016
    while True:
        battlefield.update(dt=dt); current_time += dt
        snapshot = battlefield.get_snapshot(); snapshot['time'] = round(current_time, 3)
        simulation_log["timestamps"].append(snapshot)
        blue_alive, red_alive = snapshot['blue_count'] > 0, snapshot['red_count'] > 0
        if not blue_alive or not red_alive or (time.time() - start_time > max_duration_seconds): break
    final_blue_value, final_red_value = _calculate_team_value(battlefield, blue_id), _calculate_team_value(battlefield, red_id)
    payoff = (initial_red_value - final_red_value) - (initial_blue_value - final_blue_value)
    simulation_log["metadata"] = {
        "simulation_id": sim_id, "blue_strategy": config['TEAM_BLUE_CONFIG']['strategy_name'],
        "red_strategy": config['TEAM_RED_CONFIG']['strategy_name'], "duration": round(current_time, 2),
        "result": { "payoff": round(payoff, 2), "blue_survivors": battlefield.get_snapshot()['blue_count'], "red_survivors": battlefield.get_snapshot()['red_count'] }
    }
    return simulation_log

def _calculate_team_value(battlefield, team_id):
    return sum(agent.health for agent in battlefield.agents if agent.team_id == team_id)

class ExperimentManager:
    def __init__(self, base_config):
        self.base_config = base_config; self.results = {}
        try: self.worker_count = max(1, multiprocessing.cpu_count() - 2)
        except NotImplementedError: self.worker_count = 1
        print(f"Detected {multiprocessing.cpu_count()} CPU cores. Using {self.worker_count} worker processes.")
        
        # 【新增】: 创建 replays 文件夹
        self.replays_dir = "replays"
        if not os.path.exists(self.replays_dir):
            os.makedirs(self.replays_dir)
            print(f"Created directory: {self.replays_dir}")

    def run_experiments(self, blue_strategies, red_strategies, runs_per_matchup=10):
        print("="*50); print("Starting Parallel Experiment Suite...")
        print(f"Blue Strategies: {blue_strategies}"); print(f"Red Strategies: {red_strategies}"); print(f"Runs per Matchup: {runs_per_matchup}"); print("="*50)
        
        for b_strat_name in blue_strategies:
            for r_strat_name in red_strategies:
                matchup_key = f"{b_strat_name}_vs_{r_strat_name}"
                print(f"\n--- Running Matchup: {matchup_key} ---")
                
                tasks = []
                for i in range(runs_per_matchup):
                    run_config = copy.deepcopy(self.base_config)
                    sim_id = f"sim_{b_strat_name.replace('(', '_').replace(')', '').replace(' ', '')}_vs_{r_strat_name}_{i+1}"
                    tasks.append((run_config, sim_id))

                with multiprocessing.Pool(processes=self.worker_count) as pool:
                    print(f"  Dispatching {len(tasks)} runs to {self.worker_count} worker(s)...")
                    simulation_logs = pool.map(run_single_sim_task, tasks)
                    print("  All runs for this matchup are complete.")
                
                payoff_scores = []
                for log in simulation_logs:
                    payoff_scores.append(log['metadata']['result']['payoff'])
                    # 【修改】: 将日志文件保存到 replays 文件夹内
                    log_filename = os.path.join(self.replays_dir, f"{log['metadata']['simulation_id']}.json")
                    with open(log_filename, 'w') as f:
                        json.dump(log, f) # Use compact format for smaller files
                    print(f"    - Detailed log saved to {log_filename}")

                avg_payoff = sum(payoff_scores) / len(payoff_scores)
                self.results[matchup_key] = {'scores': payoff_scores, 'average_payoff': avg_payoff}
                print(f"  > Matchup '{matchup_key}' Average Payoff: {avg_payoff:.2f}")
        
        print("\nParallel Experiment Suite Finished!"); return self.results

    def generate_payoff_matrix(self, blue_strategies, red_strategies):
        # ... (This method is correct and has no changes) ...
        matrix = {}; print("\n--- Payoff Matrix (Blue's Perspective) ---")
        col_width = max(len(s) for s in red_strategies) + 4
        blue_strat_width = max(len(s) for s in blue_strategies)
        header = " " * blue_strat_width + "".join([f"{s:>{col_width}}" for s in red_strategies])
        print(header); print("-" * len(header))
        for b_strat in blue_strategies:
            row_str = f"{b_strat:<{blue_strat_width}}"; row_data = {}
            for r_strat in red_strategies:
                matchup_key = f"{b_strat}_vs_{r_strat}"
                payoff = self.results.get(matchup_key, {}).get('average_payoff', 'N/A')
                if isinstance(payoff, float): row_str += f"{payoff:>{col_width}.2f}"; row_data[r_strat] = payoff
                else: row_str += f"{'N/A':>{col_width}}"; row_data[r_strat] = None
            print(row_str); matrix[b_strat] = row_data
        return matrix

    def save_results_to_json(self, filename="experiment_summary.json"):
        # ... (This method is correct and has no changes) ...
        with open(filename, 'w') as f: json.dump(self.results, f, indent=4)
        print(f"\nSummary results saved to {filename}")