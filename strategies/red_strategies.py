# Aegis Swarm 2.0 - Red Team Strategy Library (Ultimate Version)
import pygame, random

def strategy_dispatcher(agent, battlefield_intel):
    """ The single entry point for the red team's decision making. """
    strategy_name = agent.strategy_name
    strategy_function = globals().get(strategy_name)
    if strategy_function:
        strategy_function(agent, battlefield_intel)
    else:
        fearless_charge_strategy(agent, battlefield_intel)

def fearless_charge_strategy(agent, battlefield_intel):
    """ Simple aggressive strategy: find the nearest enemy and attack. """
    local_enemies = battlefield_intel['neighbors']['enemies']
    if local_enemies:
        closest_enemy = min(local_enemies, key=lambda e: agent.pos.distance_to(e.pos))
        agent.target_pos = closest_enemy.pos
        if agent.weapon_template and agent.weapon_template['type'] == 'suicide_aoe':
            if agent.pos.distance_to(agent.target_pos) < agent.weapon_template["detonation_range"]:
                agent.is_detonating = True
    else: # No enemies in sight, move towards general blue deployment area
        agent.target_pos = pygame.math.Vector2(battlefield_intel['screen_width'] / 4, battlefield_intel['screen_height'] / 2)

def loose_formation_charge_strategy(agent, battlefield_intel):
    """ Same as fearless_charge, but relies on boids weights set in config for loose formation. """
    # The logic is identical, the formation difference comes from the boids parameters.
    fearless_charge_strategy(agent, battlefield_intel)

def split_attack_strategy(agent, battlefield_intel):
    """ Divides the swarm into groups that attack different vectors. """
    # The 'group_id' is assigned at creation time by the battlefield.
    num_groups = battlefield_intel['red_team_num_groups']
    group_id = agent.group_id
    
    # Assign a different attack vector for each group
    attack_y = (battlefield_intel['screen_height'] / (num_groups + 1)) * (group_id + 1)
    attack_vector = pygame.math.Vector2(0, attack_y) # Attack along a horizontal line
    
    local_enemies = battlefield_intel['neighbors']['enemies']
    if local_enemies:
        closest_enemy = min(local_enemies, key=lambda e: agent.pos.distance_to(e.pos))
        agent.target_pos = closest_enemy.pos
        if agent.weapon_template and agent.weapon_template['type'] == 'suicide_aoe':
            if agent.pos.distance_to(agent.target_pos) < agent.weapon_template["detonation_range"]:
                agent.is_detonating = True
    else: # No enemies in sight, move towards assigned attack vector
        agent.target_pos = attack_vector