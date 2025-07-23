# Aegis Swarm 2.5 - Marketplace Module
# DECISIVE FIX v4: Reverted auction to MIN COST to ensure offensive behavior.

import numpy as np
from core.task import Task

class Marketplace:
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        if isinstance(task, Task): self.tasks.append(task)
        else: print(f"Warning: Attempted to add a non-Task object: {task}")

    def add_tasks(self, task_list):
        for task in task_list: self.add_task(task)

    def get_open_tasks(self):
        return [task for task in self.tasks if task.status == 'OPEN']

    def run_auction(self, agents):
        open_tasks = self.get_open_tasks()
        if not open_tasks or not agents: return {}

        available_agents = [agent for agent in agents if not agent.tour and agent.is_alive and agent.weapon_template]
        if not available_agents: return {}

        for task in open_tasks:
            bids = {} # Stores {agent_id: cost_value}
            
            for agent in available_agents:
                bid_value = agent.calculate_bid_for_task(task)
                bids[agent.id] = bid_value
            
            if not bids: continue

            # *** CRITICAL CHANGE: Award task to the agent with the LOWEST cost ***
            winner_id = min(bids, key=bids.get)
            winning_bid = bids[winner_id] # This is the cost

            winning_agent = next((agent for agent in available_agents if agent.id == winner_id), None)
            if winning_agent:
                task.assign_to(winner_id, winning_bid)
                winning_agent.add_task_to_tour(task)
                available_agents.remove(winning_agent)
                if not available_agents: break
        
        return {}

    def get_all_tasks(self):
        return self.tasks