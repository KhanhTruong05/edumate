from pydantic import BaseModel, Field, ConfigDict


class Section(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=10000)


class Claim(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str = Field(min_length=1, max_length=2000)
    source_id: str = Field(min_length=1, max_length=200)
    quote: str = Field(min_length=1, max_length=3000)


class GeneratedDraft(BaseModel):
    model_config = ConfigDict(extra='forbid')
    sections: list[Section] = Field(min_length=1, max_length=15)
    claims: list[Claim] = Field(default_factory=list, max_length=30)
    warnings: list[str] = Field(default_factory=list, max_length=15)
