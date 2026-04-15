"""
=============================================================
[2단계] 조건부 라우팅: 의도 분류 + 분기 처리
=============================================================

학습 목표:
  - 조건부 엣지(Conditional Edge)를 사용하여 분기 처리를 구현합니다.
  - 라우터(Router) 패턴으로 사용자 의도를 분류하는 방법을 익힙니다.
  - 실제 프로젝트의 router → quiz_gen / rag_search / coach_analyze 구조 원형을
    단순화된 형태로 직접 구현해 봅니다.

구현 흐름:
  START → [router] ─────┬──→ [quiz_node]  → END
                         ├──→ [qa_node]    → END
                         └──→ [coach_node] → END

실행 방법:
  uv run practice/step2_conditional_routing.py
"""

# ── 의존성 ──────────────────────────────────────────────────
from typing import TypedDict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")


# ══════════════════════════════════════════════════════════
# STEP 1: 상태 정의 — 이번엔 "의도(intent)" 필드가 추가됩니다.
# ══════════════════════════════════════════════════════════
class RouterState(TypedDict):
    user_input: str   # 사용자가 입력한 텍스트
    intent: str       # 라우터가 판별한 의도 ('quiz' | 'qa' | 'coach')
    response: str     # 최종 응답


# ══════════════════════════════════════════════════════════
# STEP 2: 라우터 노드 — 의도를 분류하고 상태에 저장합니다.
# ══════════════════════════════════════════════════════════
def router_node(state: RouterState) -> dict:
    """
    [라우터] 사용자 입력을 분석해 의도를 분류합니다.

    LLM에게 세 가지 카테고리 중 하나를 고르도록 지시합니다.
    반환된 의도는 이후 조건부 엣지 함수에서 읽혀 분기를 결정합니다.
    """
    print(f"\n  🧭 [router_node] 입력: '{state['user_input']}'")

    prompt = f"""다음 사용자 메시지의 의도를 분류하세요.
- 'quiz'  : 문제를 내달라거나 퀴즈를 풀고 싶다는 요청
- 'coach' : 성적이나 학습 현황, 피드백을 요청하는 경우
- 'qa'    : 일반적인 질문이나 내용 설명 요청

반드시 'quiz', 'coach', 'qa' 중 단어 하나로만 답변하세요.

사용자 메시지: {state['user_input']}"""

    response = llm.invoke(prompt)
    intent = response.content.strip().lower()

    # 예외 처리: 예상 외 응답이면 기본값 사용
    if intent not in ("quiz", "coach", "qa"):
        intent = "qa"

    print(f"  ✅ [router_node] 판별된 의도: '{intent}'")
    return {"intent": intent}


# ══════════════════════════════════════════════════════════
# STEP 3: 전문 에이전트 노드들
# ══════════════════════════════════════════════════════════
def quiz_node(state: RouterState) -> dict:
    """[퀴즈 에이전트] 퀴즈 문제를 생성합니다."""
    print(f"\n  📝 [quiz_node] 퀴즈 생성 중...")

    response = llm.invoke(
        "파이썬 기초 관련 4지선다 문제 하나를 만들어 주세요. "
        "형식: 문제 / 1. / 2. / 3. / 4. / 정답: N번"
    )
    print("  ✅ [quiz_node] 퀴즈 생성 완료")
    return {"response": f"[퀴즈 출제]\n{response.content}"}


def qa_node(state: RouterState) -> dict:
    """[QA 에이전트] 사용자 질문에 답변합니다."""
    print(f"\n  💬 [qa_node] 질문에 답변 중...")

    response = llm.invoke(
        f"다음 질문에 친절하고 간결하게 답변하세요.\n질문: {state['user_input']}"
    )
    print("  ✅ [qa_node] 답변 완료")
    return {"response": f"[일반 답변]\n{response.content}"}


def coach_node(state: RouterState) -> dict:
    """[코칭 에이전트] 학습 격려 메시지를 출력합니다."""
    print(f"\n  🏆 [coach_node] 코칭 메시지 생성 중...")

    response = llm.invoke(
        "학습자에게 동기를 부여하는 짧은 격려 메시지를 작성해 주세요."
    )
    print("  ✅ [coach_node] 코칭 완료")
    return {"response": f"[학습 코칭]\n{response.content}"}


# ══════════════════════════════════════════════════════════
# STEP 4: 조건부 엣지 함수
# ══════════════════════════════════════════════════════════
# add_conditional_edges()의 두 번째 인수로 전달하는 함수입니다.
# 상태를 읽어 "다음에 실행할 노드의 이름"을 문자열로 반환합니다.
def route_by_intent(state: RouterState) -> str:
    """
    상태에 저장된 'intent'를 읽어 다음 노드 이름을 반환합니다.

    반환값: 노드 이름 문자열 또는 END 상수
    """
    intent = state.get("intent", "qa")
    print(f"\n  🔀 [route_by_intent] intent='{intent}' → 분기 결정")
    return intent  # "quiz" | "qa" | "coach"


# ══════════════════════════════════════════════════════════
# STEP 5: 그래프 조립
# ══════════════════════════════════════════════════════════
workflow = StateGraph(RouterState)

# 노드 등록
workflow.add_node("router", router_node)
workflow.add_node("quiz", quiz_node)
workflow.add_node("qa",   qa_node)
workflow.add_node("coach", coach_node)

# 일반 엣지: 시작점 → 라우터
workflow.add_edge(START, "router")

# 조건부 엣지: 라우터 → (의도에 따라) quiz / qa / coach
# add_conditional_edges(출발_노드, 분기_함수, {반환값: 도착_노드})
workflow.add_conditional_edges(
    "router",        # 이 노드가 끝난 후 분기를 실행합니다
    route_by_intent, # 다음 노드 이름을 반환하는 함수
    {
        "quiz":  "quiz",   # "quiz" 반환 시 quiz 노드로
        "qa":    "qa",     # "qa" 반환 시 qa 노드로
        "coach": "coach",  # "coach" 반환 시 coach 노드로
    },
)

# 각 전문 노드 → 종료
workflow.add_edge("quiz",  END)
workflow.add_edge("qa",    END)
workflow.add_edge("coach", END)

app = workflow.compile()


# ══════════════════════════════════════════════════════════
# STEP 6: 테스트 — 세 가지 의도를 차례로 테스트합니다.
# ══════════════════════════════════════════════════════════
TEST_INPUTS = [
    "파이썬 문제 하나 내줘",          # → quiz
    "딕셔너리가 뭔지 설명해줘",        # → qa
    "내 학습 상태가 어떤지 봐줘",      # → coach
]

if __name__ == "__main__":
    print("=" * 60)
    print("  [2단계] 조건부 라우팅 실습")
    print("=" * 60)

    for i, user_input in enumerate(TEST_INPUTS, 1):
        print(f"\n{'='*60}")
        print(f"  테스트 {i}: '{user_input}'")
        print("=" * 60)

        initial_state: RouterState = {
            "user_input": user_input,
            "intent": "",
            "response": "",
        }

        result = app.invoke(initial_state)

        print(f"\n  📌 최종 응답 (앞 80자):")
        print(f"  {result['response'][:80]}...")

    print("\n" + "=" * 60)
    print("✅ 2단계 실습 완료!")
    print("\n[핵심 정리]")
    print("  - router 노드 : LLM으로 의도를 분류, 상태에 intent 저장")
    print("  - 조건부 엣지  : route_by_intent() 함수가 분기를 결정")
    print("  - 전문 에이전트: 각 의도별로 독립된 노드가 처리")
    print("  - 패턴: START → router → [분기] → 전문_노드 → END")
