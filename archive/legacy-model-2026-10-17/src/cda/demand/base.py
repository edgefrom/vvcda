"""需求模型接口。"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas import DecisionVector, TurnRecord


class DemandModel(ABC):
    """已估计的需求模型：给定决策，预测某细分份额。"""

    @abstractmethod
    def predict_share(self, decision: DecisionVector, market: str, segment: str) -> float:
        """返回我方在该细分的份额 [0,1]。"""


class DemandEstimator(ABC):
    """从历史回合记录估计 DemandModel。"""

    @abstractmethod
    def fit(self, records: list[TurnRecord]) -> DemandModel:
        """用历史记录估计需求模型。"""
