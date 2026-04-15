import re
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage
from src.config import ROUTER_MODEL, MAIN_MODEL
from src.models import QuizState, QuizSchema
from src.vectorstore import get_vectorstore, search_documents

# --- [모델 초기화] ---
router_llm = ChatGoogleGenerativeAI(model=ROUTER_MODEL)
main_llm = ChatGoogleGenerativeAI(model=MAIN_MODEL)

# --- [노드 함수 정의] ---

def router(state: QuizState) -> QuizState:
    """사용자 메시지의 의도를 분류하여 라우팅 경로를 결정합니다."""
    last_message = state["messages"][-1].content
    
    # [특수 로직] 진행 중인 퀴즈가 있고 사용자가 숫자(답변)를 입력한 경우 즉시 grade로 보냄
    if state.get("current_quiz") and re.match(r'^\s*\d+\s*$', last_message):
        return {"intent": "grade"}
    
    prompt = f"""다음 사용자 메시지의 의도를 분류하세요.
    - 'quiz': 퀴즈를 새로 풀고 싶어하거나 문제를 내달라고 하는 경우
    - 'coach': 본인의 성적, 틀린 문제 분석, 학습 가이드를 요청하는 경우
    - 'qa': 문서 내용에 대해 구체적인 질문을 하거나 일반적인 대화를 원하는 경우
    
    반드시 'quiz', 'coach', 'qa' 중 단어 하나로만 답변하세요.
    메시지: {last_message}"""
    
    response = router_llm.invoke(prompt)
    intent = response.content.strip().lower()
    
    # 예외 처리: 예상치 못한 응답 시 기본값 qa
    if intent not in ['quiz', 'coach', 'qa', 'grade']:
        intent = 'qa'
        
    return {"intent": intent}

def quiz_gen(state: QuizState) -> QuizState:
    """문서를 검색하여 새로운 퀴즈를 생성합니다."""
    # 퀴즈 소재를 위한 검색 (k=5로 조금 더 넓게 검색)
    vectorstore = st.session_state.get("vectorstore")
    if not vectorstore:
        return {"messages": [AIMessage(content="문서를 먼저 업로드해 주세요.")]}
        
    docs = search_documents(vectorstore, "퀴즈를 낼 만한 핵심 내용", k=5)
    context = "\n\n".join([d.page_content for d in docs])
    
    # Structured Output을 사용하여 Pydantic 모델로 직접 받음 (정규식 제거)
    structured_llm = main_llm.with_structured_output(QuizSchema)
    
    try:
        quiz = structured_llm.invoke(
            f"다음 내용을 바탕으로 4지선다 퀴즈를 하나 생성하세요. "
            f"선택지(options)에는 '1.', '2.'와 같은 번호를 붙이지 말고 순수 텍스트만 리스트로 제공하세요.\n\n"
            f"내용: {context}"
        )
        
        quiz_dict = quiz.model_dump()
        
        # 선택지에 번호(1~4)를 붙여서 가독성 좋게 포맷팅
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(quiz_dict['options'])])
        msg_content = f"**[문제]**\n{quiz_dict['question']}\n\n{options_text}"
        
        return {
            "current_quiz": quiz_dict,
            "retrieved_docs": [d.page_content for d in docs],
            "messages": [AIMessage(content=msg_content)]
        }
    except Exception as e:
        return {"messages": [AIMessage(content=f"퀴즈 생성 중 오류가 발생했습니다: {e}")]}

def grade(state: QuizState) -> QuizState:
    """사용자의 답변을 채점합니다."""
    user_answer = state["messages"][-1].content
    quiz = state["current_quiz"]
    
    if not quiz:
        return {"messages": [AIMessage(content="현재 진행 중인 퀴즈가 없습니다.")]}
        
    try:
        # 숫자만 추출
        match = re.search(r'\d+', user_answer)
        user_ans_num = int(match.group()) if match else -1
        
        correct_ans_num = int(quiz['answer'])
        is_correct = (user_ans_num == correct_ans_num)
        
        new_state = {
            "total_attempted": state["total_attempted"] + 1,
        }
        
        if is_correct:
            new_state["total_correct"] = state["total_correct"] + 1
            new_state["messages"] = [AIMessage(content="정답입니다! 🎉")]
            # 정답 시 퀴즈 기록에 추가 및 현재 퀴즈 초기화
            new_state["quiz_history"] = state["quiz_history"] + [quiz]
            new_state["current_quiz"] = None
        else:
            new_state["wrong_answers"] = state["wrong_answers"] + [quiz]
            # 오답 메시지는 나중에 explain 노드에서 상세히 처리할 수 있도록 보류하거나 여기서 표시
            
        return new_state
    except Exception as e:
        return {"messages": [AIMessage(content="답변 형식이 올바르지 않습니다. 번호(1~4)를 입력해 주세요.")]}

def explain(state: QuizState) -> QuizState:
    """오답에 대해 문서 근거를 기반으로 상세 해설을 생성합니다."""
    quiz = state["current_quiz"]
    context = "\n\n".join(state.get("retrieved_docs", []))
    
    prompt = f"""당신은 교육 전문가입니다. 다음 퀴즈에 대해 사용자가 오답을 입력했습니다. 
    제공된 참고 문서를 바탕으로 왜 {quiz['answer']}번이 정답인지 상세히 설명해 주세요.
    
    문제: {quiz['question']}
    정답: {quiz['answer']}번
    문서 근거: {context}"""
    
    response = main_llm.invoke(prompt)
    
    # 해설 후 퀴즈 세션 종료
    return {
        "messages": [AIMessage(content=f"오답입니다. ❌\n\n**[상세 해설]**\n{response.content}")],
        "current_quiz": None
    }

def rag_search(state: QuizState) -> QuizState:
    """문서 내용에 대해 답변을 생성합니다."""
    query = state["messages"][-1].content
    vectorstore = st.session_state.get("vectorstore")
    
    docs = search_documents(vectorstore, query, k=3)
    context = "\n\n".join([d.page_content for d in docs])
    
    prompt = f"""당신은 학습 보조 AI입니다. 다음 문서 내용을 바탕으로 사용자의 질문에 한국어로 친절하게 답변하세요. 
    문서에 내용이 없다면 솔직하게 모른다고 답변하세요.
    
    문서: {context}
    질문: {query}"""
    
    response = main_llm.invoke(prompt)
    return {"messages": [AIMessage(content=response.content)]}

def coach_analyze(state: QuizState) -> QuizState:
    """사용자의 학습 상태를 분석합니다."""
    stats = {
        "total": state["total_attempted"],
        "correct": state["total_correct"],
        "wrong": len(state["wrong_answers"])
    }
    
    if stats["total"] == 0:
        return {"messages": [AIMessage(content="아직 풀어본 문제가 없습니다. 퀴즈를 먼저 풀어보세요!")]}
        
    accuracy = (stats["correct"] / stats["total"]) * 100
    
    prompt = f"""사용자의 학습 데이터를 분석하여 격려와 피드백을 제공하세요.
    - 총 도전: {stats['total']}회
    - 정답: {stats['correct']}회
    - 오답: {stats['wrong']}회
    - 정확도: {accuracy:.1f}%
    
    오답 목록의 대표 키워드를 파악하여 어떤 부분을 보완하면 좋을지 제안하세요."""
    
    response = main_llm.invoke(prompt)
    return {"messages": [AIMessage(content=f"📊 **학습 분석 리포트**\n\n{response.content}")]}
