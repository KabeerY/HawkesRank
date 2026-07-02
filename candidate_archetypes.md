# Candidate Archetypes Discovered in `candidates.jsonl`

## Scope and method

This report is based on a complete streaming inspection of all 100,000 JSONL records. It does not use hidden labels or outside information.

The dataset is highly templated:

- 47 distinct current-title values.
- 44 exact career-description templates across every job in every profile.
- 76 normalized profile-summary templates after replacing numeric experience values.
- Every candidate's entire career history stays inside exactly one of six disjoint career-template families. No candidate crosses families.

This six-family structure strongly resembles the documented tier 0-5 relevance setup. That mapping is a data-supported inference, not an exposed label.

## Population structure

| Data-derived family | Candidates | Share | Likely tier interpretation |
|---|---:|---:|---|
| Nontechnical/business AI-curious profiles | 68,821 | 68.821% | Likely tier 0 |
| General software/cloud engineers | 25,000 | 25.000% | Likely tier 1 |
| Data/backend ML-adjacent engineers | 5,000 | 5.000% | Likely tier 2 |
| Applied-ML but role-adjacent profiles | 1,000 | 1.000% | Likely tier 3 |
| Direct search/ranking/retrieval ML specialists | 150 | 0.150% | Likely tier 4 |
| Senior search/relevance owners | 29 | 0.029% | Likely tier 5 |

The family sizes sum to exactly 100,000.

## Archetype 1: Nontechnical/business AI-curious profiles

**Count:** 68,821

**Observed titles:** Business Analyst, HR Manager, Mechanical Engineer, Accountant, Project Manager, Customer Support, Operations Manager, Content Writer, Sales Executive, Civil Engineer, Graphic Designer, Marketing Manager.

**Observed professional states:** sales, customer support, marketing, consulting/business analysis, brand design, mechanical engineering, accounting, content/SEO, or logistics operations. Summaries frequently describe ChatGPT use, AI curiosity, courses, or side projects.

**Why this family is dangerous:** candidates can carry dense AI skill lists despite having no professional AI ownership. The family averages 0.96 AI skills but reaches 13. Assessment coverage is almost absent: median zero and mean 0.12 assessed skills.

**Representative trap:** `CAND_0000021` is a Project Manager with a RAG/vector/embedding skill list, but the profile describes project management and AI experimentation. Its current-role description is brand design, its activity predates signup, and descriptions repeat across unrelated roles.

**Ranking implication:** titles alone are not enough, but career evidence decisively rules this family out for the target role. Good behavior must never rescue it.

## Archetype 2: General software/cloud engineers

**Count:** 25,000

**Observed titles:** Full Stack Developer, Cloud Engineer, Java Developer, .NET Developer, DevOps Engineer, Mobile Developer, Frontend Engineer, Software Engineer, QA Engineer.

**Observed professional states:** mobile development, cloud/DevOps, full-stack SaaS development, frontend, Java backend, or QA/test automation. Profiles often mention self-learning AI, hosted APIs, or a small RAG side project without professional ML work.

**Why this family is deceptive:** it has genuine production engineering and shipping evidence, so generic semantic similarity can overrate it. The typical candidate has one AI-listed skill, but some have 11.

**Representative example:** `CAND_0000014` has FAISS in skills and a FAISS assessment, but its career is frontend engineering and its RAG experience is explicitly a side project, not professional work.

**Ranking implication:** potentially useful backend/platform adjacency, but normally lacks production retrieval-model ownership and ranking evaluation.

## Archetype 3: Data/backend ML-adjacent engineers

**Count:** 5,000

**Observed titles:** Analytics Engineer, Data Engineer, Data Analyst, Software Engineer, Backend Engineer, Senior Data Engineer, Senior Software Engineer.

**Six current-work subtypes:**

1. Backend/data hybrid building warehouses and orchestration: 867.
2. Analytical warehouse and dbt/SQL specialist: 863.
3. Python/FastAPI backend and model-service integration: 827.
4. Analytics engineer doing roughly 30% lightweight ML: 816.
5. Airflow/Spark batch-pipeline engineer: 816.
6. Kafka/Spark Streaming data-platform engineer: 811.

The family averages 3.91 AI skills and 1.77 skill assessments. It is materially closer to the role than general software engineering but usually enabled ML rather than owning retrieval/ranking.

**Representative example:** `CAND_0000225` owns a Python analytics service and integrated another team's model-serving system, but explicitly did not build the model.

**Ranking implication:** a valuable recall pool for hidden adjacent candidates, especially strong Python/backend/data-infrastructure profiles, but direct search/evaluation evidence is usually missing.

## Archetype 4: Applied-ML but role-adjacent profiles

**Count:** 1,000

**Observed titles:** ML Engineer, AI Research Engineer, Data Scientist, Senior Software Engineer (ML), Computer Vision Engineer, Junior ML Engineer, AI Specialist.

**Six current-work subtypes:**

| Applied-ML subtype | Candidates | Main gap relative to the JD |
|---|---:|---|
| Production-side fraud ML/API/feature-store engineer | 187 | Modeling ownership is secondary |
| Lightweight production recommendation/reranking | 166 | Deployment owned by another team |
| Time-series forecasting | 166 | Wrong problem family |
| Computer vision moderation | 163 | CV-first, limited NLP/IR |
| NLP classification pipelines | 162 | Small-scale classification, not search/ranking |
| Churn/conversion/LTV predictive modeling | 156 | General predictive ML, limited retrieval |

The median candidate has seven AI skills and two assessments. These are real ML practitioners, unlike the lower families.

**Representative examples:**

- `CAND_0001151` built production recommendation-style features and gradient-boosted reranking, but platform engineers handled deployment.
- `CAND_0000165` has real production CV training/inference experience but explicitly says NLP/LLM experience is limited.

**Ranking implication:** likely the broad relevance floor. Recommendation and production-engineering subtypes may enter the top 100; CV, forecasting, and generic predictive-modeling candidates need stronger corroborating evidence.

## Archetype 5: Direct search/ranking/retrieval ML specialists

**Count:** 150

**Observed titles:** Recommendation Systems Engineer, Machine Learning Engineer, Applied ML Engineer, Search Engineer, AI Engineer, Senior Data Scientist, NLP Engineer.

**Six current-work subtypes:**

| Direct subtype | Candidates |
|---|---:|
| E-commerce search learning-to-rank + relevance labeling | 41 |
| Discovery-feed ranking + offline/online correlation | 28 |
| Semantic search with sentence-transformers and FAISS | 27 |
| Production RAG support system | 20 |
| Large-scale content recommendation + A/B testing | 17 |
| Production MLOps/churn pipeline | 17 |

This family has strong behavioral envelopes: 73.3% open to work, 76.0% recently active, 63.3% with response rate at least 0.60, and 82.0% with a linked GitHub score.

**Representative examples:**

- `CAND_0006557` owned an e-commerce search ranker, relevance-labeling pipeline, feature pipeline, and evaluation workflow.
- `CAND_0005649` built semantic search using sentence-transformers and FAISS and validated improvement through human relevance judgments.

**Ranking implication:** this is the main high-confidence shortlist pool, but behavior, experience band, exact subtype, and coherence still separate candidates.

## Archetype 6: Senior search/relevance owners

**Count:** 29

**Observed titles:** Senior NLP Engineer, Senior Machine Learning Engineer, Staff Machine Learning Engineer, Senior AI Engineer, Senior Applied Scientist, Lead AI Engineer.

These profiles own end-to-end ranking, hybrid retrieval, semantic search, personalization, evaluation, operational monitoring, and frequently teams or migrations. Current-work templates include:

- End-to-end embeddings -> retrieval -> learning-to-rank -> behavioral reranking: 6.
- Marketplace recommendation shipped through live A/B testing: 4.
- Recruiter-facing BM25+dense+LLM reranking at 50M queries/month: 4.
- Candidate-JD LLM fine-tuning and production serving: 3.
- Plain-language relevance/matching ownership: several templates totaling 6 candidates.
- Large-scale hybrid semantic search and embedding-drift operations: 2.
- Candidate-corpus embedding-search migration with recruiter metrics: 2.
- Personalization infrastructure or end-to-end discovery ownership: 2.

**Representative examples:**

- `CAND_0006567` is the important plain-language pattern. It describes connecting users to relevant matches, replacing hand-tuned heuristics with explicit modeling/evaluation, and growing the team—without leaning on fashionable vector-database vocabulary.
- `CAND_0008425` explicitly owns hybrid sparse+dense search, NDCG, latency, index refresh, drift monitoring, and online/offline correlation.
- `CAND_0046525` migrated a 30M-candidate corpus from keyword to embedding search, ran A/B tests, improved recruiter engagement, and is Pune-based with strong availability.

**Ranking implication:** this is the natural top-10 source, but it is not automatically the final top 10. Behavior and feasibility still vary substantially within identical technical templates.

## Behavioral variants are overlays, not professional archetypes

Candidates with the exact same current-work template can have sharply different hiring feasibility.

For the same end-to-end ranking template:

- `CAND_0007411`: not open, last active in December 2025, response rate 0.12, 215-hour response time.
- `CAND_0039754`: open, active in May 2026, response rate 0.81, 38.5-hour response time, willing to relocate—but has 16.2 years of experience.

The technical archetype should establish relevance; behavior and logistics should reorder candidates inside or near that relevance band.

## Coherence and trap overlays

Observed broad anomaly counts:

- Skill duration exceeds stated professional experience: 15,350 candidates.
- Repeated exact role description inside one profile: 35,984.
- Last activity predates platform signup: 7,496.
- Salary minimum exceeds salary maximum: 18,865.

These counts are far larger than the documented approximately 80 honeypots. Therefore none of these broad checks is a safe honeypot veto by itself. Much of the apparent inconsistency is ordinary synthetic-generation noise.

A narrower impossible-profile pattern exists: 21 candidates contain 84 skill claims marked `expert` with exactly zero months of experience. This is a clear honeypot-like subtype, concentrated entirely in the lower four families and absent from both direct-search families.

Risk scoring should therefore distinguish:

- **Hard impossibility evidence:** expert skill with zero duration, impossible chronology, or multiple mutually reinforcing contradictions.
- **Weak synthetic-noise evidence:** repeated templates, inverted salary alone, or modest skill-duration overrun.

## Important conclusions for the ranker

1. The dataset is not a smooth 100,000-profile semantic-search problem. It is a sharply stratified six-family population.
2. Career-description template family is substantially more informative than skill-list similarity.
3. The real ranking competition is likely concentrated among roughly 1,179 candidates: the 1,000 applied-ML, 150 direct-search, and 29 senior-search profiles.
4. The top-10 competition is likely concentrated among the 179 direct and senior profiles, after subtype, feasibility, and coherence checks.
5. Title-only filtering is insufficient: `Software Engineer` appears in both general-software and data/backend families, while the strongest senior family contains plain-language relevance owners.
6. Skill lists are intentionally noisy. Career evidence should dominate, assessments should corroborate, and isolated buzzwords should contribute little.
7. Broad anomaly penalties would overfire badly. Honeypot detection needs narrow, multi-signal evidence.
8. Behavioral signals are correlated with professional family but still vary enough to matter strongly within the direct-fit pools.
