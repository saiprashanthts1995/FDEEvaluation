# RAG Evidence Screenshots

Save genuine screenshots from the Databricks workspace session in this folder. Use the filenames below so the evidence is easy to review in workflow order.

| Filename | Evidence |
|---|---|
| `01-uc-functions.png` | `get_policy_details` and `get_customer_service_history` listed in Catalog Explorer under `uc_agentic_ai.agentic_ai_schema`, or the notebook's quick-test output for both. |
| `02-retrieval-output.png` | `02_rag_retrieval_demo.py` Step 1 output — the top-k product matches with similarity scores for a sample query. |
| `03-grounded-answer.png` | Step 3 output — the generated answer, with product names cited, next to the retrieved context it was built from. |
| `04-grounding-refusal-check.png` | Step 4 output — the off-domain question correctly declined, and the assertion passing. |
| `05-chunking-comparison.png` | `03_chunking_tradeoffs.py` output — the 200/50 vs 800/100 chunk counts and the top-3 retrieval comparison for the sample query. |
| `06-filtered-retrieval.png` | `04_metadata_filtered_retrieval.py` output — unfiltered vs. category-filtered results, plus the scoped grounded answer. |
| `07-hybrid-vs-ann.png` | `05_hybrid_retrieval_demo.py` output — the exact-reference query's rank under `HYBRID` vs `ANN`. |

Only mark evidence complete when the corresponding screenshot exists and shows the actual session result. Do not create placeholder images or invent model output.
