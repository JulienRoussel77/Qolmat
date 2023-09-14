---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.4
  kernelspec:
    display_name: env_qolmat_dev
    language: python
    name: env_qolmat_dev
---

```python
%reload_ext autoreload
%autoreload 2

from typing import List

import numpy as np
from numpy.typing import NDArray
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.datasets import make_spd_matrix
from sklearn.preprocessing import StandardScaler

from qolmat.imputations import em_sampler
from qolmat.utils import utils
```

```python
def generate_var1_process(n_samples: int, A: NDArray, B: NDArray, sigma: NDArray) -> NDArray:
    """
    Generate data from a VAR(1) process.

    Parameters
    ----------
    n_samples : int
        Number of samples to generate.
    A : : NDArray
        Coefficient matrix of shape (n_variables, n_variables) for variables relationships.
    B : NDArray
    sigma : NDArray
        Covariance of the error terms.

    Return
    ------
    NDArray
        Generated data.
    """
    n_variables = A.shape[0]
    data = np.zeros((n_samples, n_variables))
    noise = np.random.multivariate_normal(mean=np.zeros(n_variables), cov=sigma, size=n_samples)
    for i in range(1, n_samples):
        data[i] = A.dot(data[i - 1] - B) + B + noise[i]
    return data

def generate_varp_process(n_samples: int, A: List[NDArray], B: NDArray, noise: NDArray) -> NDArray:
    """
    Generate data from a VAR(1) process.

    Parameters
    ----------
    n_samples : int
        Number of samples to generate.
    A : : List[NDArray]
        List of oefficient matrix of shape (n_variables, n_variables) for variables relationships.
    B : NDArray
    sigma : NDArray
        Covariance of the error terms.

    Return
    ------
    NDArray
        Generated data.
    """
    n_variables = A[0].shape[0]
    data = np.zeros((n_samples, n_variables))
    for i in range(1, n_samples):
        for ind, mat_A in enumerate(A):
            data[i] += mat_A.dot(data[i - (ind+1)] - B)
        data[i] = data[i] + B + noise[i]
    return data
```

```python
np.random.seed(41)

d, n = 3, 100
p = 2

A1 = np.array([[0.03, 0.03, 0.13], [0.03, 0.03, 0.14], [0., 0.02, 0.23]], dtype=float)
A2 = np.array([[0.08, 0.1, 0.08], [0.03, 0.16, 0.14], [0., 0.2, 0.23]], dtype=float)
A = [A1, A2]
B = np.array([0.001, 0.023, 0.019])
sigma = make_spd_matrix(n_dim=d, random_state=208) * 1e-5
noise = np.random.multivariate_normal(mean=np.zeros(d), cov=sigma, size=n)

X = generate_varp_process(n, A, B, noise).T
X.shape
```

```python
r = np.random.RandomState(208)

d, n = 2, 10_000
p = 2

A1 = np.array([[0.03, 0.03], [0.14, 0.16]], dtype=float)
A2 = np.array([[0.08, 0.1], [0.14, 0.08]], dtype=float)
A3 = np.array([[0.009, 0.003], [0.09, 0.036]], dtype=float)
A = [A1, A2]#, A3]
B = np.array([0] * d) # [0.001, 0.023, 0.019, 0]
sigma = make_spd_matrix(n_dim=d, random_state=208) * 1e-5
noise = np.random.multivariate_normal(mean=np.zeros(d), cov=sigma, size=n)

X = generate_varp_process(n, A, B, noise).T
X.shape
```

```python
mask = np.array(np.full_like(X, False), dtype=bool)
for j in range(X.shape[0]):
    ind = np.random.choice(np.arange(X.shape[1]), size=np.int64(np.ceil(X.shape[1]*0.1)), replace=False)
    mask[j,ind] = True
X_missing = X.copy()
X_missing[mask] = np.nan
```

```python

```

```python
plt.figure(figsize=(13,3))
plt.plot(X_missing.T)
plt.show()
```

```python
%%time
em = em_sampler.MultiNormalEM(method="sample", max_iter_em=50, n_iter_ou=200)
em.fit(X_missing)
X_imputed = em.transform(X_missing)

em = em_sampler.MultiNormalEM(method="sample", max_iter_em=50, n_iter_ou=200)
X_imputed = em.fit_transform(X_missing)
```

```python
%%time
varpem = em_sampler.VARpEM(method="sample", max_iter_em=50, n_iter_ou=200, p=2, stagnation_loglik=2)
varpem.fit(X_missing)
X_imputed = varpem.transform(X_missing)
varpem.A
```

```python
varpem.p
```

```python
%%time
varpem = em_sampler.VARpEM(method="sample", max_iter_em=50, n_iter_ou=200, p=None, stagnation_loglik=2)
X_imputed = varpem.fit_transform(X_missing)
varpem.A
```

```python
print(np.allclose(A[0], varpem.A[0], rtol=1e-1, atol=1e-1))
print(np.allclose(A[1], varpem.A[1], rtol=1e-1, atol=1e-1))
print(np.allclose(B, varpem.B, rtol=1e-1, atol=1e-1))
```

```python
varpem.B, B
```

```python
X.shape, X_imputed.shape
```

```python
i = 2

plt.figure(figsize=(13,3))
plt.plot(X[i,:], lw=1.5)
plt.plot(X_imputed[i,:], "-.", lw=1.5)
plt.show()
```

```python
varpem.A
```

```python
A
```

```python
import statsmodels.api as sm
from statsmodels.tsa.api import VAR

def fit_var_model(data: NDArray, p: int, criterion: str="aic"):
    model = VAR(data)
    result = model.fit(maxlags=p, ic=criterion)
    return result

def get_lag_p(X: NDArray, max_lag_order: int=10, criterion: str="aic") -> int:
    if criterion not in ["aic", "bic"]:
        raise AssertionError("Invalid criterion. `criterion` must be `aic`or `bic`.")

    best_p = 1
    best_criteria_value = float('inf')
    for p in range(1, max_lag_order + 1):
        model_result = fit_var_model(X.T, p, criterion=criterion)
        if criterion == "aic":
            criteria_value = model_result.aic
        else:
            criteria_value = model_result.bic

        if criteria_value < best_criteria_value:
            best_p = p
            best_criteria_value = criteria_value

    return best_p
```

```python
criterion = "bic"
X_interp = utils.linear_interpolation(X)
best_p = get_lag_p(X, criterion=criterion)
print("Best lag order (p) based on AIC:", best_p)
```

```python

```

```python

```

```python

```

```python
# generate data from multivariate normal
d = 20
r = np.random.RandomState(28)
mean = [r.uniform(d) for _ in range(d)]
covariance = make_spd_matrix(n_dim=d, random_state=28)
n = 1000 # Samples to draw
X = np.random.multivariate_normal(mean=mean, cov=covariance, size=n)
X = X.T
```

```python
# create missing value (random)
mask = np.array(np.full_like(X, False), dtype=bool)
for j in range(X.shape[0]):
    ind = np.random.choice(np.arange(X.shape[1]), size=np.int64(np.ceil(X.shape[1]*0.1)), replace=False)
    mask[j,ind] = True
X_missing = X.copy()
X_missing[mask] = np.nan
```

```python
%%time
em = em_sampler.MultiNormalEM(max_iter_em=40, n_iter_ou=100)
X_imputed = em.fit_transform(X_missing).T
covariance_imputed = np.cov(X_imputed, rowvar=False)
mean_imputed = np.mean(X_imputed, axis=0)
```

```python
plt.figure(figsize=(8,3))
plt.plot(em.dict_criteria_stop["logliks"], "-o")
plt.ylabel("log-likelihood")
plt.show()
```

```python
plt.figure(figsize=(8,3))
plt.plot(abs(pd.Series(em.dict_criteria_stop["logliks"]).diff())[1:], "-o")
plt.ylabel("LL criterion")
plt.show()
```

```python
print(np.sum(np.abs(mean-mean_imputed)) / np.sum(np.abs(mean)) < 1e-2)
print(np.sum(np.abs(covariance-covariance_imputed)) / np.sum(np.abs(covariance)) < 1e-1)
```

```python
%%time
varem = em_sampler.VAR1EM(method="sample", max_iter_em=200, n_iter_ou=80)
X_imputed = varem.fit_transform(X_missing).T
covariance_imputed = np.cov(X_imputed, rowvar=False)
mean_imputed = np.mean(X_imputed, axis=0)
```

```python
plt.figure(figsize=(8,3))
plt.plot(varem.dict_criteria_stop["logliks"], "-o")
plt.ylabel("log-likelihood")
plt.show()
```

```python
plt.figure(figsize=(8,3))
plt.plot(abs(pd.Series(varem.dict_criteria_stop["logliks"]).diff(2)), "-o")
plt.ylabel("LL criterion")
plt.show()
```

```python
print(np.sum(np.abs(mean-mean_imputed)) / np.sum(np.abs(mean)) < 1e-2)
print(np.sum(np.abs(covariance-covariance_imputed)) / np.sum(np.abs(covariance)) < 1e-1)
```

**A and B estimates for VAR1EM**

```python
d, n = 2, 1000
r = np.random.RandomState(208)
A = np.array([[0.5, 0.5], [0, 1]], dtype=float) #np.random.uniform(low=-5e-2, high=5e-2, size=(d, d))
B = np.array([0.] * d) #np.random.uniform(low=-5e-3, high=5e-3, size=(d,))
sigma = make_spd_matrix(n_dim=d, random_state=208) * 1e-6

X = generate_var1_process(n, A, B, sigma).T
X.shape
```

```python
plt.figure(figsize=(12,3))
plt.plot(X.T)
plt.show()
```

```python
mask = np.array(np.full_like(X, False), dtype=bool)
for j in range(X.shape[0]):
    ind = np.random.choice(np.arange(X.shape[1]), size=np.int64(np.ceil(X.shape[1]*0.1)), replace=False)
    mask[j,ind] = True
X_missing = X.copy()
X_missing[mask] = np.nan
```

```python
%%time
varem = em_sampler.VAR1EM(method="sample", max_iter_em=600, n_iter_ou=200)
X_imputed = varem.fit_transform(X_missing).T
covariance_imputed = np.cov(X_imputed, rowvar=False)
mean_imputed = np.mean(X_imputed, axis=0)
```

```python
print(np.sum(np.abs(A-varem.A)) / np.sum(np.abs(A)) < 1e-2)
print(np.sum(np.abs(B-varem.B)) / np.sum(np.abs(B)) < 1e-1)
```

```python
varem.A
```

```python
vmin = min(np.min(varem.A), np.min(A))
vmax = max(np.max(varem.A), np.max(A))
fig, ax = plt.subplots(1, 2, figsize=(8,3))
ax[0].imshow(A, vmin=vmin, vmax=vmax, cmap="inferno")
ax[0].set_title("True")
im = ax[1].imshow(varem.A, vmin=0, vmax=1, cmap="inferno")
ax[1].set_title("Estimated")
plt.colorbar(im, ax=ax[1])
plt.show()
```

```python
plt.figure(figsize=(12,3))
plt.plot(B, "-s", label="True")
plt.plot(varem.B, "-o", label="Estimated")
plt.legend()
plt.show()
```

```python

```