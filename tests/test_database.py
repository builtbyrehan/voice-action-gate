from app.db.database import Base, SessionLocal, engine
from app.db.models import Action, ActionParameter, Execution, Parameter, AuditLog


def test_database_schema_and_relationships():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        action = Action(
            name="test_action",
            description="Database schema test",
            risk_level="HIGH",
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        action_parameter = ActionParameter(
            action_id=action.id,
            name="environment",
            data_type="string",
            required=True,
        )
        db.add(action_parameter)
        db.commit()
        db.refresh(action_parameter)

        execution = Execution(
            action_id=action.id,
            session_id="test-session",
            status="BLOCKED",
            confirmation_required=True,
            confirmed=False,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        parameter = Parameter(
            execution_id=execution.id,
            action_parameter_id=action_parameter.id,
            value="production",
            source="AI_INFERENCE",
            quote="probably production",
            is_uncertain=True,
        )
        db.add(parameter)

        audit = AuditLog(
            execution_id=execution.id,
            event_type="GATE_DECISION",
            decision="BLOCKED",
            reason="Parameter was inferred by AI",
            details="High-risk actions require explicit user parameters.",
        )
        db.add(audit)
        db.commit()

        assert action.id is not None
        assert action_parameter.id is not None
        assert execution.id is not None
        assert parameter.id is not None
        assert audit.id is not None

    finally:
        db.close()


if __name__ == "__main__":
    print("Database test file ready.")
