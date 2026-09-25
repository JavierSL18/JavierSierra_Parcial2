import pytest

from app.domain.errors import DuplicateAssignmentError
from app.services.notifications import WebhookNotifier
from app.services.tickets import TicketService
from tests.conftest import create_ticket


def test_reassigning_same_technician_raises_without_side_effects(world):
    ticket = create_ticket(world.tickets, requester=world.requester)
    world.tickets.assign(ticket.id, technician_id=world.technician.id)

    history_len_before = len(ticket.history)
    notifications_before = len(world.notifier.sent)

    with pytest.raises(DuplicateAssignmentError) as error:
        world.tickets.assign(ticket.id, technician_id=world.technician.id)

    assert error.value.code == "duplicate_assignment"
    assert error.value.properties["ticket_id"] == ticket.id
    assert error.value.properties["technician_id"] == world.technician.id
    # no se agregó historial ni notificaciones nuevas
    assert len(ticket.history) == history_len_before
    assert len(world.notifier.sent) == notifications_before


def test_webhook_notifier_stores_payload_without_http_or_print(ticket_repository, users):
    webhook = WebhookNotifier(endpoint="https://hooks.test/helpdesk")
    service = TicketService(ticket_repository, users, notifier=webhook)
    requester = users.by_email("sofia@school.edu")
    technician = users.by_email("tomas@school.edu")

    ticket = create_ticket(service, requester=requester)
    service.assign(ticket.id, technician_id=technician.id)

    assert len(webhook.sent_payloads) == 2  # ticket_created + ticket_assigned
    last_payload = webhook.sent_payloads[-1]
    assert last_payload["endpoint"] == "https://hooks.test/helpdesk"
    assert last_payload["user_id"] == technician.id
    assert last_payload["title"] == "ticket_assigned"
    assert last_payload["message"] == f"Ticket #{ticket.id} was assigned to you"


def test_valid_assignment_still_works_and_notifies(world):
    ticket = create_ticket(world.tickets, requester=world.requester)

    assigned = world.tickets.assign(ticket.id, technician_id=world.technician.id)

    assert assigned.assignee_id == world.technician.id
    assert assigned.history[-1].event_type == "assigned"
    assert world.notifier.sent[-1].title == "ticket_assigned"
