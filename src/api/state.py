from api.index import ReferenceIndex
from common.normalization import McCRisk, Normalization


class AppState:
    __slots__ = ("index", "mcc_risk", "normalization")

    def __init__(
        self,
        index: ReferenceIndex,
        normalization: Normalization,
        mcc_risk: McCRisk,
    ) -> None:
        self.index = index
        self.normalization = normalization
        self.mcc_risk = mcc_risk
