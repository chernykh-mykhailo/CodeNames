from typing import Any, Dict, List, Optional
import io
from src.core.platform.base_game import AbstractGame, GamePlayer
from src.games.codenames.engine import CodenamesEngine, Team, CardColor
from src.games.codenames.renderer import BoardRenderer
from src.games.codenames.words import WordRepository

class CodeNamesGame(AbstractGame):
    def __init__(self, chat_id: int, thread_id: Optional[int] = None):
        super().__init__(chat_id, thread_id)
        self.engine: Optional[CodenamesEngine] = None
        self.renderer = BoardRenderer()
        self.word_repo = WordRepository()
        self.spymasters: Dict[Team, int] = {} # team -> user_id
        self.language = "uk"
        self.word_set = "words_normal"
        
    async def start(self) -> str:
        if len(self.players) < 3:
            return "❌ Потрібно мінімум 3 гравці для початку гри!"
        
        p_list = list(self.players.values())
        
        if len(p_list) == 3:
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

        self.engine = CodenamesEngine(self.word_repo.get_default_ua())
        self.status = "in_progress"
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
        if self.status == "registration":
            return f"📝 Реєстрація на Кодові Імена\nГравців: {len(self.players)}"
        
        if self.status == "in_progress":
            team_emoji = "🔴" if self.engine.current_turn == Team.RED else "🔵"
            team_name = "ЧЕРВОНИХ" if self.engine.current_turn == Team.RED else "СИНІХ"
            
            msg = f"{team_emoji} <b>Хід команди {team_name}</b>\n"
            
            if not self.engine.clue:
                # Turn for Spymaster
                uid = self.spymasters.get(self.engine.current_turn)
                player = self.players.get(uid)
                name = player.full_name if player else "Зв'язківець"
                msg += f"⏳ Чекаємо на підказку від зв'язківця: <a href='tg://user?id={uid}'>{name}</a>"
            else:
                # Turn for Operatives
                agents = [p.full_name for p in self.players.values() 
                          if p.team == self.engine.current_turn.value and p.role == "agent"]
                agents_str = ", ".join(agents) if agents else "усіх агентів"
                msg += f"🔍 Підказка: <b>{self.engine.clue}</b> ({self.engine.clue_count})\n"
                msg += f"🎯 <b>{agents_str}</b>, ваша черга обирати слова!"
                
            return msg
            
        if self.status == "finished":
            winner_emoji = "🔴" if self.engine.winner == Team.RED else "🔵"
            return f"🏆 Перемогла команда {winner_emoji} {self.engine.winner.value}!"
            
        return "..."

    def get_board_image(self, spymaster_view: bool = False) -> io.BytesIO:
        state = self.engine.get_board_state(revealed_only=not spymaster_view)
        return self.renderer.render_board(state, spymaster_view=spymaster_view)
