# Aegis Swarm 2.0 - Core Agent Class (Final Cleaned Version)
import pygame, uuid, random

class Agent:
    def __init__(self, team_config, role_config, initial_pos):
        self.id = uuid.uuid4()
        self.is_alive = True
        self.team_id = team_config['id']
        self.color = team_config['color']
        self.role_template = role_config['role_template']
        self.weapon_template = role_config['weapon_template']
        self.strategy_name = role_config['strategy']
        self.boids_weights = role_config['boids_weights']
        self.max_health = self.role_template['health']
        self.health = self.role_template['health']
        self.max_speed = self.role_template['max_speed']
        self.perception_radius = self.role_template['perception_radius']
        self.drone_radius = self.role_template['drone_radius']
        self.pos = pygame.math.Vector2(initial_pos)
        self.velocity = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * self.max_speed
        self.acceleration = pygame.math.Vector2()
        self.target_pos = None
        self.is_detonating = False

    def apply_movement_physics(self, dt, boundary_behavior, screen_width, screen_height):
        if self.acceleration.length() > 1.0:
            self.acceleration.scale_to_length(1.0)
        self.velocity += self.acceleration
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)
        self.pos += self.velocity * dt * 50
        self.acceleration *= 0
        if boundary_behavior == "wrap":
            self._handle_wrap_boundary(screen_width, screen_height)

    def _handle_wrap_boundary(self, width, height):
        if self.pos.x > width: self.pos.x = 0
        elif self.pos.x < 0: self.pos.x = width
        if self.pos.y > height: self.pos.y = 0
        elif self.pos.y < 0: self.pos.y = height

    def take_damage(self, amount):
        if not self.is_alive: return
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.is_alive = False

    def draw(self, screen, config):
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.drone_radius)
        if self.health < self.max_health:
            bar_width = self.drone_radius * 2.5
            bar_height = 4
            bar_x = self.pos.x - bar_width / 2
            bar_y = self.pos.y - self.drone_radius - bar_height - 5
            health_percentage = self.health / self.max_health
            pygame.draw.rect(screen, config['HEALTH_BAR_RED'], (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(screen, config['HEALTH_BAR_GREEN'], (bar_x, bar_y, bar_width * health_percentage, bar_height))