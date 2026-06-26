from pydantic import BaseModel


class AIAnalysisResult(BaseModel):
    title: str
    brand: str
    category: str
    description: str
    condition: int
    size: str | None
    chest: int | None
    total_length: int | None
    waist: int | None
    hip: int | None
    rise: int | None
    colors: list[str]
    material: str
