from app.models.entities import Ticket
from app.models.enums import TicketStatus
from app.repositories.sqlalchemy import (
    SqlAlchemyTicketRepository,
    build_session_factory,
    build_sqlite_engine,
)


def make_ticket(ticket_id, status):
    return Ticket(
        id=ticket_id,
        title=f"Ticket {ticket_id}",
        description="descripcion",
        category="General",
        priority="Low",
        requester_id=1,
        status=status,
    )


def test_count_by_status_reports_full_dictionary_after_commit_from_new_session():
    engine = build_sqlite_engine()
    session_factory = build_session_factory(engine)
    repo = SqlAlchemyTicketRepository(session_factory)

    repo.add(make_ticket(1, TicketStatus.OPEN))
    repo.add(make_ticket(2, TicketStatus.OPEN))
    repo.add(make_ticket(3, TicketStatus.IN_PROGRESS))

    # Sesión nueva sobre el mismo engine en memoria (StaticPool comparte la
    # base), tal como pide el ejercicio: consultar tras cerrar/commitear.
    fresh_session_factory = build_session_factory(engine)
    fresh_repo = SqlAlchemyTicketRepository(fresh_session_factory)

    counts = fresh_repo.count_by_status()

    assert counts == {"open": 2, "in_progress": 1}
    assert sum(counts.values()) == 3


def test_count_by_status_returns_empty_dict_when_there_are_no_tickets():
    # Base de prueba independiente: engine propio, sin datos.
    engine = build_sqlite_engine()
    session_factory = build_session_factory(engine)
    repo = SqlAlchemyTicketRepository(session_factory)

    assert repo.count_by_status() == {}


def test_repository_contract_add_by_id_and_list_still_work():
    engine = build_sqlite_engine()
    session_factory = build_session_factory(engine)
    repo = SqlAlchemyTicketRepository(session_factory)

    stored = repo.add(make_ticket(1, TicketStatus.OPEN))

    assert repo.by_id(1) is not None
    assert repo.by_id(1).status is TicketStatus.OPEN
    assert repo.by_id(999) is None
    assert repo.next_id() == 2
    assert [t.id for t in repo.list(status=TicketStatus.OPEN)] == [stored.id]
