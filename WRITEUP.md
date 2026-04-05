# 1. Approach

My approach is a hybrid ranking pipeline that combines rule-based query parsing, deterministic candidate scoring, hard filtering, 
and selective reranking. 

The architecture has five main stages:
## 1.1 Data Normalization
The raw JSONL company data is first normalized into a consistent internal schema (CompanyProfile). At this step I:
- clean text fields
- normalize list fields such as business model, target markets and core offerings
- parse address information into country, region and town
- parse NAICS fields into code and label
- build a full_profile text field by concatenating the most useful company attributes

This gives the rest of the pipeline a stable and uniform representation to work with.

## 1.2 Query Parsing
Each user query is converted into a structured representation (QueryRepresentation). 
The parser extracts:
- geographic constraints such as country or region
- numeric constraints such as revenue, employee count, and founded year
- public/private status
- industry terms
- business model terms
- target market terms
- capability terms
- relational terms
- vague terms

The query is then classified into one of three types:
- structured
- mixed
- strong-reasoning

This classification is later used to decide whether LLM reasoning should be applied

## 1.3 Candidate Generation
The system scores all companies with a lightweight deterministic scoring function and keeps the top candidates. 
The candidate generation score uses:
- geography match
- industry match in NAICS, description, or full profile
- capability term matches
- business model matches
- target market matches
- core offering matches
- full text overlap with query terms
- public/private match

For structured and mixed queries, I also require at least one important semantic term match before a company can enter the 
candidate pool. This reduces obvious noise. 
This stage is designed for recall: it keeps a broad but still relevant set of candidates. 

## 1.4 Hard filtering
The candidate set is then filtered using explicit constraints from the query:
- country
- public/private status
- minimum or maximum employees
- minimum or maximum revenue
- minimum or maximum founded year

A company is removed only if it explicitly violates a hard constraint.
If a required field is missing, I treat this as uncertainty rather than immediate failure. This is important because the 
dataset contains many missing values, especially for employee count and revenue. 

## 1.5 Final scoring and selective LLM reranking
After hard filtering, the remaining companies are reranked with a more detailed deterministic scoring function. 
This final scoring step starts from the candidate score and adds:
- strong reward or penalties for required terms
- smaller reward for supportive terms
- query-specific helper signals for HR, packaging and fintech
- a penalty when hard-constraint field are missing

This stage produces the main ranking used by the system. For difficult queries, I optionally apply LLM reranking on only the top few candidates. 
The LLM is used mainly for strong-reasoning queries or when deterministic ranking looks weak. 

The LLM receives:
- the raw query
- the parsed query type
- the company summary
- the deterministic scores
- the scoring reasons

It returns a structured judgement:
- strong_match
- possible_match
- weak_match
- not_match

This judgement is used as a final adjustment on top of deterministic ranking. 

## Why I chose this design
I chose this design because the task mixes two different problem types:
- structured filtering problems, such as geography, size or public/private constraints
- semantic or relational problems such as "could supply packaging materials" or "competing with traditional banks"

A fully rule-based system would be fast and cheap but weal on reasoning-heavy queries. A fully LLM-based system would be more flexible, 
but expensive, slower and harder to control. 

The hybrid cascade gives a better balance:
- deterministic stages handle most of the workload
- the LLM is only used when deeper reasoning is likely to help
- each stage is modular and easy to inspect through saved intermediate outputs

# 2. Tradeoffs
I mainly optimized for:
- simplicity
- interpretability
- low cost
- reasonable accuracy on a small dataset

## Accuracy vs Cost
The main tradeoff in the system is between semantic accuracy and inference cost.
A full LLM-per-company approach could reason better about indirect matches, supplier relationships or vague concepts such as 
"fast-growing" or "critical components". However, that design would be expensive and slow. 

I intentionally chose to use the LLM only on a very small number of candidates and only for the most reasoning-heavy queries. 
This keeps the system practical while still allowing deeper semantic judgement where needed. 

## Simplicity vs Expressiveness
The core ranking logic is based on explicit term matching and hard-designed scoring rules. 
This makes the system:
- easy to debug
- transparent
- easy to explain

But it also means the system is less expressive than a model based on embeddings or richer semantic retrieval. It works 
best when relevant concepts are explicitly present in the company fields.

I accepted this tradeoff because the task dataset is small and because transparency matters. 

## Precision vs Recall
Candidate generation is designed to favor recall first and precision later. 
I score all companies and keep the top candidates, then apply hard filtering and reranking. This means the early stage may still include noisy 
candidates, but it reduces the chance of missing relevant ones too early.

I intentionally preferred this design because false positives can still be removed later, while false negatives are much harder
to recover from. 

## Robustness vs Strictness
In hard filtering, missing structured data is treated as uncertainty rather than immediate failure. This improves robustness 
on incomplete company profiles, but it can also allow some weak candidates to survive longer than they ideally should. 

I considered this acceptable because the dataset has substantial missingness in fields like employee count and revenue. 

## Deterministic control vs Semantic flexibility
The final ranking relies heavily on explicit fields such as:
- NAICS label
- business model
- target markets
- core offerings
- description
- full profile text

This provides strong control and predictable behavior, but may lead to reduced robustness in cases where the correct answer 
relies on implicit rather than explicit semantic signals.
For example, the system may struggle when a company is relevant to a query in practice, but the relevant concept is not directly
written in its profile. 

## Practical tradeoff around LLM quota 
In practice, the selective LLM stage is also constrained by API quota and cost. Because of this, I designed the system so that 
deterministic ranking is always usable even when LLM calls fail or are skipper. The system therefore degrades gracefully: it can still 
return a ranking without the LLM, even if the results are less semantically refined. In order to show that the LLM stage is working, 
due to quota problem, I have chosen to rank only the first two candidates. 

# 3. Error Analysis
The system works reasonably well on structured queries with explicit filters such as geography, public/private status, revenue 
or employee count. It performs less well when the query depends on implicit company role, hidden relationships or technology usage 
that is not explicitly written in the dataset. 
Below are several concrete failure patterns. 

## 3.1. Confusing operational activity with company role
A good example is the query **Logistic companies in Romania**.
The system returns companies such as OMW, Fildas Trading, METRO Romania, and Rompetrol near the top. These companies may have
logistics, warehousing, wholesale, or supply chain operations, but that does not necessarily mean they are logistics companies 
in the sense intended by the query. 
This happens because the ranking system gives credit when logistics-related terms appear in:
- description
- full profile
- NAICS labels
- business model
- target markets
- core offerings

As a result, the companies can confuse companies that perform logistics internally with companies whose main business is logistics. 
This is a role-understanding problem. The deterministic scoring captures lexical overlap, but not the exact economic role of the company. 

## 3.2 Weak handling of a technology-stack queries
A strong example is **E-commerce companies using Shopify or similar platforms**.
This query requires knowledge about the company's commerce stack or storefront technology. The dataset does not directly contain signals 
such as: 
- Shopify usage
- ecommerce platform provider
- website technology stack

Because of this, the system falls back to weak textual matching around "e-commerce" and related fields. This produces results 
that look plausible in ranking format but are not strongly supported by the available data. 
This is an important limitation: the system can rank companies for a query even when the dataset does not actually contain the evidence
needed to answer that query confidently.

## 3.3 Over-reliance on term overlap for supply-chain queries
The query **"Companies that manufacture or supply critical components for electric vehicle battery production"** is difficult because
it asks for a supply-chain role rather than a simple category match. 

In this case, companies can rank highly simply because they match battery-related terms, even if the connection to electric
vehicle battery production or "critical components" is weak.

This happens because the system is much better at recognizing the topic "battery" than at verifying the specific relationship to 
electric vehicle battery production and understanding what counts as critical upstream component. 

This is a general weakness of the current rule-based design: it handles entity/topic matching better than role and dependency matching.

## 3.4 Query concepts are sometimes represented too loosely
The query **Clean energy startups founded after 2018 with fewer than 200 employees** shows another weakness.
The structured constraints are handled correctly:
- founded after 2018
- fewer than 200 employees

However, concepts such as clean energy and startup are nod modeled very precisely. In practice, the system mostly uses energy-related terms
and vague signal words such as clean. 
This means some companies can rank highly because they are recent, small and energy-related, even if they are not clearly clean energy startups
in the intended sense. 

## 3.5 Term double-counting can inflate scores
The query "Food and beverage manufacturers in France" exposes another issue. 
The parser extracts: food and beverage, food, beverage as separate industry terms. This can cause the scoring stage to reward 
closely related signals multiple times even when they refer to the same concept. As a result, some candidates may receive artificially
high scores because one semantic idea is counted more than once. 

### Summary of main weaknesses
The system struggles most when:
- the query depends on implicit role rather than explicit wording
- the needed evidence is not present in the dataset
- technology usage must be inferred externally
- multiple related query terms overlap and inflate scores
- vague concepts such as "fast-growing", "critical" or "startup" require judgement rather than lexical matching. 

These errors are a direct consequence of the current design: the system is intentionally lightweight, interpretable and mostly 
deterministic, but that also makes it less robust on deeper semantic and relational queries. 

# 4. Scaling
The current system processes all companies for each query by scoring them sequentially. This approach works well for a dataset of a few hundred companies,
but it would not scale efficiently to 100000 or more companies. 
In order to handle larger datasets, several changes might be necessary.

## 4.1 Introduce a retrieval layer
The most important improvement would be to avoid scoring every company. Instead of iterating through the entire dataset, I would introduce
a retrieval step that selects a smaller subset of potentially relevant companies before scoring. 
This could be done using a vector index for semantic retrival or an inverted index for keyword-based retrival. 

The goal would be to reduce the candidate set from 100000 companies to a few hundred before applying the current scoring pipeline. 

## 4.2 Precompute searchable representations
Currently, many operations (such as building full text or matching terms across multiple fields) are done at query time. 
For better scalability, I would precompute: 
- normalized full text fields
- tokenized versions of important attributes
- possibly embeddings for each company
This would reduce repeated computation and improve latency. 

## 4.4 Replace full sorting with top-k selection
The current implementation scores all candidates and then sorts the entire list. 

For large datasets this can be optimized by 
- maintaining a heap of top-k candidates
- avoiding full sorting when only the top results are needed

This can reduce computational overhead. 

## 4.5 Optimize hard filtering
Hard constraints are currently applied after candidate generation. For better performance, structured constraints such as 
country, employee count, revenue, public/private status cound be applied earlier, directly in the retrieval step or using 
indexed filters. This would further reduce the number of candidates that need to be scored. 

## 4.6 Limit and batch LLM usage
The LLM stage is already selective, but at larger scale it becomes even more important to control its usage. 
Improvements could include:
- strict limits on how many candidates are set to the LLM
- batching multiple evaluation into a single request where possible
- caching LLM responses for repeated or similar queries

To scale from hundreds to hundreds of thousands of companies, the main change is moving from "scan all and score" approach 
to a "retrieve firs, then rank" architecture. 
The current pipeline (scoring, filtering, reranking, LLM refinement) can remain mostly unchanged, but it must operate on a much
smaller candidates set produced by an efficient retrieval layer. 

# 5. Failure Modes
The system can produce confident but incorrect results in several scenarios. These failures are particularly important because 
the ranking scores may suggest high relevance even when the underlying evidence is weak or misleading. 

## 5.1 False confidence from keyword overlap

The most common failure mode comes from heavy reliance on keyword and field matching. If a company mentions relevant terms across multiple
fields (description, NAICS, core offerings etc.) it can receive a high score if it does not truly satisfy the intent of the query. 

For example, company involved in a distribution of warehousing may rank highly for a "logistics company" query or a company mentioning
"battery" may rank highly for electric vehicle battery supply queries without actually being part of that supply chain. 
This happens because the system measures term presence, not true role or relevance.

## 5.2 Missing data leading to false positives
The system treats missing structured fields as uncertainty rather than failure. While this improves recall, it can also allow 
incorrect companies to pass filtering stages. 

For example, a company with missing revenue or employee count may pass constraints it should not satisfy, because uncertainty is 
only weakly penalized so such companies can still rank highly. 

This creates situations where the system appears confident despite incomplete evidence.

## 5.3 Queries requiring unavailable signals
Some queries require information that does not exist in the dataset. Examples include technology usage (for example, Shopify),
detailed supply chain relationships, growth metrics such as "fast-growing". 

In these cases, the system still produces a ranking based on partial or weak signals. This can lead to highly confident but incorrect outputs
because the system cannot explicitly detect that the required evidence is missing

## 5.4. Score inflation from overlapping terms
When multiple query terms represent the same concept(food, beverage, food and beverage) the system may reward them independently.
This leads to inflated scores and overconfidence in candidates that match repeated variations of the same idea. 

As a result, some companies appear stronger matches than they actually are. 

## 5.5 LLM reinforcing existing biases
The LLM reranking stage relies on the same company data, the same query and the same existing scoring signals. If the initial candidate
set is already biased or incorrect, the LLM may confirm incorrect matches and it may provide plausible bus misleading explanations. 

Additionally, if the LLM is only applied to a small subset of candidates, it cannot correct errors introduced earlier in the pipeline. 


# Monitoring in production
To detect this failure modes in a real system, I would monitor: 
### 1. Score distribution anomalies 
- unusually high scores across many candidates
- small score differences between top results
- top results with weak or generic signals

These may indicate score inflation or weak discrimination 

### 2. High uncertainty rates
- percentage of top-ranked results with has_uncertainty=True

A high rate suggests that ranking decisions rely on incomplete data. 

### 3. Query-result mismatch signals
- queries with very low final scores across all candidates
- queries where LLM labels are mostly weak_match or not_match

These may indicate that the system cannot properly answer the query. 

### 4. LLM disagreement with deterministic ranking
- cases where LLM assigns weak_match or not_match to top deterministic results. 

This can signal that earlier stages are producing misleading candidates.

### 5. Coverage gaps
- queries where important concepts are not present in any company profile

This cand be detected by low keyword match counts or lack of required term matches across all candidates. 