# Aegis Swarm 3.0 - Battlefield Orchestrator (Market Intelligence Edition)
# UPGRADED: Now correctly initializes and drives the intelligent marketplace
# and risk-aware agents.

import pygame
import random
import time
import numpy as np
from core.agent import Agent
from core.models import BoidsModel, CombatModel, PerceptionModel
from intelligence.marketplace import Marketplace # Updated import
import strategies.blue_strategies as blue_strat
import strategies.red_strategies as red_strat

class Battlefield:
    def __init__(self, config):
        self.config = config
        self.global_config = config['GLOBAL_SIMULATION_SETTINGS']
        self.intel_config = config['INTELLIGENCE_CONFIG']
        self.market_config = config['MARKET_CONFIG'] # <-- Get market config
        self.screen_dims = (self.global_config['SCREEN_WIDTH'], self.global_config['SCREEN_HEIGHT'])
        
        # --- NEW: Initialize marketplace with config ---
        self.blue_marketplace = Marketplace(config)
        
        self.agents = []
        self._create_teams()

        self.boids_model = BoidsModel()
        self.combat_model = CombatModel()
        self.perception_model = PerceptionModel()
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 24)
        self.current_frame_events = []

    def _create_teams(self):
        team_configs = {'blue': self.config['TEAM_BLUE_CONFIG'], 'red': self.config['TEAM_RED_CONFIG']}
        for team_name, team_config in team_configs.items():
            self.red_team_num_groups = team_config.get("strategy_params", {}).get("split_attack_groups", 1)
            for role_name, role_config in team_config['swarm_composition'].items():
                if role_config['count'] == 0: continue
                role_template = self.config['ROLE_TEMPLATES'][role_config['role_template']]
                weapon_template = self.config['WEAPON_TEMPLATES'].get(role_config.get('weapon_template'))
                final_config = {**role_config, 'role_template': role_template, 'weapon_template': weapon_template}
                for i in range(role_config['count']):
                    # --- NEW: Pass market_config to Agent ---
                    agent = Agent(team_config, final_config, self._get_initial_position(team_config['deployment_zone']), self.market_config)
                    if team_name == 'red': agent.group_id = i % self.red_team_num_groups
                    self.agents.append(agent)
    
    def _get_initial_position(self, zone):
        w, h = self.screen_dims
        if zone == 'left': return np.array([random.randint(50, w // 8), random.randint(50, h - 50)], dtype=float)
        if zone == 'right': return np.array([random.randint(w * 7 // 8, w - 50), random.randint(50, h - 50)], dtype=float)
        return np.array([random.randint(50, w - 50), random.randint(50, h - 50)], dtype=float)

    def update(self, dt):
        current_time = time.time()
        self.current_frame_events = []
        self.agents = [a for a in self.agents if not a.is_truly_dead(current_time)]
        
        alive_agents = [a for a in self.agents if a.health > 0]
        blue_agents = [a for a in alive_agents if a.team_id == self.config['TEAM_BLUE_CONFIG']['id']]
        red_agents = [a for a in alive_agents if a.team_id == self.config['TEAM_RED_CONFIG']['id']]
        
        # --- [NEW] Market Heartbeat: Update task values, positions, and status ---
        battlefield_context = {'screen_width': self.screen_dims[0], 'screen_height': self.screen_dims[1]}
        self.blue_marketplace.update_market_state(alive_agents, battlefield_context)

        # --- Red Team Global Intelligence and Target Assignment ---
        all_visible_blue_agents = set()
        for red_agent in red_agents:
            for blue_agent in blue_agents:
                if np.linalg.norm(red_agent.pos - blue_agent.pos) < red_agent.perception_radius:
                    if self.perception_model.detect_enemy(red_agent, blue_agent, self.intel_config['detection_model']):
                        all_visible_blue_agents.add(blue_agent)
        
        target_assignments = red_strat.assign_targets_to_groups(list(all_visible_blue_agents), self.red_team_num_groups)

        # --- Perception and Strategy Phase ---
        all_friends = {a.id: [] for a in alive_agents}
        for agent in alive_agents:
            my_friends, my_enemies = [], []
            # Use appropriate enemy list based on agent's team
            potential_enemies = blue_agents if agent.team_id == self.config['TEAM_RED_CONFIG']['id'] else red_agents
            
            for other_agent in alive_agents:
                if agent.id == other_agent.id: continue
                if np.linalg.norm(agent.pos - other_agent.pos) < agent.perception_radius:
                    if agent.team_id == other_agent.team_id:
                        my_friends.append(other_agent)
                    elif other_agent in potential_enemies and self.perception_model.detect_enemy(agent, other_agent, self.intel_config['detection_model']):
                        my_enemies.append(other_agent)

            all_friends[agent.id] = my_friends
            
            intel = {
                'neighbors': {'friends': my_friends, 'enemies': my_enemies},
                'screen_width': self.screen_dims[0], 'screen_height': self.screen_dims[1],
                'marketplace': self.blue_marketplace,
                'target_assignments': target_assignments # For Red Team
            }

            if agent.team_id == self.config['TEAM_BLUE_CONFIG']['id']:
                blue_strat.strategy_dispatcher(agent, intel)
            else:
                red_strat.strategy_dispatcher(agent, intel)

        # --- Auction Phase ---
        if blue_agents:
            self.blue_marketplace.run_auction(blue_agents)

        # --- Physics and Movement Phase ---
        for agent in alive_agents:
            force = self.boids_model.calculate_steering_force(agent, all_friends[agent.id], agent.boids_weights, agent.target_pos)
            agent.acceleration += force
            agent.apply_movement_physics(dt, self.global_config['BOUNDARY_BEHAVIOR'], *self.screen_dims)
        
        # --- Combat Phase ---
        detonators = [a for a in alive_agents if getattr(a, 'is_detonating', False)]
        if detonators:
            all_dmg_events = []
            for d in detonators:
                if d.weapon_template and d.weapon_template['type'] == 'suicide_aoe':
                    # Agent is destroyed upon detonation
                    d.take_damage(d.max_health * 2) 
                    dmg_events = self.combat_model.suicide_aoe_detonation(d, alive_agents, d.weapon_template)
                    all_dmg_events.extend(dmg_events)
                    killed_count = sum(1 for e in dmg_events if e['damage'] >= e['agent'].health)
                    self.current_frame_events.append({"type": "detonation", "agent_id": str(d.id), "pos": d.pos.tolist(), "killed": killed_count})
            for event in all_dmg_events:
                event['agent'].take_damage(event['damage'])

    def get_snapshot(self):
        blue_id = self.config['TEAM_BLUE_CONFIG']['id']
        red_id = self.config['TEAM_RED_CONFIG']['id']
        agent_states = [{ "id": str(a.id), "team_id": a.team_id, "pos": a.pos.tolist(), "health": a.health, "max_health": a.max_health, "strategy": a.strategy_name } for a in self.agents]
        # [NEW] Snapshot now includes all tasks, including bundles
        task_states = [
            { "id": str(task.id), "pos": task.position.tolist(), "status": task.status, 
              "value": round(task.current_value, 2), "is_bundle": task.is_bundle,
              "sub_task_count": len(task.sub_tasks) if task.is_bundle else 0 }
            for task in self.blue_marketplace.tasks.values() if task.status != 'COMPLETED'
        ]
        blue_count = sum(1 for a in self.agents if a.is_alive and a.team_id == blue_id)
        red_count = sum(1 for a in self.agents if a.is_alive and a.team_id == red_id)
        return { "blue_count": blue_count, "red_count": red_count, "events": self.current_frame_events, "agents": agent_states, "tasks": task_states }

    def draw(self, screen):
        # Draw logic remains largely the same, but we can enhance it in the replayer
        task_color_open = (255, 255, 100)
        task_color_assigned = (100, 100, 100)
        for task in self.blue_marketplace.tasks.values():
            if task.status == 'COMPLETED': continue
            color = task_color_open if task.status == 'OPEN' else task_color_assigned
            pos_int = task.position.astype(int)
            if task.is_bundle:
                pygame.draw.circle(screen, color, pos_int, 8, 2) # Draw bundles as circles
            else:
                pygame.draw.rect(screen, color, (pos_int[0]-3, pos_int[1]-3, 6, 6)) # Singles as squares
        
        for agent in self.agents: agent.draw(screen, self.global_config)
        
        blue_count = sum(1 for a in self.agents if a.is_alive and a.team_id == self.config['TEAM_BLUE_CONFIG']['id'])
        red_count = sum(1 for a in self.agents if a.is_alive and a.team_id == self.config['TEAM_RED_CONFIG']['id'])
        blue_text = self.font.render(f"Blue Team: {blue_count}", True, self.global_config['INFO_FONT_COLOR'])
        red_text = self.font.render(f"Red Team: {red_count}", True, self.global_config['INFO_FONT_COLOR'])
        screen.blit(blue_text, (10, 10))
        screen.blit(red_text, (self.screen_dims[0] - red_text.get_width() - 10, 10))