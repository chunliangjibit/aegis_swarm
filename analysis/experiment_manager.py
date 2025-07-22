# Aegis Swarm 2.0 - Experiment Manager (Final Architecture Fix)
# CORRECTION: Updated to use agent.team_id instead of the old agent.team attribute.

import copy, time, json, multiprocessing
from core.battlefield import Battlefield

# Top-level function for multiprocessing
def run_single_sim_task(config):
    battlefield = Battlefield(config)
    start_time = time.time()
    max_duration_seconds = 60
    
    # 【核心修正】: 使用 'id' 而不是 'color'
    blue_id = config['TEAM_BLUE_CONFIG']['id']
    red_id = config['TEAM_RED_CONFIG']['id']

    initial_blue_value = _calculate_team_value(battlefield, blue_id)
    initial_red_value = _calculate_team_value(battlefield, red_id)

    while True:
        battlefield.update(dt=0.016)
        
        # 【核心修正】: 使用 'id' 而不是 'color'
        blue_alive = any(a.team_id == blue_id for a in battlefield.agents)
        red_alive = any(a.team_id == red_id for a in battlefield.agents)
        
        if not blue_alive or not red_alive or (time.time() - start_time > max_duration_seconds):
            break
    
    final_blue_value = _calculate_team_value(battlefield, blue_id)
    final_red_value = _calculate_team_value(battlefield, red_id)
    
    blue_loss = initial_blue_value - final_blue_value
    red_loss = initial_red_value - final_red_value
    
    return red_loss - blue_loss

# 【核心修正】: 接受 team_id 并比较 agent.team_id
def _calculate_team_value(battlefield, team_id):
    """Helper function to calculate team value based on team_id."""
    total_value = sum(agent.health for agent in battlefield.agents if agent.team_id == team_id)
    return total_value


class ExperimentManager:
    def __init__(self, base_config):
        self.base_config = base_config
        self.results = {}
        try:
            cpu_count = multiprocessing.cpu_count()
            self.worker_count = max(1, cpu_count - 2) 
        except NotImplementedError:
            self.worker_count = 1
        print(f"Detected {multiprocessing.cpu_count()} CPU cores. Using {self.worker_count} worker processes for experiments.")

    def run_experiments(self, blue_strategies, red_strategies, runs_per_matchup=10):
        print("="*50); print("Starting Parallel Experiment Suite...")
        print(f"Blue Strategies: {blue_strategies}"); print(f"Red Strategies: {red_strategies}"); print(f"Runs per Matchup: {runs_per_matchup}"); print("="*50)

        total_matchups = len(blue_strategies) * len(red_strategies)
        matchup_count = 0

        for b_strat in blue_strategies:
            for r_strat in red_strategies:
                matchup_count += 1
                matchup_key = f"{b_strat}_vs_{r_strat}"
                print(f"\n--- Running Matchup {matchup_count}/{total_matchups}: {matchup_key} ---")

                task_configs = []
                for _ in range(runs_per_matchup):
                    run_config = copy.deepcopy(self.base_config)
                    # This logic assigns strategies. It is complex and may need future refinement.
                    # For now, it assumes blue strategy name contains role hints.
                    for role_config in run_config['TEAM_BLUE_CONFIG']['swarm_composition'].values():
                        if "bait" in b_strat and "bait" in role_config['strategy']:
                            role_config['strategy'] = "bait_and_observe"
                        elif "strike" in b_strat and "strike" in role_config['strategy']:
                            role_config['strategy'] = "wait_for_hva_and_strike"
                    for role_config in run_config['TEAM_RED_CONFIG']['swarm_composition'].values():
                        role_config['strategy'] = r_strat
                    task_configs.append(run_config)

                with multiprocessing.Pool(processes=self.worker_count) as pool:
                    print(f"  Dispatching {len(task_configs)} runs to {self.worker_count} worker(s)...")
                    payoff_scores = pool.map(run_single_sim_task, task_configs)
                    print("  All runs for this matchup are complete.")

                avg_payoff = sum(payoff_scores) / len(payoff_scores)
                self.results[matchup_key] = {'scores': payoff_scores, 'average_payoff': avg_payoff}
                print(f"  > Matchup '{matchup_key}' Average Payoff: {avg_payoff:.2f}")
        
        print("\nParallel Experiment Suite Finished!")
        return self.results

    def generate_payoff_matrix(self, blue_strategies, red_strategies):
        # ... (This method is correct and has no changes) ...
        matrix = {}
        print("\n--- Payoff Matrix (Blue's Perspective) ---")
        header = " " * 35 + "".join([f"{s:>20}" for s in red_strategies])
        print(header); print("-" * len(header))
        for b_strat in blue_strategies:
            row_str = f"{b_strat:<35}"
            row_data = {}
            for r_strat in red_strategies:
                matchup_key = f"{b_strat}_vs_{r_strat}"
                payoff = self.results.get(matchup_key, {}).get('average_payoff', 'N/A')
                if isinstance(payoff, float): row_str += f"{payoff:>20.2f}"; row_data[r_strat] = payoff
                else: row_str += f"{'N/A':>20}"; row_data[r_strat] = None
            print(row_str); matrix[b_strat] = row_data
        return matrix

    def save_results_to_json(self, filename="experiment_results.json"):
        # ... (This method is correct and has no changes) ...
        with open(filename, 'w') as f: json.dump(self.results, f, indent=4)
        print(f"\nFull results saved to {filename}")