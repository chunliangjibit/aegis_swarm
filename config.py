# Aegis Swarm 2.0 - Configuration File (Ultimate Version)
# TACTICAL UPGRADE 2.8: Introduced asymmetric capabilities for Scouts.

GLOBAL_SIMULATION_SETTINGS = {
    'SCREEN_WIDTH': 1600, 'SCREEN_HEIGHT': 900, 'FPS': 60, 'BOUNDARY_BEHAVIOR': "wrap",
    'BG_COLOR': (10, 10, 20), 'INFO_FONT_COLOR': (200, 200, 255), 'BLUE_COLOR': (0, 150, 255),
    'RED_COLOR': (255, 50, 50), 'HEALTH_BAR_GREEN': (0, 255, 0), 'HEALTH_BAR_RED': (255, 0, 0),
}
WEAPON_TEMPLATES = {
    "SUICIDE_FRAG_V1": { "type": "suicide_aoe", "detonation_range": 20.0, "kill_radius": 25.0, "damage_radius": 55.0, "kill_prob": 0.95, "base_damage": 80 }
}
ROLE_TEMPLATES = {
    # Scouts are now high-value, long-range sensors. Lower health, slower, but huge perception.
    "SCOUT_CHASSIS": { "health": 40, "max_speed": 3.5, "perception_radius": 400.0, "drone_radius": 4 },
    # Strikers are fast, tough, short-range hunters.
    "STRIKER_CHASSIS": { "health": 100, "max_speed": 4.5, "perception_radius": 150.0, "drone_radius": 5 }
}
TEAM_BLUE_CONFIG = {
    "name": "Blue", "id": 1, "color": GLOBAL_SIMULATION_SETTINGS['BLUE_COLOR'], "deployment_zone": "left",
    "swarm_composition": {
        "scouts": { 
            "role_template": "SCOUT_CHASSIS", "weapon_template": None, "count": 10, 
            "boids_weights": {"separation": 3.0, "alignment": 0.3, "cohesion": 0.1}, 
            "strategy": "scout_evade_and_publish_strategy" # ** NEW STRATEGY NAME **
        },
        "strikers": { 
            "role_template": "STRIKER_CHASSIS", "weapon_template": "SUICIDE_FRAG_V1", "count": 40, 
            "boids_weights": {"separation": 1.8, "alignment": 0.5, "cohesion": 0.4}, 
            "strategy": "striker_market_participant_strategy"
        }
    }
}
TEAM_RED_CONFIG = {
    "name": "Red", "id": 2, "color": GLOBAL_SIMULATION_SETTINGS['RED_COLOR'], "deployment_zone": "right",
    "strategy_params": {
        "split_attack_groups": 4 # Increase groups to counter blue's higher intelligence
    },
    "swarm_composition": {
        "aggressors": { 
            "role_template": "STRIKER_CHASSIS", "weapon_template": "SUICIDE_FRAG_V1", "count": 70, 
            "boids_weights": {"separation": 1.8, "alignment": 0.5, "cohesion": 0.4}, 
            "strategy": "distributed_attack_strategy" # Use the smarter Red AI
        }
    }
}
INTELLIGENCE_CONFIG = {
    "detection_model": { "base_prob": 0.98, "prob_decay_rate": 2.5 },
    "situational_picture": {}, # Deprecated
    "bda": {} # Deprecated
}
full_config = {
    "GLOBAL_SIMULATION_SETTINGS": GLOBAL_SIMULATION_SETTINGS, "WEAPON_TEMPLATES": WEAPON_TEMPLATES,
    "ROLE_TEMPLATES": ROLE_TEMPLATES, "TEAM_BLUE_CONFIG": TEAM_BLUE_CONFIG,
    "TEAM_RED_CONFIG": TEAM_RED_CONFIG, "INTELLIGENCE_CONFIG": INTELLIGENCE_CONFIG
}