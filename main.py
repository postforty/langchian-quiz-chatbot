import streamlit as st
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
import tempfile
import os
import json
import re
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# --- [초기 설정] ---
# 모델 초기화 (무료 티어 권장 모델 사용)
chat = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    transport='rest' # Streamlit 환경에서의 호환성 및 안정성을 위해 설정
)
db_path = "faiss_index_pdf_quiz"

# 세션 상태 초기화 (UI 상태 유지용)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_context" not in st.session_state:
    st.session_state.pdf_context = ""
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "wrong_answers" not in st.session_state:
    st.session_state.wrong_answers = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "mode" not in st.session_state:
    st.session_state.mode = "퀴즈 풀기"

# --- [유틸리티 함수] ---
def parse_ai_json(ai_response):
    """AI 응답에서 JSON 부분을 추출하여 파싱합니다."""
    try:
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        st.error(f"JSON 파싱 오류: {e}")
    return None

@st.cache_resource
def get_vectorstore():
    """FAISS 저장소가 있으면 로드합니다."""
    if os.path.exists(db_path):
        return FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    return None

st.session_state.vectorstore = get_vectorstore()

def load_and_parse_pdf(pdf_path):
    # 1. PDF 로드
    loader = PyMuPDFLoader(pdf_path)
    docs = loader.load()

    # 2. 텍스트 분할
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = text_splitter.split_documents(docs)

    # 3. 벡터스토어 생성 및 로컬 저장
    st.session_state.vectorstore = FAISS.from_documents(split_docs, embeddings)
    st.session_state.vectorstore.save_local(db_path)
    
    # 캐시 초기화
    get_vectorstore.clear()
    
    # 전체 컨텍스트 저장 (퀴즈 생성용)
    st.session_state.pdf_context = "\n".join([doc.page_content for doc in docs])

@tool
def search_pdf_documents(query: str) -> str:
    """업로드된 PDF 문서 내에서 정보를 검색합니다. 
    사실 확인이나 전문적인 내용이 필요할 때 사용하세요.
    """
    vectorstore = st.session_state.get("vectorstore")
    if vectorstore is None:
        vectorstore = get_vectorstore()
        
    if vectorstore is not None:
        docs = vectorstore.similarity_search(query, k=3)
        return "\n\n".join([doc.page_content for doc in docs])
    return "검색할 문서가 없습니다."

def initialize_agent():
    system_prompt = """당신은 업로드된 PDF 문서를 바탕으로 학습을 돕는 교육 전문가입니다.
    1. 사용자의 질문에 대해 'search_pdf_documents' 도구를 사용하여 정확한 정보를 찾으세요.
    2. 답변은 반드시 검색된 문서의 내용에만 기반하여 한국어로 작성하세요.
    3. 문서에 관련 내용이 없다면 억지로 꾸며내지 말고 솔직하게 모른다고 답변하세요.
    """
    
    st.session_state.agent = create_agent(
        model="google_genai:gemini-2.5-flash",
        tools=[search_pdf_documents],
        system_prompt=system_prompt
    )

def general_response(user_message):
    """에이전트를 통한 일반 대화"""
    if st.session_state.agent:
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
        result = st.session_state.agent.invoke({"messages": history + [{"role": "user", "content": user_message}]})
        
        ai_msg = result["messages"][-1]
        content = ai_msg.content
        
        if isinstance(content, list):
            text_parts = [part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"]
            return "".join(text_parts)
        
        return content
    return "에이전트가 설정되지 않았습니다."

def question_generator():
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
    
    chain = prompt | chat
    ai_response = chain.invoke({"context": st.session_state.pdf_context})
    content = ai_response.content
    
    if isinstance(content, list):
        content = "".join([part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"])
    
    return parse_ai_json(content)

def check_answer(user_message):
    """사용자가 입력한 숫자가 정답인지 확인"""
    q_data = st.session_state.current_question
    if not q_data: return None
    try:
        user_ans = int(user_message.strip())
        correct_ans = int(q_data['answer'])
        if user_ans == correct_ans:
            return "정답입니다! 🎉"
        else:
            if q_data not in st.session_state.wrong_answers:
                st.session_state.wrong_answers.append(q_data)
            return f"오답입니다. 정답은 {correct_ans}번입니다.\n\n해설: {q_data['explanation']}"
    except ValueError:
        return None

# --- Streamlit UI 시작 ---
st.set_page_config(page_title="PDF AI 퀴즈 챗봇", page_icon="📖")
st.title("📖 PDF AI 퀴즈 챗봇")

# 사이드바 설정 영역
with st.sidebar:
    st.header("⚙️ 설정")
    st.session_state.mode = st.radio(
        "학습 모드 선택",
        ["퀴즈 풀기", "질문하기"],
        help="퀴즈를 풀며 학습하거나, 문서에 대해 자유롭게 질문하세요."
    )
    
    if st.session_state.wrong_answers:
        st.write("---")
        st.write(f"❌ 틀린 문제: {len(st.session_state.wrong_answers)}개")
        if st.button("오답 노트 초기화"):
            st.session_state.wrong_answers = []
            st.rerun()

uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")

if uploaded_file and not st.session_state.pdf_processed:
    if st.button("학습 시작"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name
        
        with st.spinner("문서를 분석 중..."):
            load_and_parse_pdf(tmp_path)
            initialize_agent()
            st.session_state.pdf_processed = True
            
            if st.session_state.mode == "퀴즈 풀기":
                q = question_generator()
                st.session_state.current_question = q
                if q:
                    msg = q['question'] + "\n\n" + "\n".join(q['options'])
                    st.session_state.messages.append({"role": "assistant", "content": msg})
            else:
                st.session_state.messages.append({"role": "assistant", "content": "문서 분석이 완료되었습니다! 분석된 내용에 대해 무엇이든 물어보세요."})
        os.unlink(tmp_path)
        st.rerun()

# 문장 분석 완료 후 파일 업로더 숨기기 또는 상태 표시
if st.session_state.pdf_processed:
    st.success("✅ 문서 분석 완료!")

# 대화 창 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 메시지 입력 및 답변 처리
if prompt := st.chat_input("메시지를 입력하세요"):
    if not st.session_state.pdf_processed:
        st.warning("먼저 PDF 파일을 업로드하고 '학습 시작'을 눌러주세요.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        if st.session_state.mode == "퀴즈 풀기":
            ans_check = check_answer(prompt)
            if ans_check:
                st.write(ans_check)
                st.session_state.messages.append({"role": "assistant", "content": ans_check})
                with st.spinner("다음 문제를 생성 중..."):
                    new_q = question_generator()
                    st.session_state.current_question = new_q
                    if new_q:
                        msg = new_q['question'] + "\n\n" + "\n".join(new_q['options'])
                        st.write("---")
                        st.write(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
            else:
                guide = "퀴즈 풀기 모드입니다. 정답 번호(1~4)를 입력해 주세요. 질문에 답변을 듣고 싶다면 사이드바에서 '질문하기' 모드로 변경해 주세요."
                st.info(guide)
                st.session_state.messages.append({"role": "assistant", "content": guide})
        else:
            with st.spinner("답변을 찾는 중..."):
                resp = general_response(prompt)
                st.write(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})

if __name__ == "__main__":
    import sys
    from streamlit.web import cli as stcli
    
    # streamlit run main.py와 동일하게 동작하도록 설정
    sys.argv = ["streamlit", "run", "main.py"]
    sys.exit(stcli.main())
