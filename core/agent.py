# Aegis Swarm 3.2 - Core Agent Class (Visual ID Edition)
# UPGRADED: Agent now initializes with its specific role name and color.

import pygame
import uuid
import random
import numpy as np
import time
from core.task import Task

class Agent:
    def __init__(self, team_config, role_name, role_config, initial_pos, market_config):
        self.id = uuid.uuid4(); self.is_alive = True
        self.team_id = team_config['id']
        
        # --- [MODIFIED] Store role name and get role-specific color ---
        self.role_name = role_name
        self.color = role_config.get('color', team_config.get('color', (255,255,255))) # Use role color, fallback to team, then white
        
        self.role_template = role_config['role_template']
        self.weapon_template = role_config.get('weapon_template')
        
        self.strategy_name = role_config.get('strategy', '')
        self.boids_weights = role_config.get('boids_weights', {"separation": 1.0, "alignment": 1.0, "cohesion": 1.0})
        
        self.max_health = self.role_template['health']; self.health = self.role_template['health']
        self.max_speed = self.role_template['max_speed']; self.perception_radius = self.role_template['perception_radius']
        self.drone_radius = self.role_template['drone_radius']
        
        self.market_config = market_config
        self.pos = np.array(initial_pos, dtype=float)
        random_velocity = np.random.uniform(-1, 1, size=2)
        norm = np.linalg.norm(random_velocity)
        if norm > 0: self.velocity = random_velocity / norm * self.max_speed
        else: self.velocity = np.array([self.max_speed, 0], dtype=float)
        self.acceleration = np.array([0.0, 0.0], dtype=float)
        self.target_pos = None; self.is_detonating = False
        self.tour = []
        self.current_sub_task_index = -1
        self.base_pos = self.pos.copy()
        self.self_defense_radius = 75.0; self.group_id = 0
        self.time_of_death = None; self.death_linger_duration = 0.5
        
        self.strategy_profile = {}

    # ... (The rest of the file is identical to the last working version) ...
    def is_truly_dead(self, current_time):
        if self.health <= 0 and self.time_of_death is not None:
            return current_time - self.time_of_death > self.death_linger_duration
        return self.health <= 0

    def assess_risk(self, task, all_market_tasks):
        risk_score = 0.0
        assessment_radius_sq = self.market_config['RISK_ASSESSMENT_RADIUS'] ** 2
        for other_task in all_market_tasks:
            if other_task.id == task.id or other_task.status != 'OPEN': continue
            dist_sq = np.sum((task.position - other_task.position)**2)
            if dist_sq < assessment_radius_sq:
                risk_score += 1.0 
        return risk_score

    def calculate_bid_for_task(self, task: Task, all_market_tasks):
        if not self.weapon_template: return None
        travel_cost = np.linalg.norm(self.pos - task.position) + np.linalg.norm(task.position - self.base_pos)
        risk_score = self.assess_risk(task, all_market_tasks)
        risk_factor = self.market_config['RISK_AVERSION_FACTOR']
        final_bid = travel_cost * (1 + risk_score * risk_factor)
        return final_bid

    def add_task_to_tour(self, task: Task):
        self.tour = [task]
        if task.is_bundle and task.sub_tasks:
            self.current_sub_task_index = 0
        else:
            self.current_sub_task_index = -1

    def _update_target_from_tour(self):
        if not self.tour:
            self.target_pos = None
            return
        active_task = self.tour[0]
        if active_task.is_bundle:
            if self.current_sub_task_index != -1 and self.current_sub_task_index < len(active_task.sub_tasks):
                self.target_pos = active_task.sub_tasks[self.current_sub_task_index].position
            else:
                self.tour = []
                self.target_pos = None
        else:
            self.target_pos = active_task.position

    def apply_movement_physics(self, dt, boundary_behavior, screen_width, screen_height):
        if self.health <= 0:
            self.velocity *= 0.9; self.pos += self.velocity * dt * 50
            return

        if self.tour:
            active_task = self.tour[0]
            if active_task.is_bundle:
                if self.current_sub_task_index < len(active_task.sub_tasks):
                    current_sub_task = active_task.sub_tasks[self.current_sub_task_index]
                    if current_sub_task.status == 'COMPLETED':
                        self.current_sub_task_index += 1
                else:
                    active_task.complete()
                    self.tour = []
            else:
                if active_task.status == 'COMPLETED':
                    self.tour = []
        
        self._update_target_from_tour()

        accel_norm = np.linalg.norm(self.acceleration)
        if accel_norm > 1.0: self.acceleration = self.acceleration / accel_norm
        self.velocity += self.acceleration
        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed: self.velocity = (self.velocity / speed) * self.max_speed
        self.pos += self.velocity * dt * 50
        self.acceleration *= 0
        if boundary_behavior == "wrap": self._handle_wrap_boundary(screen_width, screen_height)

    def _handle_wrap_boundary(self, width, height):
        if self.pos[0] > width: self.pos[0] = 0
        elif self.pos[0] < 0: self.pos[0] = width
        if self.pos[1] > height: self.pos[1] = 0
        elif self.pos[1] < 0: self.pos[1] = height

    def take_damage(self, amount):
        if self.health <= 0: return
        self.health -= amount
        if self.health <= 0:
            self.health = 0; self.is_alive = False
            if self.time_of_death is None: self.time_of_death = time.time()

    def draw(self, screen, config):
        draw_pos = (int(self.pos[0]), int(self.pos[1]))
        if self.time_of_death is None:
            pygame.draw.circle(screen, self.color, draw_pos, self.drone_radius)
            bar_width = self.drone_radius * 2.5; bar_height = 4
            bar_x = self.pos[0] - bar_width / 2
            bar_y = self.pos[1] - self.drone_radius - bar_height - 5
            health_percentage = self.health / self.max_health
            pygame.draw.rect(screen, config['HEALTH_BAR_RED'], (bar_x, bar_y, bar_width, bar_height))
            if health_percentage > 0:
                pygame.draw.rect(screen, config['HEALTH_BAR_GREEN'], (bar_x, bar_y, bar_width * health_percentage, bar_height))
        else:
            p1,p2,p3,p4 = (draw_pos[0]-5, draw_pos[1]-5), (draw_pos[0]+5, draw_pos[1]+5), (draw_pos[0]-5, draw_pos[1]+5), (draw_pos[0]+5, draw_pos[1]-5)
            pygame.draw.line(screen, (80,80,80), p1, p2, 1)
            pygame.draw.line(screen, (80,80,80), p3, p4, 1)