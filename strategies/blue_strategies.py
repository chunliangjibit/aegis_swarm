# Aegis Swarm 2.0 - Blue Team Strategy Library (Tactical Upgrade: Self-Defense)
import pygame

def strategy_dispatcher(agent, battlefield_intel):
    """ Acts as a switchboard for the blue team's decision making. """
    strategy_name = agent.strategy_name
    
    if strategy_name == "bait_and_observe":
        bait_and_observe_strategy(agent, battlefield_intel)
    elif strategy_name == "wait_for_hva_and_strike":
        wait_for_hva_and_strike_strategy(agent, battlefield_intel)
    else:
        passive_strategy(agent, battlefield_intel)

def bait_and_observe_strategy(agent, battlefield_intel):
    """ Strategy for scout/bait drones. Their goal is to reveal the enemy and stay alive. """
    known_enemies = battlefield_intel['shared_picture'].get_known_enemies()
    if known_enemies:
        avg_enemy_pos = pygame.math.Vector2()
        for enemy in known_enemies: avg_enemy_pos += enemy['pos']
        agent.target_pos = avg_enemy_pos / len(known_enemies)
    else:
        # Simple random patrol
        if agent.target_pos is None or agent.pos.distance_to(agent.target_pos) < 50:
            agent.target_pos = pygame.math.Vector2(
                battlefield_intel['screen_width'] * 0.4, # Patrol towards the center
                battlefield_intel['screen_height'] * 0.5 
            )

def wait_for_hva_and_strike_strategy(agent, battlefield_intel):
    """
    Strategy for striker drones. They prioritize self-defense,
    then attack high-value areas (HVA).
    """
    # 【战术升级 B】: 自卫逻辑优先
    local_enemies = battlefield_intel['neighbors']['enemies']
    if local_enemies:
        closest_enemy = min(local_enemies, key=lambda e: agent.pos.distance_to(e.pos))
        # Define a self-defense perimeter
        self_defense_radius = 75.0 
        if agent.pos.distance_to(closest_enemy.pos) < self_defense_radius:
            # Immediate threat detected! Engage immediately.
            agent.target_pos = closest_enemy.pos
            if agent.weapon_template and agent.pos.distance_to(agent.target_pos) < agent.weapon_template["detonation_range"]:
                agent.is_detonating = True
            return # Exit strategy, self-defense takes precedence

    # If no immediate threat, proceed with standard HVA attack logic
    hva_target = battlefield_intel['shared_picture'].get_highest_value_area()
    if hva_target:
        agent.target_pos = hva_target['pos']
        if agent.weapon_template and agent.pos.distance_to(agent.target_pos) < agent.weapon_template["detonation_range"]:
            agent.is_detonating = True
    else:
        # No HVA, hold position with flock
        agent.target_pos = None

def passive_strategy(agent, battlefield_intel):
    """ A fallback strategy: do nothing, just flock. """
    agent.target_pos = None