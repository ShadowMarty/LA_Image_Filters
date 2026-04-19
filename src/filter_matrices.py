from typing import Dict, List

import numpy as np

LUMINANCE_VECTOR = np.array([0.299, 0.587, 0.114], dtype=np.float64)

FILTERS: Dict[str, np.ndarray] = {
    "Identity": np.eye(3, dtype=np.float64),
    "Sepia": np.array([[0.393, 0.769, 0.189], [0.349, 0.686, 0.168], [0.272, 0.534, 0.131]], dtype=np.float64),
    "Cinematic": np.array([[1.12, -0.04, -0.08], [-0.02, 1.05, 0.01], [-0.10, 0.08, 1.08]], dtype=np.float64),
    "Vintage": np.array([[0.94, 0.06, 0.02], [0.02, 0.90, 0.04], [-0.02, 0.08, 0.86]], dtype=np.float64),
    "Teal and Gold": np.array([[1.08, -0.02, -0.06], [0.00, 1.02, 0.02], [-0.12, 0.05, 1.10]], dtype=np.float64),
    "Noir": np.array([[0.60, 0.20, 0.20], [0.18, 0.68, 0.14], [0.10, 0.26, 0.64]], dtype=np.float64),
    "Cool": np.array([[0.93, 0.02, 0.00], [0.00, 1.00, 0.00], [0.02, 0.04, 1.10]], dtype=np.float64),
    "Warm": np.array([[1.10, 0.02, 0.00], [0.00, 1.02, 0.00], [0.00, -0.02, 0.90]], dtype=np.float64),
    "No Red": np.array([[0.00, 0.00, 0.00], [0.00, 1.00, 0.00], [0.00, 0.00, 1.00]], dtype=np.float64),
}

YIQ_MATRIX = np.array([[0.299, 0.587, 0.114], [0.596, -0.274, -0.322], [0.211, -0.523, 0.312]], dtype=np.float64)
YIQ_INV_MATRIX = np.linalg.inv(YIQ_MATRIX)


def _clip01(values: np.ndarray) -> np.ndarray:
    return np.clip(values, 0.0, 1.0)


def _as_unit(image: np.ndarray, normalized: bool) -> np.ndarray:
    if normalized:
        return _clip01(image.astype(np.float32, copy=False))
    return _clip01(image.astype(np.float32, copy=False) / 255.0)


def _restore_range(values: np.ndarray, normalized: bool) -> np.ndarray:
    return values if normalized else values * 255.0


def available_filters() -> List[str]:
    return list(FILTERS.keys())


def get_filter_matrix(name: str) -> np.ndarray:
    return FILTERS.get(name, FILTERS["Identity"]).copy()


def blend_with_identity(matrix: np.ndarray, strength: float) -> np.ndarray:
    s = float(np.clip(strength, 0.0, 1.0))
    return (1.0 - s) * np.eye(3, dtype=np.float64) + s * matrix


def hue_rotation_matrix(degrees: float) -> np.ndarray:
    angle = np.deg2rad(float(degrees))
    rotation = np.array([[1.0, 0.0, 0.0], [0.0, np.cos(angle), -np.sin(angle)], [0.0, np.sin(angle), np.cos(angle)]], dtype=np.float64)
    return YIQ_INV_MATRIX @ rotation @ YIQ_MATRIX


def apply_tone_controls(
    image: np.ndarray,
    exposure: float,
    contrast: float,
    saturation: float,
    temperature: float,
    tint: float,
    gamma: float,
    normalized: bool = False,
) -> np.ndarray:
    if (
        abs(float(exposure)) <= 1e-7
        and abs(float(contrast)) <= 1e-7
        and abs(float(saturation)) <= 1e-7
        and abs(float(temperature)) <= 1e-7
        and abs(float(tint)) <= 1e-7
        and abs(float(gamma) - 1.0) <= 1e-7
    ):
        return image

    x = _as_unit(image, normalized)
    x = _clip01(x * (2.0 ** float(exposure)))
    x = _clip01((x - 0.5) * (1.0 + float(contrast)) + 0.5)

    lum = np.tensordot(x, LUMINANCE_VECTOR, axes=([2], [0]))
    gray = lum[:, :, None]
    x = _clip01(gray + (x - gray) * (1.0 + float(saturation)))

    x[:, :, 0] = _clip01(x[:, :, 0] + float(temperature) * 0.08)
    x[:, :, 2] = _clip01(x[:, :, 2] - float(temperature) * 0.08)
    x[:, :, 1] = _clip01(x[:, :, 1] + float(tint) * 0.06)
    x = _clip01(np.power(x, 1.0 / max(float(gamma), 0.01)))
    return _restore_range(x, normalized)


def apply_vibrance(image: np.ndarray, amount: float, normalized: bool = False) -> np.ndarray:
    if abs(float(amount)) <= 1e-7:
        return image

    x = _as_unit(image, normalized)
    sat = np.max(x, axis=2) - np.min(x, axis=2)
    boost = float(np.clip(amount, -1.0, 1.0)) * (1.0 - sat)

    lum = np.tensordot(x, LUMINANCE_VECTOR, axes=([2], [0]))
    gray = lum[:, :, None]
    return _restore_range(_clip01(x + (x - gray) * boost[:, :, None]), normalized)


def apply_unsharp(image: np.ndarray, amount: float, normalized: bool = False) -> np.ndarray:
    a = float(np.clip(amount, 0.0, 2.0))
    if a <= 1e-6:
        return image

    x = _as_unit(image, normalized)
    p = np.pad(x, ((1, 1), (1, 1), (0, 0)), mode="edge")
    blur = (p[:-2, :-2] + p[:-2, 1:-1] + p[:-2, 2:] + p[1:-1, :-2] + p[1:-1, 1:-1] + p[1:-1, 2:] + p[2:, :-2] + p[2:, 1:-1] + p[2:, 2:]) / 9.0
    return _restore_range(_clip01(x + a * (x - blur)), normalized)


def apply_vignette(image: np.ndarray, strength: float, normalized: bool = False) -> np.ndarray:
    s = float(np.clip(strength, 0.0, 1.0))
    if s <= 1e-6:
        return image

    h, w, _ = image.shape
    yy, xx = np.mgrid[0:h, 0:w]
    xx = (xx - (w - 1) / 2.0) / max(w, 1)
    yy = (yy - (h - 1) / 2.0) / max(h, 1)
    radius = np.sqrt(xx * xx + yy * yy)
    mask = np.clip(1.0 - s * np.power(radius * 1.9, 1.4), 0.25, 1.0)
    x = _as_unit(image, normalized)
    return _restore_range(_clip01(x * mask[:, :, None]), normalized)
