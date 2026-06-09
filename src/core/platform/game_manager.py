import json
import logging
from typing import Dict, Optional, Type, Any
from src.core.platform.base_game import AbstractGame

logger = logging.getLogger(__name__)

# Redis key prefixes
GAME_KEY_PREFIX = "codenames:game:"
ACTIVE_GAMES_KEY = "codenames:active_games"

# Registry of game classes for deserialization
_GAME_CLASSES: Dict[str, Type[AbstractGame]] = {}


def register_game_class(name: str, cls: Type[AbstractGame]):
    """Register a game class so it can be deserialized from Redis."""
    _GAME_CLASSES[name] = cls


def _get_game_class_name(cls: Type[AbstractGame]) -> str:
    """Get a string identifier for a game class."""
    return f"{cls.__module__}.{cls.__name__}"


def _lookup_game_class(class_name: str) -> Optional[Type[AbstractGame]]:
    """Look up a game class by its full module path (e.g. src.games.codenames.game.CodeNamesGame)
    across all registered classes."""
    for name, cls in _GAME_CLASSES.items():
        if _get_game_class_name(cls) == class_name:
            return cls
    return None


class GameManager:
    """
    Singleton-like manager for active game sessions across all chats.
    Persists game sessions to Redis when available.
    """

    def __init__(self):
        self.sessions: Dict[int, AbstractGame] = {}  # chat_id -> Game object
        self._redis = None  # Redis connection, set via init_redis()

    def init_redis(self, redis_url: str):
        """Initialize Redis connection for persistence."""
        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
            logger.info("GameManager: Redis connection established for game persistence")
            self._load_sessions()
        except Exception as e:
            logger.warning(f"GameManager: Failed to connect to Redis: {e}. Using in-memory only.")
            self._redis = None

    def _load_sessions(self):
        """Load all active game sessions from Redis on startup."""
        if not self._redis:
            return

        try:
            chat_ids = self._redis.smembers(ACTIVE_GAMES_KEY)
            if not chat_ids:
                logger.info("GameManager: No active games in Redis")
                return

            loaded = 0
            for chat_id_str in chat_ids:
                try:
                    chat_id = int(chat_id_str)
                    key = f"{GAME_KEY_PREFIX}{chat_id}"
                    data = self._redis.get(key)
                    if data:
                        game_data = json.loads(data)
                        game_class_name = game_data.get("_game_class")
                        if game_class_name:
                            game_cls = _lookup_game_class(game_class_name)
                            if game_cls and hasattr(game_cls, 'from_dict'):
                                game = game_cls.from_dict(game_data)
                                self.sessions[chat_id] = game
                                loaded += 1
                                logger.info(f"GameManager: Restored game for chat {chat_id}")
                            else:
                                logger.warning(f"GameManager: No registered class found for {game_class_name}, removing stale entry")
                                self._redis.srem(ACTIVE_GAMES_KEY, chat_id_str)
                                self._redis.delete(key)
                        else:
                            # Missing _game_class marker, remove stale entry
                            self._redis.srem(ACTIVE_GAMES_KEY, chat_id_str)
                            self._redis.delete(key)
                    else:
                        # Data missing but key in set — remove stale entry
                        self._redis.srem(ACTIVE_GAMES_KEY, chat_id_str)
                        self._redis.delete(key)
                except Exception as e:
                    logger.error(f"GameManager: Failed to restore game {chat_id_str}: {e}")
                    # Clean up corrupted entry
                    try:
                        self._redis.srem(ACTIVE_GAMES_KEY, chat_id_str)
                        self._redis.delete(f"{GAME_KEY_PREFIX}{chat_id_str}")
                    except Exception:
                        pass

            logger.info(f"GameManager: Restored {loaded} games from Redis")
        except Exception as e:
            logger.error(f"GameManager: Error loading sessions from Redis: {e}")

    def create_game(self, chat_id: int, game_class: Type[AbstractGame], thread_id: Optional[int] = None) -> AbstractGame:
        if chat_id in self.sessions:
            return self.sessions[chat_id]

        game = game_class(chat_id, thread_id)
        self.sessions[chat_id] = game
        self._save_game(chat_id, game)
        return game

    def get_game(self, chat_id: int) -> Optional[AbstractGame]:
        return self.sessions.get(chat_id)

    def save_game(self, chat_id: int):
        """Save current game state to Redis. Call after any state mutation."""
        game = self.sessions.get(chat_id)
        if game:
            self._save_game(chat_id, game)

    def _save_game(self, chat_id: int, game: AbstractGame):
        """Persist a game to Redis."""
        if not self._redis:
            return

        try:
            if not hasattr(game, 'to_dict'):
                logger.warning(f"GameManager: Game class {type(game).__name__} has no to_dict method, skipping persistence")
                return

            game_data = game.to_dict()
            game_data["_game_class"] = _get_game_class_name(type(game))

            key = f"{GAME_KEY_PREFIX}{chat_id}"
            data = json.dumps(game_data, ensure_ascii=False)

            pipe = self._redis.pipeline()
            pipe.set(key, data)
            pipe.sadd(ACTIVE_GAMES_KEY, str(chat_id))
            pipe.execute()
        except Exception as e:
            logger.error(f"GameManager: Failed to save game {chat_id}: {e}")

    def end_game(self, chat_id: int):
        if chat_id in self.sessions:
            self.sessions[chat_id].cleanup()
            del self.sessions[chat_id]
            self._remove_game(chat_id)

    def _remove_game(self, chat_id: int):
        """Remove a game from Redis."""
        if not self._redis:
            return

        try:
            key = f"{GAME_KEY_PREFIX}{chat_id}"
            pipe = self._redis.pipeline()
            pipe.delete(key)
            pipe.srem(ACTIVE_GAMES_KEY, str(chat_id))
            pipe.execute()
        except Exception as e:
            logger.error(f"GameManager: Failed to remove game {chat_id} from Redis: {e}")


# Global instance
manager = GameManager()