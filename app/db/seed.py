from .database import Base, SessionLocal, engine
from .models import Action, ActionParameter


def create_database():
    Base.metadata.create_all(bind=engine)


def seed_actions():
    db = SessionLocal()

    try:
        if db.query(Action).count() > 0:
            return

        deploy = Action(
            name="deploy_application",
            description="Deploy an application to an environment",
            risk_level="HIGH",
        )

        delete_db = Action(
            name="delete_database",
            description="Delete a database from an environment",
            risk_level="HIGH",
        )

        transfer = Action(
            name="transfer_funds",
            description="Transfer simulated funds to a recipient",
            risk_level="HIGH",
        )

        db.add_all([deploy, delete_db, transfer])
        db.commit()

        db.refresh(deploy)
        db.refresh(delete_db)
        db.refresh(transfer)

        parameters = [
            ActionParameter(
                action_id=deploy.id,
                name="application",
                data_type="string",
                required=True,
            ),
            ActionParameter(
                action_id=deploy.id,
                name="version",
                data_type="string",
                required=True,
            ),
            ActionParameter(
                action_id=deploy.id,
                name="environment",
                data_type="string",
                required=True,
            ),
            ActionParameter(
                action_id=delete_db.id,
                name="database",
                data_type="string",
                required=True,
            ),
            ActionParameter(
                action_id=delete_db.id,
                name="environment",
                data_type="string",
                required=True,
            ),
            ActionParameter(
                action_id=transfer.id,
                name="amount",
                data_type="number",
                required=True,
            ),
            ActionParameter(
                action_id=transfer.id,
                name="currency",
                data_type="string",
                required=True,
            ),
            ActionParameter(
                action_id=transfer.id,
                name="recipient",
                data_type="string",
                required=True,
            ),
        ]

        db.add_all(parameters)
        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    create_database()
    seed_actions()
    print("Database created and seeded successfully.")
