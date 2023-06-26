from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from qolmat.imputations.rpca import rpca_utils
from qolmat.imputations.rpca.rpca import RPCA
from qolmat.utils import utils


class RPCAPCP(RPCA):
    """
    This class implements the basic RPCA decomposition using Alternating Lagrangian Multipliers.

    References
    ----------
    Candès, Emmanuel J., et al. "Robust principal component analysis."
    Journal of the ACM (JACM) 58.3 (2011): 1-37

    Parameters
    ----------
    mu: Optional
        Parameter for the convergence and shrinkage operator
    lam: Optional
        Penalizing parameter for the sparse array
    """

    def __init__(
        self,
        period: Optional[int] = None,
        mu: Optional[float] = None,
        lam: Optional[float] = None,
        max_iter: int = int(1e4),
        tol: float = 1e-6,
    ) -> None:
        super().__init__(
            period=period,
            max_iter=max_iter,
            tol=tol,
        )
        self.mu = mu
        self.lam = lam

    def get_params_scale(self, D: NDArray):
        mu = D.size / (4.0 * rpca_utils.l1_norm(D))
        lam = 1 / np.sqrt(np.max(D.shape))
        dict_params = {"mu": mu, "lam": lam}
        return dict_params

    def decompose_rpca(self, D: NDArray, Omega: NDArray) -> Tuple[NDArray, NDArray]:
        params_scale = self.get_params_scale(D)

        mu = params_scale["mu"] if self.mu is None else self.mu
        lam = params_scale["lam"] if self.lam is None else self.lam

        D_norm = np.linalg.norm(D, "fro")

        A: NDArray = np.full_like(D, 0)
        Y: NDArray = np.full_like(D, 0)

        errors: NDArray = np.full((self.max_iter,), fill_value=np.nan)

        M: NDArray = D - A
        for iteration in range(self.max_iter):
            M = rpca_utils.svd_thresholding(D - A + Y / mu, 1 / mu)
            A = rpca_utils.soft_thresholding(D - M + Y / mu, lam / mu)
            # A[~Omega] = (D - M)[~Omega]

            A[~Omega] = 0  # missing values are not outliers

            Y += mu * (D - M - A)

            error = np.linalg.norm(D - M - A, "fro") / D_norm
            errors[iteration] = error

            if error < self.tol:
                break

        # Check that the functional minimized by the RPCA
        # is smaller at the end than at the beginning
        starting_value = np.linalg.norm(D, "nuc")
        ending_value = np.linalg.norm(M, "nuc") + lam * rpca_utils.l1_norm(A)
        if starting_value + 1e-9 < ending_value:
            print(
                """RPCA algorithm may provide bad results.
                    ||D||_* + lam ||A||_1 is larger
                    at the end of the algorithm than at the start. """
            )

        return M, A
