from uuid import UUID
from fastapi_controllers import Controller, get, post, delete

from src.domain.models.games.request import GameAddRequest
from src.domain.models.games.response import GameResponse
from src.domain.models.response import StatusResponse

class ServerGameController(Controller):
    prefix = "/{server_id}/games"
    tags = ["Server game"]

    @get("/", response_model=list[GameResponse])
    def list_server_games(self, server_id: UUID): # TODO : User id depend
        pass

    @post("/", response_model=StatusResponse)
    def add_game_to_server(self, server_id: UUID, body: GameAddRequest): # TODO : User id depend
        # TODO : Member get depend
        pass

    @delete("/{game_id}", response_model=StatusResponse)
    def remove_game_from_server(self, server_id: UUID, game_id: UUID): # TODO : User id depend
        # TODO : Member get depend
        pass