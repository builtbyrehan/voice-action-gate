"""Fixture data the demo runs on. Real deployment would load this from the DB."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Entity:
    name: str
    kind: str
    aliases: tuple[str, ...] = ()   # ways a user might say it out loud


DATABASES = [
    Entity("customer_db", "database", ("customer database", "customer db", "main customer database")),
    Entity("customer_db_backup", "database", ("customer backup database", "backup database", "customer db backup")),
    Entity("customer_db_archive", "database", ("customer archive database", "archive database", "customer db archive")),
    Entity("orders_db", "database", ("orders database", "order database", "orders db")),
]

APPLICATIONS = [
    Entity("payments-service", "application", ("payments service", "payment service", "payments app")),
    Entity("web-frontend", "application", ("web frontend", "frontend app", "frontend service")),
    Entity("auth-service", "application", ("auth service", "authentication service", "auth app")),
]

ENVIRONMENTS = [
    Entity("development", "environment", ("dev", "dev environment", "development environment")),
    Entity("staging", "environment", ("staging environment", "stage")),
    Entity("production", "environment", ("prod", "prod environment", "production environment", "live")),
]

CATALOG: dict[str, list[Entity]] = {
    "database": DATABASES,
    "application": APPLICATIONS,
    "environment": ENVIRONMENTS,
}

# which action parameter maps to which entity kind
PARAM_KIND: dict[str, str] = {
    "database": "database",
    "application": "application",
    "environment": "environment",
}

# generic words that mean the user did NOT pick a specific entity
TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "database": ("database", "db"),
    "application": ("application", "app", "service"),
    "environment": ("environment",),
}