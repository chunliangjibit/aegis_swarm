# Aegis Swarm 2.0 - Blue Team Strategy Library
# This script defines the "brains" for the Blue team's agents.
# Each function represents a specific tactical behavior.

import pygame
import random

def strategy_dispatcher(agent, battlefield_intel):
    """
    Acts as a switchboard, calling the correct strategy function based on the agent's role.
    This is the single entry point for the blue team's decision making.
    """
    strategy_name = agent.strategy_name
    
    if strategy_name == "bait_and_observe":
        bait_and_observe_strategy(agent, battlefield_intel)
    elif strategy_name == "wait_for_hva_and_strike":
        wait_for_hva_and_strike_strategy(agent, battlefield_intel)
    else:
        # Default behavior if strategy is not found
        passive_strategy(agent, battlefield_intel)


def bait_and_observe_strategy(agent, battlefield_intel):
    """
    Strategy for scout/bait drones. Their goal is to reveal the enemy and stay alive.
    They do not attack.
    """
    # This agent's primary goal is to move towards areas with high uncertainty
    # or towards the general direction of known enemies to "paint" them for others.
    
    known_enemies = battlefield_intel['shared_picture'].get_known_enemies()
    
    if known_enemies:
        # Move towards the geometric center of all known enemies to get a better overall picture.
        avg_enemy_pos = pygame.math.Vector2()
        for enemy in known_enemies:
            avg_enemy_pos += enemy['pos']
        avg_enemy_pos /= len(known_enemies)
        agent.target_pos = avg_enemy_pos
    else:
        # If no enemies are known, patrol randomly or towards a pre-set patrol point.
        # For now, a simple random wander is sufficient.
        if agent.target_pos is None or agent.pos.distance_to(agent.target_pos) < 50:
            agent.target_pos = pygame.math.Vector2(
                random.uniform(0, battlefield_intel['screen_width']),
                random.uniform(0, battlefield_intel['screen_height'])
            )

def wait_for_hva_and_strike_strategy(agent, battlefield_intel):
    """
    Strategy for striker drones. They wait for a high-value area (HVA) to be designated
    by the intelligence module, then attack it.
    """
    # Strikers are "blind" and rely completely on the shared intelligence.
    hva_target = battlefield_intel['shared_picture'].get_highest_value_area()
    
    if hva_target:
        # A high-value area has been identified! Time to attack.
        agent.target_pos = hva_target['pos']
        
        # Check if we are in range to detonate
        if agent.pos.distance_to(agent.target_pos) < agent.weapon_template["detonation_range"]:
            agent.is_detonating = True
    else:
        # No high-value target. Stay with the flock and wait for orders.
        # By setting target_pos to None, the boids model will default to flocking behavior.
        agent.target_pos = None

def passive_strategy(agent, battlefield_intel):
    """A fallback strategy: do nothing, just flock with friends."""
    agent.target_pos = None