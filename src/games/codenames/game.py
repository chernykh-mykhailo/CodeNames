import asyncio
from typing import Dict, List, Optional
from src.core.platform.game_manager import manager
from src.core.platform.base_game import BaseGame, GamePlayer
from .engine import CodenamesEngine, Team
from .renderer import CodenamesRenderer
import io

class CodeNamesGame(BaseGame):
    def __init__(self, chat_id: int, thread_id: Optional[int] = None):
        super().__init__(chat_id, thread_id)
        self.engine: Optional[CodenamesEngine] = None
        self.renderer = CodenamesRenderer()
        self.language = "uk"
        self.word_set = "Standard"
        self.board_size = 5
        self.reg_timer = 120 # 2 mins
        self.turn_timer = 120 # 2 mins
        self.dark_mode = False
        self.button_board = False
        self.spymasters: Dict[Team, Optional[int]] = {Team.GREEN: None, Team.BLUE: None}
        self.metadata["mode"] = "Classic"

    async def start(self) -> str:
        # Load words from repository
        from .words import WordRepository
        repo = WordRepository()
        words = repo.get_words(self.word_set, self.language)
        
        mode = self.metadata.get("mode", "Classic").lower()
        self.engine = CodenamesEngine(words, mode=mode, size=self.board_size)
        self.status = "in_progress"
        
        # Assign roles
        self.assign_roles()
        
        from src.assets.texts import get_text
        t = get_text(self.language)
        return t.GAME_STARTED_MSG.format(desc=t.MODE_CLASSIC_DESC if mode == "classic" else t.MODE_DUET_DESC)

    def assign_roles(self):
        player_ids = list(self.players.keys())
        import random
        random.shuffle(player_ids)
        
        if self.metadata.get("mode") == "Duet":
            # Cooperative: 2 spymasters
            if len(player_ids) >= 2:
                self.spymasters[Team.GREEN] = player_ids[0]
                self.spymasters[Team.BLUE] = player_ids[1]
                self.players[player_ids[0]].role = "dual_spymaster"
                self.players[player_ids[1]].role = "dual_spymaster"
        else:
            # Teams
            half = len(player_ids) // 2
            red_players = player_ids[:half] # Keep variable name or change to green? User said "everywhere"
            blue_players = player_ids[half:]
            
            # Assign spymasters
            self.spymasters[Team.GREEN] = red_players[0]
            self.spymasters[Team.BLUE] = blue_players[0]
            
            for pid in red_players:
                self.players[pid].team = "green"
                self.players[pid].role = "spymaster" if pid == red_players[0] else "agent"
            for pid in blue_players:
                self.players[pid].team = "blue"
                self.players[pid].role = "spymaster" if pid == blue_players[0] else "agent"

    def get_board_image(self, spymaster_view: bool = False) -> io.BytesIO:
        state = self.engine.get_board_state(revealed_only=not spymaster_view)
        return self.renderer.render_board(state, self.board_size, dark_mode=self.dark_mode)

    async def start_reg_timer(self, bot):
        await asyncio.sleep(self.reg_timer)
        if self.status == "waiting":
            from src.assets.texts import get_text
            t = get_text(self.language)
            await bot.send_message(self.chat_id, t.REG_TIMEOUT, message_thread_id=self.thread_id)
            manager.end_game(self.chat_id)
