# Graph Report - .  (2026-04-20)

## Corpus Check
- Corpus is ~11,997 words - fits in a single context window. You may not need a graph.

## Summary
- 171 nodes · 201 edges · 23 communities detected
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 30 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Quiz Flow Nodes|Quiz Flow Nodes]]
- [[_COMMUNITY_Streamlit App Entry|Streamlit App Entry]]
- [[_COMMUNITY_Practice Multi-Agent|Practice Multi-Agent]]
- [[_COMMUNITY_Pydantic State Models|Pydantic State Models]]
- [[_COMMUNITY_Core Tech Stack|Core Tech Stack]]
- [[_COMMUNITY_Code Quality Docs|Code Quality Docs]]
- [[_COMMUNITY_Practice Routing|Practice Routing]]
- [[_COMMUNITY_App Core Modules|App Core Modules]]
- [[_COMMUNITY_Practice Basics|Practice Basics]]
- [[_COMMUNITY_Deployment & Infra|Deployment & Infra]]
- [[_COMMUNITY_Graph Routing Logic|Graph Routing Logic]]
- [[_COMMUNITY_PDF Ingestion|PDF Ingestion]]
- [[_COMMUNITY_Config & Env|Config & Env]]
- [[_COMMUNITY_State Management|State Management]]
- [[_COMMUNITY_Package Init|Package Init]]
- [[_COMMUNITY_Build Tools|Build Tools]]
- [[_COMMUNITY_Portfolio Problem|Portfolio Problem]]
- [[_COMMUNITY_Portfolio Design|Portfolio Design]]
- [[_COMMUNITY_Archived Portfolio Guide|Archived Portfolio Guide]]
- [[_COMMUNITY_Temp File Issues|Temp File Issues]]
- [[_COMMUNITY_Security Vulnerabilities|Security Vulnerabilities]]
- [[_COMMUNITY_Prompt Injection Risk|Prompt Injection Risk]]
- [[_COMMUNITY_Streamlit Runtime Fix|Streamlit Runtime Fix]]

## God Nodes (most connected - your core abstractions)
1. `PDF AI Quiz Chatbot Application` - 15 edges
2. `Implementation Plan (100% Complete)` - 10 edges
3. `QuizState` - 8 edges
4. `LangChain Quiz Chatbot Project` - 8 edges
5. `src/nodes.py Module (Graph Node Functions)` - 8 edges
6. `Target Modular Architecture (src/)` - 7 edges
7. `Multi-Agent Architecture Proposal` - 7 edges
8. `QuizSchema` - 6 edges
9. `main.py (Entry Point)` - 6 edges
10. `get_main_llm()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `pgvector Extension (Vector Storage)` --semantically_similar_to--> `FAISS Vector Store`  [INFERRED] [semantically similar]
  docs/DEPLOYMENT_GUIDE.md → agents.md
- `사용자의 의도에 따라 다음 노드를 결정합니다.` --uses--> `QuizState`  [INFERRED]
  src\graph.py → src\models.py
- `채점 결과에 따라 해설을 할지, 종료할지 결정합니다.` --uses--> `QuizState`  [INFERRED]
  src\graph.py → src\models.py
- `Wrong Answer Note Feature` --semantically_similar_to--> `wrong_answers Table (Supabase SQL)`  [INFERRED] [semantically similar]
  README.md → docs/DEPLOYMENT_GUIDE.md
- `parse_ai_json() JSON Parser` --semantically_similar_to--> `Structured Output via Pydantic + with_structured_output`  [INFERRED] [semantically similar]
  README.md → docs/DEV_LOG.md

## Hyperedges (group relationships)
- **LangGraph StateGraph Quiz Flow (router → quiz_gen → grade → explain loop)** — impl_plan_router_node, impl_plan_quiz_gen_node, impl_plan_grade_node, impl_plan_explain_node, impl_plan_quiz_state, impl_plan_src_graph [EXTRACTED 0.95]
- **End-to-End RAG Pipeline (PDF → FAISS → search → LLM answer)** — readme_pdf_parsing, agents_faiss, agents_search_pdf_documents, impl_plan_rag_search_node, readme_chunking [INFERRED 0.90]
- **Multi-Agent System (Supervisor + Specialists + Shared State)** — multi_agent_supervisor, multi_agent_quiz_master, multi_agent_grading_agent, multi_agent_rag_research, multi_agent_learning_coach, multi_agent_quiz_chatbot_state [EXTRACTED 0.95]

## Communities

### Community 0 - "Quiz Flow Nodes"
Cohesion: 0.12
Nodes (22): coach_analyze() Node (Learning Coach), explain() Node (Document-Based Explanation), grade() Node (Answer Grading), quiz_gen() Node (RAG-based Quiz Generation), QuizState (TypedDict LangGraph State), rag_search() Node (General QA), router() Node (Intent Classification), src/graph.py Module (StateGraph Assembly) (+14 more)

### Community 1 - "Streamlit App Entry"
Cohesion: 0.11
Nodes (21): initialize_agent() Function, main.py (Entry Point), question_generator() Function, search_pdf_documents Tool, st.session_state (Streamlit State), Critical Issue: Full PDF Context in Prompt, Critical Issue: LLM Response Parse Crash, Critical Issue: Greedy Regex JSON Parsing (+13 more)

### Community 2 - "Practice Multi-Agent"
Cohesion: 0.11
Nodes (18): BaseModel, explain_node(), grade_node(), qa_node(), quiz_gen_node(), QuizSchema, ============================================================= [3단계] 실전 멀티 에이전트:, [퀴즈 생성] Structured Output으로 안정적인 퀴즈 데이터를 생성합니다.      with_structured_output(Quiz (+10 more)

### Community 3 - "Pydantic State Models"
Cohesion: 0.18
Nodes (15): QuizSchema, QuizState, 그래프 전체에서 공유되고 유지되는 상태(State) 정의, AI가 생성할 퀴즈의 구조화된 데이터 모델, coach_analyze(), explain(), get_main_llm(), get_router_llm() (+7 more)

### Community 4 - "Core Tech Stack"
Cohesion: 0.14
Nodes (15): docs/DEV_LOG.md (Dev Tracking), FAISS Vector Store, Google Gemini LLM, LangChain Framework, LangGraph Framework, LangChain Quiz Chatbot Project, Streamlit UI Framework, S-1: FAISS Dangerous Deserialization (RCE Risk) (+7 more)

### Community 5 - "Code Quality Docs"
Cohesion: 0.21
Nodes (13): PORTFOLIO_CHECKLIST.md Reference, Code Analysis Document (v0.1.0), Single-File Monolith Architecture (Current), Improvement Roadmap (Phase 1-4), src/agent.py Module, src/config.py Module, src/ingestion.py Module, src/quiz_gen.py Module (+5 more)

### Community 6 - "Practice Routing"
Cohesion: 0.17
Nodes (11): coach_node(), qa_node(), quiz_node(), ============================================================= [2단계] 조건부 라우팅: 의도, 상태에 저장된 'intent'를 읽어 다음 노드 이름을 반환합니다.      반환값: 노드 이름 문자열 또는 END 상수, [라우터] 사용자 입력을 분석해 의도를 분류합니다.      LLM에게 세 가지 카테고리 중 하나를 고르도록 지시합니다.     반환된 의도는, [퀴즈 에이전트] 퀴즈 문제를 생성합니다., [QA 에이전트] 사용자 질문에 답변합니다. (+3 more)

### Community 7 - "App Core Modules"
Cohesion: 0.22
Nodes (8): init_session_state(), 업로드된 PDF 문서 내에서 정보를 검색합니다.      사실 확인이나 전문적인 응답이 필요할 때 사용하세요., search_pdf_documents(), get_embeddings(), get_vectorstore(), 기존 FAISS 인덱스를 로드하거나 None을 반환합니다., 문서 리스트를 벡터화하여 로컬에 저장합니다., save_vectorstore()

### Community 8 - "Practice Basics"
Cohesion: 0.2
Nodes (9): answer_node(), print_node(), ============================================================= [1단계] LangGraph 기초, [노드 1] 질문을 받아 LLM으로 답변을 생성합니다.      state["question"]을 읽어 LLM을 호출하고,     결과를 "an, [노드 2] 최종 답변을 출력합니다.      상태를 변경하지 않으므로 빈 딕셔너리를 반환합니다., SimpleState, RouterState, AgentState (+1 more)

### Community 9 - "Deployment & Infra"
Cohesion: 0.25
Nodes (8): Deployment Guide (Streamlit + Supabase), pgvector Extension (Vector Storage), Streamlit Community Cloud Hosting, Supabase (PostgreSQL + pgvector + Auth), Supabase Auth (User Management), wrong_answers Table (Supabase SQL), Quiz Generator Mode, Wrong Answer Note Feature

### Community 10 - "Graph Routing Logic"
Cohesion: 0.33
Nodes (4): 사용자의 의도에 따라 다음 노드를 결정합니다., 채점 결과에 따라 해설을 할지, 종료할지 결정합니다., route_after_grade(), route_by_intent()

### Community 11 - "PDF Ingestion"
Cohesion: 0.67
Nodes (2): load_and_split_pdf(), PDF 파일을 로드하고 지정된 크기로 분할합니다.

### Community 12 - "Config & Env"
Cohesion: 1.0
Nodes (0): 

### Community 13 - "State Management"
Cohesion: 1.0
Nodes (2): Critical Issue: Over-reliance on Global State, @st.cache_resource Optimization

### Community 14 - "Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 15 - "Build Tools"
Cohesion: 1.0
Nodes (1): uv Package Manager

### Community 16 - "Portfolio Problem"
Cohesion: 1.0
Nodes (1): Problem Definition (Portfolio)

### Community 17 - "Portfolio Design"
Cohesion: 1.0
Nodes (1): Design Structure (LangGraph + RAG)

### Community 18 - "Archived Portfolio Guide"
Cohesion: 1.0
Nodes (1): SW Portfolio Guide (Archived)

### Community 19 - "Temp File Issues"
Cohesion: 1.0
Nodes (1): Critical Issue: Temp File Resource Leak

### Community 20 - "Security Vulnerabilities"
Cohesion: 1.0
Nodes (1): Security Vulnerabilities Table

### Community 21 - "Prompt Injection Risk"
Cohesion: 1.0
Nodes (1): S-4: Prompt Injection Vulnerability

### Community 22 - "Streamlit Runtime Fix"
Cohesion: 1.0
Nodes (1): DEV LOG: Streamlit Runtime Already Exists Fix (2026-04-12)

## Knowledge Gaps
- **58 isolated node(s):** `============================================================= [1단계] LangGraph 기초`, `[노드 1] 질문을 받아 LLM으로 답변을 생성합니다.      state["question"]을 읽어 LLM을 호출하고,     결과를 "an`, `[노드 2] 최종 답변을 출력합니다.      상태를 변경하지 않으므로 빈 딕셔너리를 반환합니다.`, `============================================================= [2단계] 조건부 라우팅: 의도`, `[라우터] 사용자 입력을 분석해 의도를 분류합니다.      LLM에게 세 가지 카테고리 중 하나를 고르도록 지시합니다.     반환된 의도는` (+53 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Config & Env`** (2 nodes): `validate_env()`, `config.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `State Management`** (2 nodes): `Critical Issue: Over-reliance on Global State`, `@st.cache_resource Optimization`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Build Tools`** (1 nodes): `uv Package Manager`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Portfolio Problem`** (1 nodes): `Problem Definition (Portfolio)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Portfolio Design`** (1 nodes): `Design Structure (LangGraph + RAG)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Archived Portfolio Guide`** (1 nodes): `SW Portfolio Guide (Archived)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Temp File Issues`** (1 nodes): `Critical Issue: Temp File Resource Leak`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Security Vulnerabilities`** (1 nodes): `Security Vulnerabilities Table`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Prompt Injection Risk`** (1 nodes): `S-4: Prompt Injection Vulnerability`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Streamlit Runtime Fix`** (1 nodes): `DEV LOG: Streamlit Runtime Already Exists Fix (2026-04-12)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QuizState` connect `Pydantic State Models` to `Practice Basics`, `Graph Routing Logic`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `PDF AI Quiz Chatbot Application` connect `Streamlit App Entry` to `Deployment & Infra`, `Core Tech Stack`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `Implementation Plan (100% Complete)` connect `Code Quality Docs` to `Quiz Flow Nodes`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `QuizState` (e.g. with `사용자의 의도에 따라 다음 노드를 결정합니다.` and `채점 결과에 따라 해설을 할지, 종료할지 결정합니다.`) actually correct?**
  _`QuizState` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `============================================================= [1단계] LangGraph 기초`, `[노드 1] 질문을 받아 LLM으로 답변을 생성합니다.      state["question"]을 읽어 LLM을 호출하고,     결과를 "an`, `[노드 2] 최종 답변을 출력합니다.      상태를 변경하지 않으므로 빈 딕셔너리를 반환합니다.` to the rest of the system?**
  _58 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Quiz Flow Nodes` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._
- **Should `Streamlit App Entry` be split into smaller, more focused modules?**
  _Cohesion score 0.11 - nodes in this community are weakly interconnected._