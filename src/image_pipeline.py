"""End-to-end image pipeline: loading, filtering, analysis, and response packing."""

import base64
from io import BytesIO
from typing import Any, Dict

import numpy as np
from PIL import Image, UnidentifiedImageError

from .analysis import apply_least_squares_correction, color_statistics, covariance_eigen, pca_compress
from .filter_matrices import (
    apply_tone_controls,
    apply_unsharp,
    apply_vibrance,
    apply_vignette,
    blend_with_identity,
    get_filter_matrix,
    hue_rotation_matrix,
)
from .la_core import (
    apply_transform,
    image_to_pixels,
    matrix_properties,
    pixels_to_image,
    project_grayscale,
)


def _load_image(image_bytes: bytes, preview_max: int) -> np.ndarray:
    """Decode image and downscale for responsive live previews."""
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise ValueError("Unsupported image format. Use PNG or JPG.") from exc

    max_size = max(int(preview_max), 300)
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    return np.array(image, dtype=np.float64)


def _to_data_url(image: np.ndarray) -> str:
    """Encode image array as PNG data URL for direct browser rendering."""
    buffer = BytesIO()
    Image.fromarray(image.astype(np.uint8)).save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def run_pipeline(image_bytes: bytes, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Apply all selected operations and return image + LA metrics payload."""
    image = _load_image(image_bytes, settings.get("preview_max", 1280))
    shape = image.shape
    pixels = image_to_pixels(image)

    base_matrix = get_filter_matrix(settings.get("preset", "Identity"))
    hue_matrix = hue_rotation_matrix(settings.get("hue", 0.0))
    transform = blend_with_identity(hue_matrix @ base_matrix, settings.get("strength", 1.0))

    transformed_pixels = apply_transform(pixels, transform)
    if settings.get("grayscale", False):
        transformed_pixels = project_grayscale(transformed_pixels)

    working = pixels_to_image(transformed_pixels, shape).astype(np.float64)
    working = apply_tone_controls(
        working,
        exposure=settings.get("exposure", 0.0),
        contrast=settings.get("contrast", 0.0),
        saturation=settings.get("saturation", 0.0),
        temperature=settings.get("temperature", 0.0),
        tint=settings.get("tint", 0.0),
        gamma=settings.get("gamma", 1.0),
    )
    working = apply_vibrance(working, settings.get("vibrance", 0.0))
    working = apply_unsharp(working, settings.get("sharpen", 0.0))
    working = apply_vignette(working, settings.get("vignette", 0.0))

    processed_pixels = image_to_pixels(working)
    ls_preview_pixels, ls_matrix = apply_least_squares_correction(processed_pixels)
    least_squares_applied = bool(settings.get("least_squares", False))
    if least_squares_applied:
        processed_pixels = ls_preview_pixels

    pca_k = int(np.clip(settings.get("pca_k", 3), 1, 3))
    if pca_k < 3:
        processed_pixels = pca_compress(processed_pixels, pca_k)

    final_image = pixels_to_image(processed_pixels, shape)
    final_pixels = image_to_pixels(final_image)

    props = matrix_properties(transform)
    eigenvalues, eigenvectors, explained, _, cov = covariance_eigen(final_pixels)
    stats = color_statistics(final_pixels)

    return {
        "image": _to_data_url(final_image),
        "width": int(final_image.shape[1]),
        "height": int(final_image.shape[0]),
        "metrics": {
            "rank": props["rank"],
            "nullity": props["nullity"],
            "determinant": round(float(props["determinant"]), 6),
            "invertible": bool(props["invertible"]),
            "condition_number": round(float(props["condition_number"]), 6),
            "trace": round(float(props["trace"]), 6),
            "frobenius_norm": round(float(props["frobenius_norm"]), 6),
            "matrix": np.round(transform, 4).tolist(),
            "rref": np.round(props["rref"], 4).tolist(),
            "least_squares_matrix": np.round(ls_matrix, 4).tolist(),
            "least_squares_applied": least_squares_applied,
            "eigenvalues": np.round(eigenvalues, 6).tolist(),
            "dominant_eigenvector": np.round(eigenvectors[:, 0], 6).tolist(),
            "explained_variance": np.round(explained, 6).tolist(),
            "principal_variance": round(float(explained[0] if explained.size else 0.0), 6),
            "covariance": np.round(cov, 6).tolist(),
            "mean_rgb": np.round(stats["mean_rgb"], 6).tolist(),
            "std_rgb": np.round(stats["std_rgb"], 6).tolist(),
            "dynamic_range": round(float(stats["dynamic_range"]), 6),
        },
    }
