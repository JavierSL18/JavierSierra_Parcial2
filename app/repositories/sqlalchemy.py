from __future__ import annotations

from sqlalchemy import Column, Integer, String, func, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.models.entities import Ticket
from app.models.enums import TicketStatus
from app.repositories.base import TicketRepository


class Base(DeclarativeBase):
    """"""
class TicketORM(Base):
    

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")
    category = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    requester_id = Column(Integer, nullable=False)
    assignee_id = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default=TicketStatus.OPEN.value)


def build_sqlite_engine(url: str = "sqlite:///:memory:") -> Engine:
   
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def _to_domain(row: TicketORM) -> Ticket:
    return Ticket(
        id=row.id,
        title=row.title,
        description=row.description,
        category=row.category,
        priority=row.priority,
        requester_id=row.requester_id,
        status=TicketStatus(row.status),
        assignee_id=row.assignee_id,
    )


class SqlAlchemyTicketRepository(TicketRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, ticket: Ticket) -> Ticket:
        with self._session_factory() as session:
            row = TicketORM(
                id=ticket.id,
                title=ticket.title,
                description=ticket.description,
                category=ticket.category,
                priority=ticket.priority,
                requester_id=ticket.requester_id,
                assignee_id=ticket.assignee_id,
                status=TicketStatus(ticket.status).value,
            )
            session.add(row)
            session.commit()
            return _to_domain(row)

    def by_id(self, ticket_id: int) -> Ticket | None:
        with self._session_factory() as session:
            row = session.get(TicketORM, ticket_id)
            return _to_domain(row) if row is not None else None

    def list(
        self,
        status: TicketStatus | str | None = None,
        assignee_id: int | None = None,
        requester_id: int | None = None,
    ) -> list[Ticket]:
        with self._session_factory() as session:
            stmt = select(TicketORM)
            if status is not None:
                stmt = stmt.where(TicketORM.status == TicketStatus(status).value)
            if assignee_id is not None:
                stmt = stmt.where(TicketORM.assignee_id == assignee_id)
            if requester_id is not None:
                stmt = stmt.where(TicketORM.requester_id == requester_id)
            rows = session.execute(stmt).scalars().all()
            return [_to_domain(row) for row in rows]

    def next_id(self) -> int:
        with self._session_factory() as session:
            max_id = session.execute(select(func.max(TicketORM.id))).scalar()
            return (max_id or 0) + 1

    def count_by_status(self) -> dict[str, int]:
        
        with self._session_factory() as session:
            stmt = select(TicketORM.status, func.count()).group_by(TicketORM.status)
            rows = session.execute(stmt).all()
            return {status: count for status, count in rows}
