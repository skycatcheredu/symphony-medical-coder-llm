from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from medical_coder_llm.run_code import run_coding_to_json

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_dotenv()
    yield


app = FastAPI(title="Medical Coder LLM", version="0.1.0", lifespan=lifespan)

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class CodeRequest(BaseModel):
    note: str = Field(..., description="Clinical note text")
    ontology: str = "data/ontology/codes.csv"
    provider: str | None = None
    model: str | None = None

    @field_validator("provider", "model", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        if v == "":
            return None
        return v


@app.get("/")
def index() -> FileResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=500, detail="Web UI files are missing.")
    return FileResponse(index_path)


@app.post("/api/code")
async def api_code(body: CodeRequest) -> dict[str, object]:
    def _run() -> str:
        return run_coding_to_json(
            body.note,
            ontology_path=body.ontology,
            provider=body.provider,
            model=body.model,
        )

    try:
        raw = await anyio.to_thread.run_sync(_run)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return json.loads(raw)
