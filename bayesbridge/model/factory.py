from warnings import warn
import scipy as sp

from .linear_model import LinearModel
from .logistic_model import LogisticModel
from .cox_model import CoxModel
from ..design_matrix import DenseDesignMatrix, SparseDesignMatrix

def RegressionModel(
        outcome, X, family='linear',
        add_intercept=None, center_predictor=False
    ):
    """ Prepare input data to BayesBridge, with pre-processings as needed.

    For the Cox model, the observations (rows of X) are reordered to optimize
    likelihood, gradient, and Hessian evaluations.

    Parameters
    ----------
    outcome : 1-d numpy array, tuple of two 1-d numpy arrays
        (n_success, n_trial) if family == 'logistic'.
        The outcome is assumed binary if n_trial is None.
        (event_time, censoring_time) if family == 'cox'.
    X : numpy array or scipy sparse matrix
    family : str, {'linear', 'logit', 'cox'}
    add_intercept : bool, None
        If None, add intercept except when family == 'cox'
    center_predictor : bool
    """

    # TODO: Make each MCMC run more "independent" i.e. not rely on the
    # previous instantiation of the class. The initial run of the Gibbs
    # sampler probably depends too much the stuffs here.

    if add_intercept is None:
        add_intercept = (family != 'cox')

    if family == 'cox':
        if add_intercept:
            add_intercept = False
            warn("Intercept is not identifiable in Cox model and won't be added.")
        event_time, censoring_time = outcome
        event_time, censoring_time, X = CoxModel.preprocess_data(
            event_time, censoring_time, X
        )

    is_sparse = sp.sparse.issparse(X)
    DesignMatrix = SparseDesignMatrix if is_sparse else DenseDesignMatrix
    design = DesignMatrix(
        X, add_intercept=add_intercept, center_predictor=center_predictor
    )

    if family == 'linear':
        model = LinearModel(outcome, design)
    elif family == 'logit':
        n_success, n_trial = outcome
        model = LogisticModel(n_success, n_trial, design)
    elif family == 'cox':
        model = CoxModel(event_time, censoring_time, design)
    else:
        raise NotImplementedError()

    return model
