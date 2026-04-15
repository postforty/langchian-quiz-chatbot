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

### 3.3 Supervisor 구현 개념

```python
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END

# 각 전문 에이전트 정의
quiz_agent = create_react_agent(
    model="google_genai:gemini-2.5-flash",
    tools=[search_quiz_material, check_question_history],
    prompt="당신은 교육학 전문가입니다. 문서 기반 퀴즈를 생성하세요...",
    name="quiz_master"
)

rag_agent = create_react_agent(
    model="google_genai:gemini-2.5-flash",
    tools=[similarity_search, mmr_search, get_document_metadata],
    prompt="당신은 문서 검색 전문가입니다. 근거 기반으로 답변하세요...",
    name="rag_researcher"
)

grading_agent = create_react_agent(
    model="google_genai:gemini-2.5-flash",
    tools=[search_explanation_context, log_wrong_answer],
    prompt="당신은 채점 및 해설 전문가입니다. 상세한 피드백을 제공하세요...",
    name="grader"
)

# Supervisor 그래프 구성
from langgraph_supervisor import create_supervisor

supervisor = create_supervisor(
    agents=[quiz_agent, rag_agent, grading_agent],
    model="google_genai:gemini-2.5-flash",
    prompt=(
        "당신은 PDF 학습 도우미의 총괄 매니저입니다.\n"
        "사용자의 의도를 파악하여 적절한 전문 에이전트에게 작업을 위임하세요.\n"
        "- 퀴즈 출제 요청 → quiz_master\n"
        "- 문서 내용 질문 → rag_researcher\n"
        "- 정답 확인/채점 → grader\n"
    ),
)

app = supervisor.compile()
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
