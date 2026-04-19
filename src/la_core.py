"""Core linear algebra utilities focused on matrix operations and space structure."""

from typing import Dict, Tuple

import numpy as np

from .filter_matrices import LUMINANCE_VECTOR


def image_to_pixels(image: np.ndarray) -> np.ndarray:
    """Flatten HxWx3 image into Nx3 pixel matrix."""
    return image.reshape(-1, 3).astype(np.float32, copy=False)


def pixels_to_image(pixels: np.ndarray, shape: Tuple[int, int, int]) -> np.ndarray:
    """Restore Nx3 pixel matrix into image tensor with clipping."""
    return np.clip(pixels, 0.0, 255.0).astype(np.uint8).reshape(shape)


def apply_transform(pixels: np.ndarray, transform: np.ndarray) -> np.ndarray:
    """Apply color transform T using row-vector equivalent of v' = Tv."""
    return np.clip(pixels @ transform.T, 0.0, 255.0)


def project_grayscale(pixels: np.ndarray) -> np.ndarray:
    """Project RGB vectors onto luminance direction u."""
    u = LUMINANCE_VECTOR
    return np.outer((pixels @ u) / float(u @ u), u)


def rref(matrix: np.ndarray, tol: float = 1e-10) -> np.ndarray:
    """Compute row-reduced echelon form with Gaussian elimination."""
    a = matrix.astype(np.float64).copy()
    rows, cols, pivot_row = a.shape[0], a.shape[1], 0
    for col in range(cols):
        if pivot_row >= rows:
            break
        max_row = pivot_row + int(np.argmax(np.abs(a[pivot_row:, col])))
        if abs(a[max_row, col]) < tol:
            continue
        if max_row != pivot_row:
            a[[pivot_row, max_row]] = a[[max_row, pivot_row]]
        a[pivot_row] = a[pivot_row] / a[pivot_row, col]
        for row in range(rows):
            if row != pivot_row:
                a[row] -= a[row, col] * a[pivot_row]
        pivot_row += 1
    a[np.abs(a) < tol] = 0.0
    return a


def matrix_properties(transform: np.ndarray) -> Dict[str, object]:
    """Return structural matrix diagnostics used in viva and dashboard."""
    det = float(np.linalg.det(transform))
    rank = int(np.linalg.matrix_rank(transform))
    cond = float(np.linalg.cond(transform))
    return {
        "rank": rank,
        "nullity": 3 - rank,
        "determinant": det,
        "invertible": abs(det) > 1e-8,
        "condition_number": cond if np.isfinite(cond) else 1e12,
        "trace": float(np.trace(transform)),
        "frobenius_norm": float(np.linalg.norm(transform)),
        "rref": rref(transform),
    }
