.. -*- mode: rst -*-

|GitHubActions|_ |ReadTheDocs|_ |License|_ |PythonVersion|_ |PyPi|_ |Release|_ |Commits|_

.. |GitHubActions| image:: https://github.com/Quantmetry/qolmat/actions/workflows/test.yml/badge.svg
.. _GitHubActions: https://github.com/Quantmetry/qolmat/actions

.. |ReadTheDocs| image:: https://readthedocs.org/projects/qolmat/badge
.. _ReadTheDocs: https://qolmat.readthedocs.io/en/latest

.. |License| image:: https://img.shields.io/github/license/Quantmetry/qolmat
.. _License: https://github.com/Quantmetry/qolmat/blob/main/LICENSE

.. |PythonVersion| image:: https://img.shields.io/pypi/pyversions/qolmat
.. _PythonVersion: https://pypi.org/project/qolmat/

.. |PyPi| image:: https://img.shields.io/pypi/v/qolmat
.. _PyPi: https://pypi.org/project/qolmat/

.. |Release| image:: https://img.shields.io/github/v/release/Quantmetry/qolmat
.. _Release: https://github.com/Quantmetry/qolmat

.. |Commits| image:: https://img.shields.io/github/commits-since/Quantmetry/qolmat/latest/main
.. _Commits: https://github.com/Quantmetry/qolmat/commits/main

.. image:: https://github.com/Quantmetry/qolmat/tree/main/docs/images/logo.png
    :align: center

Qolmat -  The Tool for Data Imputation
======================================

**Qolmat** provides a convenient way to estimate optimal data imputation techniques by leveraging scikit-learn-compatible algorithms. Users can compare various methods based on different evaluation metrics.

🔗 Requirements
===============

Python 3.8+

🛠 Installation
===============

Install via `pip`:

.. code:: sh

    $ pip install qolmat

If you need to use tensorflow, you can install it with the following 'pip' command:

.. code:: sh

    $ pip install qolmat[tensorflow]

To install directly from the github repository :

.. code:: sh

    $ pip install git+https://github.com/Quantmetry/qolmat

⚡️ Quickstart
==============

Let us start with a basic imputation problem. Here, we generate one-dimensional noisy time series.

.. code:: sh

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    np.random.seed(42)
    t = np.linspace(0,1,1000)
    y = np.cos(2*np.pi*t*10)+np.random.randn(1000)/2
    df = pd.DataFrame({'y': y}, index=t)

With **Qolmat**, it's perfectly possible to generate missing data using the hole generators. In this example, we generate a Missing Complet At Random (MCAR) hole.
Thus, you need to import the hole generators with ``from qolmat.benchmark import missing_patterns``.

.. code:: sh

    from qolmat.benchmark import missing_patterns

    ratio_masked = 0.2
    mean_size = 20
    generator = missing_patterns.GeometricHoleGenerator(1, ratio_masked=ratio_masked, subset = df.columns, random_state=42)
    generator.dict_probas_out = {'y': 1 / mean_size}
    generator.dict_ratios = {'y': 1 / len(df.columns) }
    mask = generator.generate_mask(df)
    df_with_nan = df[~mask]


    plt.figure(figsize=(25,4))
    plt.plot(df['y'],'.r')
    plt.plot(df_with_nan['y'],'.b')
    plt.legend(['Data', 'Missing data'])
    plt.savefig('figure.png')
    plt.show()

.. image:: https://github.com/Quantmetry/qolmat/tree/main/docs/images/readme1.png
    :align: center

To impute missing data, there are several methods that can be imported with ``from qolmat.imputations import imputers``.
The creation of an imputation dictionary will enable us to benchmark the various imputations.

.. code:: sh

    from sklearn.linear_model import LinearRegression
    from qolmat.imputations import imputers

    imputer_mean = imputers.ImputerMean()
    imputer_median = imputers.ImputerMedian()
    imputer_mode = imputers.ImputerMode()
    imputer_locf = imputers.ImputerLOCF()
    imputer_nocb = imputers.ImputerNOCB()
    imputer_interpol = imputers.ImputerInterpolation(method="cubic")
    imputer_spline = imputers.ImputerInterpolation(method="spline", order=2)
    imputer_shuffle = imputers.ImputerShuffle()
    imputer_residuals = imputers.ImputerResiduals(period=10, model_tsa="additive", extrapolate_trend="freq", method_interpolation="linear")
    imputer_rpca = imputers.ImputerRPCA(columnwise=True, period=10, max_iter=200, tau=2, lam=.3)
    imputer_rpca_opti = imputers.ImputerRPCA(columnwise=True, period = 10, max_iter=100)
    imputer_ou = imputers.ImputerEM(model="multinormal", method="sample", max_iter_em=34, n_iter_ou=15, dt=1e-3)
    imputer_tsou = imputers.ImputerEM(model="VAR1", method="sample", max_iter_em=34, n_iter_ou=15, dt=1e-3)
    imputer_tsmle = imputers.ImputerEM(model="VAR1", method="mle", max_iter_em=34, n_iter_ou=15, dt=1e-3)
    imputer_knn = imputers.ImputerKNN(k=10)
    imputer_mice = imputers.ImputerMICE(estimator=LinearRegression(), sample_posterior=False, max_iter=100, missing_values=np.nan)
    imputer_regressor = imputers.ImputerRegressor(estimator=LinearRegression())

    dict_imputers = {
        "mean": imputer_mean,
        "median": imputer_median,
        "mode": imputer_mode,
        "interpolation": imputer_interpol,
        "spline": imputer_spline,
        "shuffle": imputer_shuffle,
        "residuals": imputer_residuals,
        "OU": imputer_ou,
        "TSOU": imputer_tsou,
        "TSMLE": imputer_tsmle,
        "RPCA": imputer_rpca,
        "RPCA_opti": imputer_rpca_opti,
        "locf": imputer_locf,
        "nocb": imputer_nocb,
        "knn": imputer_knn,
        "ols": imputer_regressor,
        "mice_ols": imputer_mice,
    }

It is possible to define a parameter dictionary for an imputer with three pieces of information: min, max and type. The aim of the dictionary is to determine the optimal parameters for data imputation. Here, we call this dictionary ``dict_config_opti``.

.. code:: sh

    search_params = {
        "RPCA_opti": {
            "tau": {"min": .5, "max": 5, "type":"Real"},
            "lam": {"min": .1, "max": 1, "type":"Real"},
        }
    }

Then with the comparator function in ``from qolmat.benchmark import comparator``, we can compare the different imputation methods while determining the optimal parameters we've requested in the dictionary. For more details on how imputors and comparator work, please see the following `link <https://qolmat.readthedocs.io/en/latest/explanation.html>`_.

.. code:: sh

    from qolmat.benchmark import comparator

    generator_holes = missing_patterns.EmpiricalHoleGenerator(n_splits=4, ratio_masked=0.1)

    comparison = comparator.Comparator(
        dict_imputers,
        ['y'],
        generator_holes = generator_holes,
        metrics = ["mae", "wmape", "KL_columnwise", "ks_test", "energy"],
        n_calls_opt = 10,
        dict_config_opti = dict_config_opti,
    )
    results = comparison.compare(df_with_nan)

We can observe the benchmark results.

.. code:: sh

    df_plot_y = results.loc["mae", "y"]
    plt.figure(figsize=(25,5))
    plt.bar(df_plot_y.index, df_plot_y)
    plt.savefig('readme2.png')
    plt.show()

.. image:: docs/images/readme2.png
    :align: center

Finally, we keep the best ``TSMLE`` imputor we represent.

.. code:: sh

    dfs_imputed =  imputer_tsmle.fit_transform(df_with_nan)

    plt.figure(figsize=(25,5))
    plt.plot(df['y'],'.g')
    plt.plot(dfs_imputed['y'],'.r')
    plt.plot(df_with_nan['y'],'.b')
    plt.show()

.. image:: https://github.com/Quantmetry/qolmat/tree/main/docs/images/readme3.png
    :align: center


📘 Documentation
================

The full documentation can be found `on this link <https://qolmat.readthedocs.io/en/latest/>`_.

📝 Contributing
===============

You are welcome to propose and contribute new ideas.
We encourage you to `open an issue <https://github.com/quantmetry/qolmat/issues>`_ so that we can align on the work to be done.
It is generally a good idea to have a quick discussion before opening a pull request that is potentially out-of-scope.
For more information on the contribution process, please go `here <https://github.com/Quantmetry/qolmat/blob/main/CONTRIBUTING.rst>`_.


🤝  Affiliation
================

Qolmat has been developed by Quantmetry.

|Quantmetry|_

.. |Quantmetry| image:: https://www.quantmetry.com/wp-content/uploads/2020/08/08-Logo-quant-Texte-noir.svg
    :width: 150
.. _Quantmetry: https://www.quantmetry.com/

🔍  References
==============

Qolmat methods belong to the field of conformal inference.

[1] Candès, Emmanuel J., et al. “Robust principal component analysis?.”
Journal of the ACM (JACM) 58.3 (2011): 1-37,
(`pdf <https://arxiv.org/abs/0912.3599>`__)

[2] Wang, Xuehui, et al. “An improved robust principal component
analysis model for anomalies detection of subway passenger flow.”
Journal of advanced transportation 2018 (2018).
(`pdf <https://www.hindawi.com/journals/jat/2018/7191549/>`__)

[3] Chen, Yuxin, et al. “Bridging convex and nonconvex optimization in
robust PCA: Noise, outliers, and missing data.” arXiv preprint
arXiv:2001.05484 (2020), (`pdf <https://arxiv.org/abs/2001.05484>`__)

[4] Shahid, Nauman, et al. “Fast robust PCA on graphs.” IEEE Journal of
Selected Topics in Signal Processing 10.4 (2016): 740-756.
(`pdf <https://arxiv.org/abs/1507.08173>`__)

[5] Jiashi Feng, et al. “Online robust pca via stochastic opti-
mization.“ Advances in neural information processing systems, 26, 2013.
(`pdf <https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.721.7506&rep=rep1&type=pdf>`__)

📝 License
==========

Qolmat is free and open-source software licensed under the `BSD 3-Clause license <https://github.com/quantmetry/qolmat/blob/main/LICENSE>`_.
