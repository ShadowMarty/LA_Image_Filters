"""Numerical analysis utilities for correction, trend discovery, and compression."""

from typing import Tuple
import numpy as np


def color_statistics(pixels: np.ndarray) -> dict:
    """Return normalized mean/std vectors and dynamic range for presentation."""
    sampled = _sample_pixels(pixels, max_points=50000)
    x = np.clip(sampled.astype(np.float32, copy=False) / 255.0, 0.0, 1.0)
    return {
        "mean_rgb": np.mean(x, axis=0),
        "std_rgb": np.std(x, axis=0),
        "dynamic_range": float(np.max(x) - np.min(x)),
    }


def _sample_pixels(pixels: np.ndarray, max_points: int = 15000) -> np.ndarray:
    """Subsample large images for fast covariance/eigen computations."""
    if pixels.shape[0] <= max_points:
        return pixels
    idx = np.linspace(0, pixels.shape[0] - 1, max_points, dtype=int)
    return pixels[idx]


def least_squares_correction_matrix(pixels: np.ndarray) -> np.ndarray:
    """Compute X_hat that best maps observed colors to a balanced target set."""
    sampled = _sample_pixels(pixels, max_points=60000)
    x = np.clip(sampled.astype(np.float32, copy=False) / 255.0, 0.0, 1.0)
    mean_rgb = x.mean(axis=0)
    mean_gray = float(np.mean(mean_rgb))

    a = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], mean_rgb], dtype=np.float64)
    b = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [mean_gray, mean_gray, mean_gray]],
        dtype=np.float64,
    )
    x_hat, _, _, _ = np.linalg.lstsq(a, b, rcond=None)
    return x_hat


def apply_least_squares_correction(pixels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Apply least-squares color correction and return corrected pixels and X_hat."""
    x_hat = least_squares_correction_matrix(pixels)
    corrected = np.clip((pixels.astype(np.float32, copy=False) / 255.0) @ x_hat, 0.0, 1.0) * 255.0
    return corrected, x_hat


def covariance_eigen(pixels: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute covariance and sorted eigendecomposition of color distribution."""
    x = _sample_pixels(pixels).astype(np.float32, copy=False) / 255.0
    mean = x.mean(axis=0)
    xc = x - mean
    cov = (xc.T @ xc) / max(x.shape[0] - 1, 1)

    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]

    total = float(np.sum(eigenvalues))
    explained = eigenvalues / total if total > 0 else np.zeros_like(eigenvalues)
    return eigenvalues, eigenvectors, explained, mean, cov


def pca_compress(pixels: np.ndarray, k: int = 2) -> np.ndarray:
    """Reconstruct colors using top-k principal directions."""
    k = int(np.clip(k, 1, 3))
    x = np.clip(pixels.astype(np.float32, copy=False) / 255.0, 0.0, 1.0)
    mean = x.mean(axis=0)
    xc = x - mean
    cov = (xc.T @ xc) / max(x.shape[0] - 1, 1)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    basis = eigenvectors[:, np.argsort(eigenvalues)[::-1]][:, :k]
    recon = (xc @ basis) @ basis.T + mean
    return np.clip(recon * 255.0, 0.0, 255.0)