# Aegis Swarm 2.0 - Blue Team Strategy Library (Ultimate Version)
# DECISIVE FIX v3: Strategies now continuously provide a navigation target (target_pos).

import numpy as np
from core.task import Task
import random

def get_closest_enemy(agent, enemies):
    if not enemies: return None
    enemy_positions = np.array([e.pos for e in enemies])
    distances_sq = np.sum((enemy_positions - agent.pos)**2, axis=1)
    closest_index = np.argmin(distances_sq)
    return enemies[closest_index]

def strategy_dispatcher(agent, battlefield_intel):
    strategy_name = agent.strategy_name
    strategy_function = globals().get(strategy_name, striker_market_participant_strategy)
    strategy_function(agent, battlefield_intel)

def _publish_new_enemies(enemies, marketplace, known_enemy_ids, screen_width):
    if marketplace is None or known_enemy_ids is None: return
    for enemy in enemies:
        if enemy.id not in known_enemy_ids:
            value = 1.0 + (enemy.pos[0] / screen_width) * 2.0
            new_task = Task(position=enemy.pos.copy(), value=value)
            new_task.enemy_target_id = enemy.id 
            marketplace.add_task(new_task)
            known_enemy_ids.add(enemy.id)

# --- SCOUT STRATEGY ---
def scout_evade_and_publish_strategy(agent, battlefield_intel):
    local_enemies = battlefield_intel['neighbors']['enemies']
    screen_width = battlefield_intel['screen_width']
    
    _publish_new_enemies(local_enemies, battlefield_intel.get('marketplace'), battlefield_intel.get('known_enemy_ids'), screen_width)

    # 1. Evasion
    if local_enemies:
        closest_enemy = get_closest_enemy(agent, local_enemies)
        if np.linalg.norm(agent.pos - closest_enemy.pos) < agent.self_defense_radius * 2.0:
            flee_vector = agent.pos - closest_enemy.pos
            norm = np.linalg.norm(flee_vector)
            if norm > 0:
                agent.target_pos = agent.pos + (flee_vector / norm) * 200
            else: # If on top of enemy, flee in a random direction
                agent.target_pos = agent.pos + np.random.uniform(-1,1,size=2) * 200
            return

    # 2. Persistent Patrol
    if agent.target_pos is None or np.linalg.norm(agent.pos - agent.target_pos) < 150:
        w, h = battlefield_intel['screen_width'], battlefield_intel['screen_height']
        agent.target_pos = np.array([random.uniform(w * 0.5, w * 0.9), random.uniform(h * 0.1, h * 0.9)], dtype=float)

# --- STRIKER STRATEGY ---
def striker_market_participant_strategy(agent, battlefield_intel):
    local_enemies = battlefield_intel['neighbors']['enemies']
    screen_width = battlefield_intel['screen_width']
    
    _publish_new_enemies(local_enemies, battlefield_intel.get('marketplace'), battlefield_intel.get('known_enemy_ids'), screen_width)

    # 1. Self-Defense Override
    if local_enemies:
        closest_enemy = get_closest_enemy(agent, local_enemies)
        if np.linalg.norm(agent.pos - closest_enemy.pos) < agent.self_defense_radius:
            agent.target_pos = closest_enemy.pos
            if agent.weapon_template and np.linalg.norm(agent.pos - closest_enemy.pos) < agent.weapon_template['detonation_range']:
                agent.is_detonating = True
            return

    # 2. Execute Market Task
    if agent.tour:
        agent.target_pos = agent.tour[0].position
        return
        
    # 3. Default Behavior: Rally
    # If no threats and no tour, rally near the base.
    if agent.target_pos is None or np.linalg.norm(agent.pos - agent.target_pos) < 50:
        rally_point = agent.base_pos + np.array([200, random.uniform(-200, 200)])
        agent.target_pos = rally_point