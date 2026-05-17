from pydantic import BaseModel

class ChatSettings(BaseModel):
    language: str = "uk"
    dark_mode: bool = False
    allow_everyone_start: bool = True
    allow_buffs: bool = True
    button_board: bool = False
    board_size: int = 5
