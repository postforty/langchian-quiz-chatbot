"""
=============================================================
[3단계] 실전 멀티 에이전트: 구조화 출력 + 상태 누적 + 복잡한 플로우
=============================================================

학습 목표:
  - Pydantic BaseModel을 사용한 구조화 출력(Structured Output)을 익힙니다.
  - 상태 누적(State Accumulation)으로 대화/이력을 관리합니다.
  - 다중 분기 + 루프 없는 순차 플로우를 조합하는 방법을 배웁니다.
  - 실제 프로젝트(Learning Pacemaker Bot)의 핵심 설계를 재현합니다.

구현 흐름:
  START → [router] ───┬──→ [quiz_gen] → END            (퀴즈 생성)
                      ├──→ [grade]  → [explain] → END  (채점 + 해설)
                      └──→ [qa]     → END              (일반 질문)

실행 방법:
  uv run practice/step3_full_multiagent.py
"""

# ── 의존성 ──────────────────────────────────────────────────
import re
from typing import Annotated, TypedDict, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

load_dotenv()

# 경량 모델: 분류 전용 (빠름, 비용 절감)
router_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite")
# 고성능 모델: 퀴즈 생성, 해설, 답변 전용
main_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")


# ══════════════════════════════════════════════════════════
# STEP 1: 구조화 출력(Structured Output) 스키마
# ══════════════════════════════════════════════════════════
# Pydantic BaseModel로 LLM 출력의 "형태"를 정의합니다.
# with_structured_output()을 사용하면 LLM이 JSON 파싱 없이
# 미리 정의한 객체를 직접 반환합니다. (정규식 파싱 불필요!)
class QuizSchema(BaseModel):
    """AI가 생성할 퀴즈의 구조화된 데이터 모델"""
    question: str = Field(description="퀴즈 문제 내용")
    options: List[str] = Field(description="4개의 객관식 선택지 (번호 없이 순수 텍스트)")
    answer: int = Field(description="정답 번호 (1~4)", ge=1, le=4)
    explanation: str = Field(description="정답에 대한 상세 해설")


# ══════════════════════════════════════════════════════════
# STEP 2: 그래프 상태(State) 정의
# ══════════════════════════════════════════════════════════
# Annotated[list, add_messages]: 메시지를 덮어쓰지 않고 "누적"합니다.
# add_messages는 LangGraph 내장 리듀서(reducer)로, 동일 id 메시지는 갱신,
# 새 메시지는 추가하는 방식으로 리스트를 병합합니다.
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # 대화 이력 누적
    intent: str                              # 라우터 판별 결과
    current_quiz: Optional[dict]             # 현재 활성 퀴즈
    total_correct: int                       # 누적 정답 수
    total_attempted: int                     # 누적 도전 수
    wrong_quizzes: List[dict]                # 오답 이력


# ══════════════════════════════════════════════════════════
# STEP 3: 라우터 노드
# ══════════════════════════════════════════════════════════
def router_node(state: AgentState) -> dict:
    """
    [라우터] 사용자 입력을 분석해 의도를 분류합니다.

    특수 로직: 진행 중인 퀴즈가 있고 숫자 입력이면 즉시 'grade'로 분류.
    이 패턴은 Streamlit 채팅과 LangGraph를 통합할 때 핵심 기법입니다.
    """
    last_msg = state["messages"][-1].content

    # ── 특수 케이스: 퀴즈 진행 중 + 숫자 입력 → grade ──
    if state.get("current_quiz") and re.match(r"^\s*\d+\s*$", last_msg):
        print(f"  🧭 [router] 숫자 입력 감지 → 채점(grade)으로 분기")
        return {"intent": "grade"}

    prompt = f"""사용자 메시지의 의도를 분류하세요.
- 'quiz'  : 퀴즈나 문제 출제 요청
- 'grade' : 답변 제출 (진행 중인 퀴즈에 답하는 경우)
- 'qa'    : 일반 질문, 설명 요청

단어 하나로만 답변하세요: quiz | grade | qa
메시지: {last_msg}"""

    response = router_llm.invoke(prompt)
    intent = response.content.strip().lower()
    if intent not in ("quiz", "grade", "qa"):
        intent = "qa"

    print(f"  🧭 [router] intent='{intent}'")
    return {"intent": intent}


# ══════════════════════════════════════════════════════════
# STEP 4: 퀴즈 생성 노드 (구조화 출력 활용)
# ══════════════════════════════════════════════════════════
def quiz_gen_node(state: AgentState) -> dict:
    """
    [퀴즈 생성] Structured Output으로 안정적인 퀴즈 데이터를 생성합니다.

    with_structured_output(QuizSchema)를 사용하면:
    - LLM이 JSON을 생성하고 Pydantic이 자동으로 파싱합니다.
    - 파싱 오류 시 LangChain이 재시도합니다.
    - 코드에서 정규식 파싱 로직이 완전히 사라집니다.
    """
    print("  📝 [quiz_gen] 구조화 출력으로 퀴즈 생성 중...")

    # with_structured_output: 반환 타입이 QuizSchema (Pydantic 객체)
    structured_llm = main_llm.with_structured_output(QuizSchema)

    try:
        quiz: QuizSchema = structured_llm.invoke(
            "파이썬 기초(변수, 자료형, 조건문, 반복문, 함수 중 하나)에 관한 "
            "4지선다 퀴즈를 생성하세요. 선택지에 번호를 붙이지 마세요."
        )

        quiz_dict = quiz.model_dump()  # Pydantic → 딕셔너리

        # 번호를 붙여 사용자에게 보여줄 텍스트 포맷
        options_text = "\n".join(
            f"{i+1}. {opt}" for i, opt in enumerate(quiz_dict["options"])
        )
        msg_content = (
            f"**[문제]** {quiz_dict['question']}\n\n"
            f"{options_text}\n\n"
            f"번호(1~4)로 답해 주세요."
        )

        print(f"  ✅ [quiz_gen] 퀴즈 생성 완료: '{quiz_dict['question'][:30]}...'")
        return {
            "current_quiz": quiz_dict,
            "messages": [AIMessage(content=msg_content)],
        }

    except Exception as e:
        print(f"  ❌ [quiz_gen] 오류: {e}")
        return {"messages": [AIMessage(content=f"퀴즈 생성 실패: {e}")]}


# ══════════════════════════════════════════════════════════
# STEP 5: 채점 노드
# ══════════════════════════════════════════════════════════
def grade_node(state: AgentState) -> dict:
    """
    [채점] 사용자 답변과 정답을 비교하고 통계를 업데이트합니다.

    상태 누적 패턴:
    - 정수 필드(total_correct, total_attempted)는 기존 값에 +1
    - 리스트 필드(wrong_quizzes)는 기존 리스트에 새 항목을 추가
    - LangGraph는 반환된 딕셔너리를 기존 상태에 병합(merge)합니다.
    """
    last_msg = state["messages"][-1].content
    quiz = state.get("current_quiz")

    if not quiz:
        return {"messages": [AIMessage(content="현재 진행 중인 퀴즈가 없습니다.")]}

    # 숫자 추출
    match = re.search(r"\d+", last_msg)
    user_ans = int(match.group()) if match else -1
    correct_ans = int(quiz["answer"])
    is_correct = (user_ans == correct_ans)

    print(f"  📊 [grade] 사용자={user_ans}, 정답={correct_ans}, 결과={'✅' if is_correct else '❌'}")

    new_state: dict = {
        "total_attempted": state.get("total_attempted", 0) + 1,
    }

    if is_correct:
        new_state["total_correct"] = state.get("total_correct", 0) + 1
        new_state["current_quiz"] = None  # 퀴즈 세션 종료
        new_state["messages"] = [AIMessage(content="🎉 정답입니다!")]
    else:
        # 오답 이력 누적
        new_state["wrong_quizzes"] = state.get("wrong_quizzes", []) + [quiz]
        # 해설 노드가 이어서 실행되므로 여기서는 메시지를 남기지 않음

    return new_state


# ══════════════════════════════════════════════════════════
# STEP 6: 해설 노드 (오답일 때만 실행)
# ══════════════════════════════════════════════════════════
def explain_node(state: AgentState) -> dict:
    """
    [해설] 오답인 경우 상세 해설을 제공하고 퀴즈 세션을 종료합니다.

    quiz["explanation"]은 구조화 출력 시 이미 포함된 내용입니다.
    (별도 LLM 호출 없이 재사용 가능한 패턴)
    """
    quiz = state.get("current_quiz")
    explanation = quiz.get("explanation", "해설 없음") if quiz else "해설 없음"

    print("  📖 [explain] 해설 제공 중...")
    msg = (
        f"❌ 오답입니다.\n\n"
        f"**정답: {quiz['answer']}번**\n\n"
        f"**[해설]** {explanation}"
    )

    return {
        "messages": [AIMessage(content=msg)],
        "current_quiz": None,  # 퀴즈 세션 종료
    }


# ══════════════════════════════════════════════════════════
# STEP 7: 일반 QA 노드
# ══════════════════════════════════════════════════════════
def qa_node(state: AgentState) -> dict:
    """[QA] 사용자 질문에 직접 답변합니다."""
    query = state["messages"][-1].content
    print(f"  💬 [qa] 질문에 답변 중: '{query[:30]}...'")

    response = main_llm.invoke(
        f"다음 파이썬 관련 질문에 친절하고 명확하게 답변하세요.\n질문: {query}"
    )
    return {"messages": [AIMessage(content=response.content)]}


# ══════════════════════════════════════════════════════════
# STEP 8: 조건부 엣지 함수들
# ══════════════════════════════════════════════════════════
def route_by_intent(state: AgentState) -> str:
    """라우터 분기: intent 값으로 다음 노드를 결정합니다."""
    return state.get("intent", "qa")


def route_after_grade(state: AgentState) -> str:
    """
    채점 후 분기:
    - 정답(messages[-1]에 '정답' 포함) → END
    - 오답 → explain 노드
    """
    last_content = state["messages"][-1].content
    if "정답" in last_content:
        return END
    return "explain"


# ══════════════════════════════════════════════════════════
# STEP 9: 그래프 조립
# ══════════════════════════════════════════════════════════
workflow = StateGraph(AgentState)

# 노드 등록
workflow.add_node("router",   router_node)
workflow.add_node("quiz_gen", quiz_gen_node)
workflow.add_node("grade",    grade_node)
workflow.add_node("explain",  explain_node)
workflow.add_node("qa",       qa_node)

# 엣지 연결
workflow.add_edge(START, "router")

# router → 조건부 분기 (3방향)
workflow.add_conditional_edges(
    "router",
    route_by_intent,
    {"quiz": "quiz_gen", "grade": "grade", "qa": "qa"},
)

# grade → 조건부 분기 (정답 시 END, 오답 시 explain)
workflow.add_conditional_edges("grade", route_after_grade)

# 단방향 종료
workflow.add_edge("quiz_gen", END)
workflow.add_edge("explain",  END)
workflow.add_edge("qa",       END)

app = workflow.compile()


# ══════════════════════════════════════════════════════════
# STEP 10: 시뮬레이션 — 퀴즈 생성 → 오답 제출 → 해설 흐름
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  [3단계] 실전 멀티 에이전트 실습")
    print("=" * 60)

    # 초기 상태 설정
    state: AgentState = {
        "messages": [],
        "intent": "",
        "current_quiz": None,
        "total_correct": 0,
        "total_attempted": 0,
        "wrong_quizzes": [],
    }

    # ── 턴 1: 퀴즈 생성 요청 ──────────────────────────────
    print("\n" + "─" * 60)
    print("[턴 1] 퀴즈 출제 요청")
    print("─" * 60)
    state["messages"] = [HumanMessage(content="파이썬 퀴즈 문제 내줘")]
    state = app.invoke(state)
    last_ai = [m for m in state["messages"] if isinstance(m, AIMessage)][-1]
    print(f"\n  🤖 봇: {last_ai.content}\n")

    # ── 턴 2: 고의 오답 제출 (무조건 '9'로 틀리게 입력) ──
    print("─" * 60)
    print("[턴 2] 오답 제출 (9번)")
    print("─" * 60)
    state["messages"] = state["messages"] + [HumanMessage(content="9")]
    state = app.invoke(state)
    last_ai = [m for m in state["messages"] if isinstance(m, AIMessage)][-1]
    print(f"\n  🤖 봇: {last_ai.content[:200]}\n")

    # ── 턴 3: 일반 질문 ───────────────────────────────────
    print("─" * 60)
    print("[턴 3] 일반 질문")
    print("─" * 60)
    state["messages"] = state["messages"] + [
        HumanMessage(content="파이썬 리스트 컴프리헨션이 뭐야?")
    ]
    state = app.invoke(state)
    last_ai = [m for m in state["messages"] if isinstance(m, AIMessage)][-1]
    print(f"\n  🤖 봇: {last_ai.content[:200]}...\n")

    # ── 최종 통계 출력 ────────────────────────────────────
    print("=" * 60)
    print("✅ 3단계 실습 완료!")
    print(f"\n[학습 통계]")
    print(f"  - 총 도전: {state['total_attempted']}회")
    print(f"  - 정답   : {state['total_correct']}회")
    print(f"  - 오답   : {len(state['wrong_quizzes'])}회")
    total_turns = len([m for m in state["messages"] if isinstance(m, HumanMessage)])
    print(f"  - 대화   : {total_turns}턴")
    print("\n[핵심 정리]")
    print("  - Structured Output : with_structured_output(Pydantic모델)")
    print("  - 상태 누적         : add_messages 리듀서, 리스트 += [새항목]")
    print("  - 다중 분기         : add_conditional_edges 여러 번 사용 가능")
    print("  - 모델 분리         : router=경량, 생성=고성능 (비용 최적화)")
