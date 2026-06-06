import asyncio
from typing import Dict, Optional, Any
from src.core.platform.game_manager import manager
from src.core.platform.base_game import BaseGame
from .engine import CodenamesEngine, Team
from .renderer import CodenamesRenderer
import io

class CodeNamesGame(BaseGame):
    def __init__(self, chat_id: int, thread_id: Optional[int] = None):
        super().__init__(chat_id, thread_id)
        self.engine: Optional[CodenamesEngine] = None
        self.renderer = CodenamesRenderer()
        self.language = "uk"
        self.word_set = "words_normal"
        self.board_size = 5
        self.reg_timer = 120 # 2 mins
        self.turn_timer = 120 # 2 mins
        self.dark_mode = False
        self.button_board = False
        self.spymasters: Dict[Team, Optional[int]] = {Team.GREEN: None, Team.RED: None}
        self.metadata["mode"] = "Classic"

    async def start(self) -> str:
        player_count = len(self.players)
        if self.metadata.get("mode") != "Hardcore":
            if player_count == 2:
                self.metadata["mode"] = "Duet"
            elif player_count == 3:
                self.metadata["mode"] = "3p"

        # Load words from repository
        from .words import WordRepository
        repo = WordRepository()
        words = repo.get_set(self.language, self.word_set)
        if not words:
            words = repo.get_set("uk", "words_normal")
        
        mode = self.metadata.get("mode", "Classic").lower()
        self.engine = CodenamesEngine(words, mode=mode, size=self.board_size)
        self.status = "in_progress"
        
        # Assign roles
        self.assign_roles()
        
        from src.assets.texts import get_text
        t = get_text(self.language)
        if mode == "duet":
            desc = t.MODE_DUET_DESC
        elif mode == "3p":
            desc = t.MODE_3P_DESC
        elif mode == "hardcore":
            desc = "💀 <b>Хардкор режим!</b> Будь-яка помилка (крім ворожої картки) — це Вбивця!" if self.language == "uk" else "💀 <b>Hardcore Mode!</b> Any mistake (except opponent cards) is an Assassin!"
        else:
            desc = t.MODE_CLASSIC_DESC
        
        # Build team list to display at start
        teams_info = []
        if mode == "duet":
            spymasters_list = []
            for team, pid in self.spymasters.items():
                if pid and pid in self.players:
                    spymasters_list.append(self.players[pid].full_name)
            teams_info.append(f"👥 Гравці: {', '.join(spymasters_list)}")
        else:
            green_team = []
            red_team = []
            for pid, p in self.players.items():
                if p.team == "green":
                    role_suffix = " (Капітан)" if p.role == "spymaster" or p.role == "dual_spymaster" else ""
                    green_team.append(f"{p.full_name}{role_suffix}")
                elif p.team == "red":
                    role_suffix = " (Капітан)" if p.role == "spymaster" or p.role == "dual_spymaster" else ""
                    red_team.append(f"{p.full_name}{role_suffix}")
            
            # Shared spymaster in 3p
            if mode == "3p":
                sm_id = self.spymasters[Team.GREEN]
                sm_name = self.players[sm_id].full_name if sm_id in self.players else "Капітан"
                teams_info.append(f"👨‍✈️ Спільний Капітан: <b>{sm_name}</b>")
                
                # Filter out the shared spymaster from the green/red team list display
                green_team = [name for name in green_team if "(Капітан)" not in name]
                red_team = [name for name in red_team if "(Капітан)" not in name]
            
            teams_info.append(f"🟢 Зелена команда: {', '.join(green_team) if green_team else 'немає'}")
            teams_info.append(f"🔴 Червона команда: {', '.join(red_team) if red_team else 'немає'}")
            
        teams_str = "\n".join(teams_info)
        
        status = self.get_status_message()
        return f"{t.GAME_STARTED_MSG.format(desc=desc)}\n\n{teams_str}\n\n{status}"

    def assign_roles(self):
        player_ids = list(self.players.keys())
        import random
        random.shuffle(player_ids)
        
        mode = self.metadata.get("mode", "Classic").lower()
        
        if mode == "duet":
            # Cooperative: 2 spymasters
            if len(player_ids) >= 2:
                self.spymasters[Team.GREEN] = player_ids[0]
                self.spymasters[Team.RED] = player_ids[1]
                self.players[player_ids[0]].role = "dual_spymaster"
                self.players[player_ids[0]].team = "green"
                self.players[player_ids[1]].role = "dual_spymaster"
                self.players[player_ids[1]].team = "red"
        elif mode == "3p" and len(player_ids) >= 3:
            # 3 Player mode: 1 shared spymaster, 2 agents (1 green, 1 red)
            self.spymasters[Team.GREEN] = player_ids[0]
            self.spymasters[Team.RED] = player_ids[0]
            self.players[player_ids[0]].role = "dual_spymaster"
            
            self.players[player_ids[1]].team = "green"
            self.players[player_ids[1]].role = "agent"
            self.players[player_ids[2]].team = "red"
            self.players[player_ids[2]].role = "agent"
        else:
            # Teams
            half = len(player_ids) // 2
            green_players = player_ids[:half]
            red_players = player_ids[half:]
            
            # Assign spymasters
            if green_players:
                self.spymasters[Team.GREEN] = green_players[0]
            if red_players:
                self.spymasters[Team.RED] = red_players[0]
            
            # Agents
            for pid in green_players:
                self.players[pid].team = "green"
                self.players[pid].role = "spymaster" if pid == green_players[0] else "agent"
            for pid in red_players:
                self.players[pid].team = "red"
                self.players[pid].role = "spymaster" if pid == red_players[0] else "agent"

    async def get_board_image(self, spymaster_view: bool = False, side: Optional[str] = None) -> io.BytesIO:
        from src.core.database.service import db_service
        light_colors = await db_service.get_system_setting("theme_colors_light")
        dark_colors = await db_service.get_system_setting("theme_colors_dark")
        self.renderer.set_custom_colors(light_colors, dark_colors)
        
        if not self.engine:
            return io.BytesIO()
        state = self.engine.get_board_state(revealed_only=not spymaster_view, side=side)
        return self.renderer.render_board(state, spymaster_view=spymaster_view, dark_mode=self.dark_mode)

    async def start_reg_timer(self, bot):
        await asyncio.sleep(self.reg_timer)
        if self.status == "waiting":
            from src.assets.texts import get_text
            t = get_text(self.language)
            await bot.send_message(self.chat_id, t.REG_TIMEOUT, message_thread_id=self.thread_id)
            manager.end_game(self.chat_id)

    async def handle_callback(self, user_id: int, data: str) -> Dict[str, Any]:
        """Handles inline button clicks."""
        return {}

    async def handle_message(self, user_id: int, text: str) -> Dict[str, Any]:
        """Handles text messages from players."""
        return {}

    def get_status_message(self) -> str:
        """Returns a string representation of the current game state for the chat."""
        if not self.engine:
            return f"Status: {self.status}"
            
        from src.assets.texts import get_text
        from .engine import Team, CardColor
        t = get_text(self.language)
        
        lines = []
        
        if self.engine.clue:
            # Guessing phase
            lines.append(f"🔎 Підказка: <b>{self.engine.clue.upper()} ({self.engine.clue_count})</b>")
            lines.append(f"🤔 Спроб залишилось: <b>{self.engine.remaining_guesses}</b>")
            
            if self.engine.mode == "duet":
                guesser_team = Team.RED if self.engine.current_turn == Team.GREEN else Team.GREEN
                guesser_id = self.spymasters.get(guesser_team)
                guesser_mention = self.players[guesser_id].mention if guesser_id in self.players else "Напарник"
                lines.append(f"👉 Обирає слово: {guesser_mention}")
            else:
                current_team_str = "green" if self.engine.current_turn == Team.GREEN else "red"
                team_agents = [p.mention for p in self.players.values() if p.team == current_team_str and p.role == "agent"]
                if team_agents:
                    agents_str = ", ".join(team_agents)
                    lines.append(f"👉 Обирає слово: {agents_str}")
                else:
                    team_color_name = "Зелені" if self.engine.current_turn == Team.GREEN else "Червоні"
                    lines.append(f"👉 Обирають слово: <b>{team_color_name}</b>")
        else:
            # Clue giving phase
            if self.engine.mode == "duet":
                giver_id = self.spymasters.get(self.engine.current_turn)
                giver_mention = self.players[giver_id].mention if giver_id in self.players else "Капітан"
                lines.append(f"👉 Дає підказку: {giver_mention}")
            else:
                spymaster_id = self.spymasters.get(self.engine.current_turn)
                team_color_name = "🟢 Зелених" if self.engine.current_turn == Team.GREEN else "🔴 Червоних"
                if self.language != "uk":
                    team_color_name = "🟢 Green" if self.engine.current_turn == Team.GREEN else "🔴 Red"
                
                current_team_str = "green" if self.engine.current_turn == Team.GREEN else "red"
                team_agents = [p.full_name for p in self.players.values() if p.team == current_team_str and p.role == "agent"]
                agents_suffix = f" — відгадують: {', '.join(team_agents)}" if team_agents else ""
                
                if spymaster_id and spymaster_id in self.players:
                    sm_mention = self.players[spymaster_id].mention
                    lines.append(f"👉 Дає підказку: {sm_mention} (для {team_color_name}{agents_suffix})")
                else:
                    lines.append(f"👉 Дає підказку: <b>Капітан {team_color_name}</b>{agents_suffix}")
            
        found = 0
        total_to_find = 0
        if self.engine.mode == "duet":
            total_to_find = 15
            for i in range(len(self.engine.board)):
                if self.engine.board[i].is_revealed:
                    ca = self.engine.get_duet_color(i, "a")
                    cb = self.engine.get_duet_color(i, "b")
                    if ca == CardColor.GREEN or cb == CardColor.GREEN:
                        found += 1
        else:
            total_to_find = (self.board_size * self.board_size // 3) + 1
            found = sum(1 for c in self.engine.board if c.is_revealed and c.color.value == self.engine.current_turn.value)

        stats_text = f"🔎 Відгадано: <b>{found}/{total_to_find}</b>"
        lines.append("")
        lines.append(stats_text)
        
        status_text = "\n".join(lines)
        if self.metadata.get("show_past_clues", True) and self.engine.clues_history:
            formatted = []
            for item in self.engine.clues_history:
                team_emoji = "🟢" if item["team"] == "green" else "🔴"
                formatted.append(f"{team_emoji} {item['clue'].upper()} ({item['count']})")
            history_str = ", ".join(formatted)
            if self.language == "uk":
                status_text += f"\n\n<tg-spoiler>📜 Минулі загадки: {history_str}</tg-spoiler>"
            else:
                status_text += f"\n\n<tg-spoiler>📜 Past clues: {history_str}</tg-spoiler>"
                
        return status_text
