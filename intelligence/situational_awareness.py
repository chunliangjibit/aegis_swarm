# Aegis Swarm 2.0 - Situational Awareness Module (Simplified)
# UPGRADED for Aegis 2.5: HVA and BDA feedback logic has been removed as it is
# superseded by the marketplace mechanism. This class is kept for basic
# enemy contact management, potentially for advanced scout strategies in the future.

import pygame
import time
import numpy as np

class SharedSituationalPicture:
    """
    Represents a team's collective understanding of the battlefield.
    In Aegis 2.5, its role is simplified to primarily tracking known enemy contacts.
    """
    def __init__(self, config, screen_dims):
        self.known_enemy_contacts = {}
        self.config = config.get('situational_picture', {})
        self.screen_width, self.screen_height = screen_dims
        self.last_purge_time = time.time()

    def update_from_perception(self, friendly_agent, detected_enemy):
        """Updates the shared picture with a new sensor reading."""
        self.known_enemy_contacts[detected_enemy.id] = {
            'id': detected_enemy.id,
            'pos': detected_enemy.pos.copy(),
            'last_seen': time.time()
        }

    def purge_stale_data(self):
        """Periodically purges old contacts."""
        current_time = time.time()
        info_lifespan = self.config.get('info_lifespan', 5.0)
        self.known_enemy_contacts = {
            eid: data for eid, data in self.known_enemy_contacts.items()
            if current_time - data['last_seen'] < info_lifespan
        }

    def get_known_enemies(self):
        """Returns a list of all currently valid enemy contacts."""
        return list(self.known_enemy_contacts.values())
    
    def draw(self, screen):
        """Visualizes the known enemy contacts."""
        # This can be used for debugging or specific visual modes.
        for contact in self.get_known_enemies():
            pygame.draw.circle(screen, (255, 255, 0, 100), contact['pos'].astype(int), 15, 1)