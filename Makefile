.PHONY: ruff

ruff:
	uv run ruff check --fix .
	uv run ruff format .

run:
	REFERENCES_PATH=./resources/references.json.gz \
	NORMALIZATION_PATH=./resources/normalization.json \
	MCC_RISK_PATH=./resources/mcc_risk.json \
	uv run granian --interface asgi --host 0.0.0.0 --port 8080 api.main:app
