# 📖 PDF AI 퀴즈 챗봇 (LangChain Quiz Chatbot)

**PDF 문서를 활용한 지능형 퀴즈 자동 생성 및 RAG 질의응답 학습 보조 시스템**

사용자가 업로드한 PDF 문서를 바탕으로 객관식 퀴즈를 생성하고, 문서 내용에 대한 질의응답을 제공하여 효율적인 학습을 돕는 교육용 AI 애플리케이션입니다.

---

## 🎯 문제 정의 및 프로젝트 배경
기존의 학습 방식은 문서를 눈으로 읽고 지나가는 정적인 과정에 그쳐, 학습자의 실제 이해도를 점검하기 어렵다는 한계가 있었습니다. 
이를 해결하기 위해 **문서를 분석하여 스스로 문제를 출제하고 즉각적인 피드백을 제공**하며, 나아가 **RAG(검색 증강 생성) 기술을 통해 문서 내에서 정확한 정보만을 기반으로 질의응답**을 나눌 수 있는 챗봇 솔루션을 기획하게 되었습니다.

## ✨ 주요 기능
- **📄 PDF 파싱 및 벡터화**: 업로드된 문서를 텍스트로 추출, 적절한 Chunk 단위로 분할 후 FAISS 벡터 공간에 인덱싱합니다.
- **💡 퀴즈 풀기 모드 (Quiz Generator)**:
  - 문서 전체의 맥락을 이해한 뒤 4지선다형 객관식 퀴즈를 자동 생성합니다.
  - 사용자의 오답 시 명확한 해설을 제공하며, 틀린 문제는 **오답 노트**에 축적됩니다.
- **💬 질문하기 모드 (RAG Agent)**:
  - 사용자의 질문에 대해 유사도 검색을 수행, 관련성 높은 상위(Top-K) 문장을 참고해 답변을 생성합니다.
  - 내용이 문서에 없을 경우 환각(Hallucination) 없이 모른다고 응답하도록 설계되었습니다.

## 🛠️ 기술 스택
- **Language**: Python (>=3.12)
- **UI Framework**: Streamlit
- **LLM / Framework**: LangChain, LangGraph, Google Gemini 2.5 Flash, Google Generative AI Embeddings
- **Storage / Vector DB**: FAISS (로컬 저장소 `faiss_index_pdf_quiz` 파일럿 기반)
- **Document Processing**: PyMuPDF (`pymupdf`)
- **Package Manager**: `uv`

---

## 🧠 시스템 설계 및 핵심 로직 (Portfolio Highlights)

### 1. 상태 관리 기반(Status Management) 흐름 파이프라인
Streamlit의 특성에 맞춰 `st.session_state`를 적극 활용하여 대화 기록, 업로드된 PDF 컨텍스트, 오답 노트, FAISS VectorStore 인스턴스, 그리고 Agent 객체의 상태를 유지하고 통제합니다.

### 2. 답변 생성을 보조하는 핵심 함수
- **`question_generator()`**  
  프롬프트 엔지니어링을 통해 AI가 4지선다 퀴즈를 직접 생성하도록 유도합니다.  
  엄격하게 JSON 포맷(문제, 보기, 정답, 해설)을 지킬 수 있도록 시스템 프롬프트에 `ChatPromptTemplate`을 결합하였으며, AI의 응답을 `Re` 정규식을 활용하여 안전하게 JSON으로 파싱하도록 최적화되어 있습니다.
- **`search_pdf_documents()` (검색 증강 Tool)**  
  LangChain Agent가 사용할 수 있는 `@tool` 데코레이터 유틸리티입니다. 사용자의 질문 맥락을 분석한 Agent가 능동적으로 이 도구를 호출하여, FAISS VectorStore 기반의 유사도 검색(`k=3`)을 거친 근거 문서 스트링을 반환받게 합니다.

### 3. 성능 개선을 위한 실험 및 최적화
- **Chunking 전략 테스트**: RecursiveCharacterTextSplitter를 통해 `chunk_size=1000`, `chunk_overlap=100`으로 분할 최적화 중복 방지 및 문맥 유지 테스트 기록.
- **포맷 강제화**: Gemini API의 특징을 살려, AI가 혼잣말을 하거나 포맷을 벗어난 출력을 하는 것을 방지하고 순수 JSON 추출을 위한 파싱 함수(`parse_ai_json`)를 추가 도입했습니다. (추후 `docs/DEV_LOG.md`를 통해 계속 업데이트)

---

## 🚀 한계 구상 및 향후 개선 방안 (Limitations & Improvements)

- **컨텍스트 제한**: 현재 퀴즈 생성 시 문서 전체를 `pdf_context` 변수에 합쳐서 넘기는 방식을 사용하고 있어 초대형 문서의 경우 토큰 제한 이슈가 발생할 우려가 있습니다.
- **개선안 (Map-Reduce 퀴즈 생성)**: 단일 프롬프트가 아닌 문서 단위 Chunk별로 퀴즈 1차 생성 후 필터링을 거치는 LangGraph 기반 워크플로우로 고도화를 계획하고 있습니다.
- **멀티모달 확장**: 이미지나 도표가 포함된 PDF의 분석 성능 한계를 보완하기 위해 최신 다중 모달용 임베딩 모델(`gemini-embedding-2-preview` 등) 도입 실험을 진행할 예정입니다.

---

## 📝 개발 철학 및 기록 원칙 (Development Principles)
본 프로젝트는 단순한 기능 구현을 넘어, 엔지니어링 역량을 증명하기 위해 다음과 같은 원칙하에 개발 및 기록되고 있습니다.

1. **과정 중심의 트러블슈팅 기록 (Process-Oriented Tracking)**: 
   - 결과물보다는 **문제 해결 과정**과 **'왜 이 아키텍처/로직을 선택했는지'**에 대한 기술적 근거를 중시합니다. 
   - 개발 중 발생한 모든 에러 로그와 해결책은 `docs/DEV_LOG.md`에 [문제 정의] ➡️ [시도/해결책] ➡️ [결론 및 채택 이유] 형태로 꼼꼼히 문서화하고 있습니다.
2. **개선 시도 및 실험 강조 (Experiment-Driven Optimization)**: 
   - **Chunking 전략 변경 실험**: 단순 RAG 구현에 그치지 않고, 검색 품질을 극대화하기 위해 `chunk_size` 및 `chunk_overlap` 비율을 동적으로 변경하며 검색율을 비교하는 실험을 진행합니다.
   - **프롬프트 엔지니어링**: AI 시스템 응답에서 JSON 포맷의 오차율을 줄이기 위해, 시스템 프롬프트를 다각도로 수정하고 최적의 결과를 내는 파이프라인을 구축하기 위해 시도합니다.

---

## ⚙️ 설치 및 애플리케이션 실행

### 1. 환경 설정 및 설치
**uv 패키지 매니저** 설치 및 Google Gemini API 키가 필요합니다.
```bash
git clone https://github.com/your-username/langchian-quiz-chatbot.git
cd langchian-quiz-chatbot

# 의존성 설치
uv sync --all-extras
```

### 2. 환경 변수 등록
```env
# .env 파일 생성
GEMINI_API_KEY="your_google_gemini_api_key_here"
```

### 3. 애플리케이션 실행
의존성이 설치된 환경에서 `uv run` 명령어를 사용하여 실행합니다.
```bash
uv run streamlit run main.py
```
> 브라우저가 자동으로 열리며, 로컬 서버(`http://localhost:8501`)에서 PDF 업로드 및 AI 질의응답을 즐길 수 있습니다.

---
**License**: MIT 
