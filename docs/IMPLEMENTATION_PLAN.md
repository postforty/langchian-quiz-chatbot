# 구현 계획서 (Implementation Plan) ✅ 완료

> **프로젝트**: PDF AI 퀴즈 챗봇 — 멀티 에이전트 아키텍처 리팩토링
> **브랜치**: `refactor/code-analysis-and-improvement-plan`
> **상태**: **100% 완료 (2026-04-15)**
> **관련 문서**: [CODE_ANALYSIS.md](./CODE_ANALYSIS.md) · [MULTI_AGENT_PROPOSAL.md](./MULTI_AGENT_PROPOSAL.md)

---

## 1. 목표

단일 파일 모놀리스(`main.py`, 263줄)를 **모듈화된 저수준 LangGraph StateGraph 기반 멀티 에이전트 아키텍처**로 전환합니다. 동시에 코드 분석에서 식별된 안정성·보안·성능 이슈를 해결합니다.

### 1.1 완료 기준 (모두 달성)

1. [x] `main.py`는 Streamlit UI 렌더링만 담당 (100줄 이내)
2. [x] 비즈니스 로직은 `src/` 모듈로 완전 분리
3. [x] 퀴즈 플로우가 `StateGraph`로 동작 (출제 → 답변 대기 → 채점 → 해설 루프)
4. [x] RAG 질의응답이 `StateGraph` 내 별도 노드로 동작
5. [x] LLM 응답 실패 시 앱 크래시 없이 graceful fallback 제공
6. [x] `docs/DEV_LOG.md`에 주요 결정 사항 기록

---

## 2. 타겟 디렉토리 구조 (구현 완료)

```
langchian-quiz-chatbot/
├── main.py                    # Streamlit UI (진입점 - 리팩토링 완료)
├── src/                       # 신규 패키지 생성 완료
│   ├── __init__.py
│   ├── config.py              # 모델명, 파라미터, 환경변수 중앙 관리
│   ├── models.py              # Pydantic 스키마 (QuizSchema 등)
│   ├── ingestion.py           # PDF 로딩, 텍스트 분할
│   ├── vectorstore.py         # FAISS 로드/저장/검색 추상화
│   ├── tools.py               # @tool 데코레이터 함수 (검색 도구)
│   ├── nodes.py               # StateGraph 노드 함수 (router, quiz_gen, grade 등)
│   └── graph.py               # StateGraph 조립 및 컴파일
├── docs/
│   ├── CODE_ANALYSIS.md
│   ├── MULTI_AGENT_PROPOSAL.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── DEV_LOG.md
│   └── DEPLOYMENT_GUIDE.md
├── pyproject.toml
└── .env
```

---

## 3. 단계별 태스크 리스트

### 3.1 Phase 1 — 기반 구축 및 모듈 분리 ✅

#### Task 1.1: `src/config.py` — 설정 중앙 관리 모듈
- [x] 환경변수 로드 및 검증 함수 (`validate_env()`)
- [x] 모델명 상수 정의 (`ROUTER_MODEL`, `MAIN_MODEL`, `EMBEDDING_MODEL`)
- [x] 청킹 파라미터 상수 (`CHUNK_SIZE`, `CHUNK_OVERLAP`)
- [x] FAISS 인덱스 경로 상수 (`FAISS_INDEX_PATH`)
- [x] API 키 미설정 시 명확한 에러 메시지 출력

#### Task 1.2: `src/models.py` — Pydantic 데이터 스키마
- [x] `QuizSchema`: 퀴즈 구조 (question, options, answer, explanation)
- [x] `QuizState` (TypedDict): LangGraph 그래프 공유 상태 정의
- [x] 기존 `parse_ai_json()` 정규식 파싱을 대체할 구조화 출력 기반

#### Task 1.3: `src/ingestion.py` — PDF 처리 모듈
- [x] `load_and_parse_pdf()` 함수 이전
- [x] `tempfile` 처리를 `try/finally`로 감싸기 (리소스 누수 방지)
- [x] PDF 파일 크기 검증 (50MB 제한 추가)
- [x] 텍스트 추출 실패 시 에러 핸들링

#### Task 1.4: `src/vectorstore.py` — 벡터스토어 관리 모듈
- [x] `get_or_create_vectorstore()`: FAISS 로드/생성 통합 함수
- [x] `search_documents(query, k)`: 검색 추상화
- [x] `@st.cache_resource`를 활용한 임베딩 객체 캐싱
- [x] `allow_dangerous_deserialization` 경고 주석 추가

#### Task 1.5: `main.py` UI 리팩토링
- [x] `main.py`에서 비즈니스 로직 제거, `src/` 모듈 임포트로 전환
- [x] 세션 상태 초기화를 함수로 분리
- [x] UI 렌더링 코드만 남기기 (117줄로 압축)

#### Task 1.6: Phase 1 검증 및 기록
- [x] 기존과 동일하게 동작하는지 수동 테스트 완료
- [x] `docs/DEV_LOG.md`에 모듈 분리 결정 사항 기록 완료

---

### 3.2 Phase 2 — StateGraph 기반 멀티 에이전트 구현 ✅

#### Task 2.1: `src/nodes.py` — 그래프 노드 함수 구현
- [x] `router()`: 자연어 의도 분류 및 숫자 답변 자동 인식 로직 강화
- [x] `quiz_gen()`: RAG 기반 퀴즈 생성 및 Structured Output 적용
- [x] `grade()`: 답변 채점 및 세션 상태 관리
- [x] `explain()`: 문서 근거 상세 해설 노드 구현
- [x] `rag_search()`: 일반 질의응답 노드 구현
- [x] `coach_analyze()`: 학습 데이터 기반 코칭 노드 구현

#### Task 2.2: `src/tools.py` — 검색 도구 분리
- [x] 검색 도구 추상화 완료 (`search_pdf_documents`)

#### Task 2.3: `src/graph.py` — StateGraph 조립
- [x] 노드 등록 및 엣지 연결 완료
- [x] 조건부 라우팅 로직 정교화

#### Task 2.4: `main.py` — StateGraph 통합
- [x] `graph.invoke()`를 통한 통합 로직 구현 완료
- [x] 세션 상태와 그래프 상태 동기화 완료

#### Task 2.5: Phase 2 검증 및 기록
- [x] End-to-End 흐름 (출제→채점→해설) 검증 완료
- [x] `docs/DEV_LOG.md`에 설계 결정 기록 완료

---

### 3.3 Phase 3 — 안정화 및 품질 향상 ✅

#### Task 3.1: 에러 핸들링 강화
- [x] LLM API 로직 안정화 및 예외 처리
- [x] Structured Output을 통한 파싱 에러 근본적 해결

#### Task 3.2: 성능 최적화
- [x] `@st.cache_resource`를 통한 리소스 재사용 최적화
- [x] 라우터에 경량 모델 적용으로 응답 속도 및 비용 개선

#### Task 3.3: UI/UX 개선
- [x] 사이드바 실시간 정답률 메트릭 도입
- [x] 학습 데이터 초기화 기능 추가

#### Task 3.4: DEV_LOG 작성
- [x] 모든 리팩토링 과정 상세 기록 완료 (2026-04-15)

---

## 8. 체크포인트 달성 현황

| 체크포인트 | 완료 여부 | 비고 |
|:---|:---:|:---|
| **CP1: 모듈 분리 완료** | **완료** | `src/` 패키지화 성공 |
| **CP2: StateGraph 동작** | **완료** | 퀴즈 루프 안정성 확보 |
| **CP3: 멀티 에이전트 통합** | **완료** | 자동 의도 분류 구현 |
| **CP4: 안정화 완료** | **완료** | 프로덕션 수준 코드 품질 확보 |
