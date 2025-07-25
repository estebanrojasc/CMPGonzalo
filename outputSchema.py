from typing import List, Literal, Optional
from pydantic import BaseModel

class DatoExtraido(BaseModel):
    empresa: Optional[Literal["Mysteel", "FasCall", "Milla"]] = None
    fecha: Optional[str] = None  # Idealmente YYYY-MM-DD
    valor: float
    unidad: str

class ResultadoFinal(BaseModel):
    resultados: List[DatoExtraido]
