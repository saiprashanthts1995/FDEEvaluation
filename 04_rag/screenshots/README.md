# RAG Evidence Screenshots

Save genuine screenshots from the Databricks workspace session in this folder. Use the filenames below so the evidence is easy to review in workflow order.

| Filename | Evidence | Status |
|---|---|---|
| `01-uc-functions.png` | `get_policy_details('return')` and `get_customer_service_history('Robert Butler')` — real query results (Return Policy row; 2 real interaction rows). | Done |
| `02-retrieval-output.png` | Top-k product matches with similarity scores for a sample query. | Needed |
| `03-grounded-answer.png` | The generated answer for "a good product for someone who hikes in cold weather," citing Arctic Shield 360° Winter Jacket and SummitShield Thermal Jacket by name from the retrieved context. | Done |
| `04-grounding-refusal-check.png` | The off-domain "capital of France" question correctly declined ("does not contain information about the capital of France"), assertion passing. | Done |
| `05-chunking-comparison.png` | `03_chunking_tradeoffs.py` output — the 200/50 vs 800/100 chunk counts and the top-3 retrieval comparison for the sample query. | Needed |
| `06-filtered-retrieval.png` | `04_metadata_filtered_retrieval.py` output — unfiltered vs. category-filtered results, plus the scoped grounded answer. | Needed |
| `07-hybrid-vs-ann.png` | `05_hybrid_retrieval_demo.py` output — the exact-reference query's rank under `HYBRID` vs `ANN`. | Needed |

Only mark evidence complete when the corresponding screenshot exists and shows the actual session result. Do not create placeholder images or invent model output.

Notes:
- `01`, `03`, `04` come from [`../lightweight_evidence_3_4_5.py`](../../lightweight_evidence_3_4_5.py), run via plain REST calls (no `%pip install`).
- Worth noting for `04` specifically: the same kind of off-domain question run through the deployed **agent** (not this RAG demo) answered "Paris" instead of declining — see `05_agent_creation/screenshots/05-agent-off-domain.png` and that folder's README for why (the agent has no system prompt enforcing this discipline; this RAG demo does).
- `05`, `06`, `07` weren't covered by the lightweight path — they need `03_chunking_tradeoffs.py`, `04_metadata_filtered_retrieval.py`, `05_hybrid_retrieval_demo.py` run directly (each needs the `databricks-vectorsearch` package installed, unlike the lightweight notebook).
