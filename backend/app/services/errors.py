class DomainNotFoundError(Exception):
    def __init__(self, resource: str, identifier: str):
        super().__init__(f"{resource} '{identifier}' was not found.")


class DomainConflictError(Exception):
    pass


class DomainValidationError(Exception):
    pass
