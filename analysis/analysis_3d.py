# Hermes Project: 3D Analysis Suite v1.1
# This script specializes in generating advanced 3D visualizations.
# v1.1: Added matplotlib.use('Agg') to explicitly set a non-interactive backend,
#       resolving Qt platform plugin errors on certain environments.

import os
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # <-- [关键修复] 在导入pyplot之前，强制使用非交互式后端
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INPUT_JSON = os.path.join(PROJECT_ROOT, 'experiment_summary.json')
REPLAYS_DIR = os.path.join(PROJECT_ROOT, 'replays')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'reports')

# --- Data Loading and Processing Functions (Unchanged) ---

def load_summary_data(json_path):
    """Loads the summary JSON for landscape plots."""
    if not os.path.exists(json_path):
        print(f"Error: Summary file not found at '{os.path.abspath(json_path)}'")
        return None
    with open(json_path, 'r') as f: data = json.load(f)
    all_runs_data = []
    for matchup in data.get('matchup_results', []):
        for run in matchup.get('individual_runs', []):
            if run.get('error') is None:
                run_info = {
                    'payoff': run.get('payoff', 0), 'duration': run.get('duration', 0),
                    'blue_survivors': run.get('blue_survivors', 0), 'red_survivors': run.get('red_survivors', 0)
                }
                all_runs_data.append(run_info)
    if not all_runs_data: return None
    return pd.DataFrame(all_runs_data)

def load_and_process_replay_data(replays_path):
    """Loads all replay files for trajectory plot."""
    if not os.path.exists(replays_path): return None
    replay_files = [f for f in os.listdir(replays_path) if f.endswith('.json')]
    if not replay_files: return None
        
    all_replay_dfs = []
    print(f"Processing {len(replay_files)} replay files for 3D trajectory analysis...")
    for filename in replay_files:
        filepath = os.path.join(replays_path, filename)
        with open(filepath, 'r') as f: replay_data = json.load(f)
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
                'blue_health_pct': 100 * (blue_health / blue_max_health) if blue_max_health > 0 else 0,
                'red_health_pct': 100 * (red_health / red_max_health) if red_max_health > 0 else 0,
            }
            frame_data.append(frame_info)
        all_replay_dfs.append(pd.DataFrame(frame_data))

    if not all_replay_dfs: return None
        
    concatenated_df = pd.concat(all_replay_dfs)
    max_time = concatenated_df['time'].max()
    common_time_index = np.arange(0, max_time, 0.1)
    
    resampled_dfs = []
    for df in all_replay_dfs:
        df = df.set_index('time').sort_index()
        df = df[~df.index.duplicated(keep='first')]
        df_reindexed = df.reindex(df.index.union(common_time_index)).interpolate(method='index').loc[common_time_index]
        resampled_dfs.append(df_reindexed.ffill().bfill())
        
    aggregated_df = pd.concat(resampled_dfs).groupby(level=0).mean()
    return aggregated_df

# --- 3D Plotting Functions (Unchanged) ---

def plot_3d_landscape(df, z_column, title, filename):
    """Generic function to plot a 3D landscape surface."""
    print(f"Generating 3D Landscape: {title}...")
    x, y, z = df['red_survivors'].values, df['blue_survivors'].values, df[z_column].values
    xi, yi = np.linspace(x.min(), x.max(), 100), np.linspace(y.min(), y.max(), 100)
    X, Y = np.meshgrid(xi, yi)
    Z = griddata((x, y), z, (X, Y), method='cubic')
    fig = plt.figure(figsize=(14, 10)); ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none', alpha=0.9)
    ax.scatter(x, y, z, c='red', s=50, depthshade=True, label='Actual Simulation Results')
    ax.set_title(title, fontsize=16, weight='bold', pad=20)
    ax.set_xlabel('Red Team Survivors', fontsize=12, labelpad=10)
    ax.set_ylabel('Blue Team Survivors', fontsize=12, labelpad=10)
    ax.set_zlabel(z_column.replace('_', ' ').title(), fontsize=12, labelpad=10)
    fig.colorbar(surf, shrink=0.5, aspect=10, label=f'Value ({z_column})')
    ax.legend(); ax.view_init(elev=30, azim=-60)
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(save_path, format='svg', bbox_inches='tight')
    plt.close(fig)

def plot_3d_trajectory(df, title, filename):
    """Plots the average battle evolution as a 3D trajectory."""
    print(f"Generating 3D Trajectory: {title}...")
    x, y, z = df['blue_health_pct'].values, df['red_health_pct'].values, df.index.values
    fig = plt.figure(figsize=(12, 10)); ax = fig.add_subplot(111, projection='3d')
    ax.plot(x, y, z, lw=2.5, label='Average Battle Trajectory')
    ax.scatter(x[0], y[0], z[0], c='green', s=100, label='Start (t=0)')
    ax.scatter(x[-1], y[-1], z[-1], c='red', s=100, label='End')
    ax.set_title(title, fontsize=16, weight='bold', pad=20)
    ax.set_xlabel('Blue Swarm Health (%)', fontsize=12, labelpad=10)
    ax.set_ylabel('Red Swarm Health (%)', fontsize=12, labelpad=10)
    ax.set_zlabel('Time (seconds)', fontsize=12, labelpad=10)
    ax.legend(); ax.view_init(elev=25, azim=45)
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(save_path, format='svg', bbox_inches='tight')
    plt.close(fig)

# --- Main Execution Block (Unchanged) ---
def main():
    print("="*50); print("Starting Hermes Project: 3D Analysis Suite"); print("="*50)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"--> 3D Reports will be saved in '{os.path.abspath(OUTPUT_DIR)}' directory.")
    summary_df = load_summary_data(INPUT_JSON)
    if summary_df is not None and not summary_df.empty:
        plot_3d_landscape(summary_df, 'payoff', 'Decision-Payoff Landscape', 'report_3d_payoff_landscape.svg')
        plot_3d_landscape(summary_df, 'duration', 'Engagement Duration Landscape', 'report_3d_duration_landscape.svg')
    else:
        print("Could not load summary data. Skipping landscape plots.")
    timeseries_df = load_and_process_replay_data(REPLAYS_DIR)
    if timeseries_df is not None and not timeseries_df.empty:
        plot_3d_trajectory(timeseries_df, 'Average Battle Evolution Trajectory', 'report_3d_battle_trajectory.svg')
    else:
        print("Could not process replay data. Skipping trajectory plot.")
    print("\n" + "="*50); print("3D Analysis script finished successfully!"); print("="*50)

if __name__ == '__main__':
    main()