import random
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel

class CardColor(Enum):
    GREEN = "green"
    RED = "red"
    BYSTANDER = "bystander"
    ASSASSIN = "assassin"

class Card(BaseModel):
    word: str
    color: CardColor
    is_revealed: bool = False
    revealed_color: Optional[CardColor] = None

class Team(Enum):
    GREEN = "green"
    RED = "red"

class CodenamesEngine:
    def __init__(self, words: List[str], mode: str = "classic", first_team: Team = Team.GREEN, size: int = 5, hardcore_mode: str = "off"):
        self.words = words
        self.mode = mode.lower()
        self.hardcore_mode = hardcore_mode  # "off", "light", "hard"
        self.first_team = first_team
        self.current_turn = first_team
        self.size = size
        self.total_cards = size * size
        self.board: List[Card] = []
        self.clue: Optional[str] = None
        self.clue_count: int = 0
        self.remaining_guesses: int = 0
        self.guesses_made: int = 0
        self.winner: Optional[Team] = None
        self.is_over: bool = False
        self.is_assassin_hit: bool = False

        self.is_armor_triggered: bool = False
        self.team_armor: List[Team] = []
        self.team_interception: List[Team] = []
        self.intercept_used_this_turn: bool = False
        self.clues_history = []
        self.generate_board()

    def generate_board(self):
        selected_words = random.sample(self.words, self.total_cards)

        if self.mode == "duet":
            # Scale Duet card pairs proportionally based on board size
            # Base proportions for 25 cards:
            # (GREEN, GREEN): 3 (12%)
            # (GREEN, ASSASSIN): 1 (4%)
            # (ASSASSIN, GREEN): 1 (4%)
            # (GREEN, BYSTANDER): 5 (20%)
            # (BYSTANDER, GREEN): 5 (20%)
            # (ASSASSIN, ASSASSIN): 1 (4%)
            # (ASSASSIN, BYSTANDER): 1 (4%)
            # (BYSTANDER, ASSASSIN): 1 (4%)
            # Remaining: (BYSTANDER, BYSTANDER)
            
            gg = max(1, int(round(0.12 * self.total_cards)))
            aa = max(1, int(round(0.04 * self.total_cards)))
            ga = max(1, int(round(0.04 * self.total_cards)))
            ab = max(1, int(round(0.04 * self.total_cards)))
            gb = max(1, int(round(0.20 * self.total_cards)))
            
            # Ensure counts don't exceed total cards
            while gg + 2*ga + 2*gb + aa + 2*ab > self.total_cards:
                if gb > 1:
                    gb -= 1
                elif gg > 1:
                    gg -= 1
                elif ga > 1:
                    ga -= 1
                elif ab > 1:
                    ab -= 1
                elif aa > 1:
                    aa -= 1
                else:
                    break
            
            bb = self.total_cards - (gg + 2*ga + 2*gb + aa + 2*ab)

            pairs = (
                [(CardColor.GREEN, CardColor.GREEN)] * gg +
                [(CardColor.ASSASSIN, CardColor.ASSASSIN)] * aa +
                [(CardColor.GREEN, CardColor.ASSASSIN)] * ga +
                [(CardColor.ASSASSIN, CardColor.GREEN)] * ga +
                [(CardColor.GREEN, CardColor.BYSTANDER)] * gb +
                [(CardColor.BYSTANDER, CardColor.GREEN)] * gb +
                [(CardColor.ASSASSIN, CardColor.BYSTANDER)] * ab +
                [(CardColor.BYSTANDER, CardColor.ASSASSIN)] * ab +
                [(CardColor.BYSTANDER, CardColor.BYSTANDER)] * bb
            )
            
            # In Hardcore Duet, all BYSTANDER states become ASSASSIN
            if self.hardcore_mode == "hard":
                new_pairs = []
                for p in pairs:
                    c0 = CardColor.ASSASSIN if p[0] == CardColor.BYSTANDER else p[0]
                    c1 = CardColor.ASSASSIN if p[1] == CardColor.BYSTANDER else p[1]
                    new_pairs.append((c0, c1))
                pairs = new_pairs
            elif self.hardcore_mode == "light":
                pass  # roaming assassin handled at runtime via rotate_light_assassin()

            random.shuffle(pairs)

            self.board = [
                Card(word=word, color=p[0])
                for word, p in zip(selected_words, pairs)
            ]
            self.duet_pairs = pairs
        else:
            # Classic logic scaling
            # Ratio: ~1/3 first, ~1/3 second, 1 assassin, rest bystanders
            first_count = (self.total_cards // 3) + 1
            second_count = first_count - 1
            
            if self.total_cards < 36:
                assassin_count = 1
            else:
                # Scale assassins: 36 cards = 2, 54 = 3, 72 = 4, etc.
                assassin_count = self.total_cards // 18
                
            bystander_count = self.total_cards - first_count - second_count - assassin_count

            colors = [self.first_team.value] * first_count
            other_team = Team.RED if self.first_team == Team.GREEN else Team.GREEN
            colors += [other_team.value] * second_count

            if self.hardcore_mode == "hard":
                assassin_count += bystander_count
                bystander_count = 0
            elif self.hardcore_mode == "light":
                pass  # roaming assassin handled at runtime via rotate_light_assassin()


            colors += [CardColor.ASSASSIN.value] * assassin_count
            colors += [CardColor.BYSTANDER.value] * bystander_count
            random.shuffle(colors)

            self.board = [
                Card(word=word, color=CardColor(color))
                for word, color in zip(selected_words, colors)
            ]

    def get_duet_color(self, index: int, side: str = "a") -> CardColor:
        if self.mode != "duet":
            return self.board[index].color
        return self.duet_pairs[index][0 if side == "a" else 1]

    def rotate_light_assassin(self):
        """Light hardcore: add one new assassin from bystanders each turn (no removal).
           Roulette hardcore: move the roaming assassin to a new bystander each turn.
        """
        if self.hardcore_mode not in ("light", "roulette"):
            return

        if self.mode == "duet":
            if self.hardcore_mode == "roulette":
                prev = getattr(self, "_light_assassin_idx", None)
                if prev is None:
                    # First call: pick one existing (ASSASSIN,ASSASSIN) as the roaming one
                    candidates = [
                        i for i, p in enumerate(self.duet_pairs)
                        if not self.board[i].is_revealed
                        and p[0] == CardColor.ASSASSIN and p[1] == CardColor.ASSASSIN
                    ]
                    if candidates:
                        self._light_assassin_idx = random.choice(candidates)
                    return
                # Restore previous roaming assassin back to bystander
                if not self.board[prev].is_revealed:
                    self.duet_pairs[prev] = (CardColor.BYSTANDER, CardColor.BYSTANDER)
                candidates = [
                    i for i, p in enumerate(self.duet_pairs)
                    if not self.board[i].is_revealed
                    and p[0] == CardColor.BYSTANDER and p[1] == CardColor.BYSTANDER
                ]
                if candidates:
                    idx = random.choice(candidates)
                    self.duet_pairs[idx] = (CardColor.ASSASSIN, CardColor.ASSASSIN)
                    self._light_assassin_idx = idx
                else:
                    self._light_assassin_idx = None
            else:  # light: add new each turn
                candidates = [
                    i for i, p in enumerate(self.duet_pairs)
                    if not self.board[i].is_revealed
                    and p[0] == CardColor.BYSTANDER and p[1] == CardColor.BYSTANDER
                ]
                if candidates:
                    idx = random.choice(candidates)
                    self.duet_pairs[idx] = (CardColor.ASSASSIN, CardColor.ASSASSIN)
        else:
            if self.hardcore_mode == "roulette":
                prev = getattr(self, "_light_assassin_idx", None)
                if prev is None:
                    candidates = [i for i, c in enumerate(self.board) if not c.is_revealed and c.color == CardColor.BYSTANDER]
                    if candidates:
                        idx = random.choice(candidates)
                        self.board[idx].color = CardColor.ASSASSIN
                        self._light_assassin_idx = idx
                    return
                if prev < len(self.board) and not self.board[prev].is_revealed:
                    self.board[prev].color = CardColor.BYSTANDER
                candidates = [i for i, c in enumerate(self.board) if not c.is_revealed and c.color == CardColor.BYSTANDER]
                if candidates:
                    idx = random.choice(candidates)
                    self.board[idx].color = CardColor.ASSASSIN
                    self._light_assassin_idx = idx
                else:
                    self._light_assassin_idx = None
            else:  # light: add new each turn
                candidates = [i for i, c in enumerate(self.board) if not c.is_revealed and c.color == CardColor.BYSTANDER]
                if candidates:
                    idx = random.choice(candidates)
                    self.board[idx].color = CardColor.ASSASSIN

    def set_clue(self, clue: str, count: int, display: str = None):
        self.clue = clue
        self.clue_count = count
        self.guesses_made = 0
        self.remaining_guesses = count + 1 if count > 0 else 25
        self.clues_history.append({
            "team": self.current_turn.value if hasattr(self.current_turn, "value") else self.current_turn,
            "clue": clue,
            "count": count,
            "display": display if display is not None else str(count),
        })

    def reveal_card(self, index: int) -> bool:
        if self.is_over or self.winner or self.board[index].is_revealed:
            return False

        card = self.board[index]
        card.is_revealed = True
        self.guesses_made += 1
        self.remaining_guesses -= 1

        # Color from current guesser's perspective in Duet
        # If current_turn is GREEN, they gave the clue (Side A), so Side B is guessing based on Side A's map.
        # Therefore, we must evaluate against the clue-giver's map!
        if self.mode == "duet":
            # If current turn (clue-giver) is GREEN (Side A), they guess based on Side A's map ('a').
            giver_side = "a" if self.current_turn == Team.GREEN else "b"
            effective_color = self.get_duet_color(index, giver_side)
        else:
            effective_color = card.color

        card.revealed_color = effective_color

        # Check for assassin
        if effective_color == CardColor.ASSASSIN:
            # In Duet mode, current_turn is the clue-giver, NOT the guessing team.
            # The guessing team is the one that hits the assassin, so use the guessing team.
            if self.mode == "duet":
                armor_team = Team.RED if self.current_turn == Team.GREEN else Team.GREEN
            else:
                armor_team = self.current_turn
            if armor_team in self.team_armor:
                # ARMOR BUFF: Save from assassin
                self.team_armor.remove(armor_team)
                # Set flag so game_router can display the "armor saved" message
                self.is_armor_triggered = True
                # Keep card revealed but don't end game
                self.end_turn()
                return True

            self.is_over = True
            self.is_assassin_hit = True
            if self.mode == "duet":
                self.winner = None
            else:
                self.winner = Team.RED if self.current_turn == Team.GREEN else Team.GREEN
            return True

        # Win conditions
        if self.check_win():
            self.is_over = True
            return True

        # Turn transitions
        if self.mode == "duet":
            if effective_color == CardColor.BYSTANDER:
                self.end_turn()
        else:
            # Classic logic: if wrong team or neutral, end turn
            is_wrong_team = effective_color.value != self.current_turn.value
            if is_wrong_team:
                if self.current_turn in self.team_interception and not self.intercept_used_this_turn:
                    # INTERCEPTION BUFF: Don't end turn after 1 mistake
                    self.team_interception.remove(self.current_turn)
                    self.intercept_used_this_turn = True
                    # Let them continue
                else:
                    self.end_turn()
            elif self.remaining_guesses <= 0:
                self.end_turn()

        return True

    def check_win(self) -> bool:
        if self.mode == "duet":
            # In Duet, win ONLY when BOTH sides have found ALL their green cards.
            # A card like (GREEN, ASSASSIN) is green for Side A but NOT Side B,
            # so revealing it helps Side A but doesn't count toward Side B's progress.
            side_a_greens = [i for i, p in enumerate(self.duet_pairs) if p[0] == CardColor.GREEN]
            side_b_greens = [i for i, p in enumerate(self.duet_pairs) if p[1] == CardColor.GREEN]

            side_a_found = all(self.board[i].is_revealed for i in side_a_greens)
            side_b_found = all(self.board[i].is_revealed for i in side_b_greens)

            if side_a_found and side_b_found:
                self.winner = Team.GREEN
                self.is_over = True
                return True
        else:
            # Classic teams
            if all(c.is_revealed for c in self.board if c.color == CardColor.GREEN):
                self.winner = Team.GREEN
                self.is_over = True
            if all(c.is_revealed for c in self.board if c.color == CardColor.RED):
                self.winner = Team.RED
                self.is_over = True
        return False

    def is_last_word_for_victory(self, team: Team) -> bool:
        if self.mode == "duet":
            side_a_greens = [i for i, p in enumerate(self.duet_pairs) if p[0] == CardColor.GREEN]
            side_b_greens = [i for i, p in enumerate(self.duet_pairs) if p[1] == CardColor.GREEN]
            side_a_unrevealed = sum(1 for i in side_a_greens if not self.board[i].is_revealed)
            side_b_unrevealed = sum(1 for i in side_b_greens if not self.board[i].is_revealed)
            return (side_a_unrevealed == 1) or (side_b_unrevealed == 1)
        else:
            target_color = CardColor.GREEN if team == Team.GREEN else CardColor.RED
            unrevealed = sum(1 for c in self.board if not c.is_revealed and c.color == target_color)
            return unrevealed == 1

    def count_unrevealed_assassins(self) -> int:
        if self.mode == "duet":
            giver_side = "a" if self.current_turn == Team.GREEN else "b"
            return sum(
                1 for i, c in enumerate(self.board)
                if not c.is_revealed and self.get_duet_color(i, giver_side) == CardColor.ASSASSIN
            )
        else:
            return sum(
                1 for c in self.board
                if not c.is_revealed and c.color == CardColor.ASSASSIN
            )

    def use_buff_reveal(self) -> Optional[str]:
        """Buff: Reveals a random unrevealed agent for the current team."""
        target_color = CardColor.GREEN if self.mode == "duet" else CardColor(self.current_turn.value)
        unrevealed = [c for c in self.board if not c.is_revealed and c.color == target_color]
        if not unrevealed:
            return None
        card = random.choice(unrevealed)
        card.is_revealed = True
        word = card.word
        self.check_win()
        return word

    def use_buff_detector(self) -> Optional[str]:
        """Buff: Reveals a neutral word (bystander) without ending turn."""
        unrevealed = [c for c in self.board if not c.is_revealed and c.color == CardColor.BYSTANDER]
        if not unrevealed:
            return None
        card = random.choice(unrevealed)
        card.is_revealed = True
        return card.word

    def use_buff_remap(self, index: int, new_word: str) -> bool:
        """Buff: Swaps a word on the field."""
        if index < 0 or index >= len(self.board) or self.board[index].is_revealed:
            return False
        self.board[index].word = new_word
        return True

    def use_buff_replace_all(self) -> bool:
        """Buff: Replaces the entire board if no words are revealed."""
        if any(c.is_revealed for c in self.board):
            return False

        # Re-generate the board
        self.board = []
        self.generate_board()
        return True

    def end_turn(self):
        self.current_turn = Team.RED if self.current_turn == Team.GREEN else Team.GREEN
        self.clue = None
        self.clue_count = 0
        self.guesses_made = 0
        self.remaining_guesses = 0
        self.intercept_used_this_turn = False

        # Light/Roulette: once per full round (when GREEN's turn starts, i.e. RED->GREEN)
        if self.hardcore_mode in ("light", "roulette"):
            if self.current_turn == Team.GREEN:
                self.rotate_light_assassin()

        # Final win check
        self.check_win()

    def to_dict(self) -> dict:
        """Serialize engine state to a JSON-compatible dict."""
        return {
            "words": self.words,
            "mode": self.mode,
            "hardcore_mode": self.hardcore_mode,
            "first_team": self.first_team.value,
            "current_turn": self.current_turn.value,
            "size": self.size,
            "total_cards": self.total_cards,
            "board": [
                {
                    "word": c.word,
                    "color": c.color.value,
                    "is_revealed": c.is_revealed,
                    "revealed_color": c.revealed_color.value if c.revealed_color else None,
                }
                for c in self.board
            ],
            "clue": self.clue,
            "clue_count": self.clue_count,
            "remaining_guesses": self.remaining_guesses,
            "guesses_made": self.guesses_made,
            "winner": self.winner.value if self.winner else None,
            "is_over": self.is_over,
            "is_assassin_hit": self.is_assassin_hit,
            "is_armor_triggered": self.is_armor_triggered,
            "team_armor": [t.value for t in self.team_armor],
            "team_interception": [t.value for t in self.team_interception],
            "intercept_used_this_turn": self.intercept_used_this_turn,
            "clues_history": self.clues_history,
            "duet_pairs": [
                [p[0].value, p[1].value] for p in getattr(self, "duet_pairs", [])
            ],
            "_light_assassin_idx": getattr(self, "_light_assassin_idx", None),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CodenamesEngine":
        """Reconstruct engine from a serialized dict without re-generating the board."""
        engine = cls.__new__(cls)
        engine.words = data["words"]
        engine.mode = data["mode"]
        engine.hardcore_mode = data.get("hardcore_mode", "off")
        engine.first_team = Team(data["first_team"])
        engine.current_turn = Team(data["current_turn"])
        engine.size = data["size"]
        engine.total_cards = data["total_cards"]
        engine.board = [
            Card(
                word=c["word"],
                color=CardColor(c["color"]),
                is_revealed=c["is_revealed"],
                revealed_color=CardColor(c["revealed_color"]) if c.get("revealed_color") else None,
            )
            for c in data["board"]
        ]
        engine.clue = data.get("clue")
        engine.clue_count = data.get("clue_count", 0)
        engine.remaining_guesses = data.get("remaining_guesses", 0)
        engine.guesses_made = data.get("guesses_made", 0)
        engine.winner = Team(data["winner"]) if data.get("winner") else None
        engine.is_over = data.get("is_over", False)
        engine.is_assassin_hit = data.get("is_assassin_hit", False)
        engine.is_armor_triggered = data.get("is_armor_triggered", False)
        engine.team_armor = [Team(t) for t in data.get("team_armor", [])]
        engine.team_interception = [Team(t) for t in data.get("team_interception", [])]
        engine.intercept_used_this_turn = data.get("intercept_used_this_turn", False)
        engine.clues_history = data.get("clues_history", [])
        engine.duet_pairs = [
            (CardColor(p[0]), CardColor(p[1]))
            for p in data.get("duet_pairs", [])
        ]
        if data.get("_light_assassin_idx") is not None:
            engine._light_assassin_idx = data["_light_assassin_idx"]
        return engine

    def get_board_state(self, revealed_only: bool = True, side: Optional[str] = None) -> List[Dict]:
        res = []
        for i, c in enumerate(self.board):
            if revealed_only and not c.is_revealed:
                color = "hidden"
            elif c.is_revealed and c.revealed_color and revealed_only:
                # If revealed on the public board, show the color it was revealed as
                color = c.revealed_color.value
            else:
                if self.mode == "duet" and side:
                    color = self.get_duet_color(i, side).value
                elif self.mode == "duet":
                    # Combined view for main board in Duet (only for unrevealed cards at end of game)
                    color_a = self.get_duet_color(i, "a")
                    color_b = self.get_duet_color(i, "b")
                    if color_a == CardColor.GREEN or color_b == CardColor.GREEN:
                        color = CardColor.GREEN.value
                    elif color_a == CardColor.ASSASSIN or color_b == CardColor.ASSASSIN:
                        color = CardColor.ASSASSIN.value
                    else:
                        color = CardColor.BYSTANDER.value
                else:
                    color = c.color.value

            res.append({
                "word": c.word,
                "color": color,
                "is_revealed": c.is_revealed,
                "revealed_color": c.revealed_color.value if c.revealed_color else None,
                "color_a": self.get_duet_color(i, "a").value if self.mode == "duet" and not side else None,
                "color_b": self.get_duet_color(i, "b").value if self.mode == "duet" and not side else None,
            })
        return res
