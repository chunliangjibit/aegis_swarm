# Aegis Swarm 2.0 - Red Team Strategy Library (Ultimate Version)
# UPGRADED for Aegis 2.7: Added persistent aggression for idle groups.

import numpy as np
import random

def get_closest_enemy(agent, enemies):
    if not enemies: return None
    agent_pos_arr = np.array([agent.pos])
    enemy_pos_arr = np.array([e.pos for e in enemies])
    distances_sq = np.sum((enemy_pos_arr - agent_pos_arr)**2, axis=1)
    closest_index = np.argmin(distances_sq)
    return enemies[closest_index]

def assign_targets_to_groups(all_enemies, num_groups):
    if not all_enemies: return {}
    assignments = {i: [] for i in range(num_groups)}
    for i, enemy in enumerate(all_enemies):
        group_id = i % num_groups
        assignments[group_id].append(enemy)
    return assignments

def strategy_dispatcher(agent, battlefield_intel):
    if not hasattr(agent, 'locked_target'):
        agent.locked_target = None
    distributed_attack_strategy(agent, battlefield_intel)

def distributed_attack_strategy(agent, battlefield_intel):
    target_assignments = battlefield_intel['target_assignments']
    my_group_targets = target_assignments.get(agent.group_id, [])

    if agent.locked_target is None or not agent.locked_target.is_alive or \
       agent.locked_target not in my_group_targets:
        agent.locked_target = get_closest_enemy(agent, my_group_targets)

    if agent.locked_target:
        agent.target_pos = agent.locked_target.pos
        if agent.weapon_template and np.linalg.norm(agent.pos - agent.locked_target.pos) < agent.weapon_template["detonation_range"]:
            agent.is_detonating = True
    else:
        # ** NEW: Persistent Aggression Logic **
        # If no assigned targets, patrol aggressively towards the enemy base area.
        w, h = battlefield_intel['screen_width'], battlefield_intel['screen_height']
        # Target a random point in the blue deployment zone
        agent.target_pos = np.array([random.uniform(w * 0.1, w * 0.4), random.uniform(h * 0.1, h * 0.9)], dtype=float)