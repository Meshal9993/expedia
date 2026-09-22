"""Hotel-search business logic and its result contract."""

from dataclasses import asdict

from backend.controllers.database import DatabaseController


class SearchController:
    """Provide hotel-search business logic through DatabaseController."""

    def __init__(self, database: DatabaseController):
        self.database = database

    def search_hotels(self, name: str) -> dict[str, list[dict]]:
        query = name.strip()
        if not query:
            return {"results": []}
        return {
            "results": [
                asdict(stay) for stay in self.database.search_hotel_stays(query)
            ]
        }
