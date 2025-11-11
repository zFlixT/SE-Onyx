from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Preferencias(BaseModel):
    marca: Optional[str] = None
    so: Optional[str] = None
    portabilidad: Optional[bool] = None

class Consulta(BaseModel):
    uso: str = Field(..., description="gaming|edicion|oficina")
    gama: Optional[str] = Field(None, description="baja|media|alta")
    presupuesto: float
    preferencias: Optional[Preferencias] = None
    top_k: int = 3

class Producto(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    cpu: str
    gpu: str
    ram: str
    storage: str
    os: str
    price: float
    url: str

class Recomendacion(BaseModel):
    product: Producto
    score: float
    reasons: List[str]
    session_id: str

class Feedback(BaseModel):
    session_id: str
    rating: float = Field(..., ge=0, le=1)
    notes: Optional[str] = None
    user_id: Optional[int] = None
    product_name: str
    brand: str
    cpu: Optional[str] = None
    gpu: Optional[str] = None
    ram: Optional[str] = None
    storage: Optional[str] = None
    os: Optional[str] = None
    price: Optional[float] = 0.0