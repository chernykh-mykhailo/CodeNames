from pydantic import BaseModel

class ChatSettings(BaseModel):
    language: str = "uk"
    dark_mode: bool = False
    allow_everyone_start: bool = True
    allow_buffs: bool = True
    button_board: bool = False
    board_size: int = 5
    last_word_set: str = "standard"
    last_reg_timer: int = 180
    last_turn_timer: int = 120
    last_mode: str = "classic"
    pin_message: bool = True
    spymaster_sheet: bool = False
    show_past_clues: bool = True
    strict_clues: bool = False
