# Hermes Project: Analysis & Reporting Suite v2.0
# This script performs a two-part analysis:
# 1. Macro Analysis: Reads experiment_summary.json for high-level, cross-simulation statistics.
# 2. Micro Analysis: Reads all individual replay files to generate dynamic, time-series charts,
#    providing deep insights into the tactical progression of a typical engagement.

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INPUT_JSON = os.path.join(PROJECT_ROOT, 'experiment_summary.json')
REPLAYS_DIR = os.path.join(PROJECT_ROOT, 'replays')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'reports')

# --- Part A: Macro Analysis Functions ---

def load_summary_data(json_path):
    """Loads the summary JSON and transforms it into a clean pandas DataFrame."""
    if not os.path.exists(json_path):
        print(f"Error: Summary file not found at '{os.path.abspath(json_path)}'")
        return None
    with open(json_path, 'r') as f: data = json.load(f)
    all_runs_data = []
    for matchup in data.get('matchup_results', []):
        for run in matchup.get('individual_runs', []):
            if run.get('error') is None:
                run_info = {
                    'matchup': f"{matchup['matchup_details']['blue_strategy']} vs.\n{matchup['matchup_details']['red_strategy']}",
                    'payoff': run.get('payoff', 0), 'duration': run.get('duration', 0),
                    'blue_survivors': run.get('blue_survivors', 0), 'red_survivors': run.get('red_survivors', 0)
                }
                all_runs_data.append(run_info)
    if not all_runs_data: return None
    return pd.DataFrame(all_runs_data)

def plot_average_payoff(df, output_dir):
    print("Generating Chart 1: Overall Strategy Effectiveness (Average Payoff)...")
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=df, x='matchup', y='payoff', ax=ax, capsize=.1, errorbar='sd')
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
    ax.set_title('Overall Strategy Effectiveness (Average Payoff)', fontsize=16, weight='bold')
    ax.set_xlabel('Matchup', fontsize=12); ax.set_ylabel("Average Payoff (Blue's Perspective)", fontsize=12)
    ax.text(ax.get_xlim()[1]*0.99, 0.05, 'Blue Advantage >', ha='right', va='bottom', color='green', transform=ax.get_yaxis_transform())
    ax.text(ax.get_xlim()[1]*0.99, -0.05, '< Red Advantage', ha='right', va='top', color='red', transform=ax.get_yaxis_transform())
    plt.tight_layout(); fig.savefig(os.path.join(output_dir, 'report_average_payoff.svg'), format='svg'); plt.close(fig)

def plot_payoff_distribution(df, output_dir):
    print("Generating Chart 2: Tactical Stability and Risk (Payoff Distribution)...")
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 7))
    sns.boxplot(data=df, x='matchup', y='payoff', ax=ax)
    sns.stripplot(data=df, x='matchup', y='payoff', ax=ax, color='black', alpha=0.3, jitter=0.2)
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
    ax.set_title('Tactical Stability and Risk (Payoff Distribution)', fontsize=16, weight='bold')
    ax.set_xlabel('Matchup', fontsize=12); ax.set_ylabel('Payoff per Simulation Run', fontsize=12)
    plt.tight_layout(); fig.savefig(os.path.join(output_dir, 'report_payoff_distribution.svg'), format='svg'); plt.close(fig)

def plot_survivor_exchange_ratio(df, output_dir):
    print("Generating Chart 3: Attrition Analysis (Survivor Exchange Ratio)...")
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.scatterplot(data=df, x='red_survivors', y='blue_survivors', hue='matchup', s=100, alpha=0.8, ax=ax)
    ax.set_title('Attrition Analysis (Survivor Exchange Ratio)', fontsize=16, weight='bold')
    ax.set_xlabel('Red Team Survivors', fontsize=12); ax.set_ylabel('Blue Team Survivors', fontsize=12)
    ax.legend(title='Matchup'); xlim = ax.get_xlim(); ylim = ax.get_ylim()
    ax.text(xlim[1]*0.95, ylim[0]*0.95 + ylim[1]*0.05, 'Blue Complete Victory', ha='right', va='bottom', fontsize=10, color='gray', style='italic')
    ax.text(xlim[0]*0.95 + xlim[1]*0.05, ylim[1]*0.95, 'Red Complete Victory', ha='left', va='top', fontsize=10, color='gray', style='italic')
    ax.text(xlim[0]*0.95 + xlim[1]*0.05, ylim[0]*0.95 + ylim[1]*0.05, 'Mutual Annihilation', ha='left', va='bottom', fontsize=10, color='gray', style='italic')
    plt.tight_layout(); fig.savefig(os.path.join(output_dir, 'report_survivor_exchange_ratio.svg'), format='svg'); plt.close(fig)

def plot_simulation_duration(df, output_dir):
    print("Generating Chart 4: Engagement Efficiency (Simulation Duration)...")
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 7))
    sns.violinplot(data=df, x='matchup', y='duration', ax=ax, inner='quartile')
    ax.set_title('Engagement Efficiency (Simulation Duration)', fontsize=16, weight='bold')
    ax.set_xlabel('Matchup', fontsize=12); ax.set_ylabel('Duration (seconds)', fontsize=12)
    plt.tight_layout(); fig.savefig(os.path.join(output_dir, 'report_simulation_duration.svg'), format='svg'); plt.close(fig)

# --- Part B: Micro Analysis (Time-Series) Functions ---

def load_and_process_replay_data(replays_path):
    """Loads all replay files, extracts time-series data, and aggregates it."""
    if not os.path.exists(replays_path):
        print(f"Warning: Replays directory not found at '{os.path.abspath(replays_path)}'. Skipping time-series charts.")
        return None
    
    replay_files = [f for f in os.listdir(replays_path) if f.endswith('.json')]
    if not replay_files:
        print("Warning: No replay files found. Skipping time-series charts.")
        return None
        
    all_replay_dfs = []
    print(f"\nProcessing {len(replay_files)} replay files for time-series analysis...")
    for i, filename in enumerate(replay_files):
        print(f"  - Reading replay {i+1}/{len(replay_files)}: {filename}")
        filepath = os.path.join(replays_path, filename)
        with open(filepath, 'r') as f:
            replay_data = json.load(f)
        
        timestamps = replay_data.get('timestamps', [])
        if not timestamps: continue

        frame_data = []
        for frame in timestamps:
            blue_health = sum(a['health'] for a in frame['agents'] if a['team_id'] == 1)
            blue_max_health = sum(a['max_health'] for a in frame['agents'] if a['team_id'] == 1)
            red_health = sum(a['health'] for a in frame['agents'] if a['team_id'] == 2)
            red_max_health = sum(a['max_health'] for a in frame['agents'] if a['team_id'] == 2)
            
            frame_info = {
                'time': frame['time'],
                'blue_survivors': frame['blue_count'],
                'red_survivors': frame['red_count'],
                'blue_health_pct': 100 * (blue_health / blue_max_health) if blue_max_health > 0 else 0,
                'red_health_pct': 100 * (red_health / red_max_health) if red_max_health > 0 else 0,
                'tasks_open': sum(1 for t in frame['tasks'] if t['status'] == 'OPEN'),
                'tasks_assigned': sum(1 for t in frame['tasks'] if t['status'] == 'ASSIGNED')
            }
            frame_data.append(frame_info)
        all_replay_dfs.append(pd.DataFrame(frame_data))

    # Aggregate all replay data into a single averaged time-series
    if not all_replay_dfs:
        print("Warning: No valid timestamp data found in replays.")
        return None
        
    print("Aggregating time-series data...")
    concatenated_df = pd.concat(all_replay_dfs)
    # To average correctly, we need to handle different simulation lengths.
    # We will interpolate each series onto a common time index.
    max_time = concatenated_df['time'].max()
    common_time_index = np.arange(0, max_time, 0.1) # Resample every 0.1s
    
    resampled_dfs = []
    for df in all_replay_dfs:
        df = df.set_index('time').sort_index()
        df = df[~df.index.duplicated(keep='first')] # Remove duplicate time steps if any
        df_reindexed = df.reindex(df.index.union(common_time_index)).interpolate(method='index').loc[common_time_index]
        resampled_dfs.append(df_reindexed.ffill().bfill()) # Fill any remaining NaNs
        
    aggregated_df = pd.concat(resampled_dfs).groupby(level=0).mean()
    print("Time-series data processed successfully.")
    return aggregated_df

def plot_timeseries_attrition(df, output_dir):
    """Chart 5: Plots the average number of surviving units over time."""
    print("Generating Chart 5: Attrition Dynamics Over Time...")
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(df.index, df['blue_survivors'], label='Blue Team Survivors (Avg.)', color='royalblue')
    ax.plot(df.index, df['red_survivors'], label='Red Team Survivors (Avg.)', color='crimson')
    
    ax.set_title('Attrition Dynamics Over Time', fontsize=16, weight='bold')
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('Average Number of Surviving Units', fontsize=12)
    ax.legend()
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'report_timeseries_attrition.svg'), format='svg')
    plt.close(fig)

def plot_timeseries_swarm_health(df, output_dir):
    """Chart 6: Plots the average swarm health percentage over time."""
    print("Generating Chart 6: Swarm Integrity Over Time...")
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(df.index, df['blue_health_pct'], label='Blue Team Health % (Avg.)', color='skyblue')
    ax.plot(df.index, df['red_health_pct'], label='Red Team Health % (Avg.)', color='lightcoral')

    ax.set_title('Swarm Integrity Over Time', fontsize=16, weight='bold')
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('Average Total Health (%)', fontsize=12)
    ax.set_ylim(0, 101)
    ax.legend()
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'report_timeseries_swarm_health.svg'), format='svg')
    plt.close(fig)
    
def plot_timeseries_market_efficiency(df, output_dir):
    """Chart 7: Plots Blue Team's market task status over time."""
    print("Generating Chart 7: Blue Team Market Efficiency Over Time...")
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.stackplot(df.index, df['tasks_open'], df['tasks_assigned'], 
                 labels=['Open Tasks (Avg.)', 'Assigned Tasks (Avg.)'],
                 colors=['gold', 'darkorange'])

    ax.set_title('Blue Team Market Efficiency Over Time', fontsize=16, weight='bold')
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('Average Number of Tasks', fontsize=12)
    ax.legend(loc='upper left')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'report_timeseries_market_efficiency.svg'), format='svg')
    plt.close(fig)

def main():
    """Main function to run the complete analysis suite."""
    print("="*50)
    print("Starting Hermes Project v2.0: Deep Analysis Suite")
    print("="*50)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"--> Reports will be saved in '{os.path.abspath(OUTPUT_DIR)}' directory.")

    # --- Part A: Run Macro Analysis ---
    print("\n--- Running Part A: Macro-level Strategy Comparison ---")
    summary_df = load_summary_data(INPUT_JSON)
    if summary_df is not None:
        plot_average_payoff(summary_df, OUTPUT_DIR)
        plot_payoff_distribution(summary_df, OUTPUT_DIR)
        plot_survivor_exchange_ratio(summary_df, OUTPUT_DIR)
        plot_simulation_duration(summary_df, OUTPUT_DIR)
        print("Part A analysis completed.")
    else:
        print("Could not load summary data. Skipping Part A.")

    # --- Part B: Run Micro (Time-Series) Analysis ---
    print("\n--- Running Part B: Micro-level Tactical Progression ---")
    timeseries_df = load_and_process_replay_data(REPLAYS_DIR)
    if timeseries_df is not None:
        plot_timeseries_attrition(timeseries_df, OUTPUT_DIR)
        plot_timeseries_swarm_health(timeseries_df, OUTPUT_DIR)
        plot_timeseries_market_efficiency(timeseries_df, OUTPUT_DIR)
        print("Part B analysis completed.")
    else:
        print("Could not process replay data. Skipping Part B.")
        
    print("\n" + "="*50)
    print("Analysis script finished.")
    print("="*50)

if __name__ == '__main__':
    main()