# Aegis Swarm 2.0 - Blue Team Strategy Library (Ultimate Version)
import pygame, random

def strategy_dispatcher(agent, battlefield_intel):
    """ The single entry point for the blue team's decision making. """
    strategy_name = agent.strategy_name
    
    # Direct mapping from strategy name to function
    strategy_function = globals().get(strategy_name)
    if strategy_function:
        strategy_function(agent, battlefield_intel)
    else:
        # Fallback if a strategy function is not found
        passive_flock_strategy(agent, battlefield_intel)

# --- SCOUT STRATEGIES ---
def bait_and_observe_strategy(agent, battlefield_intel):
    """ Actively moves towards enemy concentration to paint targets. """
    known_enemies = battlefield_intel['shared_picture'].get_known_enemies()
    if known_enemies:
        avg_enemy_pos = sum((e['pos'] for e in known_enemies), pygame.math.Vector2()) / len(known_enemies)
        agent.target_pos = avg_enemy_pos
    else: # Patrol if no enemies are known
        if agent.target_pos is None or agent.pos.distance_to(agent.target_pos) < 50:
            agent.target_pos = pygame.math.Vector2(random.uniform(agent.drone_radius, battlefield_intel['screen_width'] - agent.drone_radius),
                                                 random.uniform(agent.drone_radius, battlefield_intel['screen_height'] - agent.drone_radius))

def passive_scan_strategy(agent, battlefield_intel):
    """ Holds a defensive line, forming a sensor screen. """
    # Patrol along a vertical line in the friendly zone
    patrol_x = battlefield_intel['screen_width'] / 3
    if agent.target_pos is None or agent.pos.distance_to(agent.target_pos) < 50:
        agent.target_pos = pygame.math.Vector2(patrol_x, random.uniform(50, battlefield_intel['screen_height'] - 50))

# --- STRIKER STRATEGIES ---
def hva_only_strategy(agent, battlefield_intel):
    """ The 'dumb missile' - only attacks designated HVAs, no self-defense. """
    hva_target = battlefield_intel['shared_picture'].get_highest_value_area()
    if hva_target:
        agent.target_pos = hva_target['pos']
        if agent.weapon_template and agent.pos.distance_to(agent.target_pos) < agent.weapon_template["detonation_range"]:
            agent.is_detonating = True
    else: agent.target_pos = None

def self_defense_priority_strategy(agent, battlefield_intel):
    """ Our 'Elastic Defense'. Prioritizes any local threat over HVA targets. """
    local_enemies = battlefield_intel['neighbors']['enemies']
    if local_enemies:
        closest_enemy = min(local_enemies, key=lambda e: agent.pos.distance_to(e.pos))
        if agent.pos.distance_to(closest_enemy.pos) < agent.self_defense_radius: # Use dynamic radius
            agent.target_pos = closest_enemy.pos
            if agent.weapon_template and agent.pos.distance_to(agent.target_pos) < agent.weapon_template["detonation_range"]:
                agent.is_detonating = True
            return
    # If no immediate threat, fall back to HVA attack logic
    hva_only_strategy(agent, battlefield_intel)

def mission_focus_strategy(agent, battlefield_intel):
    """ The 'Attack Corridor' logic. Prioritizes HVA and only defends against critical threats. """
    hva_target = battlefield_intel['shared_picture'].get_highest_value_area()
    # Determine if we are on an attack run
    on_attack_run = hva_target is not None
    
    local_enemies = battlefield_intel['neighbors']['enemies']
    if local_enemies:
        closest_enemy = min(local_enemies, key=lambda e: agent.pos.distance_to(e.pos))
        
        # Define defense radius based on current mode
        defense_radius = agent.self_defense_radius / 3.0 if on_attack_run else agent.self_defense_radius
        
        if agent.pos.distance_to(closest_enemy.pos) < defense_radius:
            agent.target_pos = closest_enemy.pos
            if agent.weapon_template and agent.pos.distance_to(agent.target_pos) < agent.weapon_template["detonation_range"]:
                agent.is_detonating = True
            return

    # If not defending, and on an attack run, set target to HVA
    if on_attack_run:
        agent.target_pos = hva_target['pos']
        if agent.weapon_template and agent.pos.distance_to(agent.target_pos) < agent.weapon_template["detonation_range"]:
            agent.is_detonating = True
    else:
        agent.target_pos = None # Otherwise, hold and flock

# --- FALLBACK ---
def passive_flock_strategy(agent, battlefield_intel):
    """ A fallback strategy: do nothing, just flock. """
    agent.target_pos = None