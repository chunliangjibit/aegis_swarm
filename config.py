# Aegis Swarm 2.0 - Configuration File (Tactical Upgrade: Fortified Scouts)

GLOBAL_SIMULATION_SETTINGS = {
    'SCREEN_WIDTH': 1600, 'SCREEN_HEIGHT': 900, 'FPS': 60, 'BOUNDARY_BEHAVIOR': "wrap",
    'BG_COLOR': (10, 10, 20), 'INFO_FONT_COLOR': (200, 200, 255), 'BLUE_COLOR': (0, 150, 255),
    'RED_COLOR': (255, 50, 50), 'HEALTH_BAR_GREEN': (0, 255, 0), 'HEALTH_BAR_RED': (255, 0, 0),
}
WEAPON_TEMPLATES = {
    "SUICIDE_FRAG_V1": { "type": "suicide_aoe", "detonation_range": 15.0, "kill_radius": 25.0, "damage_radius": 55.0, "kill_prob": 0.95, "base_damage": 80 },
    "PULSE_LASER_V1": { "type": "dps", "weapon_range": 100.0, "damage_per_second": 20 }
}
ROLE_TEMPLATES = {
    "SCOUT_CHASSIS": { "health": 50, "max_speed": 4.0, "perception_radius": 250.0, "drone_radius": 4 },
    "STRIKER_CHASSIS": { "health": 100, "max_speed": 3.0, "perception_radius": 150.0, "drone_radius": 5 },
    "HEAVY_CHASSIS": { "health": 200, "max_speed": 2.2, "perception_radius": 180.0, "drone_radius": 7 }
}
TEAM_BLUE_CONFIG = {
    "name": "Blue", "id": 1, "color": GLOBAL_SIMULATION_SETTINGS['BLUE_COLOR'], "deployment_zone": "left",
    "swarm_composition": {
        # 【战术升级 A】
        "fortified_scouts": {
            "role_template": "STRIKER_CHASSIS", # 使用更坚固的底盘
            "weapon_template": None,
            "count": 12,                        # 数量增加到12
            "boids_weights": {"separation": 2.5, "alignment": 0.3, "cohesion": 0.2},
            "strategy": "bait_and_observe"
        },
        "strikers": {
            "role_template": "STRIKER_CHASSIS",
            "weapon_template": "SUICIDE_FRAG_V1",
            "count": 38,                        # 数量相应减少，总数仍为50
            "boids_weights": {"separation": 1.8, "alignment": 0.5, "cohesion": 0.4},
            "strategy": "wait_for_hva_and_strike"
        }
    }
}
TEAM_RED_CONFIG = {
    "name": "Red", "id": 2, "color": GLOBAL_SIMULATION_SETTINGS['RED_COLOR'], "deployment_zone": "right",
    "swarm_composition": {
        "aggressors": { "role_template": "STRIKER_CHASSIS", "weapon_template": "SUICIDE_FRAG_V1", "count": 70, "boids_weights": {"separation": 1.8, "alignment": 0.5, "cohesion": 0.4}, "strategy": "fearless_charge" }
    }
}
INTELLIGENCE_CONFIG = {
    "detection_model": { "base_prob": 0.98, "prob_decay_rate": 2.5 },
    "situational_picture": { "info_lifespan": 5.0, "hva_value_threshold": 3 },
    "bda": { "observer_radius": 100.0, "feedback_value_multiplier": 1.5, "feedback_lifespan": 10.0 }
}
full_config = {
    "GLOBAL_SIMULATION_SETTINGS": GLOBAL_SIMULATION_SETTINGS, "WEAPON_TEMPLATES": WEAPON_TEMPLATES,
    "ROLE_TEMPLATES": ROLE_TEMPLATES, "TEAM_BLUE_CONFIG": TEAM_BLUE_CONFIG,
    "TEAM_RED_CONFIG": TEAM_RED_CONFIG, "INTELLIGENCE_CONFIG": INTELLIGENCE_CONFIG
}