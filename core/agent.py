# Aegis Swarm 2.0 - Core Agent Class (Ultimate Version)
# DECISIVE FIX v4: Reverted bidding logic to pure COST MINIMIZATION to ensure offensive behavior.

import pygame
import uuid
import random
import numpy as np
import time
from core.task import Task

class Agent:
    def __init__(self, team_config, role_config, initial_pos):
        self.id = uuid.uuid4(); self.is_alive = True
        self.team_id = team_config['id']; self.color = team_config['color']
        self.role_template = role_config['role_template']; self.weapon_template = role_config.get('weapon_template')
        self.strategy_name = role_config['strategy']; self.boids_weights = role_config['boids_weights']
        self.max_health = self.role_template['health']; self.health = self.role_template['health']
        self.max_speed = self.role_template['max_speed']; self.perception_radius = self.role_template['perception_radius']
        self.drone_radius = self.role_template['drone_radius']
        self.pos = np.array(initial_pos, dtype=float)
        random_velocity = np.random.uniform(-1, 1, size=2)
        norm = np.linalg.norm(random_velocity)
        if norm > 0: self.velocity = random_velocity / norm * self.max_speed
        else: self.velocity = np.array([self.max_speed, 0], dtype=float)
        self.acceleration = np.array([0.0, 0.0], dtype=float)
        self.target_pos = None; self.is_detonating = False
        self.tour = []; self.tour_cost = 0.0; self.base_pos = self.pos.copy()
        self.self_defense_radius = 75.0; self.group_id = 0
        self.time_of_death = None; self.death_linger_duration = 0.5

    def is_truly_dead(self, current_time):
        if self.health <= 0 and self.time_of_death is not None:
            return current_time - self.time_of_death > self.death_linger_duration
        return self.health <= 0

    def _calculate_tour_cost(self, tour):
        if not tour: return 0.0
        points = [self.base_pos] + [t.position for t in tour] + [self.base_pos]
        return np.sum(np.linalg.norm(np.diff(points, axis=0), axis=1))

    def calculate_bid_for_task(self, task: Task):
        """
        Calculates the marginal cost of adding a new task to the current tour.
        This pure cost is the agent's bid. The lowest bidder wins.
        """
        # Since agents only bid when their tour is empty, this is the round-trip cost.
        return np.linalg.norm(self.pos - task.position) + np.linalg.norm(task.position - self.base_pos)

    def add_task_to_tour(self, task: Task):
        self.tour = [task]
        self.tour_cost = self._calculate_tour_cost(self.tour)

    def apply_movement_physics(self, dt, boundary_behavior, screen_width, screen_height):
        if self.health <= 0:
            self.velocity *= 0.9
            self.pos += self.velocity * dt * 50
            return
            
        # Task completion logic
        if self.tour and self.target_pos is not None:
            # Strikers complete tasks by detonating (handled in strategy)
            # Scouts complete tasks by arriving
            if not self.weapon_template and np.linalg.norm(self.pos - self.target_pos) < self.drone_radius * 2:
                self.tour.pop(0)

        # Physics Calculation
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
            self.health = 0
            if self.time_of_death is None:
                self.is_alive = False
                self.time_of_death = time.time()

    def draw(self, screen, config):
        draw_pos = (int(self.pos[0]), int(self.pos[1]))
        if self.time_of_death is None:
            pygame.draw.circle(screen, self.color, draw_pos, self.drone_radius)
            bar_width = self.drone_radius * 2.5
            bar_height = 4
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