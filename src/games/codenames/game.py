from typing import Any, Dict, Optional
import io
import asyncio
from src.core.platform.base_game import AbstractGame, GamePlayer
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
        self.start_time: Optional[float] = None
        self._timer_task: Optional[asyncio.Task] = None
        self.registration_msg_id: Optional[int] = None
        self.board_msg_id: Optional[int] = None
        self.last_turn_msg_id: Optional[int] = None
        self.turn_lock = asyncio.Lock()
        
    def add_player(self, player: GamePlayer) -> bool:
        if player.user_id in self.players:
            return False
            
        if self.status == "in_progress":
            # Assign to team with fewer players
            red_count = len([p for p in self.players.values() if p.team == Team.RED.value])
            blue_count = len([p for p in self.players.values() if p.team == Team.BLUE.value])
            
            if red_count <= blue_count:
                player.team = Team.RED.value
            else:
                player.team = Team.BLUE.value
            player.role = "agent"
            
        self.players[player.user_id] = player
        return True

    async def start(self) -> str:
        t = get_text(self.language)
        if len(self.players) < 2:
            return t.MIN_PLAYERS
        
        # Smart mode detection
        mode = self.metadata.get("mode")
        player_count = len(self.players)
        
        # If no explicit mode or if mode is default 'Classic' but players are 2
        if not mode or (mode == "Classic" and player_count == 2):
            if player_count == 2:
                mode = "Duet"
            elif player_count == 3:
                mode = "Classic" # Will trigger 3p logic
            else:
                mode = "Classic"
        
        # Load words
        repo = WordRepository()
        words = repo.get_set(self.language, self.word_set)
        
        from src.games.codenames.engine import CodenamesEngine
        if mode == "Duet":
            # 15 Green agents for Duet
            self.engine = CodenamesEngine(words, mode="duet")
            self.current_turn = Team.RED # Red starts in Duet
        else:
            self.engine = CodenamesEngine(words)
            self.current_turn = self.engine.current_turn
            
        import time
        self.start_time = time.time()
        self.status = "in_progress"
        self.metadata["mode"] = mode # Store detected mode
        
        p_list = list(self.players.values())
        
        if mode == "Duet":
            self.spymasters[Team.RED] = p_list[0].user_id
            self.spymasters[Team.BLUE] = p_list[1].user_id
            mode_desc = t.MODE_DUET_DESC
        elif len(p_list) == 3:
            # 3-player mode: 1 spymaster for both teams
            spymaster = p_list[0]
            self.spymasters[Team.RED] = spymaster.user_id
            self.spymasters[Team.BLUE] = spymaster.user_id
            spymaster.role = "dual_spymaster"
            
            p_list[1].team = Team.RED.value
            p_list[1].role = "agent"
            p_list[2].team = Team.BLUE.value
            p_list[2].role = "agent"
            
            mode_desc = t.MODE_3P_DESC
        else:
            # Classic mode for 4+ players
            for i, p in enumerate(p_list):
                p.team = Team.RED.value if i % 2 == 0 else Team.BLUE.value
                p.role = "agent"
                
            # Assign spymasters
            self.spymasters[Team.RED] = p_list[0].user_id
            p_list[0].role = "spymaster"
            self.spymasters[Team.BLUE] = p_list[1].user_id
            p_list[1].role = "spymaster"
            mode_desc = t.MODE_CLASSIC_DESC

        return t.GAME_STARTED_MSG.format(desc=mode_desc)

    async def handle_callback(self, user_id: int, data: str) -> Dict[str, Any]:
        if not self.engine:
            t = get_text(self.language)
            return {"text": t.GAME_NOT_FOUND}
            
        if data.startswith("reveal_"):
            idx = int(data.split("_")[1])
            self.engine.reveal_card(idx)
            self.current_turn = self.engine.current_turn # Sync turn
            return {"update_board": True}
        
        if data == "pass":
            self.engine.end_turn()
            self.current_turn = self.engine.current_turn # Sync turn
            return {"update_board": True}
            
        return {}

    async def handle_message(self, user_id: int, text: str) -> Dict[str, Any]:
        if not self.engine:
            return {}
            
        t = get_text(self.language)
        # Clean up the emoji if present (from inline query)
        text = text.replace("💡", "").strip()
        
        # Check if user is a spymaster for the current turn
        current_team = self.engine.current_turn
        is_spymaster = user_id == self.spymasters.get(current_team)
        
        # If it's a hint (word count)
        parts = text.split()
        if len(parts) >= 2 and parts[-1].isdigit():
            if not is_spymaster:
                # Get the name of current spymaster
                spy_id = self.spymasters.get(current_team)
                spy_name = self.players[spy_id].full_name if spy_id in self.players else "???"
                return {"error": t.DUET_TURN_MSG.format(name=spy_name)}
                
            if self.engine.clue:
                # Already have a clue, spymaster can't give another one yet
                return {}

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
            current_spy_id = self.spymasters.get(self.current_turn)
            spy_name = self.players[current_spy_id].full_name if current_spy_id in self.players else "???"
            
            if self.engine.clue:
                body = t.CLUE_HINT.format(clue=self.engine.clue, count=self.engine.clue_count)
                return f"{header}\n{body}\n\n{t.OPERATIVES_TURN}"
            else:
                body = t.DUET_TURN_MSG.format(name=spy_name)
                return f"{header}\n{body}"
        else:
            team_name = t.TEAM_RED_GEN if self.current_turn == Team.RED else t.TEAM_BLUE_GEN
            header = t.CLASSIC_HEADER.format(team=team_name)
            if self.engine.clue:
                body = t.CLUE_HINT.format(clue=self.engine.clue, count=self.engine.clue_count)
                return f"{header}\n{body}\n\n{t.OPERATIVES_TURN}"
            else:
                return f"{header}\n{t.SPYMASTER_WAIT}"

    def get_board_image(self, spymaster_view: bool = False, duet_side: Optional[str] = None) -> io.BytesIO:
        state = self.engine.get_board_state(revealed_only=not spymaster_view, side=duet_side)
        return self.renderer.render_board(state, spymaster_view=spymaster_view)

    def cleanup(self):
        """Stop background tasks when game ends"""
        self.stop_timer()
        self.status = "finished"

    def stop_timer(self):
        if self._timer_task:
            self._timer_task.cancel()
            self._timer_task = None

    async def _timer_loop(self, bot, message):
        """Background task for turn timeout with dynamic countdown"""
        remaining = self.turn_timer
        from src.bot.handlers.game_router import update_turn_notification
        
        while remaining > 0:
            if self.status != "in_progress":
                return

            # Determine sleep interval
            if remaining > 60:
                sleep_for = remaining - 60
            elif remaining > 10:
                sleep_for = 10 if remaining % 10 == 0 else remaining % 10
            elif remaining > 5:
                sleep_for = remaining - 5
            else:
                sleep_for = 1

            await asyncio.sleep(sleep_for)
            remaining -= sleep_for
            
            # Update notification if needed
            if remaining >= 0 and self.status == "in_progress":
                await update_turn_notification(self.chat_id, self, bot, remaining)

        if self.status == "in_progress":
            prev_turn = self.engine.current_turn
            # Auto pass turn
            self.engine.end_turn()
            self.current_turn = self.engine.current_turn
            
            t = get_text(self.language)
            from src.bot.handlers.game_router import update_main_board
            try:
                await update_main_board(message, self, bot, prev_turn=prev_turn)
                await bot.send_message(
                    self.chat_id, 
                    t.TIME_UP, 
                    message_thread_id=self.thread_id
                )
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
