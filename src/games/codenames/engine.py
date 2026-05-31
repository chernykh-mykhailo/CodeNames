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
    def __init__(self, words: List[str], mode: str = "classic", first_team: Team = Team.GREEN, size: int = 5):
        self.words = words
        self.mode = mode.lower()
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
        
        # Buff states
        self.team_armor: List[Team] = []
        self.team_interception: List[Team] = []
        self.intercept_used_this_turn: bool = False
        self.generate_board()

    def generate_board(self):
        selected_words = random.sample(self.words, self.total_cards)
        
        if self.mode == "duet":
            # For duet we currently only support 25 cards (5x5)
            # If size is different, we adjust or fallback
            if self.total_cards != 25:
                # Basic scaling for Duet if size changed
                # Standard Duet (25): 15 unique agents, 3 dual assassins, etc.
                # For simplicity, we only allow 5x5 for Duet for now or scale roughly
                pass
                
            pairs = (
                [(CardColor.GREEN, CardColor.GREEN)] * 3 +
                [(CardColor.ASSASSIN, CardColor.ASSASSIN)] * 1 +
                [(CardColor.GREEN, CardColor.ASSASSIN)] * 1 +
                [(CardColor.ASSASSIN, CardColor.GREEN)] * 1 +
                [(CardColor.GREEN, CardColor.BYSTANDER)] * 5 +
                [(CardColor.BYSTANDER, CardColor.GREEN)] * 5 +
                [(CardColor.ASSASSIN, CardColor.BYSTANDER)] * 1 +
                [(CardColor.BYSTANDER, CardColor.ASSASSIN)] * 1 +
                [(CardColor.BYSTANDER, CardColor.BYSTANDER)] * 7
            )
            # Ensure we have enough pairs if size > 5
            if len(pairs) < self.total_cards:
                pairs += [(CardColor.BYSTANDER, CardColor.BYSTANDER)] * (self.total_cards - len(pairs))
            elif len(pairs) > self.total_cards:
                pairs = pairs[:self.total_cards]
                
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
            assassin_count = 1 if self.total_cards < 36 else 2
            bystander_count = self.total_cards - first_count - second_count - assassin_count
            
            colors = [self.first_team.value] * first_count
            other_team = Team.RED if self.first_team == Team.GREEN else Team.GREEN
            colors += [other_team.value] * second_count
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

    def set_clue(self, clue: str, count: int):
        self.clue = clue
        self.clue_count = count
        self.guesses_made = 0
        self.remaining_guesses = count + 1 if count > 0 else 25 # 0 or unlimited

    def reveal_card(self, index: int) -> bool:
        if self.winner or self.board[index].is_revealed:
            return False
            
        card = self.board[index]
        card.is_revealed = True
        self.guesses_made += 1
        self.remaining_guesses -= 1
        
        # Color from current guesser's perspective in Duet
        # If current_turn is GREEN, they gave the clue (Side A), so Side B is guessing based on Side A's map.
        # Therefore, we must evaluate against the clue-giver's map!
        if self.mode == "duet":
            giver_side = "a" if self.current_turn == Team.GREEN else "b"
            effective_color = self.get_duet_color(index, giver_side)
        else:
            effective_color = card.color
            
        card.revealed_color = effective_color

        # Check for assassin
        if effective_color == CardColor.ASSASSIN:
            if self.current_turn in self.team_armor:
                # ARMOR BUFF: Save from assassin
                self.team_armor.remove(self.current_turn)
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
            # In Duet, win if ALL unique agent locations are found
            # (9 for A, 9 for B, with 3 overlap = 15 total unique agents)
            found_count = 0
            for i in range(25):
                # If a card is revealed AND it was an agent for EITHER side
                if self.board[i].is_revealed:
                    color_a = self.get_duet_color(i, "a")
                    color_b = self.get_duet_color(i, "b")
                    if color_a == CardColor.GREEN or color_b == CardColor.GREEN:
                        found_count += 1
            if found_count >= 15:
                self.winner = Team.GREEN # Unified GREEN win for Duet
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
        
        # Final win check
        self.check_win()

    def get_board_state(self, revealed_only: bool = True, side: Optional[str] = None) -> List[Dict]:
        res = []
        for i, c in enumerate(self.board):
            if revealed_only and not c.is_revealed:
                color = "hidden"
            elif c.is_revealed and c.revealed_color:
                # If revealed, it always shows the color it was revealed as
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
                "is_revealed": c.is_revealed
            })
        return res
