import numpy as np
import pytest

from rmt.cleaning import clip_mp, mp_edges, shrink_lp


def test_mp_edges_classical_ratios():
    lo, hi = mp_edges(c=0.5)
    assert abs(lo - 0.0858) < 1e-3
    assert abs(hi - 2.9142) < 1e-3

    lo, hi = mp_edges(c=1.0)
    assert abs(lo - 0.0) < 1e-9
    assert abs(hi - 4.0) < 1e-9


def test_mp_edges_invalid_c():
    with pytest.raises(ValueError):
        mp_edges(c=0.0)
    with pytest.raises(ValueError):
        mp_edges(c=-0.1)


def test_clip_mp_preserves_trace():
    np.random.seed(42)
    N, T = 50, 200
    X = np.random.randn(N, T)
    X = (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)
    C = (X @ X.T) / T

    C_clean = clip_mp(C, c=N / T)

    assert C_clean.shape == (N, N)
    np.testing.assert_allclose(np.diag(C_clean), 1.0, atol=1e-10)
    eigs = np.linalg.eigvalsh(C_clean)
    assert eigs.max() < 1.5, f"expected most eigs near 1 for pure noise, got max={eigs.max()}"


def test_clip_mp_preserves_signal_eigenvalues():
    np.random.seed(0)
    N, T = 50, 200
    factor = np.random.randn(T)
    loadings = np.ones(N) * 0.5
    noise = np.random.randn(N, T) * 0.5
    X = loadings[:, None] * factor[None, :] + noise
    X = (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)
    C = (X @ X.T) / T

    C_clean = clip_mp(C, c=N / T)

    eigs_raw = sorted(np.linalg.eigvalsh(C).tolist(), reverse=True)
    eigs_clean = sorted(np.linalg.eigvalsh(C_clean).tolist(), reverse=True)
    assert abs(eigs_raw[0] - eigs_clean[0]) < 1.0, (
        f"top eig changed too much: raw={eigs_raw[0]:.3f} clean={eigs_clean[0]:.3f}"
    )


def test_clip_mp_rejects_nonsquare():
    with pytest.raises(ValueError):
        clip_mp(np.zeros((3, 4)), c=0.5)


def test_shrink_lp_shape_and_diagonal():
    np.random.seed(1)
    N, T = 30, 100
    X = np.random.randn(N, T)
    X = (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)
    C = (X @ X.T) / T
    C_shrunk = shrink_lp(C, c=N / T)
    assert C_shrunk.shape == (N, N)
    np.testing.assert_allclose(np.diag(C_shrunk), 1.0, atol=1e-9)


def test_shrink_lp_pulls_eigenvalues_toward_one():
    """For pure noise, shrinkage must reduce eigenvalue spread."""
    np.random.seed(2)
    N, T = 50, 100
    X = np.random.randn(N, T)
    X = (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)
    C = (X @ X.T) / T
    eigs_raw = np.linalg.eigvalsh(C)
    spread_raw = eigs_raw.max() - eigs_raw.min()
    C_shrunk = shrink_lp(C, c=N / T)
    eigs_shrunk = np.linalg.eigvalsh(C_shrunk)
    spread_shrunk = eigs_shrunk.max() - eigs_shrunk.min()
    assert spread_shrunk < spread_raw, (
        f"shrinkage didn't reduce spread: raw={spread_raw:.3f} shrunk={spread_shrunk:.3f}"
    )


def test_shrink_lp_rejects_nonsquare():
    with pytest.raises(ValueError):
        shrink_lp(np.zeros((3, 4)), c=0.5)
