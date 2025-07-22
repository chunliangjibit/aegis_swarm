# Aegis Swarm 2.0 - Red Team Strategy Library
# This script defines the "brains" for the Red team's agents.

import pygame

def strategy_dispatcher(agent, battlefield_intel):
    """
    Acts as a switchboard for the red team's decision making.
    """
    strategy_name = agent.strategy_name
    
    if strategy_name == "fearless_charge":
        fearless_charge_strategy(agent, battlefield_intel)
    else:
        # Default behavior
        passive_strategy(agent, battlefield_intel)


def fearless_charge_strategy(agent, battlefield_intel):
    """
    A simple, aggressive strategy: find the nearest enemy and attack.
    This strategy uses the agent's own perception, not a shared picture.
    """
    # Note: 'local_enemies' comes from the agent's own sensors in this frame.
    local_enemies = battlefield_intel['neighbors']['enemies']
    
    if local_enemies:
        # Find the absolute closest enemy
        closest_enemy = min(local_enemies, key=lambda e: agent.pos.distance_to(e.pos))
        agent.target_pos = closest_enemy.pos
        
        # Check if we are in range to detonate (assuming red also uses suicide drones)
        if agent.weapon_template and agent.weapon_template['type'] == 'suicide_aoe':
            if agent.pos.distance_to(agent.target_pos) < agent.weapon_template["detonation_range"]:
                agent.is_detonating = True
    else:
        # No enemies in sight. Move towards the center of the screen or a general attack vector.
        # For now, let's make them move towards the center of the blue deployment zone.
        # This is a placeholder for a more complex objective system.
        attack_vector = pygame.math.Vector2(battlefield_intel['screen_width'] / 4, battlefield_intel['screen_height'] / 2)
        agent.target_pos = attack_vector


def passive_strategy(agent, battlefield_intel):
    """A fallback strategy: do nothing, just flock with friends."""
    agent.target_pos = None