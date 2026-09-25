import pytest

from app.domain.errors import TicketNotFoundError
from tests.conftest import create_ticket


def test_watchers_returns_only_requester_when_unassigned(world):
    ticket = create_ticket(world.tickets, requester=world.requester)

    watchers = world.tickets.watchers(ticket.id)

    assert [u.id for u in watchers] == [world.requester.id]


def test_watchers_returns_requester_and_distinct_technician(world):
    ticket = create_ticket(world.tickets, requester=world.requester)
    world.tickets.assign(ticket.id, technician_id=world.technician.id)

    watchers = world.tickets.watchers(ticket.id)

    assert {u.id for u in watchers} == {world.requester.id, world.technician.id}
    assert len(watchers) == 2


def test_watchers_propagates_ticket_not_found(world):
    with pytest.raises(TicketNotFoundError):
        world.tickets.watchers(999)


def test_watchers_deduplicates_when_requester_is_also_technician(world, users):
    # Escenario de control: un usuario que actúa como solicitante y además
    # queda registrado como su propio técnico asignado no debe duplicarse.
    dual_role_user = world.technician  # ya es staff (technician)
    ticket = world.tickets.create(
        title="Revisar mi propio equipo",
        description="Autoasignación de prueba",
        category="Hardware",
        priority="Low",
        requester=dual_role_user,
    )
    world.tickets.assign(ticket.id, technician_id=dual_role_user.id)

    watchers = world.tickets.watchers(ticket.id)

    assert [u.id for u in watchers] == [dual_role_user.id]
