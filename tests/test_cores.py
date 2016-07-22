import contexts as ctx

import random
import numpy as np
import pytest
from numpy.testing import assert_almost_equal
from snpp.cores.lowrank import alq


@pytest.fixture
def Q1():
    """a simple signed matrix
    """
    random.seed(12345)
    np.random.seed(12345)

    N = 4
    friends = [(1, 2), (3, 4)]
    enemies = [(1, 3)]

    Q = np.zeros((N, N))
    for i, j in friends:
        Q[i-1, j-1] = Q[j-1, i-1] = 1
    for i, j in enemies:
        Q[i-1, j-1] = Q[j-1, i-1] = -1
    for i in range(N):
        Q[i, i] = 1
        
    return Q
    

def test_lowrank_alq(Q1):
    exp = np.array([[ 1.,  1.,  -1.,  -1.],
                    [ 1.,  1.,  -1.,  -1.],
                    [-1.,  -1.,  1.,  1.],
                    [-1.,  -1.,  1.,  1.]])

    for m in ["random", "svd"]:
        X, Y, _ = alq(Q1, k=2, lambda_=0.1,
                      max_iter=20,
                      init_method=m)
    
        assert_almost_equal(np.sign(np.dot(X, Y)),
                            exp)

