# Aegis Swarm 3.0 - Blue Team Strategy Library (Patch 3.0.4)
# PATCH: Fixed the true root cause of the simulation freeze - a fatal TypeError
# when calculating detonation range against a None target_pos.

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

def _publish_intelligence(enemies, agent, battlefield_intel):
    marketplace = battlefield_intel.get('marketplace')
    if marketplace is None or not enemies:
        return
    for enemy in enemies:
        marketplace.process_new_intelligence(detected_enemy=enemy, reporting_agent=agent)

# --- SCOUT STRATEGY ---
def scout_evade_and_publish_strategy(agent, battlefield_intel):
    local_enemies = battlefield_intel['neighbors']['enemies']
    _publish_intelligence(local_enemies, agent, battlefield_intel)

    if local_enemies:
        closest_enemy = get_closest_enemy(agent, local_enemies)
        if np.linalg.norm(agent.pos - closest_enemy.pos) < agent.perception_radius * 0.6: 
            flee_vector = agent.pos - closest_enemy.pos
            norm = np.linalg.norm(flee_vector)
            if norm > 0:
                agent.target_pos = agent.pos + (flee_vector / norm) * 200
            else:
                agent.target_pos = agent.pos + np.random.uniform(-1,1,size=2) * 200
            return

    if agent.target_pos is None or np.linalg.norm(agent.pos - agent.target_pos) < 150:
        w, h = battlefield_intel['screen_width'], battlefield_intel['screen_height']
        agent.target_pos = np.array([random.uniform(w * 0.4, w * 0.8), random.uniform(h * 0.1, h * 0.9)], dtype=float)

# --- STRIKER STRATEGY ---
def striker_market_participant_strategy(agent, battlefield_intel):
    local_enemies = battlefield_intel['neighbors']['enemies']
    _publish_intelligence(local_enemies, agent, battlefield_intel)

    # 1. Self-Defense & Target Attack Logic
    # This logic now covers both assigned targets and immediate self-defense threats.
    
    # The primary target is from the assigned tour.
    attack_target_pos = agent.target_pos
    
    # Override with a closer threat if one exists and is very close (self-defense).
    if local_enemies:
        closest_enemy = get_closest_enemy(agent, local_enemies)
        if np.linalg.norm(agent.pos - closest_enemy.pos) < agent.self_defense_radius:
            attack_target_pos = closest_enemy.pos

    # --- [THE FINAL, CRITICAL FIX] ---
    # Only if we have a valid attack target, we check for detonation range.
    if attack_target_pos is not None:
        if agent.weapon_template and np.linalg.norm(agent.pos - attack_target_pos) < agent.weapon_template['detonation_range']:
            agent.is_detonating = True
        # Ensure the agent's navigation is pointing to this attack target.
        agent.target_pos = attack_target_pos
        return # If we are in attack mode, we don't need to do anything else.

    # 2. Default Behavior: If no tour/threats, rally.
    if not agent.tour and (agent.target_pos is None or np.linalg.norm(agent.pos - agent.target_pos) < 50):
        rally_point = agent.base_pos + np.array([250, random.uniform(-250, 250)])
        agent.target_pos = rally_point