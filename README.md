# Security Daily

Security Daily는 매일 보안뉴스에서 전날 기사를 수집하고, Local LLM Pipeline으로 학습 가치가 높은 뉴스를 선정·요약·분석한 뒤 단답형 Quiz까지 제공하는 개인용 보안 지식 Dashboard입니다.

## 핵심 기능

- 매일 전날 `00:00~23:59 KST`에 게시된 보안뉴스 기사 수집
- 학습 가치가 높은 기사 최대 3개 선정
- 선정 기사 요약과 실무 중심 Security Insight 생성
- 단답형 Quiz 생성, 자동 채점과 풀이 기록 저장
- 오늘의 Morning Briefing과 날짜별 과거 뉴스 조회
- Windows Task Scheduler 기반 매일 08:30 KST 자동 실행
- 단계별 Pipeline 상태와 실패 이력 기록 및 재실행

## Architecture

```mermaid
flowchart TD
    A[BoanNews] --> B[COLLECT]
    B --> C[SELECT]
    C --> D[SUMMARY]
    D --> E[ANALYZE]
    E --> F[QUIZ]
    F --> G[(PostgreSQL)]
    G --> H[FastAPI REST API]
    H --> I[Next.js Dashboard]

    J[Windows Task Scheduler] --> B
    K[Ollama / Local LLM] --> C
    K --> D
    K --> E
    K --> F
```

Backend는 API → Application → Domain ← Infrastructure 계층으로 분리합니다. FastAPI는 HTTP 요청만 담당하며 Daily Pipeline과 Scheduler는 별도 프로세스로 실행됩니다.

## Daily Pipeline

```text
COLLECT → SELECT → SUMMARY → ANALYZE → QUIZ
```

각 단계는 `PENDING`, `RUNNING`, `SUCCESS`, `FAILED` 상태로 기록됩니다. 동일 날짜 재실행 시 저장된 기사와 완료된 분석·Quiz를 재사용하여 불필요한 중복 처리를 피합니다.

## Local LLM 구성

| 역할 | 모델 |
|---|---|
| News Selector | `phi4-mini` |
| Summary | `gemma3:4b` |
| Security Analyst | `qwen3.5:9b` |
| Quiz | `llama3.2:3b` |

모델명과 Ollama URL은 환경변수로 관리하며 Agent는 공통 `LLMProvider` 경계를 통해 Ollama를 사용합니다. 모든 LLM 결과는 Structured Output과 Backend Schema Validation을 통과해야 저장됩니다.

## 기술 Stack

| 영역 | 기술 |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, CSS Modules |
| Backend | Python 3.13, FastAPI, Pydantic |
| Database | PostgreSQL, SQLAlchemy 2.x, Alembic |
| Local AI | Ollama |
| Crawling | httpx, BeautifulSoup4 |
| Package | uv, npm |
| Test | pytest, FastAPI TestClient, ESLint, TypeScript |
| Operations | Windows Task Scheduler, PowerShell |

## 프로젝트 구조

```text
security-daily/
├── backend/
│   ├── src/security_daily/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   └── jobs/
│   ├── alembic/
│   └── tests/
├── frontend/
│   └── src/
├── scripts/
│   ├── run_daily_pipeline.ps1
│   └── register_daily_task.ps1
├── docs/
│   ├── PROJECT.md
│   ├── ARCHITECTURE.md
│   └── history/
└── .github/workflows/ci.yml
```

## 설치

### 요구사항

- Git
- [uv](https://docs.astral.sh/uv/)
- Python 3.12 이상 (`backend/.python-version`은 3.13.5)
- Node.js 24와 npm
- PostgreSQL
- [Ollama](https://ollama.com/)

```powershell
git clone https://github.com/ahnjinhyeong/security-daily.git
cd security-daily

cd backend
uv sync --locked

cd ..\frontend
npm ci
```

## 환경변수 설정

실제 환경파일은 Git에 Commit하지 않습니다.

```powershell
Copy-Item .env.example .env
Copy-Item frontend\.env.example frontend\.env.local
```

루트 `.env`의 필수 항목:

```env
DATABASE_URL=postgresql+psycopg://security_daily:CHANGE_ME@localhost:5432/security_daily
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT_SECONDS=120
SELECTOR_MODEL=phi4-mini
SUMMARY_MODEL=gemma3:4b
ANALYST_MODEL=qwen3.5:9b
QUIZ_MODEL=llama3.2:3b
TIMEZONE=Asia/Seoul
```

Frontend `.env.local`:

```env
BACKEND_API_BASE_URL=http://localhost:8010
```

## PostgreSQL 준비

아래 비밀번호 예시는 반드시 개인 환경에 맞게 변경합니다.

```sql
CREATE USER security_daily WITH PASSWORD 'CHANGE_ME';
CREATE DATABASE security_daily OWNER security_daily;
```

Migration 적용:

```powershell
cd backend
uv run alembic upgrade head
uv run alembic current
```

## Ollama 모델 설치

```powershell
ollama pull phi4-mini
ollama pull gemma3:4b
ollama pull qwen3.5:9b
ollama pull llama3.2:3b
ollama list
```

## 실행

Backend:

```powershell
cd backend
uv run uvicorn security_daily.api.main:app --reload --port 8010
```

Frontend:

```powershell
cd frontend
npm run dev
```

Dashboard는 `http://localhost:3000`에서 확인합니다.

## Daily Pipeline 수동 실행

```powershell
cd backend
uv run python -m security_daily.jobs.daily
```

특정 날짜 또는 단계부터 재실행:

```powershell
uv run python -m security_daily.jobs.daily --target-date 2026-08-19 --start-stage QUIZ
```

Windows Runner Script를 직접 실행할 수도 있습니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_daily_pipeline.ps1
```

## Windows Scheduler

현재 사용자에게 매일 08:30 KST Task를 등록합니다. 동일 이름 Task가 있으면 덮어쓰지 않습니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\register_daily_task.ps1
```

```powershell
Get-ScheduledTask -TaskName "SecurityDaily-DailyPipeline"
Start-ScheduledTask -TaskName "SecurityDaily-DailyPipeline"
Disable-ScheduledTask -TaskName "SecurityDaily-DailyPipeline"
Enable-ScheduledTask -TaskName "SecurityDaily-DailyPipeline"
```

실행 로그는 Git에서 제외된 `logs/daily-pipeline-YYYY-MM-DD.log`에 기록되며 30일간 보존됩니다. PC가 꺼져 있거나 Sleep 상태이면 예약 시각에 실행되지 않을 수 있습니다.

## 테스트

Backend 전체 로컬 테스트:

```powershell
cd backend
uv run pytest
uv run alembic check
uv lock --check
```

외부 PostgreSQL, Ollama와 실제 사이트를 제외한 CI 테스트:

```powershell
uv run pytest -m "not integration and not smoke"
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## 주요 설계 결정

- 수집 기준은 실행일 전날 `00:00~23:59 KST`입니다.
- 원문 HTML이 아닌 AI 분석용 정제 본문만 저장합니다.
- 선정 기사는 최대 3개이며 가치가 부족하면 강제로 채우지 않습니다.
- Quiz는 기사별 최대 1문제를 생성한 뒤 전체 최대 3개와 중복을 검증합니다.
- Quiz 채점에는 LLM을 사용하지 않고 정규화된 대표·허용 정답만 비교합니다.
- 사용자 API에는 선정 뉴스만 노출하며 기사 원문 전체는 표시하지 않습니다.
- 외부 서비스가 필요한 Integration/Smoke Test는 기본 CI에서 제외합니다.

## 현재 제한사항

- 보안뉴스 단일 출처만 지원합니다.
- 개인용 MVP로 Authentication과 다중 사용자 기능이 없습니다.
- Local LLM 속도와 품질은 실행 장비 성능에 영향을 받습니다.
- Scheduler Task는 현재 사용자가 로그인한 상태에서 실행됩니다.
- PC가 Sleep 또는 종료 상태이면 정확한 예약 실행이 보장되지 않습니다.

## 향후 계획

현재 Windows Native 구성을 Home Server의 Docker Compose 환경으로 이전할 수 있도록 외부 연결정보와 영속 데이터는 환경변수와 PostgreSQL로 분리했습니다. Docker, 배포 자동화, 검색, RAG와 Monitoring은 현재 MVP 범위에 포함되지 않습니다.

## 문서

- [프로젝트 요구사항](docs/PROJECT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [개발 History](docs/history/)
