from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class GamePlayer(BaseModel):
    user_id: int
    full_name: str
    username: Optional[str] = None
    role: Optional[str] = None
    team: Optional[str] = None

class AbstractGame(ABC):
    """
    Interface for any Party Game on the platform.
    """
    
    def __init__(self, chat_id: int, thread_id: Optional[int] = None):
        self.chat_id = chat_id
        self.thread_id = thread_id
        self.players: Dict[int, GamePlayer] = {}
        self.status: str = "registration"  # registration, in_progress, finished
        self.metadata: Dict[str, Any] = {}

    @abstractmethod
    async def start(self) -> str:
        """Starts the game logic after registration."""
        pass

    @abstractmethod
    async def handle_callback(self, user_id: int, data: str) -> Dict[str, Any]:
        """Handles inline button clicks."""
        pass

    @abstractmethod
    async def handle_message(self, user_id: int, text: str) -> Dict[str, Any]:
        """Handles text messages from players."""
        pass

    @abstractmethod
    def get_status_message(self) -> str:
        """Returns a string representation of the current game state for the chat."""
        pass

    def add_player(self, player: GamePlayer) -> bool:
        if player.user_id not in self.players:
            self.players[player.user_id] = player
            return True
        return False

    def remove_player(self, user_id: int):
        if user_id in self.players:
            del self.players[user_id]
