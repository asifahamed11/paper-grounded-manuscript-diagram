# Figure review and method check

The two runs received the same [brief](../../assets/readme/comparison-prompt.txt), [methods draft](manuscript.md) and [Python example](retrieval.py). The baseline used those local inputs. The skill run also examined the related papers below. The Python example uses synthetic fixtures and runs with Python 3.10 or later.

## Published figures reviewed

| Paper and locator | Convention used in the new diagram |
| --- | --- |
| [Louis et al. (2025), *Know When to Fuse*, Fig. 1, p. 4293](https://aclanthology.org/2025.coling-main.290.pdf#page=1) | Separate lexical and dense retrieval visually, then converge the two rankings at one fusion step. |
| [Chen et al. (2024), *M3-Embedding*, Fig. 2, p. 2321](https://aclanthology.org/2024.findings-acl.137.pdf#page=4) | Distinguish terms and vectors with small, recognisable representation marks. |
| [Litschko et al. (2022), *Parameter-Efficient Neural Reranking*, Fig. 1, p. 1073](https://aclanthology.org/2022.coling-1.90.pdf#page=3) | Make the ranked IDs visible as a data product passed between stages. |

The full-text PDFs and figure captions were inspected. The papers informed layout and symbols. The supplied draft and code determined the method shown.

## Method trace

| What the figure represents | Where to check it |
| --- | --- |
| Both retrieval paths use the same passage collection and query. Text feeds BM25 and the supplied vectors feed cosine ranking. | Methods §1–2 and `PASSAGES`, `QUERIES`, `bm25_ranking`, `dense_ranking`, `retrieve`. |
| Each branch sends its five highest-ranked IDs to reciprocal rank fusion. The fusion uses one-based ranks and keeps the top five IDs. Ties are broken by passage ID. | Methods §2–3 and `TOP_K`, `ranked_ids`, `RRF_CONSTANT`, `reciprocal_rank_fusion`. |
| The fused ranking and fixed relevance judgments meet at evaluation. The judgments flow only to the evaluator. | Methods §4 and `main`, where `JUDGMENTS` is passed to `evaluate` after `retrieve` completes. |
| The evaluator reports nDCG@5 from the grades and Recall@5 from positive grades. | Methods §4 and `evaluate`. |

The code ran on both example queries. Changing the fixed judgments changed the evaluation scores and left the rankings identical.

## Icons and export checks

Five original symbols identify the shared archive, lexical and dense retrieval, the fused ranking and the relevance grades. Placing the icons beside the titles kept the explanations centred. The skill export passed geometry checks, and all seven nodes and seven arrows were traced to the draft and implementation. Both panels were inspected at a 6.5-inch print width and placed side by side at the same scale.
