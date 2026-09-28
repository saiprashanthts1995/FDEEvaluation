# RAG Evidence Screenshots

Genuine screenshots from the Databricks workspace, covering all 7 items.

| Filename | Evidence |
|---|---|
| `01-uc-functions.png` | `get_policy_details('return')` and `get_customer_service_history('Robert Butler')` — real query results (Return Policy row; 2 real interaction rows). |
| `02-retrieval-output.png` | Top-5 product matches with similarity scores for "comfortable waterproof hiking boots". |
| `03-grounded-answer.png` | The generated answer for "a good product for someone who hikes in cold weather," citing Arctic Shield 360° Winter Jacket and SummitShield Thermal Jacket by name from the retrieved context. |
| `04-grounding-refusal-check.png` | The off-domain "capital of France" question correctly declined ("does not contain information about the capital of France"), assertion passing. |
| `05-chunking-comparison.png` | 200 vs. 800-word-equivalent chunking on 5 long product descriptions — 21 chunks vs. 5, confirming the structural tradeoff on real data. |
| `06-filtered-retrieval.png` | "something for staying organized" filtered to `product_category = "Software"` — results stayed in-category, and the scoped grounded answer recommended TaskFlow Pro and ProTasker Suite by name. |
| `07-hybrid-vs-ann.png` | Exact-reference query "BrownBox SwiftWatch X500" — ranked #1 with score 1.000 under `HYBRID`, vs. #1 with only 0.624 under pure `ANN`. |

Only mark evidence complete when the corresponding screenshot exists and shows the actual session result. Do not create placeholder images or invent model output.

Worth noting for `04`: the same kind of off-domain question run through the deployed **agent** (not this RAG demo) answered "Paris" instead of declining — see `05_agent_creation/screenshots/05-agent-off-domain.png` and that folder's README for why (the agent has no system prompt enforcing this discipline; this RAG demo does).

Run via [`../../lightweight_evidence_3_4_5.py`](../../lightweight_evidence_3_4_5.py) and [`../../lightweight_evidence_batch2.py`](../../lightweight_evidence_batch2.py), the zero-install REST/SQL path used for this assignment's evidence.
