"""Base agent class for all agents."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    
    Agents are specialized workers that perform specific tasks,
    such as data generation, validation, or transformation.
    """

    def __init__(self, agent_id: str = None):
        """
        Initialize base agent.

        Args:
            agent_id: Unique agent identifier
        """
        self.agent_id = agent_id or self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """
        Execute the agent's primary task.

        Must be implemented by subclasses.

        Returns:
            Task result
        """
        pass

    async def pre_execute(self):
        """Hook called before execute."""
        self.logger.debug(f"Agent {self.agent_id} pre-execution")

    async def post_execute(self, result: Any):
        """Hook called after execute."""
        self.logger.debug(f"Agent {self.agent_id} post-execution")

    async def on_error(self, error: Exception):
        """Hook called on execution error."""
        self.logger.error(
            f"Agent {self.agent_id} error: {str(error)}", exc_info=True
        )

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "agent_id": self.agent_id,
            "type": self.__class__.__name__,
        }
