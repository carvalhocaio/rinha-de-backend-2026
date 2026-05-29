from datetime import datetime
from typing import Final

import numpy as np

from common.normalization import McCRisk, Normalization
from common.payload import FraudRequest

DIMS: Final[int] = 14

# Alias semântico - todo Vector14 é um np.array (14, ) float32.
type Vector14 = np.ndarray


def squared_distance(a: Vector14, b: Vector14) -> float:
    diff = a - b
    return float(np.dot(diff, diff))


def vectorize(req: FraudRequest, n: Normalization, mcc: McCRisk) -> Vector14:
    v = np.zeros(DIMS, dtype=np.float32)

    v[0] = _clamp01(req.transaction.amount / n.max_amount)
    v[1] = _clamp01(req.transaction.installments / n.max_installments)

    # Dim 2: guard contra divisão por zero (geraria inf/NaN e quebraria k-NN).
    if req.customer.avg_amount > 0.0:
        v[2] = _clamp01(
            (req.transaction.amount / req.customer.avg_amount) / n.amount_vs_avg_ratio,
        )

    # Dims 3 e 4: hora do dia / dia da semana (UTC)
    # fromisoformat aceita "Z" desde Python 3.11.
    try:
        dt = datetime.fromisoformat(req.transaction.requested_at)
        v[3] = dt.hour / 23.0
        # weekday(): seg = 0..dom=6 - alinhado com a spec.
        v[4] = dt.weekday() / 6.0
    except ValueError:
        pass  # mantém 0.0 em caso de timestamp inválido

    # Dims 5 e 6: sentinela -1 quando last_transaction é None (regra da spec).
    if req.last_transaction is not None:
        minutes = _minutes_between(
            req.last_transaction.timestamp,
            req.transaction.requested_at,
        )
        v[5] = _clamp01(minutes / n.max_minutes)
        v[6] = _clamp01(req.last_transaction.km_from_current / n.max_km)
    else:
        v[5] = -1.0
        v[6] = -1.0

    v[7] = _clamp01(req.terminal.km_from_home / n.max_km)
    v[8] = _clamp01(req.customer.tx_count_24h / n.max_tx_count_24h)
    v[9] = 1.0 if req.terminal.is_online else 0.0
    v[10] = 1.0 if req.terminal.card_present else 0.0
    v[11] = 0.0 if req.merchant.id in req.customer.known_merchants else 1.0
    v[12] = mcc.risk_for(req.merchant.mcc)
    v[13] = _clamp01(req.merchant.avg_amount / n.max_merchant_avg_amount)

    return v


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _minutes_between(start_iso: str, end_iso: str) -> float:
    try:
        start = datetime.fromisoformat(start_iso)
        end = datetime.fromisoformat(end_iso)
        delta = (end - start).total_seconds() / 60.0
        return max(delta, 0.0)
    except ValueError:
        return 0.0
