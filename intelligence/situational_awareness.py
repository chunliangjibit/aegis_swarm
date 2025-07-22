# Aegis Swarm 2.0 - Situational Awareness Module (Upgraded)
# This script handles the "fog of war" and maintains a shared intelligence picture.
# UPGRADED: Now includes handling for BDA feedback hotspots to influence targeting.

import pygame
import time

class SharedSituationalPicture:
    """
    Represents a team's collective understanding of the battlefield.
    It stores information about known enemy contacts and feedback from combat events.
    """

    def __init__(self, config, screen_dims):
        # --- Core Data Structures ---
        self.known_enemy_contacts = {}  # Key: enemy_id, Value: contact details
        self.feedback_hotspots = []     # List of temporary hotspots from BDA

        # --- Configuration ---
        self.config = config['situational_picture']
        self.screen_width, self.screen_height = screen_dims
        
        # --- Caching for Performance ---
        self.grid_size = 50  # Size of each grid cell for density calculation
        self.hva_cache = None
        self.hva_cache_time = 0

    def update_from_perception(self, friendly_agent, detected_enemy):
        """Updates the shared picture with a new sensor reading."""
        self.known_enemy_contacts[detected_enemy.id] = {
            'id': detected_enemy.id,
            'pos': detected_enemy.pos,
            'last_seen': time.time()
        }
        self.hva_cache = None  # Invalidate cache due to new information

    def purge_stale_data(self):
        """Periodically purges both old contacts and expired hotspots."""
        current_time = time.time()
        
        # Purge stale contacts
        initial_count = len(self.known_enemy_contacts)
        self.known_enemy_contacts = {
            eid: data for eid, data in self.known_enemy_contacts.items()
            if current_time - data['last_seen'] < self.config['info_lifespan']
        }
        if len(self.known_enemy_contacts) != initial_count:
            self.hva_cache = None # Invalidate if contacts were removed

        # Purge stale hotspots
        initial_count = len(self.feedback_hotspots)
        self.feedback_hotspots = [
            h for h in self.feedback_hotspots
            if current_time - h['creation_time'] < h['lifespan']
        ]
        if len(self.feedback_hotspots) != initial_count:
            self.hva_cache = None # Invalidate if hotspots expired

    def get_known_enemies(self):
        """Returns a list of all currently valid enemy contacts."""
        return list(self.known_enemy_contacts.values())

    # --- NEW BDA METHOD ---
    def add_feedback_hotspot(self, pos, value, lifespan):
        """Adds a temporary hotspot from a BDA event to influence HVA calculations."""
        self.feedback_hotspots.append({
            'pos': pos,
            'value': value,
            'creation_time': time.time(),
            'lifespan': lifespan
        })
        self.hva_cache = None # New feedback invalidates the old HVA calculation

    # --- UPGRADED HVA CALCULATION ---
    def get_highest_value_area(self):
        """
        Analyzes the current picture to find the HVA, now considering BDA feedback.
        """
        current_time = time.time()
        if self.hva_cache and current_time - self.hva_cache_time < 0.1:
            return self.hva_cache

        known_enemies = self.get_known_enemies()
        if not known_enemies and not self.feedback_hotspots:
            self.hva_cache = None
            return None

        # --- Density Calculation ---
        # Grid covers the entire screen
        grid_cols = self.screen_width // self.grid_size
        grid_rows = self.screen_height // self.grid_size
        # Use a dictionary for sparse storage of grid values
        grid_values = {}

        # 1. Add value from enemy density
        for enemy in known_enemies:
            gx = int(enemy['pos'].x // self.grid_size)
            gy = int(enemy['pos'].y // self.grid_size)
            if 0 <= gx < grid_cols and 0 <= gy < grid_rows:
                grid_cell = (gx, gy)
                grid_values[grid_cell] = grid_values.get(grid_cell, 0) + 1 # Each enemy adds 1 to density

        # 2. Add value from BDA feedback hotspots
        for hotspot in self.feedback_hotspots:
            gx = int(hotspot['pos'].x // self.grid_size)
            gy = int(hotspot['pos'].y // self.grid_size)
            if 0 <= gx < grid_cols and 0 <= gy < grid_rows:
                # Add the hotspot's value to the corresponding grid cell
                grid_cell = (gx, gy)
                grid_values[grid_cell] = grid_values.get(grid_cell, 0) + hotspot['value']

        if not grid_values:
            self.hva_cache = None
            return None

        # Find the grid cell with the highest total value
        best_cell = max(grid_values, key=grid_values.get)
        max_value = grid_values[best_cell]

        # Check if the value meets our threshold
        if max_value >= self.config['hva_value_threshold']:
            hva_pos = pygame.math.Vector2(
                (best_cell[0] + 0.5) * self.grid_size,
                (best_cell[1] + 0.5) * self.grid_size
            )
            result = {'pos': hva_pos, 'value': max_value}
            self.hva_cache = result
            self.hva_cache_time = time.time()
            return result
        
        self.hva_cache = None
        return None

    def draw(self, screen):
        """Visualizes the intelligence picture, including hotspots."""
        # Draw known enemy contacts
        for contact in self.get_known_enemies():
            pygame.draw.circle(screen, (255, 255, 0, 100), contact['pos'], 15, 1)

        # Draw BDA feedback hotspots
        current_time = time.time()
        for hotspot in self.feedback_hotspots:
            # Make the hotspot fade out over its lifespan
            life_fraction = (current_time - hotspot['creation_time']) / hotspot['lifespan']
            alpha = int(200 * (1 - life_fraction)) # Fades from 200 to 0
            radius = 10 + int(20 * life_fraction) # Expands as it fades
            
            if alpha > 0:
                surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                color = (255, 165, 0, alpha) # Orange color for feedback
                pygame.draw.circle(surface, color, (radius, radius), radius)
                screen.blit(surface, (hotspot['pos'].x - radius, hotspot['pos'].y - radius))

        # Draw the calculated HVA
        hva = self.get_highest_value_area()
        if hva:
            # Draw a more prominent HVA marker
            pos = hva['pos']
            pygame.draw.circle(screen, (255, 0, 255), pos, 20, 2)
            pygame.draw.line(screen, (255, 0, 255), (pos.x - 25, pos.y), (pos.x + 25, pos.y), 2)
            pygame.draw.line(screen, (255, 0, 255), (pos.x, pos.y - 25), (pos.x, pos.y + 25), 2)