# Aegis Swarm 2.0 - Battle Damage Assessment (BDA) Module
# This script is responsible for evaluating the outcome of an attack
# and creating feedback that can influence future strategic decisions.

import pygame
import time

class BDAModule:
    """
    Analyzes combat events to provide feedback to the intelligence system.
    """

    def __init__(self, config):
        self.config = config['bda']

    def assess_explosion_event(self, detonator, damage_events, shared_picture):
        """
        Assesses the result of a single explosion and updates the shared situational
        picture with feedback.

        Args:
            detonator (Agent): The agent that exploded.
            damage_events (list): A list of damage dicts from the CombatModel.
            shared_picture (SharedSituationalPicture): The team's intelligence object to update.
        """
        killed_count = 0
        total_damage = 0

        for event in damage_events:
            total_damage += event['damage']
            # An agent is considered killed if the damage dealt is equal to or more than its current health.
            if event['damage'] >= event['agent'].health:
                killed_count += 1
        
        # --- Create Feedback ---
        # A simple but effective feedback mechanism: if the attack was successful
        # (e.g., killed at least one enemy), we mark the area as a "hotspot",
        # temporarily increasing its value for other striker drones.

        # Define what constitutes a "successful" strike. Here, killing one enemy is enough.
        is_successful_strike = killed_count > 0

        if is_successful_strike:
            # The feedback is applied to the SharedSituationalPicture
            shared_picture.add_feedback_hotspot(
                pos=detonator.pos, 
                value=killed_count * self.config['feedback_value_multiplier'],
                lifespan=self.config['feedback_lifespan']
            )

# ==============================================================================
# We need to update the SharedSituationalPicture class to handle this new feedback.
# This requires modifying intelligence/situational_awareness.py.
# For now, let's define the methods that BDAModule will call.
# I will provide the full updated situational_awareness.py script after this step is confirmed.
#
# --- Proposed additions to SharedSituationalPicture in situational_awareness.py ---
#
# In __init__:
# self.feedback_hotspots = []
#
# New method:
# def add_feedback_hotspot(self, pos, value, lifespan):
#     """Adds a temporary hotspot to influence HVA calculations."""
#     self.feedback_hotspots.append({
#         'pos': pos,
#         'value': value,
#         'creation_time': time.time(),
#         'lifespan': lifespan
#     })
#
# New method:
# def purge_stale_hotspots(self):
#     """Removes expired feedback hotspots."""
#     current_time = time.time()
#     self.feedback_hotspots = [h for h in self.feedback_hotspots 
#                               if current_time - h['creation_time'] < h['lifespan']]
#
# In get_highest_value_area:
# The density calculation needs to be modified to include the value from these hotspots.
# It will check if any enemy is near a hotspot and add the hotspot's value to its grid cell's density.
# ==============================================================================