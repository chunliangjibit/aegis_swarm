# Aegis Swarm 2.0 - Core Models Library (Final Corrected Version)
# UPGRADED for Aegis 2.5: All vector math is now fully Numpy-based for engine-agnostic logic.

import numpy as np
import math
import random
from numba import njit

# --- Numba Accelerated Boids Calculations ---
@njit(cache=True)
def calculate_boids_forces_numba(pos, vel, friends_pos, friends_vel, drone_radius, weights):
    separation_force = np.zeros(2, dtype=np.float64)
    alignment_force = np.zeros(2, dtype=np.float64)
    cohesion_force = np.zeros(2, dtype=np.float64)
    
    friend_count = len(friends_pos)
    
    if friend_count > 0:
        # Separation
        for friend_pos in friends_pos:
            dist_vec = pos - friend_pos
            dist_sq = dist_vec[0]**2 + dist_vec[1]**2
            if 0 < dist_sq < (drone_radius * 4)**2:
                dist = np.sqrt(dist_sq)
                separation_force += dist_vec / dist
        
        # Alignment
        avg_velocity = np.sum(friends_vel, axis=0) / friend_count
        alignment_force = avg_velocity - vel
        
        # Cohesion
        avg_position = np.sum(friends_pos, axis=0) / friend_count
        cohesion_force = avg_position - pos
        
    return (separation_force * weights[0] + 
            alignment_force * weights[1] + 
            cohesion_force * weights[2])

@njit(cache=True)
def seek_numba(pos, vel, target_pos, max_speed):
    desired_velocity = target_pos - pos
    dist_sq = desired_velocity[0]**2 + desired_velocity[1]**2
    if dist_sq > 0:
        dist = np.sqrt(dist_sq)
        desired_velocity = (desired_velocity / dist) * max_speed
    return desired_velocity - vel

# --- Numba Accelerated Combat Calculation ---
@njit(cache=True)
def suicide_aoe_numba(detonator_pos, all_pos, all_health, all_teams_id, my_team_id, 
                        kill_radius, kill_prob, damage_radius, base_damage):
    damage_indices = []
    damage_values = []
    kill_radius_sq = kill_radius**2
    damage_radius_sq = damage_radius**2
    
    for i in range(len(all_pos)):
        if all_teams_id[i] == my_team_id:
            continue
            
        dist_vec = detonator_pos - all_pos[i]
        dist_sq = dist_vec[0]**2 + dist_vec[1]**2
        
        if dist_sq < kill_radius_sq:
            if random.random() < kill_prob:
                damage_indices.append(i)
                damage_values.append(all_health[i] + 1.0) # Ensure lethal damage
        elif dist_sq < damage_radius_sq:
            dist = np.sqrt(dist_sq)
            damage_factor = (damage_radius - dist) / (damage_radius - kill_radius)
            damage = base_damage * damage_factor
            damage_indices.append(i)
            damage_values.append(damage)
            
    return damage_indices, damage_values

# --- Numba Accelerated Perception Calculation ---
@njit(cache=True)
def detect_enemy_numba(observer_pos, observer_radius, target_pos, base_prob, decay_rate):
    dist_vec = observer_pos - target_pos
    dist_sq = dist_vec[0]**2 + dist_vec[1]**2
    
    if dist_sq > observer_radius**2:
        return False
        
    dist = np.sqrt(dist_sq)
    detection_prob = base_prob * math.exp(-decay_rate * (dist / observer_radius))
    return random.random() < detection_prob

# --- Main Model Classes ---

class BoidsModel:
    def calculate_steering_force(self, agent, friends, boids_weights, target_pos=None):
        friends_pos = np.array([f.pos for f in friends], dtype=float) if friends else np.empty((0, 2), dtype=float)
        friends_vel = np.array([f.velocity for f in friends], dtype=float) if friends else np.empty((0, 2), dtype=float)
        
        weights_np = np.array([boids_weights['separation'], boids_weights['alignment'], boids_weights['cohesion']], dtype=float)
        
        boids_force_np = calculate_boids_forces_numba(agent.pos, agent.velocity, friends_pos, friends_vel, agent.drone_radius, weights_np)
        
        total_force_np = boids_force_np
        
        if target_pos is not None:
            target_force_np = seek_numba(agent.pos, agent.velocity, target_pos, agent.max_speed)
            total_force_np = total_force_np * 0.2 + target_force_np * 0.8
            
        return total_force_np # Return the pure Numpy array

class CombatModel:
    def suicide_aoe_detonation(self, detonator, all_agents, weapon_config):
        agent_indices = [i for i, a in enumerate(all_agents) if a.is_alive]
        if not agent_indices:
            return []
            
        all_pos = np.array([all_agents[i].pos for i in agent_indices], dtype=float)
        all_health = np.array([all_agents[i].health for i in agent_indices], dtype=float)
        all_teams_id = np.array([all_agents[i].team_id for i in agent_indices])

        indices, values = suicide_aoe_numba(
            detonator.pos, all_pos, all_health, all_teams_id, detonator.team_id,
            weapon_config["kill_radius"], weapon_config["kill_prob"],
            weapon_config["damage_radius"], weapon_config["base_damage"]
        )
        
        damage_events = []
        for i in range(len(indices)):
            original_agent_index = agent_indices[indices[i]]
            damage_events.append({'agent': all_agents[original_agent_index], 'damage': values[i]})
            
        return damage_events

class PerceptionModel:
    def detect_enemy(self, observer, target, detection_config):
        return detect_enemy_numba(
            observer.pos, observer.perception_radius, target.pos,
            detection_config["base_prob"], detection_config["prob_decay_rate"]
        )