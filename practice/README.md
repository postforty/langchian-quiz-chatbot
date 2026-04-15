# 🎓 LangGraph 멀티 에이전트 실습 (practice/)

Learning Pacemaker Bot 프로젝트에 적용된 **LangGraph 멀티 에이전트 기술**을  
쉬운 단계부터 차례로 익힐 수 있는 실습 모음입니다.

---

## 📁 파일 구성

```
practice/
├── README.md                  ← 이 파일
├── step1_basic_graph.py       ← 1단계: LangGraph 기초
├── step2_conditional_routing.py ← 2단계: 조건부 라우팅
└── step3_full_multiagent.py   ← 3단계: 실전 멀티 에이전트
```

---

## 🗺️ 학습 로드맵

```
[1단계]            [2단계]                  [3단계]
State + Node  →  조건부 라우팅  →  구조화 출력 + 상태 누적
(개념 이해)      (분기 설계)        (실전 종합)
```

---

## 🚀 실행 방법

> `.env` 파일에 `GOOGLE_API_KEY`가 설정되어 있어야 합니다.

```bash
# 1단계
uv run practice/step1_basic_graph.py

# 2단계
uv run practice/step2_conditional_routing.py

# 3단계
uv run practice/step3_full_multiagent.py
```

---

## 📚 단계별 학습 내용

### Step 1 — LangGraph 기초 (`step1_basic_graph.py`)

**핵심 개념:** State · Node · Edge

| 개념 | 설명 |
|------|------|
| `State` (TypedDict) | 그래프 전역에서 공유되는 데이터. 노드 간 소통 수단 |
| `Node` (함수) | `state`를 받아 변경된 키-값 딕셔너리를 반환하는 함수 |
| `Edge` (연결) | 노드의 실행 순서를 결정하는 방향성 연결선 |
| `compile()` | 설계된 그래프를 실행 가능한 앱으로 변환 |
| `invoke()` | 초기 상태를 전달하여 그래프를 실행 |

**실행 흐름:**
```
START → [answer_node] → [print_node] → END
```

---

### Step 2 — 조건부 라우팅 (`step2_conditional_routing.py`)

**핵심 개념:** Conditional Edge · Router Pattern

| 개념 | 설명 |
|------|------|
| `add_conditional_edges()` | 분기 함수의 반환값에 따라 다음 노드를 동적으로 결정 |
| Router Node | LLM으로 사용자 의도를 분류, `intent`를 상태에 저장 |
| 전문 에이전트 | 각 의도(quiz/qa/coach)를 처리하는 독립된 노드 |

**실행 흐름:**
```
START → [router] ──┬──→ [quiz]  → END
                   ├──→ [qa]    → END
                   └──→ [coach] → END
```

---

### Step 3 — 실전 멀티 에이전트 (`step3_full_multiagent.py`)

**핵심 개념:** Structured Output · 상태 누적 · 다중 분기

| 개념 | 설명 |
|------|------|
| `with_structured_output(Schema)` | Pydantic 모델로 LLM 출력을 직접 받음 (정규식 파싱 불필요) |
| `Annotated[list, add_messages]` | 메시지를 덮어쓰지 않고 누적하는 리듀서 |
| 상태 누적 패턴 | `기존값 + 1`, `기존리스트 + [새항목]` |
| 모델 분리 전략 | router=경량 모델, 생성=고성능 모델 (비용 최적화) |
| 다중 조건부 분기 | `add_conditional_edges`를 여러 노드에 적용 |

**실행 흐름:**
```
START → [router] ──┬──→ [quiz_gen] ─────────────── → END
                   ├──→ [grade] ──→ (정답) ──────── → END
                   │           └──→ (오답) → [explain] → END
                   └──→ [qa] ──────────────────────── → END
```

---

## 🔍 실제 프로젝트와의 연결

| 실습 코드 개념 | 실제 프로젝트 위치 |
|---|---|
| `SimpleState` | `src/models.py` → `QuizState` |
| `router_node` | `src/nodes.py` → `router()` |
| `quiz_gen_node` | `src/nodes.py` → `quiz_gen()` |
| `grade_node` | `src/nodes.py` → `grade()` |
| `add_conditional_edges` | `src/graph.py` → `create_quiz_graph()` |
| `QuizSchema` | `src/models.py` → `QuizSchema` |

---

## 💡 학습 포인트 요약

```
1단계 → "그래프는 상태를 공유하며 노드 순서대로 실행된다"
2단계 → "조건부 엣지로 사용자 의도에 따라 다른 에이전트를 실행할 수 있다"
3단계 → "구조화 출력과 상태 누적으로 안정적이고 복잡한 흐름을 설계할 수 있다"
```
