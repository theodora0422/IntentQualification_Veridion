# 1. Approach

The core mission is to build a ranking and qualification system that determines if a company truly matches a user's intent,
moving beyond noisy search results. The system is designed as a hybrid, multi-stage qualification pipeline, that balances accuracy,
speed, cost and scalability. Instead of a naive approach, this architecture aims to appli 'intelligence' selectively 
based mainly on query complexity.

---
## Pipeline architecture 
The system is structured as a cascade of stages, where each stage progressively improves the candidate set and increases decision 
complexity.
### 1. Query Understanding
The input query is parsed into a structured internal representation, consisting of:
- Hard constrains:  employee count, geography, revenue, founding year, public/private status
- Semantic Targets: industry, business model, solution types
- Relational indices: supply chains, competition, platform usage, ecosystem role
- Vague/Subjective signals: "fast-growing","similar", "critical"

Based on these signals, the query is classified into one of three categories:
- **Structured** - explicit, field-mappable constraints
- **Mixed** - structure filters + semantinc descriptors
- **Strong-reasoning** - relationships, inferred role or vague criteria

This classification is used to determine how later stages (especially LLM usage) are applied. 

---
### 2. Candidate Generation 
A high-recall candidate set is generated using a combination of: 
- Structured filtering (country,numeric thresholds etc.)
- Keyword-based retrieval
- Embedding similarity between query and companies profiles
- Taxonomy matching (NAICS code, business model etc.)
---
### 3. Cheap Deterministic Filtering
Candidates that clearly violate hard constrains are removed or strongly penalized. 
Examples of violation of hard constrains may include:
- mismatch or required geography
- failure to meet numeric thresholds (employee count, revenue )
- explicit contradiction when it comes to boolean conditions (public vs private etc.) 

Missing values are treated as uncertainty, not as failure. This avoids unnecessary loss of recall in a dataset with incomplete fields.

---
### 4. Feature-Based Scoring
Each remaining candidate is assigned a relevance score based on multiple feature groups:
- Exact match features (country match, numeric constrains satisfaction)
- Taxonomy and field-based features (NAICS alignment, business model, target markets, core offerings)
- Textual and semantic features (keyword overlap, embedding similarity across description)
- Evidence strength and consistency (number of fields supporting the same conclusion, absence of contradictions)
- Confidence penalties (missing critical data)

This stage transforms the problem from binary filtering into graded relevance ranking.

---
### 5. Selective LLM Reasoning
LLM-based reasoning is applied only when necessary based on:
- Query complexity (strong-reasoning queries)
- Candidate uncertainty (missing data, borderline score, conflicting signals)
Rather than evaluating all companies, the LLM is invoked only on a small subset of companies (top-N candidates or ambiguous cases)
This design preserves semantic depth while controlling cost and latency
---

### 6. Final Ranking and Output
The final ranking is produced by combining: 
- deterministic feature-based scores
- semantic similarity signals
- LLM judgments (if used)
- confidence estimates
---
The proposed architecture is a hybrid cascade that progressively increases decision complexity:
> parse the query -> find a broad set of candidates -> remove clear mismatches -> score candidates using structured + semantic signald -> use LLM only if needed ->return the final ranking

The design ensures:
- higher accuracy that similarity-only approaches by including constraints and modeling roles
- lower cost and latency that LLM-per-company evaluation by limiting LLM usage
- scalability to larget datasets through efficient retrieval
The system is modular allowing each stage to be improved independently without affecting the overall structure. 

# 2. Tradeoffs

## Optimization Goals
The system is designed to balance several objectives:
- Accuracy - correctly identifying companies that truly satisfy the query intent
- Speed - keeping query-time latency loq
- Cost - minimizing the number of expensive LLM calls
- Scalability - handling large datasets efficiently
- Robustness - performing well despite incomplete or noisy data

The system mainly prioritizes accuracy under constraints of cost and scalability.

---
### 1. Accuracy vs Cost
A fully LLM-based solution (evaluating every company with an LLM) would likely achieve high semantic accuracy, especially for complex
queries involving relationships or inferred roles. However, this is expensive and slow.  
Instead, the system uses filtering and feature-based scoring for most decisions and applies LLM reasoning only to a small subset of candidates.

This results in slightly lower theoretical accuracy than a full LLM approach, but drastically improves efficiency.

---
### 2. Accuracy vs Speed
More complex reasoning (especially with LLMs) increases latency.
The system addresses this by 
- resolving simple, structured queries without LLM usage
- limiting LLM calls to top-ranked or uncertain candidates
- avoiding unnecessary deep reasoning when structured evidence is sufficient

This ensures that most queries are processed quickly, while still allowing deeper analysis when needed.

---
### 3. Recall vs Precision
Candidate generation is designed to prioritize recall, meaning it may include some irrelevant companies in the initial pool.
This is intentional:
- missing a relevant company early is difficult to recover later
- false positive can be filtered out in later stages

Precision is improved progressively through deterministic filtering, feature-based scoring and optional LLM adjudication.

---
### 4. Simplicity vs Complexity
A purely rule-based system would be simple and fast, but unable to handle complex queries involving relationships or vague criteria.
A fully LLM-based system would be highly expressive but inefficient and harder to control.
The chosen hybrid design aims to keep early stages simple and deterministic and to add expressiveness only where needed via LLM reasoning. 

---
### 5. Robustness vs Strict Filtering
Strict filtering based only on structured fields could improve precision, but would fail in cases where data is missing or incomplete.
Instead, the system treats missing data as uncertainty, not failure, allows candidates to remain if supported by other signals. 
This improves robustness at the cost of occasionally requiring additional downstream filtering.

---
The system intentionally avoids extreme solutions and instead adopts a balanced approach:
- it sacrifices some simplicity to gain flexibility
- it sacrifices exhaustive reasoning to gain efficiency
- it accepts some initial noise to preserve recall
Overall, the design prioritizes **high-quality results under realistic cost and scalability constrains**, aligning with the requirements of the task.