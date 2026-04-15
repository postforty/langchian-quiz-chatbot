# 구현 계획서 (Implementation Plan)

> **프로젝트**: PDF AI 퀴즈 챗봇 — 멀티 에이전트 아키텍처 리팩토링
> **브랜치**: `refactor/code-analysis-and-improvement-plan`
> **작성일**: 2026-04-15
> **관련 문서**: [CODE_ANALYSIS.md](./CODE_ANALYSIS.md) · [MULTI_AGENT_PROPOSAL.md](./MULTI_AGENT_PROPOSAL.md)

---

## 1. 목표

단일 파일 모놀리스(`main.py`, 263줄)를 **모듈화된 저수준 LangGraph StateGraph 기반 멀티 에이전트 아키텍처**로 전환합니다. 동시에 코드 분석에서 식별된 안정성·보안·성능 이슈를 해결합니다.

### 1.1 완료 기준

1. `main.py`는 Streamlit UI 렌더링만 담당 (100줄 이내)
2. 비즈니스 로직은 `src/` 모듈로 완전 분리
3. 퀴즈 플로우가 `StateGraph`로 동작 (출제 → 답변 대기 → 채점 → 해설 루프)
4. RAG 질의응답이 `StateGraph` 내 별도 노드로 동작
5. LLM 응답 실패 시 앱 크래시 없이 graceful fallback 제공
6. `docs/DEV_LOG.md`에 주요 결정 사항 기록

---

## 2. 타겟 디렉토리 구조

```
langchian-quiz-chatbot/
├── main.py                    # Streamlit UI (진입점)
├── src/
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
│   ├── IMPLEMENTATION_PLAN.md  # (이 문서)
│   ├── DEV_LOG.md
│   └── DEPLOYMENT_GUIDE.md
├── pyproject.toml
└── .env
```

---

## 3. 단계별 태스크 리스트

### 3.1 Phase 1 — 기반 구축 및 모듈 분리

현재 `main.py`의 로직을 기능별 모듈로 분리합니다. 이 단계에서는 **기존 동작을 유지**하면서 구조만 변경합니다.

#### Task 1.1: `src/config.py` — 설정 중앙 관리 모듈

- [ ] 환경변수 로드 및 검증 함수 (`validate_env()`)
- [ ] 모델명 상수 정의 (`ROUTER_MODEL`, `MAIN_MODEL`, `EMBEDDING_MODEL`)
- [ ] 청킹 파라미터 상수 (`CHUNK_SIZE`, `CHUNK_OVERLAP`)
- [ ] FAISS 인덱스 경로 상수 (`FAISS_INDEX_PATH`)
- [ ] API 키 미설정 시 명확한 에러 메시지 출력

```python
# 예시 구조
ROUTER_MODEL = "gemini-2.5-flash-lite"
MAIN_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "models/gemini-embedding-001"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
FAISS_INDEX_PATH = "faiss_index_pdf_quiz"
```

#### Task 1.2: `src/models.py` — Pydantic 데이터 스키마

- [ ] `QuizSchema`: 퀴즈 구조 (question, options, answer, explanation)
- [ ] `QuizState` (TypedDict): LangGraph 그래프 공유 상태 정의
- [ ] 기존 `parse_ai_json()` 정규식 파싱을 대체할 구조화 출력 기반

```python
# 예시 구조
from pydantic import BaseModel, Field

class QuizSchema(BaseModel):
    question: str = Field(description="퀴즈 문제")
    options: list[str] = Field(description="4개의 선택지")
    answer: int = Field(description="정답 번호 (1~4)", ge=1, le=4)
    explanation: str = Field(description="해설")
```

#### Task 1.3: `src/ingestion.py` — PDF 처리 모듈

- [ ] `load_and_parse_pdf()` 함수 이전
- [ ] `tempfile` 처리를 `try/finally`로 감싸기 (리소스 누수 방지)
- [ ] PDF 파일 크기 검증 (예: 최대 50MB)
- [ ] 텍스트 추출 실패 시 에러 핸들링

#### Task 1.4: `src/vectorstore.py` — 벡터스토어 관리 모듈

- [ ] `get_or_create_vectorstore()`: FAISS 로드/생성 통합 함수
- [ ] `search_documents(query, k)`: 검색 추상화
- [ ] `@st.cache_resource`를 활용한 임베딩 객체 캐싱
- [ ] `allow_dangerous_deserialization` 경고 주석 추가

#### Task 1.5: `main.py` UI 리팩토링

- [ ] `main.py`에서 비즈니스 로직 제거, `src/` 모듈 임포트로 전환
- [ ] 세션 상태 초기화를 함수로 분리
- [ ] UI 렌더링 코드만 남기기 (목표: 100줄 이내)

#### Task 1.6: Phase 1 검증 및 기록

- [ ] 기존과 동일하게 동작하는지 수동 테스트
- [ ] `docs/DEV_LOG.md`에 모듈 분리 결정 사항 기록

---

### 3.2 Phase 2 — StateGraph 기반 멀티 에이전트 구현

모듈화된 구조 위에 저수준 LangGraph `StateGraph`를 구축합니다.

#### Task 2.1: `src/nodes.py` — 그래프 노드 함수 구현

##### 2.1.1 라우터 노드

- [ ] `router()`: 사용자 의도를 `quiz` / `qa` / `coach`로 분류
- [ ] 경량 모델 (`gemini-2.5-flash-lite`) 사용
- [ ] 분류 실패 시 기본값 `qa`로 폴백

##### 2.1.2 퀴즈 생성 노드

- [ ] `quiz_gen()`: RAG 기반 퀴즈 생성 (전체 텍스트 → 검색 청크 기반으로 전환)
- [ ] `with_structured_output(QuizSchema)` 적용 (정규식 파싱 제거)
- [ ] 생성 실패 시 최대 3회 재시도 로직
- [ ] 출제 이력(`quiz_history`)으로 중복 방지

##### 2.1.3 채점 노드

- [ ] `grade()`: 사용자 답변과 정답 비교
- [ ] 정답/오답에 따라 상태 업데이트 (`total_correct`, `wrong_answers`)
- [ ] 숫자가 아닌 입력에 대한 예외 처리

##### 2.1.4 해설 노드

- [ ] `explain()`: 오답 시 문서 근거를 인용한 상세 해설 생성
- [ ] `retrieved_docs`로부터 출처 표시

##### 2.1.5 RAG 검색 노드

- [ ] `rag_search()`: 문서 검색 + 답변 생성
- [ ] 검색 결과 없을 시 "문서에 관련 내용이 없습니다" 응답

##### 2.1.6 학습 코치 노드

- [ ] `coach_analyze()`: 오답 패턴 분석 + 학습 전략 제안
- [ ] 최근 5건의 오답 데이터 기반 분석

#### Task 2.2: `src/tools.py` — 검색 도구 분리

- [ ] `search_quiz_material()`: 퀴즈 소재용 검색 (k=5)
- [ ] `search_documents()`: 일반 QA용 검색 (k=3)
- [ ] `search_explanation_context()`: 해설용 검색 (k=3)

#### Task 2.3: `src/graph.py` — StateGraph 조립

- [ ] 노드 등록 (7개: router, quiz_gen, wait_answer, grade, explain, rag_search, coach_analyze)
- [ ] 엣지 연결

```python
# 핵심 엣지 구조
graph.add_edge(START, "router")
graph.add_conditional_edges("router", route_by_intent)
graph.add_edge("quiz_gen", "wait_answer")
graph.add_edge("wait_answer", "grade")
graph.add_conditional_edges("grade", route_by_grade)
graph.add_edge("explain", "quiz_gen")       # 오답 → 다음 문제
graph.add_edge("rag_search", END)
graph.add_edge("coach_analyze", END)
```

- [ ] 조건부 라우팅 함수 구현 (`route_by_intent`, `route_by_grade`)
- [ ] `graph.compile()` 및 Streamlit 통합 테스트

#### Task 2.4: `main.py` — StateGraph 통합

- [ ] 기존 `if/else` 모드 분기 제거
- [ ] `graph.invoke()` / `graph.stream()` 호출로 전환
- [ ] 사이드바 모드 선택을 자연어 자동 라우팅으로 대체 (선택적 수동 전환 유지 가능)
- [ ] `st.chat_input` → 그래프 상태 업데이트 연결

#### Task 2.5: Phase 2 검증 및 기록

- [ ] 퀴즈 플로우 End-to-End 테스트 (출제 → 정답 → 종료)
- [ ] 퀴즈 플로우 오답 루프 테스트 (출제 → 오답 → 해설 → 다음 문제)
- [ ] RAG QA 테스트 (문서 질의 → 근거 기반 답변)
- [ ] 학습 코치 테스트 (오답 분석 → 전략 제안)
- [ ] `docs/DEV_LOG.md`에 StateGraph 설계 결정 기록

---

### 3.3 Phase 3 — 안정화 및 품질 향상

#### Task 3.1: 에러 핸들링 강화

- [ ] LLM API 호출 실패 시 exponential backoff 재시도 (최대 3회)
- [ ] Structured Output 파싱 실패 시 폴백 (JSON 정규식 파싱 → 사용자 에러 메시지)
- [ ] 벡터스토어 로드 실패 시 graceful 에러 화면
- [ ] 대용량 PDF 토큰 초과 시 경고 메시지

#### Task 3.2: 성능 최적화

- [ ] LLM/임베딩 객체에 `@st.cache_resource` 적용
- [ ] 대화 히스토리 최대 길이 제한 (최근 20개)
- [ ] 퀴즈 생성 시 전체 텍스트 대신 RAG 검색 결과 사용 (토큰 절감)

#### Task 3.3: UI/UX 개선

- [ ] 정답률 표시 (사이드바에 `total_correct / total_attempted`)
- [ ] 퀴즈 생성 중 Streaming 응답 지원 (`st.write_stream`)
- [ ] 오답 노트 상세 보기 (expander로 문제/해설 표시)

#### Task 3.4: DEV_LOG 작성

- [ ] Phase 전체 과정에서의 트러블슈팅 기록
- [ ] `create_react_agent` vs `StateGraph` 선택 근거 기록
- [ ] Structured Output 도입 전후 비교 기록

---

## 4. 파일별 의존 관계

```
main.py
  └── src/graph.py
        ├── src/nodes.py
        │     ├── src/config.py
        │     ├── src/models.py
        │     ├── src/vectorstore.py
        │     └── src/tools.py
        └── src/config.py

main.py
  └── src/ingestion.py
        ├── src/config.py
        └── src/vectorstore.py
```

구현 순서는 **의존성이 없는 하위 모듈부터 상위로** 진행합니다:

```
config.py → models.py → vectorstore.py → tools.py → ingestion.py → nodes.py → graph.py → main.py
```

---

## 5. 태스크 우선순위 매트릭스

| 태스크 | 영향도 | 난이도 | 우선순위 |
|:---|:---:|:---:|:---:|
| Task 1.1 config.py | 높음 | 낮음 | **P0** |
| Task 1.2 models.py | 높음 | 낮음 | **P0** |
| Task 1.3 ingestion.py | 중간 | 낮음 | **P0** |
| Task 1.4 vectorstore.py | 높음 | 중간 | **P0** |
| Task 1.5 main.py 리팩토링 | 높음 | 중간 | **P0** |
| Task 2.1 nodes.py | 높음 | 높음 | **P1** |
| Task 2.2 tools.py | 중간 | 낮음 | **P1** |
| Task 2.3 graph.py | 높음 | 높음 | **P1** |
| Task 2.4 main.py 통합 | 높음 | 중간 | **P1** |
| Task 3.1 에러 핸들링 | 높음 | 중간 | **P2** |
| Task 3.2 성능 최적화 | 중간 | 낮음 | **P2** |
| Task 3.3 UI/UX 개선 | 중간 | 중간 | **P2** |

---

## 6. 기술적 결정 사항 (ADR 요약)

### 6.1 StateGraph vs create_react_agent

- **결정**: 저수준 `StateGraph` 채택
- **근거**: 퀴즈 플로우는 결정적 상태 머신이므로 LLM 자율 판단이 불필요. Human-in-the-Loop 패턴 구현이 자연스러움. 포트폴리오 차별화.
- **상세**: [Appendix A (MULTI_AGENT_PROPOSAL.md)](./MULTI_AGENT_PROPOSAL.md) 참조

### 6.2 정규식 JSON 파싱 → Structured Output

- **결정**: `with_structured_output(QuizSchema)` + Pydantic 모델 도입
- **근거**: 기존 `re.search(r'\{.*\}')` 방식은 중괄호 포함 텍스트에서 오작동 위험. Gemini API의 구조화 출력 기능으로 파싱 안정성 확보.

### 6.3 전체 텍스트 → RAG 기반 퀴즈 생성

- **결정**: `pdf_context` 전체 전달 대신 `vectorstore.similarity_search(k=5)` 결과 기반 출제
- **근거**: 대용량 PDF 시 토큰 한도 초과 방지. 비용 절감. 특정 영역에 집중된 퀴즈 생성 가능.

### 6.4 라우터 모델 차등 적용

- **결정**: 라우터에 `gemini-2.5-flash-lite`, 생성 작업에 `gemini-2.5-flash` 사용
- **근거**: 의도 분류는 단순 작업이므로 경량 모델로 충분. 전체 API 비용 약 30~40% 절감.

---

## 7. 리스크 및 대응 방안

| 리스크 | 발생 확률 | 대응 방안 |
|:---|:---:|:---|
| Structured Output 미지원 시 | 낮음 | `JsonOutputParser` 폴백 체인 구현 |
| 라우터 의도 분류 오류 | 중간 | few-shot 예시 추가 + 사용자에게<br>"모드 전환" 수동 옵션 유지 |
| StateGraph interrupt 호환 이슈 | 중간 | Streamlit의 `st.chat_input` 루프로<br>수동 중단/재개 패턴 구현 |
| API 요금 무료 한도 초과 | 낮음 | 라우터/코치에 경량 모델 적용,<br>응답 캐싱 도입 |
| FAISS 역직렬화 보안 | 높음 | Phase 4(프로덕션)에서<br>pgvector 마이그레이션으로 해결 |

---

## 8. 체크포인트

| 체크포인트 | 완료 기준 | 예상 소요 |
|:---|:---|:---:|
| **CP1: 모듈 분리 완료** | `src/` 6개 모듈 생성,<br>`main.py`에서 기존 동작 유지 | 1~2일 |
| **CP2: StateGraph 동작** | 퀴즈 출제→채점→해설 루프 동작 확인 | 2~3일 |
| **CP3: 멀티 에이전트 통합** | 자연어 라우팅으로 Quiz/QA/Coach 전환 | 1~2일 |
| **CP4: 안정화 완료** | 에러 핸들링, 성능 최적화,<br>DEV_LOG 기록 완료 | 1~2일 |
