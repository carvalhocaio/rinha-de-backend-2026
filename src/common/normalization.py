from pathlib import Path

import msgspec


class Normalization(msgspec.Struct):
    max_amount: float
    max_installments: float
    amount_vs_avg_ratio: float
    max_minutes: float
    max_km: float
    max_tx_count_24h: float
    max_merchant_avg_amount: float

    @staticmethod
    def load_from_file(path: str | Path) -> "Normalization":
        content = Path(path).read_bytes()
        return msgspec.json.decode(content, type=Normalization)

    @staticmethod
    def clamp01(value: float, max_value: float) -> float:
        v = value / max_value
        if v < 0.0:
            return 0.0
        if v > 1.0:
            return 1.0
        return v


class McCRisk:
    __slots__ = ("risks",)

    def __init__(self, risks: dict[str, float]) -> None:
        self.risks = risks

    @staticmethod
    def load_from_file(path: str | Path) -> "McCRisk":
        content = Path(path).read_bytes()
        risks = msgspec.json.decode(content, type=dict[str, float])
        return McCRisk(risks)

    def risk_for(self, mcc: str) -> float:
        # Hot path. MCC ausent -> 0.5 (default da spec).
        return self.risks.get(mcc, 0.5)
