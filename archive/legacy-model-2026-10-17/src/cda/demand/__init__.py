"""需求模型：从回合记录估计需求参数，预测细分份额。"""
from __future__ import annotations

from .attraction import LogitDemandEstimator, LogitDemandModel
from .base import DemandEstimator, DemandModel
from .bayes import BayesianLinearModel, DEFAULT_PRIOR, bayesian_linear_fit, prior_from_research
from .diagnostics import diagnostics, is_linear_sufficient
from .features import build_dataset, fit_relative_model, relative_features
from .online import RecursiveLeastSquares

__all__ = [
    "DemandEstimator",
    "DemandModel",
    "LogitDemandEstimator",
    "LogitDemandModel",
    "relative_features",
    "build_dataset",
    "fit_relative_model",
    "BayesianLinearModel",
    "bayesian_linear_fit",
    "prior_from_research",
    "DEFAULT_PRIOR",
    "RecursiveLeastSquares",
    "diagnostics",
    "is_linear_sufficient",
]
