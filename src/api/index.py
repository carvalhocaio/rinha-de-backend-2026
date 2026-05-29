import gzip
import sys
import time
from pathlib import Path

import msgspec
import numpy as np

from common.vector import DIMS, Vector14

# K=5 vem da spec da Rinha. Constante para deixar claro e permitir tunning futuro.
K: int = 5

# Threshold para approved=False (>=). Spec: approved = fraud_score < 0.6.
THRESHOLD: float = 0.6


class _RawReference(msgspec.Struct):
    # Forma intermediária do JSON: vector como lista e label como string.
    # Convertemos para ndarray + bool na carga; a struct é descartada depois.
    vector: list[float]
    label: str


class ReferenceIndex:
    __slots__ = ("labels", "vectors")

    def __init__(self, vectors: np.ndarray, labels: np.ndarray) -> None:
        self.vectors = vectors  # shape (N, 14), dtype float
        self.labels = labels  # shape (N,),    dtype bool

    @staticmethod
    def load_from_json_gz(path: str | Path) -> "ReferenceIndex":
        path = Path(path)
        if not path.exists():
            print(f"[index] {path} não existe - índice vazio (modo dev)", file=sys.stderr)
            return ReferenceIndex(
                vectors=np.zeros((0, DIMS), dtype=np.float32),
                labels=np.zeros((0,), dtype=bool),
            )

        t0 = time.perf_counter()

        # Detecta gzip pelo sufixo. Builder e exemplos descompactados também funcionam
        opener = gzip.open if str(path).endswith(".gz") else open
        with opener(path, "rb") as f:
            raw_bytes = f.read()

            raw = msgspec.json.decode(raw_bytes, type=list[_RawReference])
            n = len(raw)

            # Pré-aloca os arrays - evita N realloc de Vec durante o preenchimento.
            vectors = np.empty((n, DIMS), dtype=np.float32)
            labels = np.empty((n,), dtype=bool)
            for i, r in enumerate(raw):
                vectors[i] = r.vector
                labels[i] = r.label == "fraud"

            elapsed = time.perf_counter() - t0
            print(f"[index] carregadas {n} referências em {elapsed:.2f}s", file=sys.stderr)

            return ReferenceIndex(vectors=vectors, labels=labels)

    def __len__(self) -> int:
        return len(self.labels)

    def is_empty(self) -> bool:
        return len(self.labels) == 0

    def fraud_score(self, query: Vector14) -> float:
        # Edge case: índice vazio (modo dev) - score neutro.
        if self.is_empty():
            return 0.5

        # Distância euclidiana ao quadrado para CADA referência.
        # (X - q) usa broadcasting: shape (N, 14) - (14,) -> (N, 14).
        # Sem sqrt: ordem relativa é o que importa para k-NN,e sqrt custa ~30% do tempo.
        diff = self.vectors - query
        dist_sq = np.einsum("ij,ij->i", diff, diff)

        # argpartition é 0(N), retorna os K menores em qualquer ordem entre si.
        # Sufficient para k-NN porque só precisamos do CONJUNTO dos K vizinhos, não da ordem
        k_idx = np.argpartition(dist_sq, K)[:K]

        # Voting por maioria: quantos dos K vizinhos são fraude.
        n_fraud = int(self.labels[k_idx].sum())
        return n_fraud / K
