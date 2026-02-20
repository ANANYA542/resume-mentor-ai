## 1. Project Overview
Resume Mentor AI is an AI-powered (and offline-capable) resume review system that:

- Parses resumes (text today; PDF supported for backend/CLI).
- Detects ATS/formatting risks.
- Scores the resume with an ATS alignment component against a provided job description.
- Generates feedback (strengths, weaknesses, suggestions).
- Produces skill-gap insights and basic bullet rewrite suggestions.
- Stores analysis “versions” for later retrieval.

This repository now supports:

- **CLI**: quick local analysis (legacy mode + upgraded analyzer).
- **Backend API (FastAPI)**: production-oriented JSON API.
- **AI service layer**: pluggable LLM module (Gemini supported when `GEMINI_API_KEY` is set), with deterministic fallbacks.

---

## 2. Existing System Analysis
### What was already present
- A **stdin-based CLI** (`cli.py`) that accepted pasted resume text.
- A **simple heuristic detector** (`pipeline.py`) that flagged a few formatting problems.
- A **local RAG retriever** (`rag.py`, `retriever.py`) using `sentence-transformers` + FAISS over text files in `data/`.
- A rule-to-suggestion mapper (`improver.py`) that existed but was not used by the pipeline.

### Issues found
- **No actual resume parsing** (no PDF ingestion, no structured extraction).
- **No LLM-backed analysis** (Gemini test existed but not integrated).
- **No job description matching / ATS matching**.
- **No proper scoring breakdown** (only a penalty score existed and was unused).
- **RAG bugs/risks**:
  - Query embeddings were normalized but corpus embeddings were not.
  - FAISS L2 distances were labeled as “score” (lower is better) causing confusing semantics.
  - Index built at import-time in `retriever.py` (slow and unsafe for servers).

---

## 3. Changes Made
### Refactoring & cleanup
- **Fixed RAG scoring semantics**:
  - Switched from L2 distance to **cosine similarity** via normalized vectors and `IndexFlatIP`.
  - Removed noisy `print()` side effects from the core RAG engine.
- **Removed import-time side effects**:
  - `retriever.py` now lazily initializes the index on first use.
- **Connected the existing rule-based improver**:
  - `pipeline.py` now uses `improver.generate_suggestions()` and returns a numeric score.

### Added production structure
Added a proper Python package and API server:
- `resume_mentor_ai/` (core library)
  - `core/` models + parsing + scoring logic
  - `ai/` LLM wrapper (Gemini JSON output when configured)
  - `services/` analysis + storage
- `backend/main.py` FastAPI server providing consistent JSON responses

### Added features (new)
- **PDF → text** using `pypdf` (`resume_mentor_ai/core/pdf.py`).
- **Structured-ish extraction**:
  - section splitting
  - bullet extraction
  - heuristic skill extraction
- **ATS scoring vs job description**:
  - keyword overlap-based match score
  - missing keywords list (skill-gap style output)
- **Feedback generation**:
  - strengths / weaknesses / suggestions produced deterministically
- **Basic bullet rewrite suggestions** (deterministic placeholder rewrites; LLM upgrades plug in cleanly).
- **Resume version tracking**:
  - persisted JSON results under `.resume_mentor/analyses/`
  - API endpoints to list and fetch versions
- **Standardized API responses** with a consistent `{ ok, data, error }` envelope.

---

## 4. Architecture Explanation
### High-level design
- **CLI (`cli.py`)**
  - Supports legacy pipeline (`--legacy`)
  - Supports upgraded analysis (text or `--pdf`)
- **Backend API (`backend/main.py`)**
  - Stateless compute + local persistence of results
  - Optional RAG retrieval (safe fallback if embeddings are unavailable)
- **Core services**
  - `resume_mentor_ai/services/analyzer.py`: main analysis pipeline and scoring
  - `resume_mentor_ai/services/storage.py`: basic local version tracking
- **RAG knowledge base (optional)**
  - Uses `data/*.txt` to retrieve relevant ATS rules/best practices

### Data flow (API)
1. Client sends `POST /analyze` with `resume_text` and optionally `job_description`.
2. Backend optionally fetches RAG rules (best-effort).
3. Analyzer generates:
   - issues
   - score breakdown
   - feedback
   - skill gap and bullet rewrites
4. Backend persists results and returns JSON.

---

## 5. Feature Breakdown
### 1) Resume parsing (PDF → structured data)
- Implemented: **PDF to text** and lightweight structure extraction (sections/bullets/skills).
- Limitations: not a full “schema extraction” (company/role/date parsing can be added later).

### 2) AI-based resume analysis
- Implemented: deterministic analysis + a modular `ai/llm.py` that can later enrich outputs.
- When `GEMINI_API_KEY` is set, the LLM layer can be used to produce structured JSON (not yet wired into the analyzer by default).

### 3) ATS matching with job description
- Implemented: overlap-based ATS keyword match score + missing keywords list.

### 4) Resume scoring system
- Implemented: breakdown into:
  - formatting
  - content
  - ats_match
  - overall weighted score

### 5) Feedback generation
- Implemented:
  - strengths
  - weaknesses
  - suggestions

### Enhancements requested (status)
- **Better prompt engineering + structured JSON**: scaffolding in `resume_mentor_ai/ai/llm.py` (ready to integrate).
- **Advanced JD matching**: current implementation is keyword overlap; can be upgraded to embedding-based semantic scoring when local embeddings are stable.
- **Skill gap analysis**: provided via missing keyword list; can be upgraded to skill ontology.
- **Bullet rewrites**: deterministic placeholder rewrites exist; LLM rewrite integration is straightforward.
- **Version tracking**: implemented via `.resume_mentor/analyses/` plus API endpoints.
- **Modular AI service layer**: created (`resume_mentor_ai/ai`).

---

## 6. Future Scope
- **True resume schema extraction** (experience entries, dates, roles, education items) using LLM JSON with validation.
- **Semantic ATS matching** using embeddings (cosine similarity) and calibrated weights.
- **Bullet rewrite engine** with:
  - STAR format enforcement
  - quantified impact suggestions
  - duplicate/weak verb detection
- **UI**:
  - Streamlit app or a small React frontend hitting the FastAPI API
  - PDF upload, JD paste, version comparison
- **Testing**:
  - pytest suite for scoring + parsing
  - golden-file tests for stable outputs

