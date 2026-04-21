from pydantic import BaseModel, Field

class ChatSettings(BaseModel):
    allow_everyone_start: bool = Field(default=True, description="Allow any player to start the game")
    # You can add more settings here later, like custom timers etc.
