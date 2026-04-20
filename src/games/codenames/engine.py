import random
from enum import Enum
from typing import List, Dict, Optional, Set
from pydantic import BaseModel

class CardColor(Enum):
    RED = "red"
    BLUE = "blue"
    BYSTANDER = "bystander"
    ASSASSIN = "assassin"

class Card(BaseModel):
    word: str
    color: CardColor
    is_revealed: bool = False

class Team(Enum):
    RED = "red"
    BLUE = "blue"

class CodenamesEngine:
    def __init__(self, words: List[str], mode: str = "classic", first_team: Team = Team.RED):
        self.words = words
        self.mode = mode.lower()
        self.first_team = first_team
        self.current_turn = first_team
        self.board: List[Card] = []
        self.clue: Optional[str] = None
        self.clue_count: int = 0
        self.remaining_guesses: int = 0
        self.guesses_made: int = 0
        self.winner: Optional[Team] = None
        self.generate_board()

    def generate_board(self):
        # 25 words
        selected_words = random.sample(self.words, 25)
        
        if self.mode == "duet":
            # 15 agents (BLUE because it's co-op), 1 assassin, 9 bystanders
            colors = [CardColor.BLUE.value] * 15
            colors += [CardColor.ASSASSIN.value]
            colors += [CardColor.BYSTANDER.value] * 9
        else:
            # Color distribution: 9 for first, 8 for second, 1 assassin, 7 bystanders
            colors = [self.first_team.value] * 9
            other_team = Team.BLUE if self.first_team == Team.RED else Team.RED
            colors += [other_team.value] * 8
            colors += [CardColor.ASSASSIN.value]
            colors += [CardColor.BYSTANDER.value] * 7
        
        random.shuffle(colors)
        
        self.board = [
            Card(word=word, color=CardColor(color)) 
            for word, color in zip(selected_words, colors)
        ]

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
        
        # Check for assassin
        if card.color == CardColor.ASSASSIN:
            if self.mode == "duet":
                self.winner = Team.RED # Means game lost in duet
            else:
                self.winner = Team.BLUE if self.current_turn == Team.RED else Team.RED
            return True
            
        # Win conditions
        if self.check_win():
            return True
            
        # Turn transitions
        if self.mode == "duet":
            if card.color == CardColor.BYSTANDER:
                self.end_turn()
        else:
            # Classic logic: if wrong team or neutral, end turn
            if card.color.value != self.current_turn.value:
                self.end_turn()
            elif self.remaining_guesses <= 0:
                self.end_turn()
                
        return True

    def check_win(self) -> bool:
        if self.mode == "duet":
            # Cooperative team wins if all BLUE Agents found
            if all(c.is_revealed for c in self.board if c.color == CardColor.BLUE):
                self.winner = Team.BLUE
                return True
        else:
            # Classic teams
            if all(c.is_revealed for c in self.board if c.color == CardColor.RED):
                self.winner = Team.RED
                return True
            if all(c.is_revealed for c in self.board if c.color == CardColor.BLUE):
                self.winner = Team.BLUE
                return True
        return False

    def use_buff_reveal(self) -> Optional[str]:
        """Buff: Reveals a random unrevealed agent for the current team."""
        target_color = CardColor.BLUE if self.mode == "duet" else CardColor(self.current_turn.value)
        unrevealed = [c for c in self.board if not c.is_revealed and c.color == target_color]
        if not unrevealed:
            return None
        card = random.choice(unrevealed)
        card.is_revealed = True
        word = card.word
        self.check_win()
        return word

    def end_turn(self):
        self.current_turn = Team.BLUE if self.current_turn == Team.RED else Team.RED
        self.clue = None
        self.clue_count = 0
        self.guesses_made = 0
        self.remaining_guesses = 0
        
        # Final win check
        self.check_win()

    def get_board_state(self, revealed_only: bool = True) -> List[Dict]:
        return [
            {
                "word": c.word,
                "color": c.color.value if (revealed_only and c.is_revealed) or not revealed_only else "hidden",
                "is_revealed": c.is_revealed
            }
            for c in self.board
        ]
