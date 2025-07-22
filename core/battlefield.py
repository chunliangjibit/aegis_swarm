# Aegis Swarm 2.0 - Battlefield Orchestrator (Ultimate Version)
import pygame, random, time
from core.agent import Agent
from core.models import BoidsModel, CombatModel, PerceptionModel
from intelligence.situational_awareness import SharedSituationalPicture
from intelligence.bda import BDAModule
import strategies.blue_strategies as blue_strat, strategies.red_strategies as red_strat

class Battlefield:
    def __init__(self, config):
        self.config = config
        self.global_config = config['GLOBAL_SIMULATION_SETTINGS']
        self.intel_config = config['INTELLIGENCE_CONFIG']
        self.screen_dims = (self.global_config['SCREEN_WIDTH'], self.global_config['SCREEN_HEIGHT'])
        self.agents = []
        self._create_teams()
        self.blue_ssp = SharedSituationalPicture(self.intel_config, self.screen_dims)
        self.bda_module = BDAModule(self.intel_config)
        self.boids_model, self.combat_model, self.perception_model = BoidsModel(), CombatModel(), PerceptionModel()
        pygame.font.init(); self.font = pygame.font.SysFont('Arial', 24); self.last_purge_time = time.time()
    
    def _create_teams(self):
        team_configs = {'blue': self.config['TEAM_BLUE_CONFIG'], 'red': self.config['TEAM_RED_CONFIG']}
        for team_name, team_config in team_configs.items():
            
            # 【新增】Handle special parameters for strategies
            red_num_groups = team_config.get("strategy_params", {}).get("split_attack_groups", 1)
            self.red_team_num_groups = red_num_groups # Store for access by strategies
            agent_idx = 0

            for role_name, role_config in team_config['swarm_composition'].items():
                if role_config['count'] == 0: continue
                role_template = self.config['ROLE_TEMPLATES'][role_config['role_template']]
                weapon_template = self.config['WEAPON_TEMPLATES'].get(role_config.get('weapon_template'))
                final_config = {**role_config, 'role_template': role_template, 'weapon_template': weapon_template}
                for i in range(role_config['count']):
                    agent = Agent(team_config, final_config, self._get_initial_position(team_config['deployment_zone']))
                    # Assign group_id for red team split attack
                    if team_name == 'red':
                        agent.group_id = agent_idx % red_num_groups
                    
                    # Pass GUI values to the agent
                    if 'self_defense_radius' in team_config:
                        agent.self_defense_radius = team_config['self_defense_radius']

                    self.agents.append(agent)
                    agent_idx += 1
    
    # ... (the rest of the file is unchanged, only _create_teams is modified)
    def _get_initial_position(self, zone):
        w, h = self.screen_dims
        if zone == 'left': return (random.randint(50, w // 4), random.randint(50, h - 50))
        if zone == 'right': return (random.randint(w * 3 // 4, w - 50), random.randint(50, h - 50))
        return (random.randint(50, w - 50), random.randint(50, h - 50))
    def update(self, dt):
        neighbors = {a.id: {'friends': [], 'enemies': []} for a in self.agents if a.is_alive}
        for a1 in self.agents:
            if not a1.is_alive: continue
            for a2 in self.agents:
                if not a2.is_alive or a1.id == a2.id: continue
                if a1.pos.distance_to(a2.pos) < a1.perception_radius:
                    if a1.team_id == a2.team_id: neighbors[a1.id]['friends'].append(a2)
                    elif self.perception_model.detect_enemy(a1, a2, self.intel_config['detection_model']):
                        neighbors[a1.id]['enemies'].append(a2)
                        if a1.team_id == self.config['TEAM_BLUE_CONFIG']['id']: self.blue_ssp.update_from_perception(a1, a2)
        if time.time() - self.last_purge_time > 1.0: self.blue_ssp.purge_stale_data(); self.last_purge_time = time.time()
        for agent in self.agents:
            if agent.is_alive:
                intel = {'neighbors': neighbors[agent.id], 'shared_picture': self.blue_ssp if agent.team_id == self.config['TEAM_BLUE_CONFIG']['id'] else None, 
                         'screen_width': self.screen_dims[0], 'screen_height': self.screen_dims[1],
                         'red_team_num_groups': self.red_team_num_groups}
                if agent.team_id == self.config['TEAM_BLUE_CONFIG']['id']: blue_strat.strategy_dispatcher(agent, intel)
                else: red_strat.strategy_dispatcher(agent, intel)
        for agent in self.agents:
            if agent.is_alive:
                force = self.boids_model.calculate_steering_force(agent, neighbors[agent.id]['friends'], agent.boids_weights, agent.target_pos)
                agent.acceleration += force; agent.apply_movement_physics(dt, self.global_config['BOUNDARY_BEHAVIOR'], *self.screen_dims)
        detonators = [a for a in self.agents if getattr(a, 'is_detonating', False) and a.is_alive]
        if detonators:
            all_dmg = []
            for d in detonators:
                if d.weapon_template and d.weapon_template['type'] == 'suicide_aoe':
                    d.is_alive = False
                    dmg_events = self.combat_model.suicide_aoe_detonation(d, self.agents, d.weapon_template)
                    all_dmg.extend(dmg_events)
                    if d.team_id == self.config['TEAM_BLUE_CONFIG']['id']: self.bda_module.assess_explosion_event(d, dmg_events, self.blue_ssp)
            for event in all_dmg: event['agent'].take_damage(event['damage'])
        self.agents = [a for a in self.agents if a.is_alive]
    def draw(self, screen):
        self.blue_ssp.draw(screen)
        for agent in self.agents: agent.draw(screen, self.global_config)
        blue_count = sum(1 for a in self.agents if a.team_id == self.config['TEAM_BLUE_CONFIG']['id'])
        red_count = sum(1 for a in self.agents if a.team_id == self.config['TEAM_RED_CONFIG']['id'])
        blue_text = self.font.render(f"Blue Team: {blue_count}", True, self.global_config['INFO_FONT_COLOR'])
        red_text = self.font.render(f"Red Team: {red_count}", True, self.global_config['INFO_FONT_COLOR'])
        screen.blit(blue_text, (10, 10)); screen.blit(red_text, (self.screen_dims[0] - red_text.get_width() - 10, 10))