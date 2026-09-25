from app.domain.errors import InvalidStatusTransitionError
from app.models.enums import TicketStatus


TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.OPEN: {TicketStatus.IN_PROGRESS, TicketStatus.CANCELLED},
    TicketStatus.IN_PROGRESS: {
        TicketStatus.OPEN,
        TicketStatus.RESOLVED,
        TicketStatus.CANCELLED,
    },
    TicketStatus.RESOLVED: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
    TicketStatus.CLOSED: set(),
    TicketStatus.CANCELLED: set(),
}


def can_transition(from_status: TicketStatus | str, to_status: TicketStatus | str) -> bool:
    current = TicketStatus(from_status)
    target = TicketStatus(to_status)
    return target in TRANSITIONS[current]


def assert_transition(from_status: TicketStatus | str, to_status: TicketStatus | str) -> None:
    current = TicketStatus(from_status)
    target = TicketStatus(to_status)
    if not can_transition(current, target):
        raise InvalidStatusTransitionError(current, target)
