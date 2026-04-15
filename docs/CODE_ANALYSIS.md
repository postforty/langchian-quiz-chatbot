# 코드 분석 및 개선 계획서

> **작성일**: 2026-04-15
> **분석 대상**: `main.py` (v0.1.0, 263 lines)
> **브랜치**: `refactor/code-analysis-and-improvement-plan`

---

## 1. 분석 개요

PDF 문서를 분석하여 퀴즈를 생성하고 RAG 기반 질의응답을 제공하는 Streamlit 웹 애플리케이션의 코드 품질, 아키텍처, 보안, 성능을 시니어 LLM 앱 엔지니어 관점에서 진단한 문서입니다.

### 1.1 현재 상태 요약

| 영역 | 등급 | 평가 |
|:---:|:---:|:---|
| 아키텍처 | C | 단일 파일 모놀리스, 관심사 분리 부재 |
| 코드 품질 | C+ | 동작하지만 프로덕션 안정성에 치명적 결함 다수 |
| 에러 처리 | D | 거의 전무 — LLM 응답 실패 시 앱 중단 위험 |
| 보안 | D | API 키 노출 위험, 입력 검증 없음 |
| 성능 | C | 로컬 FAISS 단일 사용자 구조, 캐싱 전략 미흡 |
| 테스트 | F | 테스트 코드 0건 |
| 문서화 | B+ | README, DEV_LOG, 배포 가이드 등 양호 |

### 1.2 긍정적 평가 항목

- PDF → FAISS 벡터화 → Agent 기반 QA의 End-to-End 파이프라인이 완성됨
- `@tool` + `create_agent`를 활용한 도구 사용 패턴이 올바르게 적용됨
- README, DEV_LOG, 배포 가이드 등 문서화에 대한 의식이 높음
- 무료 티어 모델 사용, uv 패키지 매니저 등 실용적 기술 선택

---

## 2. 치명적 이슈 상세 분석

### 2.1 LLM 응답 파싱 실패 시 앱 크래시

#### 1) 문제 정의

`question_generator()`가 `None`을 반환할 경우, 후속 로직에서 `TypeError`가 발생하여 앱이 중단됩니다.

```python
# main.py:150 — None 반환 가능
return parse_ai_json(content)

# main.py:202-206 — None 체크가 불완전
q = question_generator()
st.session_state.current_question = q  # None이 저장됨
if q:
    msg = q['question'] + "\n\n" + "\n".join(q['options'])
```

`q`가 `None`인 상태에서 사용자가 답변을 입력하면 `check_answer()` 내부의 `q_data['answer']`에서 크래시가 발생합니다.

#### 2) 영향 범위

- 퀴즈 생성 실패 시 사용자에게 빈 화면 표시
- 이후 어떤 입력을 해도 `TypeError` 발생으로 세션 복구 불가

#### 3) 해결 방안

- 재시도 로직 (최대 3회, exponential backoff) 추가
- 실패 시 사용자에게 명시적 에러 메시지 + "다시 시도" 버튼 제공
- `current_question`이 `None`일 때 `check_answer()` 진입 차단

### 2.2 대용량 PDF의 전체 텍스트를 프롬프트에 직접 전달

#### 1) 문제 정의

```python
# main.py:83 — 전체 PDF 텍스트를 메모리에 적재
st.session_state.pdf_context = "\n".join([doc.page_content for doc in docs])

# main.py:144 — 전체 컨텍스트를 프롬프트에 그대로 전달
ai_response = chain.invoke({"context": st.session_state.pdf_context})
```

100페이지 이상의 PDF는 수십 MB의 텍스트를 생성하며, 이를 LLM 프롬프트에 전달하면 토큰 한도를 초과합니다.

#### 2) 영향 범위

- Gemini API 토큰 제한 초과 → API 에러 및 비용 폭증
- Streamlit 세션 메모리 과다 소비 → 서버 불안정

#### 3) 해결 방안

- 퀴즈 생성에도 RAG 기반 접근 도입 (랜덤 청크 샘플링 또는 벡터 검색 활용)
- 토큰 수 기반 컨텍스트 크기 제한 (예: 최대 8,000 토큰)
- 맵리듀스 패턴으로 대용량 문서 요약 후 퀴즈 생성

### 2.3 임시 파일 삭제 실패 시 리소스 누수

#### 1) 문제 정의

```python
# main.py:192-209
with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
    tmp_file.write(uploaded_file.read())
    tmp_path = tmp_file.name

with st.spinner("문서를 분석 중..."):
    load_and_parse_pdf(tmp_path)       # ← 여기서 예외 발생 가능
    initialize_agent()
    st.session_state.pdf_processed = True
    # ...
os.unlink(tmp_path)                    # ← 예외 시 실행되지 않음
```

#### 2) 해결 방안

```python
# 수정안: try/finally로 임시 파일 정리 보장
try:
    with st.spinner("문서를 분석 중..."):
        load_and_parse_pdf(tmp_path)
        initialize_agent()
        st.session_state.pdf_processed = True
finally:
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)
```

### 2.4 JSON 파싱 정규식의 신뢰성

#### 1) 문제 정의

```python
# main.py:50
json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
```

이 정규식은 **가장 첫 `{`부터 가장 마지막 `}`까지** 탐욕적으로 매칭합니다. LLM이 JSON 외부에 중괄호를 포함한 텍스트를 반환하면 의도치 않은 범위가 캡처됩니다.

#### 2) 해결 방안

- LangChain의 `JsonOutputParser` 또는 `PydanticOutputParser` 도입
- Gemini의 `response_mime_type="application/json"` 구조화 출력 기능 활용
- Pydantic 모델을 정의하여 `with_structured_output()` 바인딩

### 2.5 전역 상태에 과도하게 의존하는 초기화 흐름

#### 1) 문제 정의

```python
# main.py:20 — 모듈 로드 시점에 즉시 LLM 인스턴스 생성
chat = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# main.py:64 — 매 rerun 시 실행
st.session_state.vectorstore = get_vectorstore()
```

Streamlit은 사용자 인터랙션마다 전체 스크립트를 재실행하므로, 모듈 최상위의 `ChatGoogleGenerativeAI()` 초기화가 매번 불필요하게 반복됩니다.

#### 2) 해결 방안

- 모든 무거운 객체 (`chat`, `embeddings`) 를 `@st.cache_resource`로 감싸기
- 모델명을 `config.py`로 중앙 집중화하여 단일 변경점 확보

---

## 3. 보안 취약점

| 번호 | 위험 요소 | 심각도 | 설명 |
|:---:|:---|:---:|:---|
| S-1 | FAISS 역직렬화 | 높음 | `allow_dangerous_deserialization=True` 사용 —<br>악의적 인덱스 파일 로드 시 임의 코드 실행 가능 |
| S-2 | 환경변수 미검증 | 높음 | API 키 미설정 시 암호화되지 않은 에러 메시지 노출 |
| S-3 | 입력 유효성 검증 부재 | 중간 | PDF 파일 크기 제한 없음, 파일 타입 위장 가능 |
| S-4 | 프롬프트 인젝션 | 중간 | 시스템 프롬프트 외 사용자 입력 필터링 없음 |

---

## 4. 성능 병목 분석

### 4.1 현재 파이프라인 흐름

```
PDF 업로드 → [동기 블로킹] 텍스트 추출 → [API 호출] 임베딩 생성 → FAISS 인덱싱 → [API 호출] 퀴즈 생성
```

### 4.2 병목 지점

| 병목 | 영향 | 개선안 |
|:---|:---|:---|
| 임베딩 생성 (전체 청크 일괄) | 대용량 PDF 시 수 분 소요 | 배치 처리 + 진행률 표시 |
| 퀴즈 생성에 전체 컨텍스트 전달 | 토큰 한도 초과, 응답 지연 | RAG 기반 퀴즈 생성 전환 |
| `@st.cache_resource` 미적용 | LLM/임베딩 객체 매번 재생성 | 캐싱 적용 |
| `similarity_search(k=3)` 고정 | 적응형 검색 불가 | MMR 검색 또는 동적 k값 조정 |

---

## 5. LangChain/LangGraph 미활용 기능

| 미활용 기능 | 현재 구현 | 권장 개선 |
|:---|:---|:---|
| Structured Output | 정규식 JSON 파싱 | `with_structured_output()` +<br>Pydantic 모델 바인딩 |
| Output Parser | 수동 `parse_ai_json()` | `JsonOutputParser` |
| Streaming | 응답 완료까지 스피너 표시 | `st.write_stream()` +<br>LangChain streaming 콜백 |
| LangGraph 상태 머신 | 단순 Agent 하나 | 퀴즈 출제 → 채점 → 해설의<br>명시적 그래프 |
| Memory | 수동 히스토리 슬라이싱 | `MemorySaver` 체크포인터 |
| Callbacks/Tracing | 없음 | LangSmith 연동 |

---

## 6. 개선 로드맵

### 6.1 Phase 1: 즉시 수정 (안정성 확보) — 예상 1~2일

- [ ] LLM 응답 실패에 대한 재시도 로직 및 graceful fallback 추가
- [ ] `tempfile` 처리를 `try/finally`로 감싸기
- [ ] LLM/임베딩 객체에 `@st.cache_resource` 적용
- [ ] `pdf_context` 크기 제한 (토큰 수 기반 truncation)
- [ ] 환경변수 미설정 시 명확한 에러 메시지 표시

### 6.2 Phase 2: 구조 리팩토링 — 예상 3~5일

- [ ] `src/` 디렉토리로 모듈 분리

```
src/
├── config.py         # 모델명, 파라미터 중앙 관리
├── ingestion.py      # PDF 로딩, 텍스트 분할
├── vectorstore.py    # FAISS 로드/저장/검색 추상화
├── quiz_gen.py       # 퀴즈 생성 체인, JSON 파싱
├── agent.py          # RAG Agent 초기화, 대화 처리
└── tools.py          # @tool 데코레이터 함수 모음
```

- [ ] `JsonOutputParser` 또는 Gemini structured output 도입
- [ ] 대화 히스토리 최대 길이 제한
- [ ] 퀴즈 생성을 RAG 기반으로 전환

### 6.3 Phase 3: 기능 고도화 — 예상 1~2주

- [ ] LangGraph 상태 그래프로 퀴즈 플로우 재설계
- [ ] Streaming 응답 지원
- [ ] 오답 노트 기반 취약 영역 재출제 로직
- [ ] PDF 출처 (페이지 번호) 표시
- [ ] LangSmith 트레이싱 연동
- [ ] `pytest` 기반 단위/통합 테스트 추가

### 6.4 Phase 4: 프로덕션 배포 — 예상 2~3주

- [ ] FAISS → Supabase pgvector 마이그레이션
- [ ] Supabase Auth 연동
- [ ] 입력 가드레일 (파일 크기 제한, 프롬프트 인젝션 필터)
- [ ] Streamlit Community Cloud 배포
- [ ] CI/CD 파이프라인 구성

---

## 7. 권장 타겟 아키텍처

```
main.py (UI Layer)
  ├── src/config.py ─── .env
  ├── src/ingestion.py
  │     └── src/vectorstore.py
  ├── src/quiz_gen.py
  │     └── src/vectorstore.py
  └── src/agent.py
        ├── src/tools.py
        └── src/vectorstore.py
```

| 파일 | 책임 |
|:---|:---|
| `main.py` | Streamlit UI 렌더링만 담당 |
| `src/config.py` | 모델명, 임베딩 설정, 환경변수 중앙 관리 |
| `src/ingestion.py` | PDF 로딩, 텍스트 분할, 벡터스토어 저장 |
| `src/vectorstore.py` | FAISS 로드/저장, 검색 추상화 |
| `src/quiz_gen.py` | 퀴즈 생성 체인, JSON 파싱 |
| `src/agent.py` | RAG Agent 초기화, 대화 처리 |
| `src/tools.py` | `@tool` 데코레이터 함수 모음 |

> **참고**: `AGENTS.md`에서 이미 `src/ingestion.py`, `src/quiz_gen.py`, `src/agent.py`로의 분리를 개발 원칙으로 명시하고 있으므로, 이 계획은 기존 지침과 일관됩니다.
