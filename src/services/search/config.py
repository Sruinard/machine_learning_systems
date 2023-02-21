# configuration for search service

class SearchConfig:
    """Configuration for search service."""
    host: str = "localhost"
    port: int = 8080
    index: str = "ml_index"
    model: str = "ml_model"
    load_model_and_index: bool = False