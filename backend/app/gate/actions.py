"""Action schemas (PRD section 22). Every executable action has a defined schema."""
from pydantic import BaseModel

from app.schemas import RiskLevel


class ActionDefinition(BaseModel):
    name: str
    description: str
    risk: RiskLevel
    required_params: list[str]
    requires_confirmation: bool = False


ACTIONS: dict[str, ActionDefinition] = {
    "DEPLOY_APPLICATION": ActionDefinition(
        name="DEPLOY_APPLICATION",
        description="Deploy an application version to an environment.",
        risk=RiskLevel.HIGH,
        required_params=["application", "version", "environment"],
        requires_confirmation=True,
    ),
    "DELETE_DATABASE": ActionDefinition(
        name="DELETE_DATABASE",
        description="Permanently delete a database in an environment.",
        risk=RiskLevel.HIGH,
        required_params=["database", "environment"],
        requires_confirmation=True,
    ),
    "TRANSFER_FUNDS": ActionDefinition(
        name="TRANSFER_FUNDS",
        description="Transfer simulated demo funds to a recipient.",
        risk=RiskLevel.HIGH,
        required_params=["amount", "currency", "recipient"],
        requires_confirmation=True,
    ),
}


def get_action(name: str | None) -> ActionDefinition | None:
    if not name:
        return None
    return ACTIONS.get(name.strip().upper())