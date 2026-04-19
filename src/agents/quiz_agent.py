from typing import Dict, Any, List
from src.core.state import AgentState
from src.utils.helpers import parse_ai_json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

# 모델 초기화 (AGENTS.md 준수)
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

def generate_quiz(context: str) -> Dict[str, Any]:
    """PDF 컨텍스트를 바탕으로 퀴즈를 생성합니다."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 제공된 텍스트에서 4지선다 객관식 문제를 생성하는 교육용 AI입니다.
        반드시 다음 JSON 형식으로만 응답하세요:
        {{
            "question": "문제 내용",
            "options": ["1. 보기1", "2. 보기2", "3. 보기3", "4. 보기4"],
            "answer": "정답 번호 (1~4)",
            "explanation": "해설"
        }}
        
        텍스트: {context}"""),
        ("human", "문제를 1개 생성해 주세요.")
    ])
    
    chain = prompt | model
    ai_response = chain.invoke({"context": context})
    return parse_ai_json(ai_response.content)

def quiz_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    퀴즈 마스터 노드: 퀴즈 생성 및 정답 채점 로직을 담당합니다.
    """
    last_message = state["messages"][-1]
    user_input = last_message.content.strip() if hasattr(last_message, "content") else str(last_message).strip()
    
    # 1. 정답 제출 여부 확인 (기존 문제가 있고, 입력이 숫자인 경우)
    if state.get("current_question") and user_input.isdigit() and user_input in ["1", "2", "3", "4"]:
        q_data = state["current_question"]
        user_ans = int(user_input)
        correct_ans = int(q_data['answer'])
        
        updates = {}
        if user_ans == correct_ans:
            feedback = f"정답입니다! 🎉\n\n해설: {q_data['explanation']}"
        else:
            feedback = f"오답입니다. 정답은 {correct_ans}번입니다.\n\n해설: {q_data['explanation']}"
            updates["wrong_answers"] = state["wrong_answers"] + [q_data]
            
        # 다음 단계 안내 (바로 다음 문제를 생성)
        new_q = generate_quiz(state["pdf_context"])
        if new_q:
            msg = feedback + "\n\n---\n\n**[다음 문제]**\n" + new_q['question'] + "\n\n" + "\n".join(new_q['options'])
            updates["current_question"] = new_q
            updates["messages"] = [AIMessage(content=msg)]
        else:
            updates["messages"] = [AIMessage(content=feedback + "\n\n(다음 문제를 생성하는 데 실패했습니다.)")]
            
        return updates

    # 2. 퀴즈 생성 요청 처리 (첫 시작 또는 '다음 문제' 요청 등)
    new_q = generate_quiz(state["pdf_context"])
    if new_q:
        msg = "**[새로운 문제]**\n" + new_q['question'] + "\n\n" + "\n".join(new_q['options'])
        return {
            "current_question": new_q,
            "messages": [AIMessage(content=msg)]
        }
    
    return {"messages": [AIMessage(content="죄송합니다. 퀴즈를 생성할 수 있는 정보가 부족합니다.")]}
