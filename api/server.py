import sys
import os
from pathlib import Path

# Add the parent directory to sys.path so we can import data_manager
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List

import data_manager as dm

app = FastAPI(title="Florin Local API", description="API wrapper for budget tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    dm.init_env()

@app.get("/api/month/{month_str}")
def get_month(month_str: str):
    data = dm.get_month_data(month_str)
    return data

@app.put("/api/month/{month_str}")
def save_month(month_str: str, data: Dict[str, Any]):
    try:
        dm.save_month(month_str, data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/savings_planner")
def get_savings_planner(year: Optional[str] = None):
    return dm.get_savings_planner(year)

@app.put("/api/savings_planner")
def save_savings_planner(sp: Dict[str, Any]):
    try:
        dm.save_savings_planner(sp)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
