"""Agent registry API routes."""

from typing import List
from fastapi import APIRouter, Depends
from server.dependencies import get_current_user
from server.models import User
from server.schemas import AgentDefinition
from server.services.agent_registry import agent_registry

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.get("", response_model=List[AgentDefinition])
async def list_agents(user: User = Depends(get_current_user)):
    """List available AI agents and capabilities."""
    return agent_registry.list_agents()
