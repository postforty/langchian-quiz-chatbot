# 🚀 Streamlit + Supabase 웹 배포 및 마이그레이션 가이드

이 문서는 로컬 환경에서 구동되는 LangChain Quiz Chatbot을 **Streamlit Community Cloud**와 **Supabase (PostgreSQL)**를 활용하여 실제 외부 사용자가 접근할 수 있는 클라우드 기반 SaaS 웹 애플리케이션으로 배포하는 절차를 안내합니다.

---

## 🏗️ 아키텍처 변경 요약
* **프론트엔드/호스팅**: Streamlit 로컬 구동 ➡️ **Streamlit Community Cloud**
* **벡터 저장소**: 로컬 파일 시스템 (FAISS) ➡️ **Supabase pgvector (PostgreSQL)**
* **데이터 보관 및 상태 유지**: `st.session_state` 휘발성 메모리 ➡️ **Supabase Database (대화 기록, 오답 노트 저장)**
* **사용자 관리**: 인증 없음 ➡️ **Supabase Auth (이메일/비밀번호, 소셜 로그인)**

---

## 📝 1단계: Supabase 프로젝트 설정

1. **Supabase 가입 및 새로운 프로젝트 생성**
   * [Supabase 공식 홈페이지](https://supabase.com)에 접속하여 회원가입 후 `New Project`를 생성합니다.
   * Database Password를 안전한 곳에 기록해 둡니다.

2. **pgvector 익스텐션 활성화**
   * Supabase 대시보드 좌측 메뉴에서 **`Database` ➡️ `Extensions`** 로 이동합니다.
   * `vector` 확장(Extension)을 검색하여 **Enable** 버튼을 누릅니다. (벡터 데이터를 저장하고 RAG를 가동하기 위해 필수입니다)

3. **테이블 생성 (SQL Editor 활용)**
   * 좌측 메뉴 **`SQL Editor`**에서 아래와 같은 테이블을 생성합니다. (예시)
   ```sql
   -- 사용자별 오답 노트 테이블 생성
   create table public.wrong_answers (
     id uuid default gen_random_uuid() primary key,
     user_id uuid references auth.users not null,
     question text,
     options jsonb,
     correct_answer text,
     explanation text,
     created_at timestamp with time zone default timezone('utc'::text, now()) not null
   );
   ```

4. **API 키 및 URL 확보**
   * **`Project Settings` ➡️ `API`** 화면으로 이동합니다.
   * `Project URL`과 `Project API keys (anon, public)` 값을 복사해 둡니다.

---

## 💻 2단계: 로컬 코드 수정 및 환경 변수 세팅

1. **필요 패키지 추가 (uv 사용)**
   Supabase 연동과 pgvector용 LangChain 클래스를 위해 의존성을 추가합니다.
   ```bash
   uv add supabase langchain-postgres psycopg2-binary
   ```

2. **로컬 환경변수(`.env`) 세팅**
   복사해둔 Supabase 정보와 기존 Gemini API Key를 세팅합니다.
   ```env
   GEMINI_API_KEY="your_google_gemini_api_key_here"
   SUPABASE_URL="https://your-project-id.supabase.co"
   SUPABASE_KEY="your_supabase_anon_key"
   SUPABASE_DB_URL="postgresql://postgres:[PASSWORD]@[DB-HOST]:5432/postgres"
   ```

3. **기존 FAISS 로직을 pgvector 로직으로 변경 (코드 마이그레이션)**
   `main.py`에 적용되어 있던 FAISS 코드를 주석 처리(또는 삭제)하고, `langchain-postgres`의 `PGVector`를 활용하도록 변경해야 합니다.

---

## ☁️ 3단계: Streamlit Community Cloud 배포 (무료)

1. **GitHub에 코드 푸시**
   * 위에서 변경한 코드와 `pyproject.toml`, `uv.lock` 파일 등이 최신 상태로 GitHub 레포지토리에 푸시되어 있어야 합니다. (가급적 `.gitignore`에 `.env`가 잘 포함되어 있는지 재확인하세요.)

2. **Streamlit 회원가입 및 앱 연동**
   * [Streamlit 커뮤니티 클라우드](https://share.streamlit.io/)에 GitHub 계정으로 로그인합니다.
   * 우측 상단의 **`New app`** 버튼을 클릭합니다.
   * 배포하려는 레포지토리(Repository), 브랜치(Branch), 메인 파일 경로(`main.py`)를 선택합니다.

3. **클라우드 환경 변수(Secrets) 등록**
   * 설정 화면 하단의 **`Advanced settings`** 버튼을 클릭합니다.
   * `Secrets` 입력창에 로컬의 `.env` 내용과 동일하게 값들을 입력합니다. (TOML 포맷을 사용합니다)
   ```toml
   GEMINI_API_KEY = "your_google_gemini_api_key_here"
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_KEY = "your_supabase_anon_key"
   SUPABASE_DB_URL = "postgresql://postgres:[PASSWORD]@[DB-HOST]:5432/postgres"
   ```

4. **Deploy 클릭**
   * `Deploy!` 버튼을 클릭하면 서버가 할당되고, requirements/uv 의존성 설치가 자동으로 진행된 뒤 앱이 실행됩니다.
   * 이 과정에서 문제가 생기면 우측 아래 `Manage app` 콘솔 창에서 에러 로그를 확인하고 수정 후 커밋하면 자동으로 재배포됩니다.

---

## 🎉 배포 완료 후 작업

* **URL 공유**: 이제 생성된 도메인(예: `https://your-chatbot-app.streamlit.app/`)을 통해 누구나 접근할 수 있습니다.
* **지속적 통합**: GitHub Main 브랜치에 푸시되는 즉시 Streamlit 배포 환경이 자동으로 갱신됩니다.
* **DB 모니터링**: Supabase 대시보드의 `Table Editor`를 통해 실제 사용자들이 어떤 문제를 틀리고 있는지, 데이터가 잘 축적되고 있는지 실시간으로 모니터링할 수 있습니다.
