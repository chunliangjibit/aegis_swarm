# Aegis Swarm 3.1 - Experiment Manager (Comprehensive Logging Edition)
# UPGRADED: The manager now produces a rich, self-contained JSON summary file,
# logging all critical configuration and detailed run-by-run results.

import copy, time, json, multiprocessing, uuid, os, traceback
from datetime import datetime, timezone

from core.battlefield import Battlefield

def run_single_sim_task(config_and_id):
    config, sim_id = config_and_id
    run_summary = { "simulation_id": sim_id, "error": None }
    
    try:
        import pygame
        pygame.init()
        battlefield = Battlefield(config)
        start_time = time.time(); max_duration_seconds = 60
        
        # Get metadata from the specific config for this run
        blue_strat_name = config['TEAM_BLUE_CONFIG']['strategy_name']
        red_profile = config['TEAM_RED_CONFIG'].get('active_strategy_profile', {})
        red_strat_name = red_profile.get('display_name', 'Unknown')
        
        simulation_log = {"metadata": {}, "timestamps": []}
        
        blue_id = config['TEAM_BLUE_CONFIG']['id']
        red_id = config['TEAM_RED_CONFIG']['id']
        initial_blue_value = sum(agent.health for agent in battlefield.agents if agent.team_id == blue_id)
        initial_red_value = sum(agent.health for agent in battlefield.agents if agent.team_id == red_id)
        
        current_time, dt = 0.0, 0.016
        while True:
            battlefield.update(dt=dt); current_time += dt
            snapshot = battlefield.get_snapshot()
            snapshot['time'] = round(current_time, 3)
            simulation_log["timestamps"].append(snapshot)
            blue_alive, red_alive = snapshot['blue_count'] > 0, snapshot['red_count'] > 0
            if not blue_alive or not red_alive or (time.time() - start_time > max_duration_seconds): break
            
        final_snapshot = battlefield.get_snapshot()
        final_blue_value = sum(a['health'] for a in final_snapshot['agents'] if a['team_id'] == blue_id)
        final_red_value = sum(a['health'] for a in final_snapshot['agents'] if a['team_id'] == red_id)
        
        payoff = (initial_red_value - final_red_value) - (initial_blue_value - final_blue_value)
        
        # Populate the full log for replay
        simulation_log["metadata"] = {
            "simulation_id": sim_id, "blue_strategy": blue_strat_name, "red_strategy": red_strat_name,
            "duration": round(current_time, 2),
            "result": { "payoff": round(payoff, 2), "blue_survivors": final_snapshot['blue_count'], "red_survivors": final_snapshot['red_count'] }
        }
        
        # Populate the concise summary for the main report
        run_summary.update({
            "payoff": round(payoff, 2), "duration": round(current_time, 2),
            "blue_survivors": final_snapshot['blue_count'], "red_survivors": final_snapshot['red_count']
        })
        
        return simulation_log, run_summary

    except Exception as e:
        run_summary["error"] = f"{type(e).__name__}: {e}"
        traceback.print_exc()
        return None, run_summary


class ExperimentManager:
    def __init__(self, base_config):
        self.base_config = base_config
        self.results = {} # This will now store much richer data
        try: self.worker_count = max(1, multiprocessing.cpu_count() - 2)
        except NotImplementedError: self.worker_count = 1
        print(f"Detected {multiprocessing.cpu_count()} CPU cores. Using {self.worker_count} worker processes.")
        self.replays_dir = "replays"
        if not os.path.exists(self.replays_dir):
            os.makedirs(self.replays_dir)

    def run_experiments(self, blue_strategies, red_strategies, runs_per_matchup=10):
        print("="*50); print("Starting Parallel Experiment Suite...")
        
        for b_strat_name in blue_strategies:
            # Note: red_strategies is now a list of display names
            for r_strat_name in red_strategies:
                # The key is now based on display names for clarity
                matchup_key = f"{b_strat_name}_vs_{r_strat_name}"
                print(f"\n--- Running Matchup: {matchup_key} ---")
                
                tasks = []
                # We only need one config for the matchup, as it's the same for all runs
                run_config = copy.deepcopy(self.base_config)
                
                for i in range(runs_per_matchup):
                    # Create a unique ID for each run
                    sim_id = f"sim_{b_strat_name.replace(' ', '')}_vs_{r_strat_name.replace(' ', '')}_{i+1}"
                    tasks.append((run_config, sim_id))

                with multiprocessing.Pool(processes=self.worker_count) as pool:
                    print(f"  Dispatching {len(tasks)} runs to {self.worker_count} worker(s)...")
                    # The result is now a list of (log, summary) tuples
                    run_results = pool.map(run_single_sim_task, tasks)
                    print("  All runs for this matchup are complete.")
                
                # --- NEW: Process rich results ---
                individual_run_summaries = []
                for full_log, run_summary in run_results:
                    if run_summary.get("error"):
                        print(f"  Run {run_summary['simulation_id']} failed: {run_summary['error']}")
                        continue
                    
                    if full_log:
                        replay_filename = os.path.join(self.replays_dir, f"{full_log['metadata']['simulation_id']}.json")
                        with open(replay_filename, 'w') as f: json.dump(full_log, f)
                        run_summary['replay_file'] = replay_filename.replace('\\', '/') # Use forward slashes
                        print(f"    - Detailed log saved to {replay_filename}")
                    
                    individual_run_summaries.append(run_summary)
                
                # Store everything for this matchup
                self.results[matchup_key] = {
                    "config_snapshot": self._create_config_snapshot(run_config),
                    "individual_runs": individual_run_summaries
                }
        
        print("\nParallel Experiment Suite Finished!")
        return self.results
    
    def _create_config_snapshot(self, config):
        """Creates a concise snapshot of the run's configuration."""
        blue_comp = config['TEAM_BLUE_CONFIG']['swarm_composition']
        red_profile = config['TEAM_RED_CONFIG'].get('active_strategy_profile', {})
        
        return {
            "blue_team": {
                "scouts_count": blue_comp['scouts']['count'],
                "strikers_count": blue_comp['strikers']['count']
            },
            "red_team_profile": {
                "display_name": red_profile.get('display_name'),
                "mission_type": red_profile.get('mission_type'),
                "roe": red_profile.get('roe'),
                "params": red_profile.get('params')
            }
        }

    def generate_payoff_matrix(self, blue_strategies, red_strategies):
        matrix = {}; print("\n--- Payoff Matrix (Blue's Perspective) ---")
        col_width = max(len(s) for s in red_strategies) + 4
        blue_strat_width = max(len(s) for s in blue_strategies)
        header = " " * blue_strat_width + "".join([f"{s:>{col_width}}" for s in red_strategies])
        print(header); print("-" * len(header))
        
        for b_strat in blue_strategies:
            row_str = f"{b_strat:<{blue_strat_width}}"; row_data = {}
            for r_strat in red_strategies:
                matchup_key = f"{b_strat}_vs_{r_strat}"
                matchup_data = self.results.get(matchup_key, {})
                
                payoff_scores = [run['payoff'] for run in matchup_data.get('individual_runs', []) if 'payoff' in run]
                
                if payoff_scores:
                    avg_payoff = sum(payoff_scores) / len(payoff_scores)
                    row_str += f"{avg_payoff:>{col_width}.2f}"
                    row_data[r_strat] = avg_payoff
                else:
                    row_str += f"{'N/A':>{col_width}}"; row_data[r_strat] = None
            print(row_str); matrix[b_strat] = row_data
        return matrix

    def save_results_to_json(self, filename="experiment_summary.json"):
        """Saves the comprehensive experiment results to a JSON file."""
        final_report = {
            "experiment_metadata": {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "aegis_version": "3.1"
            },
            "global_settings": self.base_config.get('GLOBAL_SIMULATION_SETTINGS', {}),
            "matchup_results": []
        }
        
        for matchup_key, matchup_data in self.results.items():
            runs = matchup_data.get('individual_runs', [])
            scores = [r['payoff'] for r in runs if 'payoff' in r]
            
            blue_wins = sum(1 for s in scores if s > 0)
            red_wins = sum(1 for s in scores if s < 0)
            
            summary_stats = {
                "average_payoff": round(sum(scores) / len(scores), 2) if scores else 0,
                "total_runs": len(runs),
                "blue_win_rate": f"{100 * blue_wins / len(runs):.2f}%" if runs else "0.00%",
                "red_win_rate": f"{100 * red_wins / len(runs):.2f}%" if runs else "0.00%",
                "stalemates": len(runs) - blue_wins - red_wins
            }
            
            # Reconstruct the matchup name from the config snapshot
            blue_name = self.base_config['TEAM_BLUE_CONFIG']['strategy_name']
            red_name = matchup_data['config_snapshot']['red_team_profile']['display_name']
            
            report_entry = {
                "matchup_details": {"blue_strategy": blue_name, "red_strategy": red_name},
                "config_snapshot": matchup_data['config_snapshot'],
                "summary_stats": summary_stats,
                "individual_runs": runs
            }
            final_report['matchup_results'].append(report_entry)
            
        with open(filename, 'w') as f:
            json.dump(final_report, f, indent=4)
        print(f"\nComprehensive summary results saved to {filename}")