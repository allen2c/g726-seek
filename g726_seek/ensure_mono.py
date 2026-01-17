import numpy as np


def ensure_mono(data: np.ndarray) -> np.ndarray:
    if data.ndim == 1:
        return data
    elif data.ndim == 2:
        return data.mean(axis=1)
    else:
        raise ValueError(f"Unsupported number of dimensions: {data.ndim}")
