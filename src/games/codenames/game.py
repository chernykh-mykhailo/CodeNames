from typing import Any, Dict, Optional
import io
import asyncio
from src.core.platform.base_game import AbstractGame
from src.games.codenames.engine import CodenamesEngine, Team
from src.games.codenames.renderer import BoardRenderer
from src.games.codenames.words import WordRepository
from src.assets.texts import get_text

class CodeNamesGame(AbstractGame):
    def __init__(self, chat_id: int, thread_id: Optional[int] = None):
        super().__init__(chat_id, thread_id)
        self.engine: Optional[CodenamesEngine] = None
        self.renderer = BoardRenderer()
        self.word_repo = WordRepository()
        self.spymasters: Dict[Team, int] = {} # team -> user_id
        self.language = "uk"
        self.word_set = "words_normal"
        self.reg_timer = 300 # 5 min default
        self.turn_timer = 120 # 2 min default
        self._timer_task: Optional[asyncio.Task] = None
        
    async def start(self) -> str:
        if len(self.players) < 2:
            return "❌ Необхідно мінімум 2 гравці!"
        
        mode = self.metadata.get("mode", "Classic")
        
        # Load words
        repo = WordRepository()
        words = repo.get_set(self.language, self.word_set)
        
        from src.games.codenames.engine import CodenamesEngine
        if mode == "Duet":
            # 15 Green agents for Duet
            self.engine = CodenamesEngine(words, mode="duet")
            self.current_turn = Team.BLUE # In Duet we can just use one team color
        else:
            self.engine = CodenamesEngine(words)
            self.current_turn = self.engine.current_turn
            
        self.status = "in_progress"
        
        p_list = list(self.players.values())
        
        if mode == "Duet":
            self.spymasters[Team.RED] = p_list[0].user_id
            self.spymasters[Team.BLUE] = p_list[1].user_id
            mode_desc = "👥 <b>Дует</b>: Кооперативний режим!"
        elif len(p_list) == 3:
            # Режим 3 гравці: 1 капітан на обидві команди
            spymaster = p_list[0]
            self.spymasters[Team.RED] = spymaster.user_id
            self.spymasters[Team.BLUE] = spymaster.user_id
            spymaster.role = "dual_spymaster"
            
            p_list[1].team = Team.RED.value
            p_list[1].role = "agent"
            p_list[2].team = Team.BLUE.value
            p_list[2].role = "agent"
            
            mode_desc = "👥 <b>Режим для 3 гравців</b>: Один зв'язківець на дві команди!"
        else:
            # Класичний режим 4+ гравців
            for i, p in enumerate(p_list):
                p.team = Team.RED.value if i % 2 == 0 else Team.BLUE.value
                p.role = "agent"
                
            # Assign spymasters
            self.spymasters[Team.RED] = p_list[0].user_id
            p_list[0].role = "spymaster"
            self.spymasters[Team.BLUE] = p_list[1].user_id
            p_list[1].role = "spymaster"
            mode_desc = "👥 Класичний командний режим."

        return f"🏁 Гру розпочато! {mode_desc}\nЗв'язківцям надіслано карти."

    async def handle_callback(self, user_id: int, data: str) -> Dict[str, Any]:
        if not self.engine:
            return {"text": "Гра ще не почалася"}
            
        if data.startswith("reveal_"):
            idx = int(data.split("_")[1])
            # Only current team leaders/operatives can reveal? 
            # Logic depends on session rules.
            self.engine.reveal_card(idx)
            return {"update_board": True}
        
        if data == "pass":
            self.engine.end_turn()
            return {"update_board": True}
            
        return {}

    async def handle_message(self, user_id: int, text: str) -> Dict[str, Any]:
        if not self.engine:
            return {}
            
        # Check if user is the current spymaster
        current_team = self.engine.current_turn
        if user_id == self.spymasters.get(current_team) and not self.engine.clue:
            # Try to parse clue: "word count"
            parts = text.split()
            if len(parts) >= 2 and parts[-1].isdigit():
                clue = " ".join(parts[:-1])
                count = int(parts[-1])
                self.engine.set_clue(clue, count)
                return {"clue_set": True, "clue": clue, "count": count}
                
        return {}

    def get_status_message(self) -> str:
        t = get_text(self.language)
        mode = self.metadata.get("mode", "Classic").lower()
        
        if self.status == "registration":
            return t.REGISTRATION_TITLE.format(count=len(self.players))
        
        if self.status == "finished":
            if mode == "duet":
                win_text = t.WIN_DUET if self.engine.winner == Team.BLUE else t.LOSE_DUET
            else:
                win_text = t.WIN_RED if self.engine.winner == Team.RED else t.WIN_BLUE
            return f"{t.GAME_OVER}\n{win_text}"

        # Active game status
        if mode == "duet":
            header = t.DUET_HEADER
            if self.engine.clue:
                body = t.CLUE_HINT.format(clue=self.engine.clue, count=self.engine.clue_count)
            else:
                body = t.SPYMASTER_WAIT # In duet we reuse spymaster wait
            return f"{header}\n{body}"
        else:
            team_name = t.TEAM_RED_GEN if self.current_turn == Team.RED else t.TEAM_BLUE_GEN
            header = t.CLASSIC_HEADER.format(team=team_name)
            if self.engine.clue:
                body = t.CLUE_HINT.format(clue=self.engine.clue, count=self.engine.clue_count)
                return f"{header}\n{body}\n\n{t.OPERATIVES_TURN}"
            else:
                return f"{header}\n{t.SPYMASTER_WAIT}"

    def get_board_image(self, spymaster_view: bool = False) -> io.BytesIO:
        state = self.engine.get_board_state(revealed_only=not spymaster_view)
        return self.renderer.render_board(state, spymaster_view=spymaster_view)

    def stop_timer(self):
        if self._timer_task:
            self._timer_task.cancel()
            self._timer_task = None

    async def _timer_loop(self, bot, message):
        """Background task for turn timeout"""
        await asyncio.sleep(self.turn_timer)
        if self.status == "in_progress":
            # Auto pass turn
            self.engine.end_turn()
            self.current_turn = self.engine.current_turn
            
            t = get_text(self.language)
            from src.bot.handlers.game_router import update_main_board
            try:
                await update_main_board(message, self, bot)
                await bot.send_message(
                    self.chat_id, 
                    t.TIME_UP, 
                    message_thread_id=self.thread_id
                )
                # Restart timer for next turn
                self.start_timer(bot, message)
            except Exception:
                pass

    def start_timer(self, bot, message):
        self.stop_timer()
        if self.turn_timer > 0 and self.status == "in_progress":
            self._timer_task = asyncio.create_task(self._timer_loop(bot, message))

    async def start_reg_timer(self, bot):
        """Timer for registration phase"""
        await asyncio.sleep(self.reg_timer)
        if self.status == "registration":
            t = get_text(self.language)
            from src.core.platform.game_manager import manager
            manager.end_game(self.chat_id)
            try:
                await bot.send_message(
                    self.chat_id, 
                    t.REG_TIMEOUT, 
                    message_thread_id=self.thread_id
                )
            except Exception:
                pass
