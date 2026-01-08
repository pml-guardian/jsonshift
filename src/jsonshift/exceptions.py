class MappingMissingError(KeyError):
    def __init__(self, source_path: str, dest_path: str):
        super().__init__(
            f"Missing source path '{source_path}' (for destination '{dest_path}')"
        )
        self.source_path = source_path
        self.dest_path = dest_path