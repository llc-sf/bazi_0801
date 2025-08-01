from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conint
from .bazi_core import solar_to_bazi
from typing import Optional

app = FastAPI(title="精准八字 API", version="2.0.0")

class BaziRequest(BaseModel):
    name: str  # 必填字段
    city: str  # 必填字段
    gender: Optional[str] = "男"  # 可选字段，默认None
    year:  conint(ge=1900, le=2100)
    month: conint(ge=1,   le=12)
    day:   conint(ge=1,   le=31)
    hour:  conint(ge=0,   le=23)
    minute: conint(ge=0, le=59) = 0  # 可选

@app.post("/bazi")
def get_bazi(req: BaziRequest):
    try:
        result = solar_to_bazi(req.name, req.city, req.gender, req.year, req.month, req.day, req.hour, req.minute)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
