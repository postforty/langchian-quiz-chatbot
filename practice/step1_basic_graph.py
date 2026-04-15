"""
=============================================================
[1단계] LangGraph 기초: 상태(State), 노드(Node), 엣지(Edge)
=============================================================

학습 목표:
  - LangGraph의 세 가지 핵심 개념을 이해합니다.
  - 상태(State): 그래프 전체에서 공유되는 데이터 공간
  - 노드(Node): 상태를 받아 변환하는 함수
  - 엣지(Edge): 노드 사이의 실행 순서를 결정하는 연결선

실행 방법:
  uv run practice/step1_basic_graph.py

사전 준비:
  .env 파일에 GOOGLE_API_KEY가 설정되어 있어야 합니다.
"""

# ── 의존성 ──────────────────────────────────────────────────
from typing import TypedDict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

# .env에서 API 키 로드
load_dotenv()


# ══════════════════════════════════════════════════════════
# STEP 1: 상태(State) 정의
# ══════════════════════════════════════════════════════════
# TypedDict를 사용하면 딕셔너리에 타입 힌트를 부여할 수 있습니다.
# LangGraph는 이 스키마를 그래프 전역에서 공유되는 "데이터 저장소"로 활용합니다.
class SimpleState(TypedDict):
    # 사용자가 입력한 질문
    question: str
    # AI가 생성한 답변 (초기값: 빈 문자열)
    answer: str


# ══════════════════════════════════════════════════════════
# STEP 2: 노드(Node) 정의
# ══════════════════════════════════════════════════════════
# 노드는 반드시 (state) 를 인수로 받아야 합니다.
# 반환값은 상태(State)에서 변경할 키-값 쌍만 담은 딕셔너리입니다.
# LangGraph가 반환된 딕셔너리를 기존 상태에 자동으로 병합(merge)합니다.

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")


def answer_node(state: SimpleState) -> dict:
    """
    [노드 1] 질문을 받아 LLM으로 답변을 생성합니다.

    state["question"]을 읽어 LLM을 호출하고,
    결과를 "answer" 키에 담아 반환합니다.
    """
    print(f"\n  🤖 [answer_node 실행] 질문: '{state['question']}'")

    response = llm.invoke(state["question"])

    print(f"  ✅ [answer_node 완료] 답변 생성 완료")
    # 변경된 키만 반환 — state 전체를 반환할 필요 없음
    return {"answer": response.content}


def print_node(state: SimpleState) -> dict:
    """
    [노드 2] 최종 답변을 출력합니다.

    상태를 변경하지 않으므로 빈 딕셔너리를 반환합니다.
    """
    print(f"\n  📢 [print_node 실행] 최종 답변 출력")
    print(f"  Q: {state['question']}")
    print(f"  A: {state['answer']}")
    return {}


# ══════════════════════════════════════════════════════════
# STEP 3: 그래프 조립
# ══════════════════════════════════════════════════════════
# StateGraph(스키마)로 그래프를 초기화합니다.
workflow = StateGraph(SimpleState)

# add_node("이름", 함수): 노드를 그래프에 등록합니다.
workflow.add_node("answer", answer_node)
workflow.add_node("print", print_node)

# add_edge(A, B): A 실행 후 B를 실행합니다.
# START는 그래프의 진입점, END는 종료점입니다.
workflow.add_edge(START, "answer")  # 시작 → answer 노드
workflow.add_edge("answer", "print")  # answer → print 노드
workflow.add_edge("print", END)  # print → 종료

# compile()로 그래프를 실행 가능한 앱으로 변환합니다.
app = workflow.compile()


# ══════════════════════════════════════════════════════════
# STEP 4: 실행
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  [1단계] LangGraph 기초 실습")
    print("=" * 60)

    # invoke()에 초기 상태를 딕셔너리로 전달합니다.
    # "answer"는 아직 빈 값이지만, answer_node에서 채워집니다.
    initial_state = {
        "question": "파이썬에서 리스트와 튜플의 차이점을 한 문장으로 설명해줘.",
        "answer": "",
    }

    print(f"\n[초기 상태] {initial_state}\n")
    print("-" * 60)

    # 그래프 실행: START → answer → print → END 순서로 흐릅니다.
    final_state = app.invoke(initial_state)

    print("\n" + "-" * 60)
    print(f"\n[최종 상태] answer = '{final_state['answer'][:50]}...'")
    print("\n✅ 1단계 실습 완료!")
    print("\n[핵심 정리]")
    print("  - State : 그래프 전역 공유 데이터 (TypedDict)")
    print("  - Node  : 상태를 변환하는 함수 (dict 반환)")
    print("  - Edge  : 노드 간 실행 순서 연결")
    print("  - compile() → invoke() 로 실행")
