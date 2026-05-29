from typing import Annotated

from litestar import Request, get, post
from litestar.enums import RequestEncodingType
from litestar.params import Body

from api.state import AppState
from common import FraudRequest, vectorize


@get("/ready", sync_to_thread=False)
def handle_ready() -> str:
    return "ok"


@post("/fraud-score", sync_to_thread=False)
def handle_fraud_score(
    data: Annotated[FraudRequest, Body(media_type=RequestEncodingType.JSON)],
    request: Request,
) -> dict[str, bool | float]:
    state: AppState = request.app.state.app_state

    query = vectorize(data, state.normalization, state.mcc_risk)
    score = state.index.fraud_score(query)

    return {
        "approved": score < 0.6,
        "fraud_score": score,
    }
