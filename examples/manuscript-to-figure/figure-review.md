# Figure review and method check

The two runs received the same [brief](../../assets/readme/comparison-prompt.txt), [methods draft](manuscript.md) and [Python example](retrieval.py). The baseline used those local inputs. The skill run also examined the related papers below. The Python example uses synthetic fixtures and runs with Python 3.10 or later.

## Published figures reviewed

| Paper and locator | Convention used in the new diagram |
| --- | --- |
| [Louis et al. (2025), *Know When to Fuse*, Fig. 1, p. 4293](https://aclanthology.org/2025.coling-main.290.pdf#page=1) | Separate lexical and dense retrieval visually into parallel tracks, then converge both ranked lists at a single fusion step. |
| [Chen et al. (2024), *M3-Embedding*, Fig. 2, p. 2321](https://aclanthology.org/2024.findings-acl.137.pdf#page=4) | Distinguish lexical terms and dense embedding vectors with compact, recognisable visual symbols and restrained flat styling. |
| [Litschko et al. (2022), *Parameter-Efficient Neural Reranking*, Fig. 1, p. 1073](https://aclanthology.org/2022.coling-1.90.pdf#page=3) | Expose ranked ID outputs explicitly between retrieval/fusion and downstream scoring stages. |
| [Toksoz et al. (2026), *PseudoSeer: a Search Engine for Pseudocode*, Fig. 3, p. 39709](https://aclanthology.org/2026.findings-acl.1978.pdf) | Route ground-truth queries/judgments along a dashed evaluation-only path straight to `nDCG@5` / `Recall@5` so evaluation signals visibly bypass indexing and retrieval. |
| [Kanishkavardhan et al. (2026), *A retrieval-augmented multi-stage prompting framework for legal analysis in the Indian judicial system*, Fig. 1, p. 5](https://www.frontiersin.org/journals/big-data/articles/10.3389/fdata.2026.1933830/pdf) | Group hybrid retrieval and verification/evaluation into distinct labeled stages; replace low-contrast dark-on-saturated fills with high-contrast Okabe–Ito soft tints and clean borders. |

The full-text PDFs and figure captions were inspected. The papers informed layout, non-leaky evaluation routing, and symbols. The supplied draft and code determined every detail of the method shown.

## Method trace

| What the figure represents | Where to check it |
| --- | --- |
| Both retrieval paths use the same 8-passage collection and 2 evaluation queries. Text feeds BM25 (`k1 = 1.2, b = 0.75`) and supplied vectors feed cosine ranking. | Methods §1–2 and `PASSAGES`, `QUERIES`, `bm25_ranking`, `dense_ranking`, `retrieve`. |
| Each branch emits its top 5 passage IDs (ties broken by passage ID) to reciprocal rank fusion (`1 / (60 + rank)`), returning the fused top 5 IDs. | Methods §2–3 and `TOP_K`, `ranked_ids`, `RRF_CONSTANT`, `reciprocal_rank_fusion`. |
| The fused ranking and fixed graded relevance judgments (`g in {0, 1, 2}`) meet exclusively at evaluation. | Methods §4 and `main`, where `JUDGMENTS` passes to `evaluate` after `retrieve` completes. |
| The evaluator computes `nDCG@5` from full grades and `Recall@5` from positive grades. | Methods §4 and `evaluate`. |

The code ran on both example queries. Changing the fixed judgments changed the evaluation scores and left the rankings identical.

## Icons and export checks

Five crisp pure-vector symbols (`database`, `search`, `layers`, `table`, `check`) identify the shared archive, lexical and dense retrieval, fused ranking, and evaluation metrics. Placing the icons beside the node titles keeps explanations balanced. The skill diagram is rendered with `scripts/render_diagram.py` (`--theme okabe-ito --require-sources --require-paper-figures`, `paper_figures_inspected >= 5`) at 6.5 inches width with 0 geometry errors, verified against SVG structural checks, and inspected alongside the baseline AI output in `assets/readme/hero-comparison.png`.
