from pydantic import BaseModel, Field

class ChatSettings(BaseModel):
    allow_everyone_start: bool = Field(default=True, description="Allow any player to start the game")
    allow_buffs: bool = Field(default=True, description="Allow using tactical buffs in game")
