class MappingMissingError(KeyError):
    """Raised when a required source path is missing in the input payload."""

    def __init__(self, source_path: str, dest_path: str):
        message = f"Missing source path '{source_path}' (for destination '{dest_path}')"
        super().__init__(message)
        self.source_path = source_path
        self.dest_path = dest_path


class InvalidDestinationPath(ValueError):
    """Raised when a destination path is invalid (e.g., contains an index)."""

    def __init__(self, dest_path: str):
        message = f"Invalid destination path (indices are not allowed): '{dest_path}'"
        super().__init__(message)
        self.dest_path = dest_path