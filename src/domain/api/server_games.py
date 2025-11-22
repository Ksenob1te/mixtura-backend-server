from uuid import UUID
from fastapi_controllers import Controller, get, post, delete

class ServerGamesController(Controller):
    # Четкий префикс только для игр конкретного сервера
    prefix = "/{server_id}/games"
    tags = ["Server games"]

    @get("/")
    def list_server_games(self, server_id: UUID):
        """Получить список игр, привязанных к серверу"""
        pass

    @post("/")
    def add_game_to_server(self, server_id: UUID):
        """Привязать игру к серверу (для поиска)"""
        pass

    @delete("/{game_id}")
    def remove_game_from_server(self, server_id: UUID, game_id: UUID):
        """Отвязать игру"""
        pass