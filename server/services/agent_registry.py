"""Agent Registry for Life Hub Assistant and future agents."""

from typing import Dict, List, Optional
from server.schemas import AgentDefinition

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentDefinition] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        self.register(
            AgentDefinition(
                id="notion",
                name="Life Hub Assistant",
                description="Manages and queries Andrei's Notion workspace (Calendar, Tasks, Notes, Health Log)",
                capabilities=["text", "voice", "image", "tools", "briefings"],
                status="available"
            )
        )

    def register(self, agent: AgentDefinition) -> None:
        self._agents[agent.id] = agent

    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[AgentDefinition]:
        return list(self._agents.values())

agent_registry = AgentRegistry()
