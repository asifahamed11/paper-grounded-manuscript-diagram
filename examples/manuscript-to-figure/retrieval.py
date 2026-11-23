"""Run the hybrid retrieval example with Python 3.10+ and no dependencies."""

import json
import math
import re
from collections import Counter


TOP_K = 5
RRF_CONSTANT = 60

# Each record contains passage text and a fixed, synthetic vector.
PASSAGES = {
    "p01": ("Cross-validation for small text classification datasets.", (0.8, 0.2, 0.2)),
    "p02": ("Relevance judgments for ranking scientific articles.", (0.2, 0.9, 0.1)),
    "p03": ("Sentence vectors for finding relevant research passages.", (0.1, 0.8, 0.3)),
    "p04": ("Coastal precipitation and river water quality monitoring.", (0.1, 0.1, 0.9)),
    "p05": ("Pooling documents for search evaluation with graded judgments.", (0.3, 0.9, 0.1)),
    "p06": ("Sensitivity of greenhouse gas estimates to sample selection.", (0.5, 0.1, 0.8)),
    "p07": ("Training and validation partitions for time series forecasting.", (0.9, 0.1, 0.2)),
    "p08": ("Article metadata and author identifiers for digital archives.", (0.1, 0.5, 0.4)),
}

QUERIES = {
    "q01": ("judgments for scientific search", (0.2, 1.0, 0.1)),
    "q02": ("validation for forecasting", (1.0, 0.1, 0.1)),
}

JUDGMENTS = {"q01": {"p02": 1, "p05": 2, "p03": 1}, "q02": {"p07": 2, "p01": 1}}


def terms(text):
    return re.findall(r"\w+", text.casefold())


def ranked_ids(scores):
    return sorted(scores, key=lambda passage_id: (-scores[passage_id], passage_id))


def bm25_ranking(passages, query):
    counts = {key: Counter(terms(text)) for key, (text, _) in passages.items()}
    lengths = {key: sum(frequencies.values()) for key, frequencies in counts.items()}
    mean_length = sum(lengths.values()) / len(lengths)
    scores = dict.fromkeys(counts, 0.0)
    k1, b = 1.2, 0.75
    for term in sorted(set(terms(query))):
        frequency = sum(term in document for document in counts.values())
        idf = math.log1p((len(counts) - frequency + 0.5) / (frequency + 0.5))
        for key, document in counts.items():
            count = document[term]
            norm = k1 * (1 - b + b * lengths[key] / mean_length)
            scores[key] += idf * count * (k1 + 1) / (count + norm)
    return ranked_ids(scores)[:TOP_K]


def cosine(left, right):
    dot = math.fsum(a * b for a, b in zip(left, right, strict=True))
    return dot / (math.hypot(*left) * math.hypot(*right))


def dense_ranking(passages, query_vector):
    scores = {key: cosine(query_vector, vector) for key, (_, vector) in passages.items()}
    return ranked_ids(scores)[:TOP_K]


def reciprocal_rank_fusion(*rankings):
    scores = {}
    for ranking in rankings:
        for rank, passage_id in enumerate(ranking, start=1):
            scores[passage_id] = scores.get(passage_id, 0.0) + 1 / (RRF_CONSTANT + rank)
    return ranked_ids(scores)[:TOP_K]


def retrieve(passages, query, query_vector):
    lexical = bm25_ranking(passages, query)
    dense = dense_ranking(passages, query_vector)
    return reciprocal_rank_fusion(lexical, dense)


def evaluate(ranking, judgments):
    grades = [judgments.get(passage_id, 0) for passage_id in ranking[:TOP_K]]
    ideal = sorted(judgments.values(), reverse=True)[:TOP_K]
    relevant = sum(grade > 0 for grade in judgments.values())

    def dcg(values):
        return sum((2**grade - 1) / math.log2(rank + 2) for rank, grade in enumerate(values))

    return {
        "nDCG@5": dcg(grades) / dcg(ideal) if relevant else 0.0,
        "Recall@5": sum(grade > 0 for grade in grades) / relevant if relevant else 0.0,
    }


def main():
    for query_id, (query, vector) in QUERIES.items():
        ranking = retrieve(PASSAGES, query, vector)
        metrics = evaluate(ranking, JUDGMENTS[query_id])
        print(json.dumps({"query": query_id, "ranking": ranking, **metrics}))


if __name__ == "__main__":
    main()
