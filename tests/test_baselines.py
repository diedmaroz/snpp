import contexts as ctx
import numpy as np
from scipy.sparse import csr_matrix

from numpy.testing import assert_almost_equal, assert_allclose

from snpp.utils.data import make_signed_matrix
from snpp.cores.spectral import build_laplacian_related_matrices, \
    build_laplacian_related_matrices_sparse
from snpp.cores.zheng2015 import build_L_sns as build_zheng2015
from snpp.cores.kunegis2010 import build_L as build_kunegis2010


def test_build_laplacian_related_matrices(Q1):
    N = 4
    W_p, W_n, D_p, D_n, D_hat = build_laplacian_related_matrices(Q1)
    assert_almost_equal(
        make_signed_matrix(N, [(1, 2), (3, 4)], []),
        W_p)

    expected_Wn = - make_signed_matrix(N, [], [(1, 3)])
    np.fill_diagonal(expected_Wn, 0)
    assert_almost_equal(
        expected_Wn,
        W_n)

    assert_almost_equal(
        np.diag([2, 2, 2, 2]),
        D_p)
    assert_almost_equal(
        np.diag([1, 0, 1, 0]),
        D_n)
    assert_almost_equal(
        np.diag([3, 2, 3, 2]),
        D_hat
    )


def test_build_laplacian_related_matrices_sparse(Q1):
    W_p, W_n, D_p, D_n, D_hat = build_laplacian_related_matrices(Q1)
    Ws_p, Ws_n, Ds_p, Ds_n, Ds_hat = build_laplacian_related_matrices_sparse(csr_matrix(Q1))
    assert_allclose(W_p, Ws_p.toarray())
    assert_allclose(W_n, Ws_n.toarray())
    assert_allclose(D_p, Ds_p.toarray())
    assert_allclose(D_n, Ds_n.toarray())
    assert_allclose(D_hat, Ds_hat.toarray())


def test_build_zheng2015(Q1):
    L = build_zheng2015(Q1)
    assert L.shape == (4, 4)


def test_build_kunegis2010(Q1):
    L = build_kunegis2010(Q1)
    assert L.shape == (4, 4)
