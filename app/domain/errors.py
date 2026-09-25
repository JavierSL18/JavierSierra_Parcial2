class DomainError(Exception):

    code = "domain_error"

    def __init__(self, message: str | None = None, **properties: object) -> None:
        self.properties = properties
        super().__init__(message or self.code)


class ValidationError(DomainError):

    code = "validation_error"

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        **properties: object,
    ) -> None:
        if field is not None:
            properties = {"field": field, **properties}
        super().__init__(message, **properties)


class NotFoundError(DomainError):

    code = "not_found"

    def __init__(self, resource: str, identifier: object) -> None:
        super().__init__(
            f"{resource} {identifier} was not found",
            resource=resource,
            identifier=identifier,
        )


class TicketNotFoundError(NotFoundError):

    code = "ticket_not_found"

    def __init__(self, ticket_id: int) -> None:
        DomainError.__init__(
            self,
            f"Ticket {ticket_id} was not found",
            ticket_id=ticket_id,
        )


class UserNotFoundError(NotFoundError):

    code = "user_not_found"

    def __init__(self, user_id: int) -> None:
        DomainError.__init__(
            self,
            f"User {user_id} was not found",
            user_id=user_id,
        )


class PermissionDeniedError(DomainError):

    code = "permission_denied"


class InvalidStatusTransitionError(ValidationError):

    code = "invalid_status_transition"

    def __init__(self, from_status: object, to_status: object) -> None:
        from_value = getattr(from_status, "value", from_status)
        to_value = getattr(to_status, "value", to_status)
        super().__init__(
            f"Cannot transition ticket from {from_value} to {to_value}",
            from_status=str(from_value),
            to_status=str(to_value),
        )


class DuplicateAssignmentError(DomainError):

    code = "duplicate_assignment"

    def __init__(self, ticket_id: int, technician_id: int) -> None:
        super().__init__(
            f"Ticket {ticket_id} is already assigned to technician {technician_id}",
            ticket_id=ticket_id,
            technician_id=technician_id,
        )
