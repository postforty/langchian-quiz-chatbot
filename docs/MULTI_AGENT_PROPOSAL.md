# 멀티 에이전트 아키텍처 적용 제안서

> **작성일**: 2026-04-15
> **대상 프로젝트**: PDF AI 퀴즈 챗봇 (LangChain Quiz Chatbot)
> **핵심 프레임워크**: LangGraph (Supervisor Pattern + Agent Handoff)

---

## 1. 현재 구조의 한계

현재 프로젝트는 **단일 에이전트(Single Agent)** 가 퀴즈 생성, 정답 판별, RAG 질의응답을 모두 담당하는 구조입니다.

```
사용자 입력 → [단일 Agent] → 퀴즈 생성 / 정답 확인 / RAG 검색 / 답변 생성
```

### 1.1 단일 에이전트의 구체적 한계

| 한계 | 설명 |
|:---|:---|
| 역할 혼재 | 출제자, 채점자, 해설자, 검색자가 하나의 프롬프트 안에 뒤섞임 |
| 프롬프트 비대화 | 모든 지시사항을 하나의 시스템 프롬프트에 넣어야 해서 품질 저하 |
| 확장 불가 | 새 기능 (예: 난이도 조절, 학습 분석) 추가 시 전체 로직 수정 필요 |
| 모드 전환의 비효율 | `if/else`로 모드를 분기하는 하드코딩 방식에 의존 |

---

## 2. 멀티 에이전트 적용 시나리오

이 프로젝트에 멀티 에이전트를 적용할 수 있는 **5가지 핵심 시나리오**를 제안합니다.

### 2.1 Supervisor (라우터) 에이전트 — 작업 분배 허브

#### 1) 역할

사용자의 의도를 파악하여 적절한 전문 에이전트에게 작업을 위임하는 **오케스트레이터** 입니다.
현재 `st.session_state.mode`로 수동 분기하는 로직을 **LLM 기반 자동 라우팅**으로 대체합니다.

#### 2) 처리 흐름

```
사용자: "이 문서에서 시험 문제 내줘"
  → Supervisor 판단: 퀴즈 관련 → Quiz Master Agent로 핸드오프

사용자: "3장에서 설명하는 알고리즘이 뭐야?"
  → Supervisor 판단: 문서 질의 → RAG Research Agent로 핸드오프

사용자: "내가 뭘 자주 틀려?"
  → Supervisor 판단: 학습 분석 → Learning Coach Agent로 핸드오프
```

#### 3) 적용 가치

- 사용자가 **사이드바에서 모드를 수동 전환할 필요 없음** → UX 대폭 개선
- 새로운 에이전트 추가 시 Supervisor의 라우팅 목록에만 등록하면 됨
- 의도 분류 실패 시 폴백 메시지로 안전하게 처리 가능

### 2.2 Quiz Master Agent — 퀴즈 출제 전문가

#### 1) 역할

문서 내용을 기반으로 **교육학적으로 효과적인 퀴즈**를 생성하는 전문 에이전트입니다.
현재 `question_generator()` 함수의 역할을 확장합니다.

#### 2) 현재 대비 개선점

| 현재 | 멀티 에이전트 적용 후 |
|:---|:---|
| 전체 PDF 텍스트를 프롬프트에 전달 | RAG 검색으로 관련 청크만 선별 후 출제 |
| 난이도 조절 불가 | 이전 정답률 기반 적응형 난이도 조정 |
| 4지선다만 지원 | OX 퀴즈, 빈칸 채우기, 서술형 등 다양한 유형 |
| 중복 출제 방지 없음 | 출제 이력 추적으로 중복 방지 |

#### 3) 전용 도구 (Tools)

- `search_quiz_material`: 퀴즈 소재용 문서 검색 (일반 검색과 다른 k값/전략)
- `check_question_history`: 이전에 출제한 문제 조회 (중복 방지)
- `get_difficulty_level`: 사용자 정답률 기반 난이도 산정

### 2.3 Grading & Explanation Agent — 채점 및 해설 전문가

#### 1) 역할

사용자의 답변을 채점하고, **문서 근거를 인용한 상세 해설**을 생성하는 에이전트입니다.
현재 `check_answer()` 함수의 단순 번호 비교를 넘어선 깊이 있는 피드백을 제공합니다.

#### 2) 현재 대비 개선점

| 현재 | 멀티 에이전트 적용 후 |
|:---|:---|
| 번호 일치 여부만 확인 | 서술형 답변도 의미 기반 채점 가능 |
| 고정 해설 텍스트 반환 | 문서 원문을 인용하며 "왜 틀렸는지" 설명 |
| 즉시 다음 문제로 이동 | 오답 시 관련 개념 추가 설명 후 재시도 제안 |

#### 3) 전용 도구 (Tools)

- `search_explanation_context`: 해설용 문서 근거 검색
- `log_wrong_answer`: 오답 기록 저장 (향후 취약점 분석용)

### 2.4 RAG Research Agent — 문서 검색 및 질의응답 전문가

#### 1) 역할

업로드된 PDF 문서에서 **정밀한 정보 검색과 근거 기반 답변 생성**을 전담하는 에이전트입니다.
현재 `search_pdf_documents` 도구 + `general_response()` 기능을 강화합니다.

#### 2) 현재 대비 개선점

| 현재 | 멀티 에이전트 적용 후 |
|:---|:---|
| `similarity_search(k=3)` 고정 | 질문 복잡도에 따라 k값 동적 조정 |
| 단순 유사도 검색 | MMR (Maximal Marginal Relevance) 로 다양성 확보 |
| 출처 표시 없음 | "p.12, 3번째 단락" 형태의 명확한 출처 인용 |
| 문서에 없으면 "모른다"만 답변 | 문서 범위 관련 가이드 + 추가 학습 제안 |

#### 3) 전용 도구 (Tools)

- `similarity_search`: 기본 유사도 검색
- `mmr_search`: 다양성 확보를 위한 MMR 검색
- `get_document_metadata`: 페이지 번호, 섹션 제목 등 메타데이터 조회

### 2.5 Learning Coach Agent — 학습 코치 (고도화 단계)

#### 1) 역할

사용자의 학습 이력 (정답률, 오답 패턴, 소요 시간)을 분석하여 **개인화된 학습 전략을 제안**하는 에이전트입니다.
현재 오답 노트(`wrong_answers`) 기능의 확장입니다.

#### 2) 제공 기능

- 취약 영역 분석: "3장 '알고리즘 복잡도' 관련 문제를 3회 연속 틀렸습니다"
- 복습 추천: 틀린 문제의 관련 문서 섹션을 요약하여 제시
- 학습 리포트: 전체 학습 진행도 및 성취도 시각화 데이터 생성
- 적응형 출제 요청: Quiz Master에게 취약 영역 집중 출제를 핸드오프

#### 3) 전용 도구 (Tools)

- `analyze_wrong_answers`: 오답 패턴 분석
- `generate_study_report`: 학습 리포트 생성
- `request_targeted_quiz`: Quiz Master에게 취약 영역 퀴즈 요청 (에이전트 간 핸드오프)

---

## 3. 제안 아키텍처: LangGraph Supervisor 패턴

### 3.1 전체 그래프 구조

```
                    ┌─────────────────────┐
                    │   사용자 입력        │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │  Supervisor Agent   │
                    │  (의도 분류/라우팅)   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Quiz Master  │  │ RAG Research │  │ Learning     │
    │ Agent        │  │ Agent        │  │ Coach Agent  │
    │ (출제)        │  │ (검색/QA)     │  │ (학습분석)    │
    └──────┬───────┘  └──────────────┘  └──────────────┘
           │
           ▼
    ┌──────────────┐
    │ Grading &    │
    │ Explanation  │
    │ Agent (채점)  │
    └──────────────┘
```

### 3.2 LangGraph 상태 정의

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class QuizChatbotState(TypedDict):
    """멀티 에이전트 공유 상태"""
    # 대화 메시지 (자동 누적)
    messages: Annotated[list, add_messages]
    # 현재 활성 에이전트
    active_agent: str
    # 퀴즈 관련 상태
    current_quiz: dict | None
    quiz_history: list[dict]
    wrong_answers: list[dict]
    # 학습 분석 데이터
    total_correct: int
    total_attempted: int
    # 라우팅 결과
    next_agent: str
```

### 3.3 저수준 StateGraph 기반 구현

> **설계 결정**: `create_react_agent` 대신 **저수준 `StateGraph`** 를 채택합니다.
> 퀴즈 학습 플로우는 본질적으로 **결정적 상태 머신** (출제 → 답변 대기 → 채점 → 해설 → 다음 문제)이므로, LLM이 자율적으로 도구 호출 루프를 결정하는 ReAct 패턴보다, 개발자가 전이(transition)를 명시적으로 제어하는 StateGraph가 더 적합합니다.

#### 1) 그래프 흐름도

```
              START
                │
                ▼
        ┌──────────────┐
        │   router     │  ← 사용자 의도를 LLM으로 분류
        └──────┬───────┘
               │
       ┌───────┼───────────┐
       ▼       ▼           ▼
   ┌────────┐ ┌────────┐ ┌────────────┐
   │ quiz   │ │  rag   │ │  coach     │
   │ _gen   │ │ _search│ │  _analyze  │
   └───┬────┘ └───┬────┘ └─────┬──────┘
       │          │            │
       ▼          ▼            ▼
   ┌────────┐ ┌────────┐      END
   │ wait   │ │ format │
   │ _answer│ │ _answer│
   └───┬────┘ └───┬────┘
       │          │
       ▼          ▼
   ┌────────┐    END
   │ grade  │
   └───┬────┘
       │
       ├──── 오답 ──→ explain ──→ quiz_gen (루프)
       │
       └──── 정답 ──→ END
```

#### 2) 상태 및 노드 정의

```python
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage


# ── 1. 공유 상태 스키마 ──────────────────────────────────
class QuizState(TypedDict):
    """그래프 전체에서 공유되는 상태"""
    messages: Annotated[list, add_messages]   # 대화 이력
    intent: str                               # router 판별 결과
    current_quiz: dict | None                 # 현재 출제된 퀴즈
    quiz_history: list[dict]                  # 출제 이력 (중복 방지)
    wrong_answers: list[dict]                 # 오답 노트
    total_correct: int
    total_attempted: int
    retrieved_docs: list[str]                 # 검색된 문서 청크


# ── 2. 모델 초기화 ───────────────────────────────────────
router_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite"   # 라우팅은 경량 모델
)
main_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"        # 생성 작업은 표준 모델
)


# ── 3. 노드 함수 정의 ────────────────────────────────────
def router(state: QuizState) -> QuizState:
    """사용자 의도를 분류하는 라우터 노드"""
    last_msg = state["messages"][-1].content
    response = router_llm.invoke(
        f"다음 사용자 메시지의 의도를 분류하세요.\n"
        f"'quiz', 'qa', 'coach' 중 하나만 답하세요.\n"
        f"메시지: {last_msg}"
    )
    return {"intent": response.content.strip().lower()}


def quiz_gen(state: QuizState) -> QuizState:
    """문서 기반 퀴즈를 생성하는 노드"""
    # 1) 벡터 검색으로 관련 청크 수집
    docs = vectorstore.similarity_search(
        state["messages"][-1].content, k=5
    )
    context = "\n".join([d.page_content for d in docs])
    
    # 2) 퀴즈 생성 (Structured Output)
    quiz = main_llm.with_structured_output(QuizSchema).invoke(
        f"다음 내용으로 4지선다 퀴즈 1개를 생성하세요:\n{context}"
    )
    return {
        "current_quiz": quiz.model_dump(),
        "retrieved_docs": [d.page_content for d in docs],
        "messages": [AIMessage(content=format_quiz(quiz))],
    }


def wait_answer(state: QuizState) -> QuizState:
    """사용자 답변을 대기하는 중단점 (Human-in-the-Loop)"""
    # LangGraph의 interrupt() 활용 — 사용자 입력까지 그래프 일시정지
    return state


def grade(state: QuizState) -> QuizState:
    """정답 확인 및 채점 노드"""
    user_answer = state["messages"][-1].content
    quiz = state["current_quiz"]
    is_correct = int(user_answer.strip()) == quiz["answer"]
    
    new_state = {
        "total_attempted": state["total_attempted"] + 1,
    }
    if is_correct:
        new_state["total_correct"] = state["total_correct"] + 1
        new_state["messages"] = [AIMessage(content="정답입니다! 🎉")]
    else:
        new_state["wrong_answers"] = [
            *state["wrong_answers"], quiz
        ]
    return new_state


def explain(state: QuizState) -> QuizState:
    """오답 시 문서 근거를 인용한 해설 생성 노드"""
    quiz = state["current_quiz"]
    context = "\n".join(state["retrieved_docs"])
    explanation = main_llm.invoke(
        f"문제: {quiz['question']}\n"
        f"정답: {quiz['answer']}번\n"
        f"참고 문서:\n{context}\n\n"
        f"위 근거를 인용하여 왜 이것이 정답인지 상세히 해설하세요."
    )
    return {
        "messages": [
            AIMessage(content=f"오답입니다.\n\n{explanation.content}")
        ]
    }


def rag_search(state: QuizState) -> QuizState:
    """문서 검색 + RAG 답변 생성 노드"""
    query = state["messages"][-1].content
    docs = vectorstore.similarity_search(query, k=3)
    context = "\n".join([d.page_content for d in docs])
    answer = main_llm.invoke(
        f"다음 문서를 근거로 질문에 답하세요.\n"
        f"문서:\n{context}\n질문: {query}"
    )
    return {"messages": [AIMessage(content=answer.content)]}


def coach_analyze(state: QuizState) -> QuizState:
    """학습 이력 분석 및 코칭 노드"""
    stats = {
        "attempted": state["total_attempted"],
        "correct": state["total_correct"],
        "wrong_count": len(state["wrong_answers"]),
    }
    analysis = main_llm.invoke(
        f"학습 통계: {stats}\n"
        f"오답 목록: {state['wrong_answers'][-5:]}\n\n"
        f"취약 영역을 분석하고 학습 전략을 제안하세요."
    )
    return {"messages": [AIMessage(content=analysis.content)]}


# ── 4. 조건부 엣지 (라우팅 로직) ─────────────────────────
def route_by_intent(state: QuizState) -> str:
    """router 노드 결과에 따라 다음 노드를 결정"""
    intent = state.get("intent", "qa")
    if intent == "quiz":
        return "quiz_gen"
    elif intent == "coach":
        return "coach_analyze"
    else:
        return "rag_search"


def route_by_grade(state: QuizState) -> str:
    """채점 결과에 따라 해설 또는 종료를 결정"""
    user_answer = state["messages"][-1].content
    quiz = state["current_quiz"]
    if int(user_answer.strip()) == quiz["answer"]:
        return END
    return "explain"


# ── 5. 그래프 조립 ───────────────────────────────────────
graph = StateGraph(QuizState)

# 노드 등록
graph.add_node("router", router)
graph.add_node("quiz_gen", quiz_gen)
graph.add_node("wait_answer", wait_answer)
graph.add_node("grade", grade)
graph.add_node("explain", explain)
graph.add_node("rag_search", rag_search)
graph.add_node("coach_analyze", coach_analyze)

# 엣지 연결
graph.add_edge(START, "router")
graph.add_conditional_edges("router", route_by_intent)
graph.add_edge("quiz_gen", "wait_answer")
graph.add_edge("wait_answer", "grade")
graph.add_conditional_edges("grade", route_by_grade)
graph.add_edge("explain", "quiz_gen")    # 오답 → 다음 문제
graph.add_edge("rag_search", END)
graph.add_edge("coach_analyze", END)

# 컴파일
app = graph.compile()
```

### 3.4 에이전트 간 핸드오프 흐름

#### 1) 퀴즈 학습 플로우

```
사용자: "문제 내줘"
  → Supervisor → Quiz Master Agent
    → [search_quiz_material] 관련 청크 검색
    → 퀴즈 생성 후 사용자에게 반환

사용자: "3"
  → Supervisor → Grading Agent
    → [search_explanation_context] 해설 근거 검색
    → 채점 결과 + 해설 반환
    → [log_wrong_answer] 오답 시 기록 저장
    → Supervisor에게 "다음 문제 요청" 핸드오프
  → Supervisor → Quiz Master Agent
    → 다음 문제 생성
```

#### 2) 자연어 라우팅 플로우

```
사용자: "3장에서 설명하는 정렬 알고리즘을 비교해줘"
  → Supervisor 분석: 문서 내용 질의
  → RAG Research Agent로 핸드오프
    → [mmr_search] 다양한 관련 청크 검색
    → [get_document_metadata] 출처 정보 획득
    → 비교 분석 답변 생성

사용자: "그 내용으로 문제 만들어줘"
  → Supervisor 분석: 이전 대화 컨텍스트 + 퀴즈 요청
  → Quiz Master Agent로 핸드오프 (이전 검색 결과를 상태로 전달)
    → 해당 주제 기반 퀴즈 생성
```

---

## 4. 단계별 구현 전략

### 4.1 1단계: 최소 멀티 에이전트 (MVP)

**목표**: 현재 `if/else` 모드 전환을 Supervisor 기반 자동 라우팅으로 교체

| 구성 요소 | 설명 |
|:---|:---|
| Supervisor | 의도 분류만 담당 (Quiz / QA 2가지) |
| Quiz Agent | 기존 `question_generator()` 로직 래핑 |
| QA Agent | 기존 `search_pdf_documents` + `general_response()` 래핑 |

이 단계에서는 기존 로직을 그대로 재사용하되, **라우팅만 LLM 기반으로 전환**합니다.

### 4.2 2단계: Grading Agent 분리

**목표**: 채점 로직을 독립 에이전트로 분리하여 **해설 품질 향상**

- Quiz Master → 출제만 담당
- Grading Agent → 채점 + 해설 + 오답 기록
- 에이전트 간 상태 공유(`current_quiz`)로 채점 연동

### 4.3 3단계: Learning Coach 도입

**목표**: 학습 분석 기반 **개인화 학습 경험** 제공

- 오답 패턴 분석 → 취약 영역 식별
- Quiz Master에게 적응형 출제 요청 (에이전트 간 핸드오프)
- 학습 리포트 생성

---

## 5. 기대 효과

### 5.1 기술적 효과

| 항목 | 단일 에이전트 | 멀티 에이전트 |
|:---|:---|:---|
| 프롬프트 품질 | 하나에 모든 지시 → 품질 저하 | 역할별 최적화된 프롬프트 |
| 확장성 | 새 기능 추가 시 전체 수정 | 새 에이전트만 플러그인 |
| 디버깅 | 전체 흐름 추적 어려움 | 에이전트별 독립 추적 (LangSmith) |
| 비용 최적화 | 모든 요청에 동일 모델 | 에이전트별 모델 차등 적용 가능 |

### 5.2 사용자 경험 효과

| 항목 | 현재 | 개선 후 |
|:---|:---|:---|
| 모드 전환 | 사이드바에서 수동 전환 | 자연어로 자동 인식 |
| 해설 품질 | 고정 텍스트 | 문서 근거 + 맥락 해설 |
| 학습 효과 | 단순 반복 | 취약 영역 집중 + 적응형 난이도 |
| 연속성 | 모드 전환 시 맥락 단절 | 대화 컨텍스트 유지 |

### 5.3 포트폴리오 효과

- **LangGraph 활용 심화**: 단순 Agent 사용을 넘어 Supervisor 패턴 구현 경험
- **상태 관리 설계**: 에이전트 간 상태 공유 및 핸드오프 설계 역량 증명
- **교육 도메인 전문성**: 적응형 학습 시스템 설계 능력 어필
- **프로덕션 아키텍처 사고**: 확장 가능한 모듈형 설계 역량

---

## 6. 모델 비용 최적화 전략

멀티 에이전트 시 API 호출이 증가하므로 비용 전략이 중요합니다.

| 에이전트 | 권장 모델 | 근거 |
|:---|:---|:---|
| Supervisor | `gemini-2.5-flash-lite` | 의도 분류만 수행 → 가벼운 모델로 충분 |
| Quiz Master | `gemini-2.5-flash` | 창의적 문제 생성 → 표준 모델 필요 |
| Grading Agent | `gemini-2.5-flash` | 채점 + 해설 → 정확도 필요 |
| RAG Research | `gemini-2.5-flash` | 검색 결과 종합 → 표준 모델 |
| Learning Coach | `gemini-2.5-flash-lite` | 패턴 분석 + 요약 → 가벼운 모델로 가능 |

> **참고**: 모든 모델은 무료 티어 범위 내에서 사용 가능합니다. Supervisor와 Learning Coach에 경량 모델을 적용하면 전체 API 호출 비용을 약 30~40% 절감할 수 있습니다.

---

## Appendix A. `create_react_agent` vs 저수준 `StateGraph` 비교 분석

### A.1 두 접근 방식의 본질적 차이

| 관점 | `create_react_agent` (고수준) | `StateGraph` (저수준) |
|:---|:---|:---|
| 제어 모델 | **LLM 자율 결정** — 어떤 도구를<br>언제 호출할지 LLM이 판단 | **개발자 명시 제어** — 전이 조건을<br>코드로 정의 |
| 흐름 예측성 | 비결정적 — 같은 입력에도<br>다른 경로 가능 | 결정적 — 동일 입력이면<br>동일 경로 보장 |
| 내부 구조 | 블랙박스 — 내부 루프를<br>커스터마이즈하기 어려움 | 화이트박스 — 모든 노드/엣지<br>직접 설계 |
| 적합 유형 | 열린(open-ended) 질의응답,<br>자유도 높은 도구 사용 | 정해진 워크플로우,<br>상태 머신 기반 흐름 |
| 개발 속도 | 빠름 (5줄이면 에이전트 완성) | 느림 (노드/엣지/상태 직접 정의) |
| 디버깅 | 어려움 (LLM의 추론이 변수) | 쉬움 (어떤 노드에서 어떤<br>조건으로 분기했는지 명확) |

### A.2 이 프로젝트에서 저수준 StateGraph가 적합한 이유

#### 1) 퀴즈 플로우는 결정적 상태 머신

퀴즈 학습의 핵심 흐름은 아래와 같이 **순서가 고정**되어 있습니다:

```
출제 → 사용자 답변 대기 → 채점 → (정답)종료 / (오답)해설 → 다음 출제
```

이 흐름에서 **LLM이 자율적으로 결정할 부분이 없습니다.** `create_react_agent`의 "생각(Think) → 행동(Act) → 관찰(Observe)" 루프는 이 고정 흐름에 불필요한 복잡성만 추가합니다.

반면 `StateGraph`의 `add_conditional_edges()`로 `정답 → END`, `오답 → explain → quiz_gen` 같은 분기를 명시하면 **예측 가능하고 안정적인 흐름**이 보장됩니다.

#### 2) Human-in-the-Loop (사용자 답변 대기)가 자연스러움

퀴즈 앱의 핵심은 "문제 출제 → 사용자가 답변할 때까지 대기"입니다. `StateGraph`에서는 `interrupt()` 또는 `breakpoint`를 특정 노드에 설정하여 **그래프 실행을 일시정지**하고, 사용자 입력이 들어오면 이어서 실행할 수 있습니다. `create_react_agent`에서는 이런 중단/재개 패턴을 구현하기 어렵습니다.

#### 3) 상태 관리의 투명성

`QuizState`에 `current_quiz`, `wrong_answers`, `total_correct` 등을 명시적으로 정의하면:
- 각 노드가 어떤 상태를 읽고 쓰는지 **코드만 보고 파악** 가능
- `MemorySaver` 체크포인터와 결합하면 **세션 간 상태 영속화**도 자연스러움
- `create_react_agent`의 암묵적 메시지 히스토리 관리보다 **훨씬 통제 가능**

#### 4) 포트폴리오 관점에서의 차별화

| 접근 방식 | 면접관이 보는 관점 |
|:---|:---|
| `create_react_agent` 사용 | "프리빌트 API를 호출할 줄 안다" |
| `StateGraph` 직접 설계 | "프레임워크 내부를 이해하고,<br>도메인에 맞는 아키텍처를 설계할 수 있다" |

저수준 구현은 **상태 설계, 전이 조건 설계, 에러 처리 전략** 등을 직접 고민한 흔적이 코드에 남으므로, 엔지니어링 역량을 더 강하게 증명합니다.

### A.3 하이브리드 전략: 적재적소 활용

모든 노드를 저수준으로 구현할 필요는 없습니다. **핵심 흐름은 StateGraph로, 내부 노드 일부는 고수준 도구를 활용**하는 하이브리드가 가장 실용적입니다.

```python
# 그래프 골격 — 저수준 StateGraph로 명시적 제어
graph = StateGraph(QuizState)
graph.add_edge(START, "router")
graph.add_conditional_edges("router", route_by_intent)
graph.add_edge("quiz_gen", "wait_answer")
graph.add_edge("wait_answer", "grade")
graph.add_conditional_edges("grade", route_by_grade)

# 개별 노드 내부 — 필요 시 chain/tool 활용
def quiz_gen(state: QuizState) -> QuizState:
    # 이 내부에서는 LangChain chain (prompt | llm | parser)을 사용해도 OK
    chain = quiz_prompt | main_llm | JsonOutputParser()
    quiz = chain.invoke({"context": ..., "history": ...})
    return {"current_quiz": quiz}
```

이렇게 하면:
- **매크로 수준** (어떤 순서로 어떤 작업을 할지)은 StateGraph가 통제
- **마이크로 수준** (각 노드 안에서 LLM을 어떻게 호출할지)은 LangChain 체인으로 유연하게 처리

> **결론**: 이 프로젝트에서는 **저수준 `StateGraph`를 기본 뼈대로 채택**하고, 각 노드 내부에서 필요에 따라 LangChain 체인/파서를 활용하는 하이브리드 접근을 권장합니다.
