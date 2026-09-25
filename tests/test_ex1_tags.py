import pytest

from app.domain.errors import ValidationError
from app.models.entities import Ticket


def make_ticket(ticket_id=1, requester_id=1):
    return Ticket(
        id=ticket_id,
        title="No puedo conectarme al WiFi",
        description="La red institucional no autentica",
        category="Network",
        priority="High",
        requester_id=requester_id,
    )


def test_add_tag_normalizes_and_avoids_duplicates():
    ticket = make_ticket()

    ticket.add_tag("  WiFi ")
    ticket.add_tag("wifi")  # duplicado tras normalizar
    ticket.add_tag("VPN")

    assert ticket.tags == ("wifi", "vpn")


def test_add_tag_rejects_blank_values():
    ticket = make_ticket()

    with pytest.raises(ValidationError):
        ticket.add_tag("   ")

    with pytest.raises(ValidationError):
        ticket.add_tag("")

    assert ticket.tags == ()


def test_tags_are_independent_between_tickets():
    first = make_ticket(ticket_id=1)
    second = make_ticket(ticket_id=2)

    first.add_tag("wifi")

    assert first.tags == ("wifi",)
    assert second.tags == ()


def test_tags_property_cannot_be_reassigned():
    ticket = make_ticket()

    with pytest.raises(AttributeError):
        ticket.tags = ["hack"]
