"""Single application entrypoint and API host for the LA image studio."""

from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.filter_matrices import available_filters
from src.image_pipeline import run_pipeline

app = FastAPI(title="LA Image Filter Studio", version="1.1.0")
frontend_dir = Path(__file__).parent / "frontend"
app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="frontend")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Serve the custom frontend shell."""
    return (frontend_dir / "index.html").read_text(encoding="utf-8")


@app.get("/api/presets")
def presets() -> dict:
    """Expose preset filter names for the dropdown list."""
    return {"presets": available_filters()}


@app.post("/api/apply")
async def apply_filters(
    file: UploadFile = File(...),
    preset: str = Form("Cinematic"),
    strength: float = Form(1.0),
    hue: float = Form(0.0),
    exposure: float = Form(0.0),
    contrast: float = Form(0.0),
    saturation: float = Form(0.0),
    vibrance: float = Form(0.0),
    temperature: float = Form(0.0),
    tint: float = Form(0.0),
    gamma: float = Form(1.0),
    sharpen: float = Form(0.0),
    vignette: float = Form(0.0),
    grayscale: bool = Form(False),
    least_squares: bool = Form(False),
    pca_k: int = Form(3),
    preview_max: int = Form(1280),
) -> JSONResponse:
    """Run the full image pipeline and return preview + LA metrics."""
    image_bytes = await file.read()
    if not image_bytes:
        return JSONResponse({"error": "No image file received."}, status_code=400)

    settings = {
        "preset": preset,
        "strength": strength,
        "hue": hue,
        "exposure": exposure,
        "contrast": contrast,
        "saturation": saturation,
        "vibrance": vibrance,
        "temperature": temperature,
        "tint": tint,
        "gamma": gamma,
        "sharpen": sharpen,
        "vignette": vignette,
        "grayscale": grayscale,
        "least_squares": least_squares,
        "pca_k": pca_k,
        "preview_max": preview_max,
    }

    try:
        return JSONResponse(run_pipeline(image_bytes, settings))
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception:
        return JSONResponse({"error": "Processing failed. Try a smaller image."}, status_code=500)


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
