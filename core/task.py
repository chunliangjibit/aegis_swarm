# Aegis Swarm 3.0 - Task Data Class (Patch 3.0.1)
# PATCH: Added `is_part_of_bundle` flag to prevent re-bundling bugs.

import uuid
import time
import numpy as np

class Task:
    def __init__(self, position, enemy_target_id, reporting_agent_id, initial_value=1.0):
        self.id = uuid.uuid4()
        self.creation_time = time.time()
        self.last_update_time = self.creation_time
        self.enemy_target_id = enemy_target_id
        self.position = np.array(position, dtype=float)
        self.base_value = float(initial_value)
        self.current_value = float(initial_value)
        self.reporters = {reporting_agent_id}
        self.status = 'OPEN'
        self.assigned_agent_id = None
        self.winning_bid = float('inf')
        self.is_bundle = False
        self.sub_tasks = []

        # --- [FIX] NEW FLAG ---
        # This flag is set to True when a single task is absorbed into a bundle.
        # This prevents it from being considered for other bundles.
        self.is_part_of_bundle = False

    def update_position(self, new_position):
        self.position = np.array(new_position, dtype=float)

    def add_reporter(self, agent_id):
        self.reporters.add(agent_id)

    def assign_to(self, agent_id, winning_bid):
        self.status = 'ASSIGNED'
        self.assigned_agent_id = agent_id
        self.winning_bid = winning_bid
        if self.is_bundle:
            for sub_task in self.sub_tasks:
                sub_task.status = 'ASSIGNED'
                sub_task.assigned_agent_id = agent_id

    def release(self):
        self.status = 'OPEN'
        self.assigned_agent_id = None
        self.winning_bid = float('inf')
        if self.is_bundle:
            for sub_task in self.sub_tasks:
                sub_task.release()
                
    def complete(self):
        self.status = 'COMPLETED'
        if self.is_bundle:
            for sub_task in self.sub_tasks:
                sub_task.complete()

    @staticmethod
    def create_bundle(tasks_to_bundle):
        if not tasks_to_bundle:
            return None
        
        bundle_position = np.mean([t.position for t in tasks_to_bundle], axis=0)
        first_task = tasks_to_bundle[0]
        bundle_task = Task(bundle_position, first_task.enemy_target_id, first_task.reporters.copy().pop())
        bundle_task.is_bundle = True
        
        # --- [FIX] Mark sub-tasks as claimed ---
        for task in tasks_to_bundle:
            task.is_part_of_bundle = True
        bundle_task.sub_tasks = tasks_to_bundle
        
        bundle_task.base_value = sum(t.base_value for t in tasks_to_bundle)
        bundle_task.current_value = sum(t.current_value for t in tasks_to_bundle)
        bundle_task.reporters = set.union(*[t.reporters for t in tasks_to_bundle])
        
        return bundle_task

    def __repr__(self):
        if self.is_bundle:
            return (f"BundleTask(id={str(self.id)[-6:]}, value={self.current_value:.2f}, "
                    f"sub_tasks={len(self.sub_tasks)}, status={self.status})")
        else:
            return (f"Task(id={str(self.id)[-6:]}, value={self.current_value:.2f}, "
                    f"target={str(self.enemy_target_id)[-6:]}, status={self.status})")