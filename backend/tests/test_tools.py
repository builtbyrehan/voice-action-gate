"""Tool registry tests — simulated tool execution (SR-7)."""
from app.schemas import ParamEvidence, ParamSource
from app.tools.registry import ToolRegistry


def test_delete_database():
    reg = ToolRegistry()
    evidence = [
        ParamEvidence(name="database", value="customer_db", source=ParamSource.USER_EXPLICIT),
        ParamEvidence(name="environment", value="production", source=ParamSource.USER_EXPLICIT),
    ]
    result = reg.execute("DELETE_DATABASE", evidence)
    assert result["status"] == "COMPLETED"
    assert result["result"]["simulated"] is True
    assert "customer_db@production" in result["result"]["deleted"]


def test_deploy_application():
    reg = ToolRegistry()
    evidence = [
        ParamEvidence(name="application", value="payments-service", source=ParamSource.USER_EXPLICIT),
        ParamEvidence(name="version", value="4.8.2", source=ParamSource.USER_EXPLICIT),
        ParamEvidence(name="environment", value="staging", source=ParamSource.USER_EXPLICIT),
    ]
    result = reg.execute("DEPLOY_APPLICATION", evidence)
    assert result["status"] == "COMPLETED"
    assert result["result"]["simulated"] is True
    assert "payments-service v4.8.2 -> staging" in result["result"]["deployed"]


def test_transfer_funds():
    reg = ToolRegistry()
    evidence = [
        ParamEvidence(name="amount", value="1000", source=ParamSource.USER_EXPLICIT),
        ParamEvidence(name="currency", value="USD", source=ParamSource.USER_EXPLICIT),
        ParamEvidence(name="recipient", value="alice", source=ParamSource.USER_EXPLICIT),
    ]
    result = reg.execute("TRANSFER_FUNDS", evidence)
    assert result["status"] == "COMPLETED"
    assert result["result"]["simulated"] is True
    assert "1000 USD to alice" in result["result"]["transferred"]


def test_unknown_action_fallback():
    reg = ToolRegistry()
    evidence = []
    result = reg.execute("SOME_UNKNOWN_ACTION", evidence)
    assert result["status"] == "COMPLETED"
    assert result["result"]["simulated"] is True
