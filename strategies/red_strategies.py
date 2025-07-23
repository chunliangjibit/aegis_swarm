# Aegis Swarm 3.0 - Red Team Strategy Library (Red Dawn Edition)
# This module has been re-architected to support a new framework of combining
# high-level "Missions" with low-level "Rules of Engagement" (ROE).

import numpy as np
import random

# --- Helper Functions ---
def get_closest_enemy(agent, enemies):
    if not enemies: return None
    agent_pos_arr = np.array([agent.pos])
    enemy_pos_arr = np.array([e.pos for e in enemies])
    distances_sq = np.sum((enemy_pos_arr - agent_pos_arr)**2, axis=1)
    closest_index = np.argmin(distances_sq)
    return enemies[closest_index]

def assign_targets_to_groups(all_enemies, num_groups):
    if not all_enemies: return {i: [] for i in range(num_groups)}
    assignments = {i: [] for i in range(num_groups)}
    for i, enemy in enumerate(all_enemies):
        group_id = i % num_groups
        assignments[group_id].append(enemy)
    return assignments


# --- Main Strategy Dispatcher ---
def strategy_dispatcher(agent, battlefield_intel):
    """
    The new main entry point for all Red Team AI.
    It reads the agent's assigned strategy function and calls it.
    """
    # This function name is now loaded from the config profile
    strategy_func_name = agent.strategy_profile.get('strategy_function', 'distributed_attack_strategy')
    strategy_function = globals().get(strategy_func_name)
    
    if strategy_function:
        strategy_function(agent, battlefield_intel)
    else:
        # Fallback to the legacy strategy if something is wrong
        distributed_attack_strategy(agent, battlefield_intel)


# --- Mission-Specific Logic ---
def _get_target_for_assault_mission(agent, mission_params):
    """Calculates navigation target for an assault mission."""
    return np.array(mission_params['target_pos'])

def _get_target_for_sweep_mission(agent, mission_params):
    """Calculates navigation target for an area sweep mission."""
    if not hasattr(agent, 'patrol_target') or agent.patrol_target is None or \
       np.linalg.norm(agent.pos - agent.patrol_target) < 100:
        
        box = mission_params['sweep_box'] # [x_min, y_min, x_max, y_max]
        agent.patrol_target = np.array([random.uniform(box[0], box[2]), random.uniform(box[1], box[3])])
    
    return agent.patrol_target


# --- New Advanced Strategy Dispatcher ---
def advanced_strategy_dispatcher(agent, battlefield_intel):
    """
    Handles all advanced strategies based on Mission + ROE.
    """
    profile = agent.strategy_profile
    mission_type = profile.get('mission_type', 'ASSAULT_POINT')
    roe = profile.get('roe', 'REACTIVE_HUNTER')
    mission_params = profile.get('params', {})
    
    local_enemies = battlefield_intel['neighbors']['enemies']
    
    # 1. Determine Macro Target (based on Mission)
    macro_target = None
    if mission_type == 'ASSAULT_POINT':
        macro_target = _get_target_for_assault_mission(agent, mission_params)
    elif mission_type == 'SWEEP_AREA':
        macro_target = _get_target_for_sweep_mission(agent, mission_params)
    
    # Set the default navigation target to the macro target
    agent.target_pos = macro_target

    # 2. Apply Micro Logic (based on Rules of Engagement)
    if not local_enemies:
        # If no enemies, just proceed with the mission
        if agent.target_pos is None: # Failsafe for missions without a target
            agent.target_pos = np.array([0, battlefield_intel['screen_height']/2])
        return

    # --- ROE: REACTIVE_HUNTER ---
    if roe == 'REACTIVE_HUNTER':
        closest_enemy = get_closest_enemy(agent, local_enemies)
        if closest_enemy:
            # Engage the closest enemy, overriding the macro mission target
            agent.target_pos = closest_enemy.pos
            if agent.weapon_template and np.linalg.norm(agent.pos - closest_enemy.pos) < agent.weapon_template["detonation_range"]:
                agent.is_detonating = True
        return # Decision made

    # --- ROE: EVADE_AND_ENGAGE ---
    if roe == 'EVADE_AND_ENGAGE':
        closest_enemy = get_closest_enemy(agent, local_enemies)
        if closest_enemy:
            distance_to_enemy = np.linalg.norm(agent.pos - closest_enemy.pos)
            # Only engage if threat is very close (self-defense)
            if distance_to_enemy < agent.self_defense_radius:
                agent.target_pos = closest_enemy.pos
                if agent.weapon_template and distance_to_enemy < agent.weapon_template["detonation_range"]:
                    agent.is_detonating = True
            else:
                # Otherwise, try to evade by steering away from the enemy
                flee_vector = agent.pos - closest_enemy.pos
                norm = np.linalg.norm(flee_vector)
                if norm > 0:
                    # Steer away, but still generally towards the macro target
                    evade_target = agent.pos + (flee_vector / norm) * 100
                    # Blend evasion with mission objective
                    agent.target_pos = (agent.target_pos * 0.7) + (evade_target * 0.3)
        return # Decision made


# --- Legacy Strategy (Kept for compatibility and as a baseline) ---
def distributed_attack_strategy(agent, battlefield_intel):
    """
    The original "Zombie Charge" strategy. It locks onto assigned targets
    from the start and ignores everything else.
    """
    target_assignments = battlefield_intel.get('target_assignments', {})
    my_group_targets = target_assignments.get(agent.group_id, [])

    # Initialize locked_target if it doesn't exist
    if not hasattr(agent, 'locked_target'):
        agent.locked_target = None

    if agent.locked_target is None or not agent.locked_target.is_alive or \
       (my_group_targets and agent.locked_target not in my_group_targets):
        agent.locked_target = get_closest_enemy(agent, my_group_targets)

    if agent.locked_target:
        agent.target_pos = agent.locked_target.pos
        if agent.weapon_template and np.linalg.norm(agent.pos - agent.locked_target.pos) < agent.weapon_template["detonation_range"]:
            agent.is_detonating = True
    else:
        # If no assigned targets, patrol aggressively towards the enemy base area.
        w, h = battlefield_intel['screen_width'], battlefield_intel['screen_height']
        agent.target_pos = np.array([random.uniform(w * 0.1, w * 0.4), random.uniform(h * 0.1, h * 0.9)], dtype=float)