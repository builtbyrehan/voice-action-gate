from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from .database import Base


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    risk_level = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    parameters = relationship(
        "ActionParameter",
        back_populates="action",
        cascade="all, delete-orphan",
    )

    executions = relationship(
        "Execution",
        back_populates="action",
    )


class ActionParameter(Base):
    __tablename__ = "action_parameters"
    __table_args__ = (
        UniqueConstraint("action_id", "name", name="uq_action_parameter_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False)
    name = Column(String(100), nullable=False)
    data_type = Column(String(50), nullable=False)
    required = Column(Boolean, default=True, nullable=False)

    action = relationship("Action", back_populates="parameters")

    parameters = relationship(
        "Parameter",
        back_populates="action_parameter",
    )


class Execution(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False)
    session_id = Column(String(100), nullable=True)

    status = Column(String(50), nullable=False)

    confirmation_required = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    confirmed = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    executed_at = Column(DateTime, nullable=True)

    action = relationship("Action", back_populates="executions")

    parameters = relationship(
        "Parameter",
        back_populates="execution",
        cascade="all, delete-orphan",
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="execution",
        cascade="all, delete-orphan",
    )


class Parameter(Base):
    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), nullable=False)
    action_parameter_id = Column(
        Integer,
        ForeignKey("action_parameters.id"),
        nullable=False,
    )

    value = Column(Text, nullable=True)
    source = Column(String(50), nullable=False)
    quote = Column(Text, nullable=True)
    is_uncertain = Column(Boolean, default=False, nullable=False)

    execution = relationship("Execution", back_populates="parameters")

    action_parameter = relationship(
        "ActionParameter",
        back_populates="parameters",
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), nullable=True)

    event_type = Column(String(100), nullable=False)
    decision = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    details = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    execution = relationship("Execution", back_populates="audit_logs")
