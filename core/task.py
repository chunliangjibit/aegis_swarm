# Aegis Swarm 2.5 - Task Data Class
# This file defines the Task object, which represents a tradable entity in the marketplace.

import uuid
import numpy as np

class Task:
    """
    Represents a single task (e.g., target to be attacked) in the simulation.
    Tasks are treated as economic goods to be auctioned and traded among agents.
    """
    def __init__(self, position, value=1.0):
        """
        Initializes a new task.
        
        Args:
            position (np.array): The [x, y] coordinates of the task.
            value (float): The intrinsic value or reward for completing the task.
        """
        self.id = uuid.uuid4()
        self.position = np.array(position, dtype=float)
        self.value = float(value)
        
        # --- Market-related attributes ---
        self.status = 'OPEN'  # Can be 'OPEN' or 'ASSIGNED'
        self.assigned_agent_id = None
        self.winning_bid = float('inf')

    def assign_to(self, agent_id, winning_bid):
        """Assigns the task to an agent who won the bid."""
        self.status = 'ASSIGNED'
        self.assigned_agent_id = agent_id
        self.winning_bid = winning_bid

    def release(self):
        """Releases the task back to the market, making it available for auction again."""
        self.status = 'OPEN'
        self.assigned_agent_id = None
        self.winning_bid = float('inf')

    def __repr__(self):
        """Provides a developer-friendly string representation of the task."""
        return (f"Task(id={str(self.id)[-6:]}, pos={self.position}, "
                f"status={self.status}, assigned_to={str(self.assigned_agent_id)[-6:]})")