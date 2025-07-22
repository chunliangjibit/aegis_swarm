# Aegis Swarm 2.0 - Core Models Library (Final Corrected Version)
# This version ensures all internal logic uses team_id, fixing the final bug.

import pygame, numpy as np, math, random
from numba import jit, njit

@njit(cache=True)
def calculate_boids_forces_numba(pos, vel, friends_pos, friends_vel, drone_radius, weights):
    separation_force = np.zeros(2); alignment_force = np.zeros(2); cohesion_force = np.zeros(2)
    if len(friends_pos) > 0:
        for friend_pos in friends_pos:
            dist_vec = pos - friend_pos; dist_sq = dist_vec[0]**2 + dist_vec[1]**2
            if 0 < dist_sq < (drone_radius * 4)**2: dist = np.sqrt(dist_sq); separation_force += dist_vec / dist
    if len(friends_vel) > 0:
        avg_velocity = np.sum(friends_vel, axis=0) / len(friends_vel); alignment_force = avg_velocity - vel
    if len(friends_pos) > 0:
        avg_position = np.sum(friends_pos, axis=0) / len(friends_pos); cohesion_force = avg_position - pos
    return (separation_force * weights[0] + alignment_force * weights[1] + cohesion_force * weights[2])

@njit(cache=True)
def seek_numba(pos, vel, target_pos, max_speed):
    desired_velocity = target_pos - pos; dist_sq = desired_velocity[0]**2 + desired_velocity[1]**2
    if dist_sq > 0: desired_velocity = (desired_velocity / np.sqrt(dist_sq)) * max_speed
    return desired_velocity - vel

class BoidsModel:
    def calculate_steering_force(self, agent, friends, boids_weights, target_pos=None):
        friends_pos = np.array([f.pos for f in friends]) if friends else np.empty((0, 2))
        friends_vel = np.array([f.velocity for f in friends]) if friends else np.empty((0, 2))
        agent_pos_np = np.array(agent.pos); agent_vel_np = np.array(agent.velocity)
        weights_np = np.array([boids_weights['separation'], boids_weights['alignment'], boids_weights['cohesion']])
        boids_force_np = calculate_boids_forces_numba(agent_pos_np, agent_vel_np, friends_pos, friends_vel, agent.drone_radius, weights_np)
        total_force_np = boids_force_np
        if target_pos:
            target_pos_np = np.array(target_pos); target_force_np = seek_numba(agent_pos_np, agent_vel_np, target_pos_np, agent.max_speed)
            total_force_np = total_force_np * 0.2 + target_force_np * 0.8
        return pygame.math.Vector2(total_force_np[0], total_force_np[1])

@njit(cache=True)
def suicide_aoe_numba(detonator_pos, all_pos, all_health, all_teams_id, my_team_id, kill_radius, kill_prob, damage_radius, base_damage):
    damage_indices, damage_values = [], []
    kill_radius_sq = kill_radius**2; damage_radius_sq = damage_radius**2
    for i in range(len(all_pos)):
        if all_teams_id[i] == my_team_id: continue
        dist_vec = detonator_pos - all_pos[i]; dist_sq = dist_vec[0]**2 + dist_vec[1]**2
        if dist_sq < kill_radius_sq:
            if random.random() < kill_prob: damage_indices.append(i); damage_values.append(all_health[i])
        elif dist_sq < damage_radius_sq:
            dist = np.sqrt(dist_sq); damage_factor = (damage_radius - dist) / (damage_radius - kill_radius)
            if random.random() < damage_factor:
                damage = base_damage * damage_factor; damage_indices.append(i); damage_values.append(damage)
    return damage_indices, damage_values

class CombatModel:
    def suicide_aoe_detonation(self, detonator, all_agents, weapon_config):
        all_pos = np.array([a.pos for a in all_agents]); all_health = np.array([a.health for a in all_agents])
        # 【核心修正】: 确保在所有地方都使用 agent.team_id
        all_teams_id = np.array([a.team_id for a in all_agents])
        detonator_pos_np = np.array(detonator.pos)

        indices, values = suicide_aoe_numba(
            detonator_pos_np, all_pos, all_health, all_teams_id, detonator.team_id,
            weapon_config["kill_radius"], weapon_config["kill_prob"],
            weapon_config["damage_radius"], weapon_config["base_damage"])
        
        damage_events = []
        for i in range(len(indices)):
            damage_events.append({'agent': all_agents[indices[i]], 'damage': values[i]})
        return damage_events

@njit(cache=True)
def detect_enemy_numba(observer_pos, observer_radius, target_pos, base_prob, decay_rate):
    dist_vec = observer_pos - target_pos; dist_sq = dist_vec[0]**2 + dist_vec[1]**2
    if dist_sq > observer_radius**2: return False
    dist = np.sqrt(dist_sq); detection_prob = base_prob * math.exp(-decay_rate * (dist / observer_radius))
    return random.random() < detection_prob

class PerceptionModel:
    def detect_enemy(self, observer, target, detection_config):
        return detect_enemy_numba(np.array(observer.pos), observer.perception_radius, np.array(target.pos), detection_config["base_prob"], detection_config["prob_decay_rate"])