import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from litestar import Litestar

from api.handlers import handle_fraud_score, handle_ready
from api.index import ReferenceIndex
from api.state import AppState
from common.normalization import McCRisk, Normalization


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncIterator[None]:
    references_path = os.environ.get("REFERENCES_PATH", "/app/resources/refererences.json.gz")
    normalization_path = os.environ.get("NORMALIZATION_PATH", "/app/resources/normalization.json")
    mcc_risk_path = os.environ.get("MCC_RISK_PATH", "/app/resources/mcc_risk.json")

    print(f"[api] references={references_path}", file=sys.stderr)
    print(f"[api] normalization={normalization_path}", file=sys.stderr)
    print(f"[api] mcc_risk={mcc_risk_path}", file=sys.stderr)

    normalization = Normalization.load_from_file(normalization_path)
    mcc_risk = McCRisk.load_from_file(mcc_risk_path)
    index = ReferenceIndex.load_from_json_gz(references_path)

    app.state.app_state = AppState(index=index, normalization=normalization, mcc_risk=mcc_risk)

    yield  # app sobe e fica rodando até receber sinal de shutdown


app = Litestar(
    route_handlers=[handle_ready, handle_fraud_score],
    lifespan=[lifespan],
    openapi_config=None,  # desliga geração de docs OpenAPI: economiza memória e tempo de boot
    debug=False,
)
