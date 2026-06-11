from pydantic import BaseModel, field_validator

class ChatSettings(BaseModel):
    language: str = "uk"
    dark_mode: bool = False
    allow_everyone_start: bool = True
    allow_buffs: str = "on"
    button_board: bool = False
    board_size: int = 5
    last_word_set: str = "standard"

    @field_validator("allow_buffs", mode="before")
    @classmethod
    def validate_allow_buffs(cls, v):
        if isinstance(v, bool):
            return "on" if v else "off"
        if isinstance(v, str):
            if v.lower() == "true":
                return "on"
            if v.lower() == "false":
                return "off"
            return v
        return "on"
    last_reg_timer: int = 180
    last_turn_timer: int = 120
    last_mode: str = "classic"
    pin_message: bool = True
    spymaster_sheet: bool = False
    show_past_clues: bool = True
    strict_clues: bool = False
    allow_pass: bool = True
    auto_bot_enabled: bool = False
    auto_bot_difficulty: str = "medium"
    hardcore_mode: str = "off"  # "off", "light", "roulette", "hard"
    admin_only_settings: bool = False
    # New fields for custom board background (skin)
    background_image: str | None = None
    background_opacity: float = 1.0
    card_background_opacity: float = 1.0
