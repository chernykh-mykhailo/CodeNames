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
    def __init__(self, words: List[str], first_team: Team = Team.RED):
        self.words = words
        self.first_team = first_team
        self.current_turn = first_team
        self.board: List[Card] = []
        self.generate_board()
        self.clue: Optional[str] = None
        self.clue_count: int = 0
        self.remaining_guesses: int = 0
        self.winner: Optional[Team] = None

    def generate_board(self):
        # 25 words
        selected_words = random.sample(self.words, 25)
        
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
        self.remaining_guesses = count + 1 if count > 0 else 25 # 0 or unlimited

    def reveal_card(self, index: int) -> Card:
        card = self.board[index]
        if card.is_revealed:
            return card
        
        card.is_revealed = True
        
        # Check logic
        if card.color.value == CardColor.ASSASSIN.value:
            self.winner = Team.BLUE if self.current_turn == Team.RED else Team.RED
        elif card.color.value != self.current_turn.value:
            self.end_turn()
        else:
            self.remaining_guesses -= 1
            if self.remaining_guesses <= 0:
                self.end_turn()
                
        self.check_winner()
        return card

    def end_turn(self):
        self.current_turn = Team.BLUE if self.current_turn == Team.RED else Team.RED
        self.clue = None
        self.clue_count = 0
        self.remaining_guesses = 0

    def check_winner(self):
        if self.winner:
            return
        
        red_rem = len([c for c in self.board if c.color == CardColor.RED and not c.is_revealed])
        blue_rem = len([c for c in self.board if c.color == CardColor.BLUE and not c.is_revealed])
        
        if red_rem == 0:
            self.winner = Team.RED
        elif blue_rem == 0:
            self.winner = Team.BLUE

    def get_board_state(self, revealed_only: bool = True) -> List[Dict]:
        return [
            {
                "word": c.word,
                "color": c.color.value if (revealed_only and c.is_revealed) or not revealed_only else "hidden",
                "is_revealed": c.is_revealed
            }
            for c in self.board
        ]
