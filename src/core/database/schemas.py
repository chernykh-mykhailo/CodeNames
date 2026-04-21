from pydantic import BaseModel, Field

class ChatSettings(BaseModel):
    allow_everyone_start: bool = Field(default=True)
    allow_buffs: bool = Field(default=True)
    dark_mode: bool = Field(default=False)
    language: str = Field(default="uk")
