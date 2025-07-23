# Aegis Swarm 3.0 - Marketplace Module (Patch 3.0.2)
# PATCH: Fixed a critical KeyError when updating a bundle task after its
# primary sub-task was completed. The update logic is now robust.

import numpy as np
import time
from core.task import Task

class Marketplace:
    def __init__(self, config):
        self.market_config = config['MARKET_CONFIG']
        self.team_blue_config = config['TEAM_BLUE_CONFIG']
        self.tasks = {}
        self.enemy_id_to_task_id = {}
        self.last_value_update_time = time.time()

    def get_open_tasks_for_auction(self):
        open_tasks = []
        for task in self.tasks.values():
            if task.status == 'OPEN' and not task.is_part_of_bundle:
                open_tasks.append(task)
        return open_tasks

    def process_new_intelligence(self, detected_enemy, reporting_agent):
        enemy_id = detected_enemy.id
        if enemy_id in self.enemy_id_to_task_id:
            task_id = self.enemy_id_to_task_id[enemy_id]
            existing_task = self.tasks.get(task_id)
            if existing_task and reporting_agent.id not in existing_task.reporters:
                existing_task.add_reporter(reporting_agent.id)
        else:
            screen_width = 1600
            base_value = 1.0 + (detected_enemy.pos[0] / screen_width) * 2.0
            new_task = Task(position=detected_enemy.pos.copy(),
                            enemy_target_id=enemy_id,
                            reporting_agent_id=reporting_agent.id,
                            initial_value=base_value)
            self.tasks[new_task.id] = new_task
            self.enemy_id_to_task_id[enemy_id] = new_task.id
            self._attempt_to_bundle(new_task)

    def _attempt_to_bundle(self, new_task):
        if new_task.is_part_of_bundle: return
        max_dist_sq = self.market_config['TASK_BUNDLING_MAX_DIST'] ** 2
        max_time_diff = self.market_config['TASK_BUNDLING_MAX_TIME_DIFF']
        potential_partners = []
        for task in self.tasks.values():
            if (task.id == new_task.id or task.is_bundle or 
                task.status != 'OPEN' or task.is_part_of_bundle):
                continue
            dist_sq = np.sum((new_task.position - task.position)**2)
            time_diff = abs(new_task.creation_time - task.creation_time)
            if dist_sq < max_dist_sq and time_diff < max_time_diff:
                potential_partners.append(task)
        if potential_partners:
            tasks_to_bundle = [new_task] + potential_partners
            bundle = Task.create_bundle(tasks_to_bundle)
            self.tasks[bundle.id] = bundle

    def update_market_state(self, all_agents, battlefield_context):
        current_time = time.time()
        if current_time - self.last_value_update_time < self.market_config['VALUE_UPDATE_INTERVAL']:
            return

        red_team_id = 2
        enemy_map = {agent.id: agent for agent in all_agents if agent.team_id == red_team_id}
        
        tasks_to_remove = []
        for task_id, task in list(self.tasks.items()):
            
            # --- [FINAL FIX] This entire block is rewritten for robustness ---
            is_valid = True
            if task.is_bundle:
                # For bundles, update children and check their collective status
                living_sub_task_positions = []
                for sub_task in task.sub_tasks:
                    if sub_task.status != 'COMPLETED':
                        if sub_task.enemy_target_id in enemy_map:
                            # Update sub-task position and add to centroid calculation
                            sub_task.update_position(enemy_map[sub_task.enemy_target_id].pos.copy())
                            living_sub_task_positions.append(sub_task.position)
                        else:
                            # If enemy is gone, complete the sub-task
                            sub_task.complete()

                if not living_sub_task_positions: # No living targets left
                    task.complete()
                else:
                    # Update bundle's main position to the new centroid
                    task.update_position(np.mean(living_sub_task_positions, axis=0))

            else: # For single tasks
                if task.enemy_target_id not in enemy_map:
                    task.complete()
                else:
                    task.update_position(enemy_map[task.enemy_target_id].pos.copy())

            # Now, check the final status
            if task.status == 'COMPLETED':
                tasks_to_remove.append(task_id)
                if not task.is_bundle and task.enemy_target_id in self.enemy_id_to_task_id:
                     del self.enemy_id_to_task_id[task.enemy_target_id]
                continue

            # Dynamic value calculation (no changes here)
            time_since_update = current_time - task.last_update_time
            decay_multiplier = (1 - self.market_config['BASE_VALUE_DECAY_RATE']) ** (time_since_update / self.market_config['VALUE_UPDATE_INTERVAL'])
            reliability_bonus = 1.0 + (len(task.reporters) - 1) * self.market_config['RELIABILITY_BONUS']
            threat_bonus = 1.0 + (battlefield_context['screen_width'] - task.position[0]) / battlefield_context['screen_width'] * self.market_config['THREAT_VALUE_FACTOR']
            task.current_value = task.base_value * decay_multiplier * reliability_bonus * threat_bonus
            task.last_update_time = current_time

        for task_id in tasks_to_remove:
            if task_id in self.tasks:
                del self.tasks[task_id]
        self.last_value_update_time = current_time

    def run_auction(self, agents):
        open_tasks = self.get_open_tasks_for_auction()
        if not open_tasks or not agents: return
        available_agents = [agent for agent in agents if not agent.tour and agent.is_alive and agent.weapon_template]
        if not available_agents: return

        all_tasks_for_risk_assessment = list(self.tasks.values())
        for task in sorted(open_tasks, key=lambda t: t.current_value, reverse=True):
            if not available_agents: break
            bids = {}
            for agent in available_agents:
                bid_value = agent.calculate_bid_for_task(task, all_tasks_for_risk_assessment)
                if bid_value is not None: bids[agent.id] = bid_value
            if not bids: continue
            winner_id = min(bids, key=bids.get)
            winning_agent = next((agent for agent in available_agents if agent.id == winner_id), None)
            if winning_agent:
                task.assign_to(winner_id, bids[winner_id])
                winning_agent.add_task_to_tour(task)
                available_agents.remove(winning_agent)