from pydantic import BaseModel, Field

class ChatSettings(BaseModel):
    allow_everyone_start: bool = Field(default=True, description="Allow any player to start the game")
    allow_buffs: bool = Field(default=True, description="Allow using tactical buffs in game")
    dark_mode: bool = Field(default=False, description="Enable dark theme for game boards")
