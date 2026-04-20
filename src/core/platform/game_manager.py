from typing import Dict, Optional, Type
from src.core.platform.base_game import AbstractGame

class GameManager:
    """
    Singleton-like manager for active game sessions across all chats.
    """
    
    def __init__(self):
        self.sessions: Dict[int, AbstractGame] = {}  # chat_id -> Game object

    def create_game(self, chat_id: int, game_class: Type[AbstractGame], thread_id: Optional[int] = None) -> AbstractGame:
        if chat_id in self.sessions:
            return self.sessions[chat_id]
        
        game = game_class(chat_id, thread_id)
        self.sessions[chat_id] = game
        return game

    def get_game(self, chat_id: int) -> Optional[AbstractGame]:
        return self.sessions.get(chat_id)

    def end_game(self, chat_id: int):
        if chat_id in self.sessions:
            del self.sessions[chat_id]

# Global instance
manager = GameManager()
