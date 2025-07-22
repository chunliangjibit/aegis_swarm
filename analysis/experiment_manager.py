# Aegis Swarm 2.0 - Experiment Manager (Ultimate Version)
import copy, time, json, multiprocessing
from core.battlefield import Battlefield

def run_single_sim_task(config):
    battlefield = Battlefield(config)
    start_time = time.time(); max_duration_seconds = 60
    blue_id, red_id = config['TEAM_BLUE_CONFIG']['id'], config['TEAM_RED_CONFIG']['id']
    initial_blue_value, initial_red_value = _calculate_team_value(battlefield, blue_id), _calculate_team_value(battlefield, red_id)
    while True:
        battlefield.update(dt=0.016)
        blue_alive, red_alive = any(a.team_id == blue_id for a in battlefield.agents), any(a.team_id == red_id for a in battlefield.agents)
        if not blue_alive or not red_alive or (time.time() - start_time > max_duration_seconds): break
    final_blue_value, final_red_value = _calculate_team_value(battlefield, blue_id), _calculate_team_value(battlefield, red_id)
    return (initial_red_value - final_red_value) - (initial_blue_value - final_blue_value)

def _calculate_team_value(battlefield, team_id):
    return sum(agent.health for agent in battlefield.agents if agent.team_id == team_id)

class ExperimentManager:
    def __init__(self, base_config):
        self.base_config = base_config; self.results = {}
        try: self.worker_count = max(1, multiprocessing.cpu_count() - 2)
        except NotImplementedError: self.worker_count = 1
        print(f"Detected {multiprocessing.cpu_count()} CPU cores. Using {self.worker_count} worker processes.")
    def run_experiments(self, blue_strategies, red_strategies, runs_per_matchup=10):
        print("="*50); print("Starting Parallel Experiment Suite...")
        print(f"Blue Strategies: {blue_strategies}"); print(f"Red Strategies: {red_strategies}"); print(f"Runs per Matchup: {runs_per_matchup}"); print("="*50)
        for b_strat_name in blue_strategies:
            for r_strat_name in red_strategies:
                matchup_key = f"{b_strat_name}_vs_{r_strat_name}"
                print(f"\n--- Running Matchup: {matchup_key} ---")
                task_configs = [self.base_config for _ in range(runs_per_matchup)] # Use the already-configured dict
                with multiprocessing.Pool(processes=self.worker_count) as pool:
                    print(f"  Dispatching {len(task_configs)} runs to {self.worker_count} worker(s)...")
                    payoff_scores = pool.map(run_single_sim_task, task_configs)
                    print("  All runs for this matchup are complete.")
                avg_payoff = sum(payoff_scores) / len(payoff_scores)
                self.results[matchup_key] = {'scores': payoff_scores, 'average_payoff': avg_payoff}
                print(f"  > Matchup '{matchup_key}' Average Payoff: {avg_payoff:.2f}")
        print("\nParallel Experiment Suite Finished!"); return self.results

    def generate_payoff_matrix(self, blue_strategies, red_strategies):
        matrix = {}; print("\n--- Payoff Matrix (Blue's Perspective) ---")
        # Adjust column width for potentially long strategy names
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

    def save_results_to_json(self, filename="experiment_results.json"):
        with open(filename, 'w') as f: json.dump(self.results, f, indent=4)
        print(f"\nFull results saved to {filename}")