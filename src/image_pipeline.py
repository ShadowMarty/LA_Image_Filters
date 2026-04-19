"""End-to-end image pipeline: loading, filtering, analysis, and response packing."""

import base64
from io import BytesIO
from typing import Any, Dict, Optional

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


def _load_image(image_bytes: bytes, preview_max: Optional[int]) -> np.ndarray:
    """Decode image and optionally downscale for responsive live previews."""
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise ValueError("Unsupported image format. Use PNG or JPG.") from exc

    if preview_max is not None:
        max_size = max(int(preview_max), 300)
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    return np.asarray(image, dtype=np.uint8)


def _to_data_url(image: np.ndarray, fmt: str = "PNG", quality: int = 92) -> str:
    """Encode image array as image data URL for direct browser rendering."""
    buffer = BytesIO()
    format_name = (fmt or "PNG").upper()
    image_obj = Image.fromarray(image.astype(np.uint8, copy=False))
    if format_name == "JPEG":
        image_obj.save(buffer, format="JPEG", quality=int(np.clip(quality, 40, 100)))
        mime = "image/jpeg"
    else:
        image_obj.save(buffer, format="PNG")
        mime = "image/png"
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def run_pipeline(
    image_bytes: bytes,
    settings: Dict[str, Any],
    keep_resolution: bool = False,
    preview_format: str = "PNG",
    preview_quality: int = 92,
) -> Dict[str, Any]:
    """Apply all selected operations and return image + LA metrics payload."""
    preview_max = None if keep_resolution else settings.get("preview_max", 1280)
    image = _load_image(image_bytes, preview_max)
    shape = image.shape
    pixels = image_to_pixels(image)

    base_matrix = get_filter_matrix(settings.get("preset", "Identity"))
    hue_matrix = hue_rotation_matrix(settings.get("hue", 0.0))
    transform = blend_with_identity(hue_matrix @ base_matrix, settings.get("strength", 1.0))
    pixel_transform = transform.astype(np.float32, copy=False)

    transformed_pixels = apply_transform(pixels, pixel_transform)
    if settings.get("grayscale", False):
        transformed_pixels = project_grayscale(transformed_pixels)

    working = np.clip(transformed_pixels.reshape(shape).astype(np.float32, copy=False) / 255.0, 0.0, 1.0)
    working = apply_tone_controls(
        working,
        exposure=settings.get("exposure", 0.0),
        contrast=settings.get("contrast", 0.0),
        saturation=settings.get("saturation", 0.0),
        temperature=settings.get("temperature", 0.0),
        tint=settings.get("tint", 0.0),
        gamma=settings.get("gamma", 1.0),
        normalized=True,
    )
    working = apply_vibrance(working, settings.get("vibrance", 0.0), normalized=True)
    working = apply_unsharp(working, settings.get("sharpen", 0.0), normalized=True)
    working = apply_vignette(working, settings.get("vignette", 0.0), normalized=True)

    processed_pixels = image_to_pixels(working * 255.0)
    ls_preview_pixels, ls_matrix = apply_least_squares_correction(processed_pixels)
    least_squares_applied = bool(settings.get("least_squares", False))
    if least_squares_applied:
        processed_pixels = ls_preview_pixels

    pca_k = int(np.clip(settings.get("pca_k", 3), 1, 3))
    if pca_k < 3:
        processed_pixels = pca_compress(processed_pixels, pca_k)

    final_image = pixels_to_image(processed_pixels, shape)
    final_pixels = final_image.reshape(-1, 3)

    props = matrix_properties(transform.astype(np.float64, copy=False))
    eigenvalues, eigenvectors, explained, _, cov = covariance_eigen(final_pixels)
    stats = color_statistics(final_pixels)

    return {
        "image": _to_data_url(final_image, fmt=preview_format, quality=preview_quality),
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
