# Aegis Swarm 3.2 - Configuration File (Visual ID Edition)
# UPGRADED: Blue team roles (Scouts, Strikers) now have distinct colors.

GLOBAL_SIMULATION_SETTINGS = {
    'SCREEN_WIDTH': 1600, 'SCREEN_HEIGHT': 900, 'FPS': 60, 'BOUNDARY_BEHAVIOR': "wrap",
    'BG_COLOR': (10, 10, 20), 'INFO_FONT_COLOR': (200, 200, 255),
    
    # --- [NEW] Distinct colors for Blue roles ---
    'SCOUT_BLUE_COLOR': (100, 200, 255), # Lighter, cyan-like blue
    'STRIKER_BLUE_COLOR': (0, 100, 255),   # Deeper, royal blue
    
    'RED_COLOR': (255, 50, 50), 
    'HEALTH_BAR_GREEN': (0, 255, 0), 'HEALTH_BAR_RED': (255, 0, 0),
}

MARKET_CONFIG = {
    'TASK_BUNDLING_MAX_DIST': 100.0, 'TASK_BUNDLING_MAX_TIME_DIFF': 2.0,
    'VALUE_UPDATE_INTERVAL': 1.0, 'BASE_VALUE_DECAY_RATE': 0.05,
    'THREAT_VALUE_FACTOR': 3.0, 'RELIABILITY_BONUS': 0.5,
    'RISK_ASSESSMENT_RADIUS': 150.0, 'RISK_AVERSION_FACTOR': 0.8,
}

WEAPON_TEMPLATES = {
    "SUICIDE_FRAG_V1": { "type": "suicide_aoe", "detonation_range": 20.0, "kill_radius": 25.0, "damage_radius": 55.0, "kill_prob": 0.95, "base_damage": 80 }
}

ROLE_TEMPLATES = {
    "SCOUT_CHASSIS": { "health": 40, "max_speed": 3.5, "perception_radius": 400.0, "drone_radius": 4 },
    "STRIKER_CHASSIS": { "health": 100, "max_speed": 4.5, "perception_radius": 150.0, "drone_radius": 5 }
}

TEAM_BLUE_CONFIG = {
    "name": "Blue", "id": 1, "deployment_zone": "left",
    "strategy_name": "Market-Based AI",
    "swarm_composition": {
        "scouts": { 
            "role_template": "SCOUT_CHASSIS", "count": 10, "strategy": "scout_evade_and_publish_strategy",
            "boids_weights": {"separation": 3.0, "alignment": 0.3, "cohesion": 0.1},
            "color": GLOBAL_SIMULATION_SETTINGS['SCOUT_BLUE_COLOR'] # <-- [NEW] Scout-specific color
        },
        "strikers": { 
            "role_template": "STRIKER_CHASSIS", "weapon_template": "SUICIDE_FRAG_V1", "count": 40, 
            "strategy": "striker_market_participant_strategy",
            "boids_weights": {"separation": 1.8, "alignment": 0.5, "cohesion": 0.4},
            "color": GLOBAL_SIMULATION_SETTINGS['STRIKER_BLUE_COLOR'] # <-- [NEW] Striker-specific color
        }
    }
}

TEAM_RED_CONFIG = {
    "name": "Red", "id": 2, "color": GLOBAL_SIMULATION_SETTINGS['RED_COLOR'], "deployment_zone": "right",
    "default_strategy": "Armed Assault",

    "strategy_profiles": {
        "Zombie Charge": { "display_name": "Zombie Charge (Legacy)", "strategy_function": "distributed_attack_strategy", "mission_type": "BLIND_CHARGE", "roe": "NONE", "params": { "split_attack_groups": 4 } },
        "Armed Assault": { "display_name": "Armed Assault", "strategy_function": "advanced_strategy_dispatcher", "mission_type": "ASSAULT_POINT", "roe": "REACTIVE_HUNTER", "params": { "target_pos": [100, GLOBAL_SIMULATION_SETTINGS['SCREEN_HEIGHT'] / 2] } },
        "Stealth Infiltration": { "display_name": "Stealth Infiltration", "strategy_function": "advanced_strategy_dispatcher", "mission_type": "ASSAULT_POINT", "roe": "EVADE_AND_ENGAGE", "params": { "target_pos": [100, GLOBAL_SIMULATION_SETTINGS['SCREEN_HEIGHT'] / 2] } },
        "Area Sweep Force": { "display_name": "Area Sweep Force", "strategy_function": "advanced_strategy_dispatcher", "mission_type": "SWEEP_AREA", "roe": "REACTIVE_HUNTER", "params": { "sweep_box": [ GLOBAL_SIMULATION_SETTINGS['SCREEN_WIDTH'] * 0.25, 100, GLOBAL_SIMULATION_SETTINGS['SCREEN_WIDTH'] * 0.75, GLOBAL_SIMULATION_SETTINGS['SCREEN_HEIGHT'] - 100 ]} }
    },
    "swarm_composition": {
        "aggressors": { 
            "role_template": "STRIKER_CHASSIS", "weapon_template": "SUICIDE_FRAG_V1", "count": 70, 
            "boids_weights": {"separation": 1.8, "alignment": 0.5, "cohesion": 0.4},
            "color": GLOBAL_SIMULATION_SETTINGS['RED_COLOR'] # <-- Red team still uses a single color
        }
    }
}

INTELLIGENCE_CONFIG = { "detection_model": { "base_prob": 0.98, "prob_decay_rate": 2.5 } }

full_config = {
    "GLOBAL_SIMULATION_SETTINGS": GLOBAL_SIMULATION_SETTINGS, "MARKET_CONFIG": MARKET_CONFIG,
    "WEAPON_TEMPLATES": WEAPON_TEMPLATES, "ROLE_TEMPLATES": ROLE_TEMPLATES, 
    "TEAM_BLUE_CONFIG": TEAM_BLUE_CONFIG, "TEAM_RED_CONFIG": TEAM_RED_CONFIG, 
    "INTELLIGENCE_CONFIG": INTELLIGENCE_CONFIG
}