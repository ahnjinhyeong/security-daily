# Security Daily — ARCHITECTURE

> Version: 1.0  
> Status: Implemented MVP  
> Related: `PROJECT.md`

---

# 1. 문서 목적

이 문서는 `PROJECT.md`에서 정의한 Security Daily의 요구사항을 실제 시스템으로 구현하기 위한 기술 아키텍처를 정의한다.

`PROJECT.md`가 **무엇을 만들고 왜 만드는가**를 정의한다면, 이 문서는 다음 질문에 답한다.

> **"그 시스템을 기술적으로 어떻게 구현할 것인가?"**

주요 설계 대상:

- 전체 시스템 구조
- Frontend / Backend 책임
- PostgreSQL 데이터 구조
- Crawling Pipeline
- Local LLM Multi-Agent 구조
- Agent와 LLM 모델의 분리
- Daily Pipeline
- Scheduler
- 실패 복구
- REST API
- 환경설정
- Logging
- Testing
- 향후 Docker/Home Server 이전

---

# 2. Architecture Goals

시스템은 다음 원칙을 우선한다.

## 2.1 단순성

개인용 MVP 규모에 불필요한 인프라를 추가하지 않는다.

초기 버전에서는 다음 기술을 사용하지 않는다.

- Redis
- Celery
- Kafka
- Kubernetes
- 별도의 Vector DB
- 복잡한 Multi-Agent Framework

필요성이 발생하면 이후 도입한다.

## 2.2 관심사의 분리

각 컴포넌트는 명확한 책임을 가진다.

```text
Crawler
→ 데이터 수집

News Selector Agent
→ 기사 선정

Summary Agent
→ 사실관계 압축

Security Analyst Agent
→ 보안 분석

Quiz Agent
→ 학습 문제 생성

Repository
→ 데이터 저장/조회

FastAPI
→ API 제공

Next.js
→ 사용자 인터페이스
```

## 2.3 낮은 결합도

특정 Local LLM 모델이나 실행 환경에 애플리케이션 전체가 종속되지 않도록 한다.

예를 들어 Agent가 Ollama API를 직접 호출하도록 만들지 않는다.

```text
Agent
  ↓
LLM Provider Interface
  ↓
Ollama Adapter
  ↓
Ollama
```

이를 통해 향후 다른 Local LLM Runtime으로 교체할 수 있도록 한다.

## 2.4 재현 가능성

개발 환경과 운영 환경의 차이를 최소화한다.

초기에는 Windows Native 환경을 사용하지만, 향후 Docker Compose 기반 홈서버로 이전할 수 있도록 외부 연결정보는 환경변수로 관리한다.

## 2.5 실패 복구 가능성

Daily Pipeline 도중 일부 작업이 실패해도 처음부터 모든 작업을 다시 실행하지 않는다.

각 처리 단계의 상태를 추적하고 가능한 경우 실패한 지점부터 재실행한다.

---

# 3. Runtime Environment

## Phase 1 — 현재

초기 개발 및 운영 환경:

```text
Windows PC
│
├── Next.js
├── FastAPI
├── PostgreSQL
└── Ollama
     └── Local LLM
```

기본 Local Endpoint:

```text
Next.js      : localhost:3000
FastAPI      : localhost:8010
PostgreSQL   : localhost:5432
Ollama       : localhost:11434
```

단, 해당 주소를 애플리케이션 코드에 직접 하드코딩하지 않는다.

## Phase 2 — 향후

홈서버 구축 이후 Docker Compose 환경으로 이전한다.

예상 구조:

```text
Home Server
│
├── Docker Compose
│    ├── frontend
│    │    └── Next.js
│    │
│    ├── backend
│    │    └── FastAPI
│    │
│    └── database
│         └── PostgreSQL
│
└── Ollama
     └── Host 또는 별도 GPU Machine
```

초기 구현부터 이 이전 가능성을 고려한다.

---

# 4. Technology Stack

| 영역 | 기술 |
|---|---|
| Frontend | Next.js + TypeScript |
| Backend | FastAPI + Python |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Migration | Alembic |
| HTTP Client | httpx |
| HTML Parser | BeautifulSoup4 |
| Local LLM Runtime | Ollama |
| Configuration | Environment Variables |
| Backend Test | pytest |
| Frontend Test | Vitest 검토 |
| Version Control | Git |
| Repository | GitHub |
| CI | GitHub Actions |
| Scheduler | Windows Task Scheduler → 향후 cron/systemd timer |
| Container | MVP 이후 Docker Compose |

---

# 5. Overall Architecture

```text
                    ┌───────────────────────┐
                    │       Next.js         │
                    │                       │
                    │ Morning Briefing      │
                    │ History               │
                    │ Quiz                  │
                    └───────────┬───────────┘
                                │
                             REST API
                                │
                                ▼
                    ┌───────────────────────┐
                    │       FastAPI         │
                    │                       │
                    │ API Layer             │
                    │ Application Layer     │
                    │ Domain                │
                    └──────┬────────┬───────┘
                           │        │
                    SQLAlchemy      │
                           │        │
                           ▼        ▼
                 ┌────────────┐  ┌──────────────┐
                 │ PostgreSQL │  │ LLM Provider │
                 └────────────┘  └──────┬───────┘
                                        │
                                        ▼
                                   ┌─────────┐
                                   │ Ollama  │
                                   └─────────┘


       Windows Task Scheduler
                │
                ▼
       Daily Pipeline Runner
                │
                ▼
           boannews.com
                │
                ▼
             Crawler
                │
                ▼
        Multi-Agent Pipeline
                │
                ▼
           PostgreSQL
```

---

# 6. Backend Layer Architecture

Backend는 책임 분리를 위해 Layer Architecture를 사용한다.

```text
API
 ↓
Application
 ↓
Domain
 ↑
Infrastructure
```

## 6.1 Domain Layer

시스템의 핵심 개념을 표현한다.

예:

```text
Article
DailySelection
AIAnalysis
Quiz
QuizAttempt
```

외부 Framework나 DB 구현 세부사항에 최대한 의존하지 않는다.

## 6.2 Application Layer

실제 Use Case를 담당한다.

예:

```text
CollectDailyNews
SelectDailyNews
SummarizeArticle
AnalyzeSecurityArticle
GenerateDailyQuiz

GetMorningBriefing
GetNewsByDate
GetAvailableDates
GetDailyQuiz
SubmitQuizAnswer
```

> **Use Case**
> 사용자가 시스템을 통해 수행하거나 시스템이 자동으로 수행하는 하나의 구체적인 작업.

## 6.3 Infrastructure Layer

외부 기술과 직접 통신한다.

예:

```text
PostgreSQL
Ollama
boannews.com
Windows Scheduler
```

구현체 예:

```text
SQLAlchemyArticleRepository
OllamaLLMProvider
BoanNewsCrawler
```

## 6.4 API Layer

FastAPI Endpoint를 담당한다.

API Layer에서는 복잡한 비즈니스 로직을 처리하지 않는다.

```text
HTTP Request
      ↓
FastAPI Router
      ↓
Application Use Case
      ↓
Domain / Repository
      ↓
HTTP Response
```

---

# 7. Frontend Architecture

Frontend는 Next.js + TypeScript 기반으로 구성한다.

MVP는 Single Page 중심으로 구현한다.

주요 UI 영역:

```text
Morning Security Briefing

├── 오늘의 Briefing
├── 지난 뉴스
└── 오늘의 Quiz
```

Desktop:

```text
NEWS 01 | NEWS 02 | NEWS 03
```

Mobile:

```text
NEWS 01
   ↓
NEWS 02
   ↓
NEWS 03
```

CSS Grid와 Flexbox를 사용하여 반응형 레이아웃을 구현한다.

Frontend는 다음 역할만 담당한다.

- 데이터 표시
- 날짜 선택
- Quiz 답안 입력
- API 호출
- Loading / Error UI
- Responsive UI

뉴스 선정, AI 호출, 채점 등의 비즈니스 로직은 Frontend에서 처리하지 않는다.

---

# 8. Database Architecture

DBMS:

```text
PostgreSQL
```

ORM:

```text
SQLAlchemy 2.x
```

Schema Migration:

```text
Alembic
```

주요 테이블:

```text
articles
pipeline_runs
daily_selections
ai_analyses
quizzes
quiz_attempts
```

---

# 9. Database ERD

```text
┌──────────────────┐
│     articles     │
├──────────────────┤
│ PK id            │
│ source            │
│ source_article_id │
│ title            │
│ url UNIQUE       │
│ content          │
│ published_at     │
│ collected_at     │
│ created_at       │
└────────┬─────────┘
         │
         ├─────────────────────────┐
         │                         │
         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│ daily_selections │      │   ai_analyses    │
├──────────────────┤      ├──────────────────┤
│ PK id            │      │ PK id            │
│ FK article_id    │      │ FK article_id    │
│ selection_date   │      │ summary          │
│ rank             │      │ importance       │
│ score            │      │ attack_scenario  │
│ reason           │      │ security_actions │
│ model_name       │      │ key_concepts     │
│ created_at       │      │ related_info     │
└──────────────────┘      │ summary_model    │
                          │ analyst_model    │
                          │ created_at       │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │     quizzes      │
                          ├──────────────────┤
                          │ PK id            │
                          │ FK article_id    │
                          │ quiz_date        │
                          │ question         │
                          │ answer           │
                          │ accepted_answers │
                          │ explanation      │
                          │ model_name       │
                          │ created_at       │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │  quiz_attempts   │
                          ├──────────────────┤
                          │ PK id            │
                          │ FK quiz_id       │
                          │ user_answer      │
                          │ is_correct       │
                          │ answered_at      │
                          └──────────────────┘
```

---

# 10. Table Design

## 10.1 articles

| Column | Type | Constraint |
|---|---|---|
| id | BIGINT | PK |
| source | TEXT | NOT NULL |
| source_article_id | TEXT | NOT NULL |
| title | TEXT | NOT NULL |
| url | TEXT | UNIQUE, NOT NULL |
| content | TEXT | NOT NULL |
| published_at | TIMESTAMPTZ | NOT NULL |
| collected_at | TIMESTAMPTZ | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |

Index:

```text
published_at
```

Constraint:

```text
UNIQUE(source, source_article_id)
```

`source`는 출처 식별자이며 보안뉴스 기사는 `boannews`를 사용한다. `source_article_id`에는 보안뉴스의 기사 `idx`를 저장한다.

`content`에는 이미지 URL이나 원문 HTML이 아니라 AI 분석에 사용할 수 있도록 기자 서명, 저작권 문구와 불필요한 마크업을 제거한 정제 본문 텍스트를 장기 보관한다.

## 10.2 pipeline_runs

Daily Pipeline의 날짜별 실행 이력을 독립적으로 기록한다. 같은 날짜를 재실행해도 기존 행을 덮어쓰지 않고 새 실행 행을 생성한다.

| Column | Type | Constraint |
|---|---|---|
| id | BIGINT | PK |
| target_date | DATE | NOT NULL, INDEX |
| stage | TEXT | NOT NULL |
| status | TEXT | NOT NULL |
| started_at | TIMESTAMPTZ | |
| finished_at | TIMESTAMPTZ | |
| crawled_count | INTEGER | NOT NULL |
| saved_count | INTEGER | NOT NULL |
| duplicate_count | INTEGER | NOT NULL |
| candidate_count | INTEGER | NOT NULL |
| selected_count | INTEGER | NOT NULL |
| error_type | TEXT | |
| created_at | TIMESTAMPTZ | NOT NULL |

현재 연결된 단계는 `COLLECT`, `SELECT`, `SUMMARY`, `ANALYZE`, `QUIZ`이며 상태는 `PENDING`, `RUNNING`, `SUCCESS`, `FAILED`를 사용한다. 실패 시 기사 원문이나 Secret이 포함될 수 있는 메시지 대신 예외 형식만 저장한다.

## 10.3 daily_selections

| Column | Type | Constraint |
|---|---|---|
| id | BIGINT | PK |
| article_id | BIGINT | FK, NOT NULL |
| selection_date | DATE | NOT NULL |
| rank | SMALLINT | NOT NULL |
| score | NUMERIC(5,2) | NOT NULL, 0~100 |
| reason | TEXT | NOT NULL |
| model_name | TEXT | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |

Constraint:

```text
UNIQUE(selection_date, rank)
UNIQUE(selection_date, article_id)
```

Index:

```text
selection_date
```

동일 날짜를 재실행하면 LLM 출력 전체가 Validation을 통과한 뒤 기존 선정 결과를 트랜잭션 안에서 새 결과로 교체한다. Validation 또는 저장이 실패하면 기존 결과를 유지한다.

## 10.4 ai_analyses

| Column | Type |
|---|---|
| id | BIGINT PK |
| article_id | BIGINT FK |
| summary | TEXT |
| importance | TEXT |
| attack_scenario | TEXT |
| security_actions | JSONB |
| key_concepts | JSONB |
| related_security_info | JSONB |
| summary_model | TEXT |
| analyst_model | TEXT |
| summary_status | TEXT |
| analyst_status | TEXT |
| error_type | TEXT |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

`article_id`는 UNIQUE로 설정하여 MVP에서는 기사 하나당 하나의 활성 분석 결과를 유지한다.

기사별 실패 복구를 위해 Summary와 Analyst 상태를 각각 `PENDING`, `RUNNING`, `SUCCESS`, `FAILED`로 기록한다. Summary 성공 직후 결과를 저장하므로 Analyst 실패 시 재실행에서는 저장된 Summary를 재사용하고 해당 기사 Analyst부터 이어서 처리한다. Analyst까지 성공한 기사는 재실행에서 건너뛴다.

## 10.5 quizzes

| Column | Type |
|---|---|
| id | BIGINT PK |
| article_id | BIGINT FK |
| quiz_date | DATE |
| question | TEXT |
| answer | TEXT |
| accepted_answers | JSONB |
| explanation | TEXT |
| model_name | TEXT |
| created_at | TIMESTAMPTZ |

Index:

```text
quiz_date
```

하루 최대 3문제 제한은 DB가 아니라 Application Layer에서 보장한다.

동일 날짜에 Quiz가 이미 저장되어 있으면 성공 결과로 간주하고 Quiz Agent를 다시 호출하지 않는다. 새 결과는 Structured Output과 Backend Validation을 모두 통과한 뒤 최대 3건을 한 트랜잭션으로 저장한다.

## 10.6 quiz_attempts

| Column | Type |
|---|---|
| id | BIGINT PK |
| quiz_id | BIGINT FK |
| user_answer | TEXT |
| is_correct | BOOLEAN |
| answered_at | TIMESTAMPTZ |

`quiz_id`에는 조회 성능을 위한 Index를 두며 Quiz 삭제 시 관련 풀이 기록도 함께 삭제한다. 채점은 LLM 없이 Application Layer에서 대표 정답과 허용 정답을 비교한다. 비교 전 앞뒤 공백 제거, 연속 공백 축약, 영문 대소문자 무시만 적용하며 의미가 다른 표현을 추론해 정답으로 인정하지 않는다.

---

# 11. Crawling Architecture

크롤링 대상은 보안뉴스 단일 사이트이다.

Crawler는 AI Agent가 아니다.

```text
HTTP Request
     ↓
HTML
     ↓
BeautifulSoup
     ↓
Article Parsing
     ↓
Article Domain Object
     ↓
PostgreSQL
```

기본 구현:

```text
httpx
+
BeautifulSoup4
```

JavaScript Rendering이 실제로 필요한 페이지가 확인되는 경우에만 Playwright 등의 도입을 검토한다.

---

# 12. Crawling Policy

매일 오전 **08:30 KST** 실행한다.

수집 대상 기간:

```text
전날 00:00:00 KST
~
전날 23:59:59 KST
```

예:

```text
실행:
2026-08-19 08:30

수집 대상:
2026-08-18 00:00
~
2026-08-18 23:59
```

기사 날짜 판단은 크롤링 시각이 아닌 `published_at`을 기준으로 한다.

URL UNIQUE Constraint를 통해 중복 저장을 방지한다.

---

# 13. Multi-Agent Architecture

4개의 논리적 Agent를 사용한다.

```text
News Selector Agent
        ↓
Summary Agent
        ↓
Security Analyst Agent
        ↓
Quiz Agent
```

Agent와 LLM Model은 동일한 개념이 아니다.

```text
4 Agents
≠
4 LLM Models
```

하나의 모델을 여러 Agent가 공유할 수도 있고 Agent마다 서로 다른 모델을 사용할 수도 있다.

현재 MVP 초기 구성에서는 서로 다른 모델 패밀리를 역할별로 배치한다.

---

# 14. News Selector Agent

역할:

> 오늘 학습할 가치가 높은 뉴스는 무엇인가?

입력:

```text
전날 수집 기사의 article_id, title, published_at, content_excerpt
```

모든 후보 기사는 유지하되 Context 크기를 제한하기 위해 기사 수에 따라 본문 예산을 균등 배분한다. 긴 본문은 앞부분과 끝부분을 함께 보존하여 사건 개요와 후반의 영향·대응 정보가 모두 포함되도록 축약한다. 기사별·전체 본문 문자 제한은 환경변수로 조정한다.

평가 기준:

- 실무 보안 중요도
- 공격/취약점 관련성
- 영향 범위
- 학습 가치
- 기사 중복성
- 홍보/행사성 여부

출력:

```text
최대 3개 기사

+
rank
score
reason
```

점수 범위는 `0~100`으로 통일한다. Structured Output이 최대 3개, 후보에 존재하는 기사 ID, 중복 없는 연속 순위, 중복 없는 기사와 필수 선정 사유 조건을 모두 통과한 경우에만 저장한다.

학습 가치가 부족한 경우 3개를 강제로 채우지 않는다.

초기 모델:

```text
Phi-4 Mini 3.8B
```

---

# 15. Summary Agent

역할:

> 무슨 일이 있었는가?

입력:

```text
기사 원문
```

출력:

```text
핵심 요약
최대 5문장
```

원칙:

- 사실 중심
- 추측 금지
- 불필요한 분석 금지
- 중요한 CVE/제품/기관 정보 유지
- 기사에서 확인되지 않는 사실 생성 금지

초기 모델:

```text
Gemma 3 4B
```

---

# 16. Security Analyst Agent

역할:

> 이 기사에서 보안 관점으로 무엇을 배워야 하는가?

입력:

```text
기사 원문
+
Summary Agent 결과
```

사실 판단 우선순위:

```text
1. 기사 원문
2. 기사 Metadata
3. Summary
4. LLM 내부 지식
```

LLM 내부 지식은 기사 사실 확인이 아니라 보안적 해석에만 사용한다.

출력:

```text
importance

attack_scenario

security_actions
최대 5개

key_concepts
최대 5개

related_security_info
최대 5개
```

실제 공격 사례와 AI가 추론한 가능한 공격 시나리오는 명확하게 구분한다.

초기 모델:

```text
Qwen 3.5 9B
```

Security Analyst는 전체 Pipeline에서 가장 높은 추론 품질이 필요한 Agent이므로 가장 큰 모델을 배치한다.

---

# 17. Quiz Agent

역할:

> 오늘 학습한 내용 중 무엇을 기억해야 하는가?

입력:

```text
선정 기사 제목
+
Summary
+
Security Insight
```

출력:

```text
단답형 문제
최대 3개

question
answer
accepted_answers
explanation
```

문제가 충분하지 않으면 3개를 강제로 생성하지 않는다.

Quiz 생성은 선정 기사별로 최대 1문제를 독립 요청한 뒤 전체 결과에 최대 3개, 기사 ID, 질문·핵심 개념 중복 Validation을 다시 적용한다. 기사 원문은 입력하지 않으며 각 요청에는 제목, Summary와 Security Insight만 사용한다. Ollama 요청은 비정상적으로 긴 Structured Output 생성을 방지하기 위해 Quiz 단계에 한해 출력 token 상한을 적용한다.

초기 모델:

```text
Llama 3.2 3B
```

---

# 18. Quiz Grading

Quiz 채점에는 LLM을 사용하지 않는다.

```text
사용자 답변
      ↓
Normalize
      ↓
대표 정답 / 허용 정답 비교
      ↓
Correct / Incorrect
```

Normalize 대상:

- 앞뒤 공백 제거
- 영문 대소문자 차이 제거
- 연속 공백 정규화

예:

```text
RCE
rce
Remote Code Execution
remote code execution
원격 코드 실행
```

허용 정답 목록에 포함되어 있으면 정답 처리한다.

---

# 19. LLM Provider Architecture

Agent가 Ollama에 직접 의존하지 않도록 추상화한다.

개념적 구조:

```text
Agent
   ↓
LLMProvider
   ↓
OllamaLLMProvider
   ↓
Ollama API
```

Interface:

```text
LLMProvider

generate_json(
    model,
    system_prompt,
    user_prompt,
    schema
)
```

Ollama Adapter는 `/api/chat`의 Structured Output에 JSON Schema를 전달하고 HTTP Envelope와 JSON 응답을 검증한다. Agent는 다시 Pydantic Schema로 최대 선정 수, ID, 순위, 점수와 필수 사유를 검증한다. 이를 통해 향후 다른 Runtime으로 교체할 수 있다.

---

# 20. Agent별 Local LLM Configuration

Security Daily는 각 Agent의 역할과 요구 성능에 따라 서로 다른 Local LLM을 배치한다.

초기 모델 구성은 다음과 같다.

| Agent | Model | Provider 계열 | 역할 |
|---|---|---|---|
| News Selector Agent | Phi-4 Mini 3.8B | Microsoft | 당일 기사 비교 및 학습 가치 판단 |
| Summary Agent | Gemma 3 4B | Google | 기사 원문의 핵심 사실 요약 |
| Security Analyst Agent | Qwen 3.5 9B | Alibaba | 보안 의미, 공격 시나리오, 대응 및 핵심 개념 분석 |
| Quiz Agent | Llama 3.2 3B | Meta | 단답형 복습 문제 생성 |

모델 배치 원칙:

```text
News Selector
→ Phi-4 Mini 3.8B
→ 경량 추론 및 분류

Summary
→ Gemma 3 4B
→ 사실 압축 및 요약

Security Analyst
→ Qwen 3.5 9B
→ 가장 높은 추론 품질이 필요한 핵심 Agent

Quiz
→ Llama 3.2 3B
→ 정리된 학습정보를 단답형 문제로 변환
```

## 20.1 Model Runtime Policy

4개의 Agent가 서로 다른 모델을 사용하지만 모든 모델을 GPU 메모리에 동시에 상주시킬 필요는 없다.

Daily Pipeline은 기본적으로 순차 실행한다.

```text
News Selector
    ↓
Summary
    ↓
Security Analyst
    ↓
Quiz
```

각 단계에서 필요한 모델을 Ollama를 통해 호출한다.

특히 Security Analyst는 전체 Pipeline에서 가장 높은 추론 품질이 필요한 Agent이므로 가장 큰 모델을 배치한다.

기본 모델 크기 우선순위:

```text
Security Analyst > Summary ≈ Selector > Quiz
```

현재 개발 노트북과 향후 Mac Studio 모두에서 안정적인 실행을 우선하며, 실제 운영 전 Smoke Test를 통해 한국어 품질, Structured Output 준수율, 처리시간, 메모리 사용량을 확인한다.

## 20.2 Model Configuration

모델 이름은 Application Code에 하드코딩하지 않고 환경변수로 관리한다.

초기 설정 예:

```env
SELECTOR_MODEL=phi4-mini
SUMMARY_MODEL=gemma3:4b
ANALYST_MODEL=qwen3.5:9b
QUIZ_MODEL=llama3.2:3b
```

## 20.3 Model Replacement Policy

Agent 구현 코드와 실제 LLM 모델을 분리한다.

향후 Benchmark 결과에 따라 코드 수정 없이 각 Agent의 모델을 독립적으로 교체할 수 있어야 한다.

예:

```text
ANALYST_MODEL=qwen3.5:9b

↓

ANALYST_MODEL=<future-model>
```

단순 모델 변경은 Architecture 변경으로 간주하지 않는다.

단, Agent의 책임이나 데이터 흐름 자체가 변경되는 경우에는 `ARCHITECTURE.md`를 갱신한다.

---

# 21. Daily Pipeline

전체 Pipeline:

```text
08:30 KST

START
  │
  ▼
[1] 전날 기사 Crawling
  │
  ▼
[2] articles 저장
  │
  ▼
[3] News Selector
  │
  ▼
최대 3개 선정
  │
  ▼
[4] Summary
  │
  ▼
[5] Security Analysis
  │
  ▼
[6] AI Analysis 저장
  │
  ▼
[7] Quiz Generation
  │
  ▼
[8] Quiz 저장
  │
  ▼
COMPLETE

목표 완료:
08:50 KST 이전
```

Daily Pipeline의 목표 처리시간:

```text
≤ 20분
```

---

# 22. Scheduler

Phase 1:

```text
Windows Task Scheduler
```

매일:

```text
08:30 KST
```

Daily Job을 실행한다.

FastAPI Server 자체에 Scheduler를 내장하지 않는다.

```text
FastAPI
→ HTTP Request 처리

Daily Job
→ 자동 수집/AI Pipeline
```

두 책임을 분리한다.

향후 Linux/Home Server에서는:

```text
cron
또는
systemd timer
```

로 교체할 수 있다.

---

# 23. Pipeline Failure Recovery

Daily Pipeline은 중간 실패 가능성을 고려한다.

예:

```text
Crawler       SUCCESS
Selector      SUCCESS

Article 101
Summary       SUCCESS
Analyst       SUCCESS

Article 102
Summary       SUCCESS
Analyst       FAILED

Article 103
Summary       SUCCESS
Analyst       SUCCESS

Quiz          PENDING
```

재실행 시 이미 완료된 작업을 불필요하게 다시 수행하지 않는다.

가능한 경우:

```text
Article 102
Analyst 재실행
      ↓
Quiz 실행
```

형태로 복구한다.

---

# 24. Pipeline State

실패 복구를 위해 처리 상태가 필요하다.

다만 MVP에서 복잡한 Workflow Engine을 도입하지 않는다.

개념적으로 다음 상태를 사용한다.

```text
PENDING
RUNNING
SUCCESS
FAILED
```

`pipeline_runs` 테이블에 실행 대상 날짜, 현재 단계, 상태, 시작·종료 시각과 처리 건수를 기록한다. 동일 날짜의 각 재실행은 별도 행으로 남겨 성공과 실패 이력을 구분한다.

현재는 `COLLECT`, `SELECT`, `SUMMARY`, `ANALYZE`, `QUIZ` 단계를 순차 연결한다. 각 단계는 별도 실행 이력으로 기록하며 지정한 단계부터 재실행하면 앞선 단계를 건너뛴다. Summary와 Analyst는 `ai_analyses`의 기사별 상태를 확인하고 Quiz는 날짜별 저장 결과를 확인하여 이미 성공한 작업을 다시 호출하지 않는다.

---

# 25. LLM Failure Handling

Local LLM에서는 다음 오류가 발생할 수 있다.

- Ollama 연결 실패
- Model 미설치
- Model Loading 실패
- VRAM 부족
- Timeout
- 잘못된 JSON 출력
- 필수 Field 누락

Agent 결과는 가능한 한 Structured Output 형태로 요청하고 Backend에서 Validation한다.

예:

```text
LLM Response
      ↓
Schema Validation
      ↓
VALID?
 ├─ YES → 저장
 └─ NO  → 재시도 / FAILED
```

무한 재시도는 하지 않는다.

---

# 26. REST API

Frontend에 필요한 최소 API를 제공한다.

## Morning Briefing

```http
GET /api/news/today
```

현재 제공할 Morning Briefing을 반환한다.

Morning Briefing 대상 날짜는 `Asia/Seoul` 기준 현재 날짜의 전날이다. `daily_selections`를 기준으로 `articles`와 결합하고 선정 순위대로 반환하며, 선정되지 않은 수집 기사는 API에 노출하지 않는다. 분석이 아직 없는 선정 기사는 기사 정보는 반환하고 분석 필드는 `null`로 표시한다.

## 날짜별 뉴스

```http
GET /api/news?date=YYYY-MM-DD
```

해당 날짜에 선정된 뉴스를 반환한다.

데이터가 없는 날짜는 오류가 아니라 요청 날짜와 함께 `count: 0`, `articles: []`를 반환한다. 잘못된 날짜 형식은 Request Validation 오류로 처리한다.

## 뉴스 데이터 존재 날짜

```http
GET /api/news/dates
```

과거 뉴스 Calendar에 사용한다.

선정 뉴스가 존재하는 날짜와 날짜별 선정 기사 수를 최신 날짜부터 반환한다.

## 오늘의 Quiz

```http
GET /api/quizzes/today
```

정답은 Response에 포함하지 않는다.

`today`는 실행 시점의 `Asia/Seoul` 날짜에서 하루를 뺀 Morning Briefing 대상 날짜를 의미한다. 날짜별 Quiz API는 요청받은 날짜를 그대로 조회한다.

## 날짜별 Quiz

```http
GET /api/quizzes?date=YYYY-MM-DD
```

## Quiz 답안 제출

```http
POST /api/quizzes/{quiz_id}/answer
```

Request:

```json
{
  "answer": "RCE"
}
```

Response:

```json
{
  "correct": true,
  "correct_answer": "RCE",
  "explanation": "..."
}
```

---

# 27. Configuration

환경별 값은 코드에 하드코딩하지 않는다.

`.env` 기반으로 관리한다.

예:

```env
DATABASE_URL=postgresql+psycopg://...

OLLAMA_BASE_URL=http://localhost:11434

SELECTOR_MODEL=phi4-mini
SUMMARY_MODEL=gemma3:4b
ANALYST_MODEL=qwen3.5:9b
QUIZ_MODEL=llama3.2:3b

TIMEZONE=Asia/Seoul
```

`.env`는 Git Repository에 Commit하지 않는다.

대신:

```text
.env.example
```

을 제공한다.

---

# 28. Initial Directory Structure

초기 구조는 다음을 기본 방향으로 한다.

```text
security-daily/
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── src/
│   │   └── security_daily/
│   │
│   │       ├── domain/
│   │       │
│   │       ├── application/
│   │       │
│   │       ├── infrastructure/
│   │       │   ├── database/
│   │       │   ├── llm/
│   │       │   └── crawler/
│   │       │
│   │       ├── agents/
│   │       │   ├── selector/
│   │       │   ├── summary/
│   │       │   ├── analyst/
│   │       │   └── quiz/
│   │       │
│   │       ├── api/
│   │       ├── jobs/
│   │       └── config/
│   │
│   ├── tests/
│   ├── alembic/
│   └── pyproject.toml
│
├── docs/
│   ├── PROJECT.md
│   └── ARCHITECTURE.md
│
├── .env.example
├── .gitignore
└── README.md
```

구현 과정에서 필요하지 않은 디렉터리를 미리 생성하지 않는다.

---

# 29. Logging

자동 Pipeline이기 때문에 Logging은 필수다.

최소 기록 대상:

```text
Pipeline 시작/종료

Crawler
- 요청 성공/실패
- 수집 기사 수

Selector
- 후보 기사 수
- 선정 기사 수

Summary
- 처리 기사
- 성공/실패

Analyst
- 처리 기사
- 성공/실패

Quiz
- 생성 문제 수

LLM
- 사용 모델
- 처리시간
- 오류

Database
- 저장 실패
```

기사 원문 전체나 LLM Prompt 전체를 일반 로그에 무분별하게 기록하지 않는다.

---

# 30. Testing Strategy

테스트는 Layer별로 분리한다.

## Domain / Application

```text
pytest
```

주요 테스트:

- Article 생성
- 중복 기사 처리
- 날짜 범위 처리
- 최대 3개 선정 검증
- 최대 3개 Quiz 검증
- Quiz 정답 Normalize
- 실패 상태 전환

## Infrastructure

- PostgreSQL Repository
- Ollama Adapter
- BoanNews Parser

Crawler 테스트에서는 실제 사이트에 매번 요청하지 않고 저장된 HTML Fixture 사용을 우선한다.

> **Fixture**
> 테스트를 위해 미리 준비해 둔 고정된 입력 데이터.

## API

FastAPI TestClient 등을 이용하여:

```text
GET /api/news/today
GET /api/news
GET /api/quizzes/today
POST /api/quizzes/{id}/answer
```

를 테스트한다.

---

# 31. Security Considerations

MVP는 개인용 시스템이지만 기본 보안 원칙을 적용한다.

- DB Password 코드 하드코딩 금지
- `.env` Git Commit 금지
- 사용자 입력 Validation
- SQLAlchemy Parameter Binding 사용
- 외부 URL 입력 제한
- Crawler Timeout 설정
- LLM Output Validation
- API Error Detail 과다 노출 방지
- 기사 원문 UI 직접 노출 금지

향후 외부 인터넷에 공개할 경우 Authentication, Rate Limiting, Reverse Proxy 등의 추가 보안 설계를 수행한다.

---

# 32. Copyright / Source Handling

기사 원문은 내부 AI 분석 및 개인 학습 목적으로 저장한다.

Frontend에는 기사 원문 전체를 재게시하지 않는다.

표시 대상:

```text
기사 제목
게시일
AI Summary
AI Security Insight
원문 링크
```

원문 확인은 원 출처로 이동하도록 한다.

---

# 33. Performance Requirements

주요 목표:

```text
Daily Pipeline
08:30 시작
08:50 이전 완료
```

즉:

```text
전체 처리시간 ≤ 20분
```

Local LLM 자원 사용량을 고려하여 모든 기사에 심층 분석을 수행하지 않는다.

```text
전체 기사
    ↓
Selector
    ↓
최대 3개
    ↓
심층 AI Processing
```

방식을 사용한다.

---

# 34. Future Docker Migration

현재 Windows Native 환경에서도 Container Migration을 고려한다.

따라서:

- DB URL 하드코딩 금지
- Ollama URL 하드코딩 금지
- OS 종속 경로 최소화
- 환경변수 기반 설정
- Stateless API 지향
- 영속 데이터 PostgreSQL 관리

원칙을 따른다.

향후:

```text
docker compose up -d
```

수준으로 주요 서비스를 실행할 수 있는 구조를 목표로 한다.

---

# 35. Architecture Summary

최종 시스템 처리 흐름:

```text
매일 08:30 KST
        ↓
전날 보안뉴스 전체 수집
        ↓
PostgreSQL 원본 저장
        ↓
News Selector Agent
(Phi-4 Mini 3.8B)
        ↓
학습 가치 높은 기사 최대 3개
        ↓
Summary Agent
(Gemma 3 4B)
        ↓
5문장 이내 핵심 요약
        ↓
기사 원문 + Summary
        ↓
Security Analyst Agent
(Qwen 3.5 9B)
        ↓
Security Insight
        ↓
Quiz Agent
(Llama 3.2 3B)
        ↓
단답형 최대 3문제
        ↓
PostgreSQL
        ↓
FastAPI
        ↓
Next.js
        ↓
08:50~09:00
Morning Security Briefing
```

---

# 36. 핵심 Architecture Decision

현재 Architecture v1.0에서 확정된 핵심 결정:

1. 초기 실행 환경은 Windows Native이다.
2. 향후 Home Server + Docker Compose 환경으로 이전한다.
3. Daily Pipeline은 매일 08:30 KST 실행한다.
4. 전날 00:00~23:59 KST 기사를 처리한다.
5. 08:50 이전 Pipeline 완료를 목표로 한다.
6. PostgreSQL에 기사 원문을 장기 보관한다.
7. SQLAlchemy 2.x와 Alembic을 사용한다.
8. Local LLM Runtime은 Ollama를 사용한다.
9. Agent와 LLM Model을 분리한다.
10. Agent별로 서로 다른 LLM을 설정할 수 있다.
11. 4개의 논리적 Agent를 사용한다.
12. 선정 뉴스는 최대 3개다.
13. 핵심 요약은 최대 5문장이다.
14. Quiz는 단답형 최대 3문제다.
15. 단답형 채점에는 LLM을 사용하지 않는다.
16. Pipeline은 단계별 실패 상태를 기록하고 재실행할 수 있도록 한다.
17. FastAPI와 Scheduler의 책임을 분리한다.
18. MVP에서는 Redis/Celery/Kafka 등의 추가 인프라를 사용하지 않는다.
19. 외부 의존성 설정은 환경변수로 관리한다.
20. 기사 원문 전체는 사용자 UI에 재게시하지 않는다.
21. 초기 News Selector 모델은 Phi-4 Mini 3.8B를 사용한다.
22. 초기 Summary 모델은 Gemma 3 4B를 사용한다.
23. 초기 Security Analyst 모델은 Qwen 3.5 9B를 사용한다.
24. 초기 Quiz 모델은 Llama 3.2 3B를 사용한다.
25. 모델은 환경변수를 통해 Agent별로 독립 교체 가능하게 한다.
26. 4개의 모델을 동시에 GPU 메모리에 상주시켜야 한다는 요구사항은 없다.
27. 실제 운영 전 한국어 품질, Structured Output 준수율, 처리시간, 메모리 사용량을 Smoke Test로 검증한다.

---

# 37. 구현 원칙

이 문서는 구현 과정의 기준점으로 사용한다.

구현 중 현재 설계와 다른 중요한 기술적 결정이 필요한 경우 임의로 구조를 변경하지 않는다.

다음 순서를 따른다.

```text
문제 발견
   ↓
대안 검토
   ↓
Architecture 영향 확인
   ↓
결정
   ↓
ARCHITECTURE.md 갱신
   ↓
구현
```

사소한 코드 수준의 결정까지 문서화하지 않는다.

**시스템 구조, 책임, 데이터 흐름 또는 향후 유지보수에 영향을 주는 결정만 Architecture에 반영한다.**
