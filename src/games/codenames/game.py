import asyncio
from typing import Dict, Optional, Any, TYPE_CHECKING
from src.core.platform.game_manager import manager
from src.core.platform.base_game import BaseGame
from .engine import CodenamesEngine, Team
from .renderer import CodenamesRenderer
from src.core.database.service import db_service
import io

if TYPE_CHECKING:
    from aiogram import Bot

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
            elif player_count == 1:
                # For solo play, force duet mode so auto-bot can give clues
                # and human player can guess words
                self.metadata["mode"] = "Duet"

        # Load chat settings for auto-bot
        chat_settings = await db_service.get_chat_settings(self.chat_id)
        self.metadata["auto_bot_enabled"] = chat_settings.auto_bot_enabled
        self.metadata["auto_bot_difficulty"] = chat_settings.auto_bot_difficulty

        # Load words from repository
        from .words import WordRepository
        repo = WordRepository()
        words = repo.get_set(self.language, self.word_set)
        if not words:
            words = repo.get_set("uk", "words_normal")
        
        mode = self.metadata.get("mode", "Classic").lower()
        self.engine = CodenamesEngine(words, mode=mode, size=self.board_size)
        self.status = "in_progress"
        
        # Pre-fetch captain buff data for all players
        avoid_ready = set()
        become_ready = set()
        for pid in self.players:
            flags = await db_service.get_user_captain_buff_flags(pid)
            if flags.get("avoid_captain_ready"):
                avoid_ready.add(pid)
            if flags.get("become_captain_ready"):
                become_ready.add(pid)
        
        # Store in metadata for assign_roles to read
        self.metadata["captain_avoid_players"] = list(avoid_ready)
        self.metadata["captain_become_players"] = list(become_ready)
        
        # Assign roles (reads from metadata)
        self.assign_roles()
        
        # After role assignment: consume triggered buffs and build notification text
        captain_buff_notifications = []
        
        # Spymaster IDs after assignment
        sm_ids = set()
        for sm_id in self.spymasters.values():
            if sm_id is not None:
                sm_ids.add(sm_id)
        
        # For avoid_captain: if player had the buff active and is NOT a spymaster, it triggered
        # Skip this logic if auto-bot is enabled (auto-bot should be captain, not human)
        auto_bot_enabled = self.metadata.get("auto_bot_enabled", False)
        if not auto_bot_enabled:
            for pid in avoid_ready:
                if pid in self.players and pid not in sm_ids:
                    # This player avoided being captain successfully
                    await db_service.consume_captain_buff(pid, "avoid_captain")
                    player_name = self.players[pid].full_name
                    # Find who became captain instead (in their team)
                    replacement = None
                    for team, sp_id in self.spymasters.items():
                        if sp_id and sp_id in self.players:
                            p = self.players[pid]
                            if p.team and p.team == self.players[sp_id].team:
                                replacement = self.players[sp_id].full_name
                                break
                    if replacement:
                        from src.assets.texts import get_text
                        t = get_text(self.language)
                        captain_buff_notifications.append(
                            t.AVOID_CAPTAIN_TRIGGERED.format(player=player_name, replacement=replacement)
                        )
                    else:
                        captain_buff_notifications.append(
                            f"⚡ Баф «Уникнути капітанства» спрацював для {player_name}!"
                            if self.language == "uk"
                            else f"⚡ «Avoid Captain» buff triggered for {player_name}!"
                        )
        
        # For become_captain: if player had the buff active and IS a spymaster, it triggered
        for pid in become_ready:
            if pid in sm_ids:
                await db_service.consume_captain_buff(pid, "become_captain")
                # Find who they replaced
                player_name = self.players[pid].full_name
                captain_buff_notifications.append(
                    f"⚡ Баф «Стати капітаном» спрацював! {player_name} стає капітаном!"
                    if self.language == "uk"
                    else f"⚡ «Become Captain» buff triggered! {player_name} becomes captain!"
                )
        
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
            # Show side A and side B players
            side_a_players = []
            side_b_players = []
            for pid, p in self.players.items():
                if p.team == "green":
                    role_suffix = " (🎯)" if p.role == "dual_spymaster" else ""
                    side_a_players.append(f"{p.full_name}{role_suffix}")
                elif p.team == "red":
                    role_suffix = " (🎯)" if p.role == "dual_spymaster" else ""
                    side_b_players.append(f"{p.full_name}{role_suffix}")

            teams_info.append(f"🅰️ Сторона A (підказки): {', '.join(side_a_players)}")
            teams_info.append(f"🅱️ Сторона B (відгадування): {', '.join(side_b_players)}")
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
        
        final_msg = f"{t.GAME_STARTED_MSG.format(desc=desc)}\n\n{teams_str}"
        
        # Append captain buff notifications if any
        if captain_buff_notifications:
            final_msg += "\n\n" + "\n".join(captain_buff_notifications)
        
        status = self.get_status_message()
        return f"{final_msg}\n\n{status}"

    def assign_roles(self, avoid_ready_set: set = None, become_ready_set: set = None):
        import random
        player_ids = list(self.players.keys())
        random.shuffle(player_ids)
        
        mode = self.metadata.get("mode", "Classic").lower()
        
        # Read buff flags from metadata (set by start() before calling assign_roles)
        if avoid_ready_set is None:
            avoid_ready_set = set(self.metadata.get("captain_avoid_players", []))
        if become_ready_set is None:
            become_ready_set = set(self.metadata.get("captain_become_players", []))

        # Only apply captain buffs in team modes with at least 2 players per team
        if mode not in ("duet", "3p"):
            half = len(player_ids) // 2
            green_players = list(player_ids[:half])
            red_players = list(player_ids[half:])

            # Avoid: shift first avoid_captain player to back in each team
            for team_players in [green_players, red_players]:
                if len(team_players) > 1:
                    for i, pid in enumerate(team_players):
                        if pid in avoid_ready_set:
                            team_players.append(team_players.pop(i))
                            break  # Only first avoid triggers

            # Become: make first become_captain player the first in team
            for team_players in [green_players, red_players]:
                if len(team_players) > 1:
                    for pid in team_players:
                        if pid in become_ready_set and team_players[0] != pid:
                            team_players.remove(pid)
                            team_players.insert(0, pid)
                            break  # Only first become triggers

            player_ids = green_players + red_players

        if mode == "duet":
            if len(player_ids) >= 2:
                # Split players into side A (green) and side B (red)
                # Side A gives clues, side B guesses
                side_a_count = len(player_ids) // 2
                side_b_count = len(player_ids) - side_a_count

                side_a_players = player_ids[:side_a_count]
                side_b_players = player_ids[side_a_count:]

                # Handle captain buffs for side A
                if side_a_players and side_a_players[0] in avoid_ready_set and len(side_a_players) > 1:
                    side_a_players.append(side_a_players.pop(0))

                # Choose spymaster for side A (first in list)
                if side_a_players:
                    side_a_spymaster = side_a_players[0]
                    self.spymasters[Team.GREEN] = side_a_spymaster
                    self.players[side_a_spymaster].role = "dual_spymaster"
                    self.players[side_a_spymaster].team = "green"

                # Assign all side A players to green team
                for pid in side_a_players:
                    self.players[pid].team = "green"
                    self.players[pid].role = "dual_spymaster" if pid == side_a_spymaster else "agent"

                # Create queue for side B spymasters (all side B players cycle through)
                side_b_spymaster_queue = list(side_b_players)
                if side_b_spymaster_queue:
                    side_b_spymaster = side_b_spymaster_queue[0]
                    self.spymasters[Team.RED] = side_b_spymaster

                # Assign all side B players to red team
                for pid in side_b_players:
                    self.players[pid].team = "red"
                    self.players[pid].role = "dual_spymaster" if pid == side_b_spymaster else "agent"

                # Store queue for side B spymasters
                self.metadata["duet_side_b_queue"] = side_b_spymaster_queue
                self.metadata["duet_side_b_current_index"] = 0

            elif len(player_ids) == 1:
                # Solo play: make the single player an agent on one team
                # and let auto-bot handle both spymaster roles
                solo_player_id = player_ids[0]
                self.spymasters[Team.GREEN] = None  # Auto-bot will handle this
                self.spymasters[Team.RED] = None   # Auto-bot will handle this
                self.players[solo_player_id].role = "agent"
                self.players[solo_player_id].team = "green"  # Can be either team
        elif mode == "3p" and len(player_ids) >= 3:
            # 3 Player mode: 1 shared spymaster with captain buffs
            sm_pool = list(player_ids)
            if sm_pool[0] in avoid_ready_set and len(sm_pool) > 1:
                sm_pool.pop(0)
            for pid in sm_pool:
                if pid in become_ready_set and sm_pool[0] != pid:
                    sm_pool.remove(pid)
                    sm_pool.insert(0, pid)
                    break

            self.spymasters[Team.GREEN] = sm_pool[0]
            self.spymasters[Team.RED] = sm_pool[0]
            self.players[sm_pool[0]].role = "dual_spymaster"
            
            remaining = [p for p in player_ids if p != sm_pool[0]]
            if remaining:
                self.players[remaining[0]].team = "green"
                self.players[remaining[0]].role = "agent"
            if len(remaining) > 1:
                self.players[remaining[1]].team = "red"
                self.players[remaining[1]].role = "agent"
        else:
            # Teams
            green_players = list(player_ids[:len(player_ids)//2])
            red_players = list(player_ids[len(player_ids)//2:])

            # Assign spymasters
            if green_players:
                self.spymasters[Team.GREEN] = green_players[0]
            if red_players:
                self.spymasters[Team.RED] = red_players[0]
            
            for pid in green_players:
                self.players[pid].team = "green"
                self.players[pid].role = "spymaster" if pid == green_players[0] else "agent"
            for pid in red_players:
                self.players[pid].team = "red"
                self.players[pid].role = "spymaster" if pid == red_players[0] else "agent"

    def update_duet_spymaster_queue(self, previous_turn=None):
        """Updates the current spymaster for side B (red team) in Duet mode based on queue.

        Args:
            previous_turn: The turn before the switch. If provided, only rotates queue
                          when switching TO side B (GREEN -> RED).
        """
        if self.metadata.get("mode", "").lower() != "duet":
            return

        queue = self.metadata.get("duet_side_b_queue", [])
        if not queue or len(queue) <= 1:
            return

        current_index = self.metadata.get("duet_side_b_current_index", 0)

        # Only rotate when switching TO side B (GREEN -> RED)
        # If previous_turn is provided, check if we're switching to RED
        if previous_turn is not None:
            if previous_turn == Team.RED:
                # RED -> GREEN: side B finished guessing, no queue rotation needed
                return
            # GREEN -> RED: side A gave clue, side B about to guess - rotate queue!

        # Store previous spymaster to demote them
        old_spymaster_id = queue[current_index]

        # Cycle to next spymaster in queue
        current_index = (current_index + 1) % len(queue)
        self.metadata["duet_side_b_current_index"] = current_index
        new_spymaster_id = queue[current_index]
        self.spymasters[Team.RED] = new_spymaster_id

        # Update roles: old spymaster becomes agent, new spymaster becomes dual_spymaster
        if old_spymaster_id in self.players:
            self.players[old_spymaster_id].role = "agent"
        if new_spymaster_id in self.players:
            self.players[new_spymaster_id].role = "dual_spymaster"

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
            
            try:
                if self.metadata.get("registration_msg_id"):
                    await bot.unpin_chat_message(
                        self.chat_id, self.metadata["registration_msg_id"]
                    )
            except Exception:
                pass

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
            display_count = "∞" if self.engine.clue_count == 0 else self.engine.clue_count
            lines.append(f"🔎 Підказка: <b>{self.engine.clue.upper()} ({display_count})</b>")
            lines.append(f"🤔 Спроб залишилось: <b>{self.engine.remaining_guesses}</b>")
            
            if self.engine.mode == "duet":
                # Determine which team should be guessing
                guessing_team_val = "red" if self.engine.current_turn == Team.GREEN else "green"
                # Show only players from the guessing team
                guessers = [p.mention for pid, p in self.players.items() if p.team == guessing_team_val]
                if guessers:
                    guessers_str = ", ".join(guessers)
                    lines.append(f"👉 Обирають слово: {guessers_str}")
                else:
                    # Fallback: show team name instead of "Команда"
                    team_name = "🅱️ Сторона B" if guessing_team_val == "red" else "🅰️ Сторона A"
                    lines.append(f"👉 Обирають слово: {team_name}")
                    # Log this issue for debugging
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"No guessers found for team {guessing_team_val} in Duet mode. Players: {[(pid, p.team) for pid, p in self.players.items()]}")
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

                # Check if auto-bot is enabled and should be giving hints
                auto_bot_enabled = self.metadata.get("auto_bot_enabled", False)
                if auto_bot_enabled and (spymaster_id is None or spymaster_id not in self.players):
                    lines.append(f"👉 Дає підказку: <b>🤖 Auto-Bot</b>{agents_suffix}")
                elif spymaster_id and spymaster_id in self.players:
                    sm_mention = self.players[spymaster_id].mention
                    lines.append(f"👉 Дає підказку: {sm_mention} (для {team_color_name}{agents_suffix})")
                else:
                    lines.append(f"👉 Дає підказку: <b>Капітан {team_color_name}</b>{agents_suffix}")
            
        found = 0
        total_to_find = 0
        if self.mode == "duet":
            total_to_find = sum(1 for p in self.engine.duet_pairs if p[0] == CardColor.GREEN or p[1] == CardColor.GREEN)
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
                display_count = "∞" if item['count'] == 0 else item['count']
                formatted.append(f"{team_emoji} {item['clue'].upper()} ({display_count})")
            history_str = ", ".join(formatted)
            if self.language == "uk":
                status_text += f"<blockquote>📜 Минулі загадки: {history_str}</blockquote>"
            else:
                status_text += f"<blockquote>📜 Past clues: {history_str}</blockquote>"
                
        return status_text
    
    async def try_auto_bot_hint(self, bot: Any):
        """Try to generate and send an auto-bot hint if enabled."""
        if not self.engine or self.engine.is_over:
            return
        
        # Check if auto-bot is enabled
        auto_bot_enabled = self.metadata.get("auto_bot_enabled", False)
        if not auto_bot_enabled:
            return
        
        # Check if there's already a clue set (spymaster already gave hint)
        if self.engine.clue is not None:
            return
        
        # Import AI bot
        from .ai_bot import AIBot
        
        # Get difficulty from metadata or settings
        difficulty = self.metadata.get("auto_bot_difficulty", "medium")
        
        # Create AI bot instance
        ai_bot = AIBot(language=self.language, difficulty=difficulty)
        
        # Generate clue for current team
        clue_result = ai_bot.generate_clue(self.engine, self.engine.current_turn)
        
        if clue_result:
            clue_word, count, explanation = clue_result
            
            # Set the clue in the engine
            self.engine.set_clue(clue_word, count)
            
            # Get texts
            from src.assets.texts import get_text
            t = get_text(self.language)
            
            # Send auto-bot message to chat (without debug info for players)
            team_emoji = "🟢" if self.engine.current_turn == Team.GREEN else "🔴"
            display_count = "∞" if count == 0 else count
            auto_msg = f"{team_emoji} <b>🤖 {t.AUTOBOT_TITLE if hasattr(t, 'AUTOBOT_TITLE') else 'Auto-Bot Host'}</b>\n"
            auto_msg += f"📢 <b>{t.HINT_ANNOUNCE if hasattr(t, 'HINT_ANNOUNCE') else 'Підказка'}:</b> {clue_word.upper()} {display_count}"
            
            try:
                await bot.send_message(
                    self.chat_id,
                    auto_msg,
                    parse_mode="HTML",
                    message_thread_id=self.thread_id
                )
            except Exception as e:
                print(f"Error sending auto-bot hint: {e}")
