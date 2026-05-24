"""Marchenko-Pastur and Ledoit-Péché correlation cleaning primitives.

Pure-numpy implementations used to denoise sample correlation matrices before
mean-variance portfolio optimization. References:

- Marchenko & Pastur 1967 — limiting eigenvalue distribution of large sample
  covariance matrices.
- Laloux, Cizeau, Bouchaud, Potters 1999 — eigenvalue clipping on S&P500.
- Ledoit & Péché 2011 — optimal nonlinear shrinkage via Stieltjes transform.
"""

import numpy as np


def mp_edges(c: float) -> tuple[float, float]:
    """Marchenko-Pastur bulk edges for aspect ratio c = N/T.

    For a sample correlation matrix C built from N variables × T iid
    standardized noise observations, the eigenvalues of C lie almost surely
    in [lambda_minus, lambda_plus] as N, T → ∞ with N/T → c.

    Args:
        c: aspect ratio N/T, must be > 0.

    Returns:
        (lambda_minus, lambda_plus) — closed interval bounds of the noise bulk.

    Raises:
        ValueError: if c <= 0.
    """
    if c <= 0:
        raise ValueError(f"c must be positive, got {c}")
    sqrt_c = np.sqrt(c)
    return ((1.0 - sqrt_c) ** 2, (1.0 + sqrt_c) ** 2)


def clip_mp(C: np.ndarray, c: float) -> np.ndarray:
    """Marchenko-Pastur eigenvalue clipping (Laloux et al. 1999).

    Eigenvalues falling inside the MP noise bulk [lambda_-, lambda_+] are
    replaced by their average (preserving the bulk trace contribution). Outlier
    eigenvalues are left untouched. The matrix is reconstructed and its
    diagonal renormalized to 1 to remain a valid correlation matrix.

    Args:
        C: NxN sample correlation matrix (symmetric, positive semidefinite).
        c: aspect ratio N/T of the underlying sample.

    Returns:
        Cleaned NxN correlation matrix.

    Raises:
        ValueError: if C is not square.
    """
    if C.shape[0] != C.shape[1]:
        raise ValueError(f"C must be square, got {C.shape}")

    lo, hi = mp_edges(c)
    eigvals, eigvecs = np.linalg.eigh(C)
    in_bulk = (eigvals >= lo) & (eigvals <= hi)
    if in_bulk.any():
        bulk_mean = eigvals[in_bulk].mean()
        eigvals_clean = np.where(in_bulk, bulk_mean, eigvals)
    else:
        eigvals_clean = eigvals.copy()

    C_clean = (eigvecs * eigvals_clean) @ eigvecs.T
    d = np.sqrt(np.diag(C_clean))
    C_clean = C_clean / np.outer(d, d)
    return 0.5 * (C_clean + C_clean.T)
