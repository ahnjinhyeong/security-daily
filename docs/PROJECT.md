# Security Daily — PROJECT

## 1. 프로젝트 개요

**Security Daily**는 매일 08:30 KST에 보안 전문 매체에서 전날 00:00~23:59 KST에 게시된 뉴스를 자동 수집하고, Local LLM 기반 Multi-Agent Pipeline을 이용하여 학습 가치가 높은 뉴스를 선별·요약·분석한 뒤 퀴즈와 함께 PostgreSQL에 축적하는 **개인용 보안 뉴스 학습 및 지식 축적 시스템**이다.

단순한 뉴스 크롤러나 AI 요약 서비스를 만드는 것이 목적이 아니다.

매일 쏟아지는 보안 정보 중 실제로 학습할 가치가 높은 정보를 최대 3개로 압축하고,

**수집 → 선별 → 요약 → 분석 → 학습 → 퀴즈 → 축적 → 복습**

으로 이어지는 지식의 선순환 구조를 구축하는 것이 핵심 목표다.

---

## 2. 프로젝트 목적

### 2.1 사용자 관점

매일 많은 보안 뉴스를 직접 탐색하는 대신 시스템이 자동으로 뉴스를 수집하고, 그중 학습 가치가 높은 기사만 최대 3개 제공한다.

사용자는 각 기사에서 다음 내용을 빠르게 학습한다.

- 무슨 일이 발생했는가?
- 왜 중요한가?
- 실제 공격에서는 어떻게 활용될 수 있는가?
- 보안 담당자는 무엇을 확인해야 하는가?
- 어떤 보안 개념을 기억해야 하는가?
- 관련 기술·취약점·CVE는 무엇인가?

학습 후에는 최대 3개의 단답형 퀴즈를 통해 핵심 내용을 다시 회상한다.

과거 뉴스와 학습 기록은 날짜별로 축적하여 지속적으로 복습할 수 있도록 한다.

### 2.2 포트폴리오 관점

다음 역량을 실제 동작하는 시스템을 통해 보여주는 것을 목표로 한다.

- Web Crawling
- Local LLM 활용
- Multi-Agent Workflow 설계
- Prompt Engineering
- AI 기반 정보 가공
- Next.js Frontend
- FastAPI Backend
- PostgreSQL 데이터 모델링
- REST API 설계
- ORM 및 DB Migration
- 반응형 UI
- 자동화된 일일 처리 Pipeline
- Git/GitHub 기반 프로젝트 관리

---

# 3. 뉴스 데이터 수집

## 3.1 수집 대상

보안뉴스 단일 사이트를 대상으로 한다.

- 사이트: `boannews.com`
- 다른 뉴스 사이트는 MVP 범위에 포함하지 않는다.

## 3.2 수집 정책

시스템은 매일 08:30 KST에 자동으로 실행되어 전날 00:00~23:59 KST에 게시된 보안뉴스 기사를 수집한다.

수집 대상 데이터:

- 기사 제목
- 원문 URL
- 게시일시
- 기사 본문
- 데이터 수집 시각

기사의 게시일과 시스템의 수집 시각은 별도로 관리한다.

동일한 기사가 중복 저장되지 않도록 원문 URL을 고유하게 관리한다.

## 3.3 원문 사용 원칙

기사 원문은 AI 분석을 위한 내부 데이터로 사용한다.

사용자 UI에서는 원문 전체를 재게시하지 않고 다음 정보만 제공한다.

- 기사 제목
- AI 핵심 요약
- AI Security Insight
- 원문 링크

---

# 4. 오늘의 보안 뉴스 선정

전날 게시되어 수집된 모든 기사를 사용자에게 제공하지 않는다.

AI가 전날 게시 기사 중 **학습 가치가 높은 기사를 최대 3개 선정**한다.

유의미한 기사가 3개 미만이라면 억지로 3개를 채우지 않는다.

예:

```text
전날 게시 기사 12개
      ↓
AI 평가
      ↓
학습 가치가 충분한 기사 2개
      ↓
오늘의 보안 뉴스 2개
```

## 4.1 선정 기준

News Selector Agent는 다음 요소를 종합적으로 고려한다.

1. 실무 보안 중요도
2. 실제 공격 및 취약점 관련성
3. 영향 범위
4. 보안 학습 가치
5. 기사 간 내용 중복성
6. 단순 홍보·행사·업계 동향 여부

각 선정 결과에는 다음 정보를 기록한다.

- 선정 여부
- 선정 순위
- 선정 점수
- 선정 이유
- 사용된 AI 모델

---

# 5. Local LLM Multi-Agent System

시스템은 역할이 명확하게 분리된 **4개의 논리적 AI Agent**를 사용한다.

Agent 수를 늘리기 위한 인위적인 분리가 아니라, 실제 정보 처리 단계의 책임을 기준으로 분리한다.

```text
전날 게시 기사 전체
      ↓
News Selector Agent
      ↓
최대 3개
      ↓
Summary Agent
      ↓
Security Analyst Agent
      ↓
Quiz Agent
```

**Agent 4개가 반드시 서로 다른 LLM 모델 4개를 의미하지는 않는다.**

하나의 Local LLM을 여러 역할에서 사용할 수도 있으며, 필요하면 역할별로 다른 모델을 사용할 수 있도록 확장 가능하게 설계한다.

---

# 6. News Selector Agent

### 역할

> **"오늘 무엇을 볼 것인가?"**

전날 게시되어 수집된 기사들을 평가하여 학습 가치가 높은 기사를 최대 3개 선정한다.

### 입력

- 전날 게시 기사 후보
- 기사 제목
- 기사 내용
- 게시일 등 필요한 메타데이터

### 출력

- 선정 기사
- 선정 순위
- 선정 점수
- 선정 이유

---

# 7. Summary Agent

### 역할

> **"무슨 일이 있었는가?"**

선정된 기사 원문의 핵심 사실관계를 압축한다.

### 입력

- 기사 원문

### 출력

- 핵심 요약 최대 5문장

### 원칙

- 기사에서 확인되는 사실을 중심으로 작성한다.
- 불필요한 반복 표현을 제거한다.
- 핵심 사건·대상·원인·영향을 우선한다.
- 중요한 CVE, 제품명, 기관명 등의 정보는 가능한 한 유지한다.
- 임의의 보안 분석이나 조언을 추가하지 않는다.
- 기사에서 확인되지 않는 사실을 생성하지 않는다.

---

# 8. Security Analyst Agent

### 역할

> **"이 기사에서 보안 관점으로 무엇을 이해하고 기억해야 하는가?"**

Summary Agent와 역할을 명확하게 분리한다.

Summary Agent는 사실관계 압축을 담당하고, Security Analyst Agent는 보안적 의미와 학습 포인트를 분석한다.

### 입력

Security Analyst Agent는 정보 손실과 잘못된 추론을 줄이기 위해 다음 두 정보를 모두 사용한다.

```text
기사 원문
+
Summary Agent 요약본
```

사실 판단에서는 기사 원문을 우선적인 근거로 사용하며, Summary는 핵심 맥락 파악을 위한 보조 정보로 사용한다.

### 출력 — AI Security Insight

#### 1. 왜 중요한가?

보안 관점에서 해당 뉴스가 갖는 의미를 설명한다.

- 권장 분량: 2~3문장

#### 2. 실제 공격에서는 어떻게 활용되는가?

공격자가 해당 취약점이나 기술을 어떤 공격 흐름에서 활용할 수 있는지 설명한다.

- 권장 분량: 2~4문장

기사에 실제 악용 사례가 존재하는 경우와 AI가 보안 지식을 기반으로 분석한 가능한 공격 시나리오는 명확하게 구분한다.

#### 3. 보안 담당자가 확인해야 할 것은?

실제 보안 담당자가 확인하거나 대응해야 하는 Action Item을 제공한다.

- 최대 5개

#### 4. 내가 기억해야 할 핵심 개념은?

장기적으로 기억할 가치가 높은 보안 개념을 추출한다.

- 최대 5개
- `개념명 + 간단한 설명` 형태

예:

```text
RCE
→ Remote Code Execution. 원격에서 대상 시스템에 임의 코드를 실행할 수 있는 취약점.
```

#### 5. 관련 기술 / 취약점 / CVE

기사와 관련된 다음 정보를 구조화한다.

- CVE
- 보안 기술
- 공격 기법
- 제품
- 취약점 유형

최대 5개를 기본 기준으로 한다.

기사에서 확인할 수 없는 CVE나 제품 등의 사실을 임의로 생성하지 않는다.

---

# 9. Quiz Agent

### 역할

> **"오늘 배운 내용 중 무엇을 기억하고 있는가?"**

오늘 선정된 뉴스와 AI 분석 결과를 이용하여 복습 문제를 생성한다.

### 문제 형식

**단답형으로 고정한다.**

객관식과 서술형은 MVP 범위에서 제외한다.

### 문제 수

**하루 최대 3문제**

학습할 가치가 있는 문제가 3개 미만이면 억지로 문제 수를 채우지 않는다.

### 입력

- 기사 제목
- 핵심 요약
- AI Security Insight

### 출력

각 문제는 다음 데이터를 가진다.

- 문제
- 대표 정답
- 허용 가능한 다른 정답
- 간단한 해설

예:

```text
Q. 원격에서 대상 시스템에 임의의 코드를
실행할 수 있는 취약점을 무엇이라고 하는가?

대표 정답:
RCE

허용 정답:
- RCE
- Remote Code Execution
- 원격 코드 실행
```

단답형 채점은 LLM을 다시 호출하지 않고 애플리케이션에서 정답 및 허용 정답을 비교하여 처리한다.

---

# 10. 데이터 저장

DBMS는 **PostgreSQL**을 사용한다.

Backend와 PostgreSQL 사이의 ORM은 **SQLAlchemy 2.x**, DB Schema Migration은 **Alembic​**을 사용한다.

### 주요 테이블

```text
articles
daily_selections
ai_analyses
quizzes
quiz_attempts
```

## 10.1 articles

크롤링한 원본 기사 데이터.

주요 데이터:

- ID
- 제목
- 원문 URL
- 기사 원문
- 게시일시
- 수집일시

원문 URL은 중복 저장을 방지하기 위해 `UNIQUE`로 관리한다.

## 10.2 daily_selections

News Selector Agent의 판단 결과.

주요 데이터:

- 기사 ID
- 선정 날짜
- 선정 순위
- 선정 점수
- 선정 이유
- 사용 모델

원본 기사 데이터와 AI의 판단 결과를 분리하기 위해 별도 테이블로 관리한다.

## 10.3 ai_analyses

Summary Agent와 Security Analyst Agent가 생성한 결과.

주요 데이터:

- 기사 ID
- 핵심 요약
- 중요성
- 공격 시나리오
- 보안 담당자 확인사항
- 핵심 개념
- 관련 기술 / 취약점 / CVE
- Summary 모델
- Analyst 모델

목록형·구조화된 AI 결과는 PostgreSQL `JSONB` 사용을 고려한다.

## 10.4 quizzes

Quiz Agent가 생성한 단답형 문제.

주요 데이터:

- 기사 ID
- 퀴즈 날짜
- 문제
- 대표 정답
- 허용 정답
- 해설
- 사용 모델

## 10.5 quiz_attempts

사용자의 실제 문제 풀이 기록.

주요 데이터:

- Quiz ID
- 사용자 답변
- 정답 여부
- 풀이 시각

---

# 11. 사용자 화면

서비스는 **원페이지 웹 애플리케이션**을 기본으로 한다.

핵심 UI는 세 영역으로 구성한다.

## 11.1 오늘의 보안 뉴스

오늘 선정된 최대 3개의 보안 뉴스를 제공한다.

각 뉴스에서 다음 내용을 확인할 수 있다.

- 기사 제목
- 게시일
- 핵심 요약
- AI Security Insight
- 원문 링크

## 11.2 지난 뉴스 보기

날짜를 선택하여 과거의 선정 뉴스와 AI 분석 내용을 다시 확인할 수 있다.

날짜별 데이터가 누적되는 개인 보안 지식 저장소 역할을 한다.

## 11.3 오늘의 퀴즈

오늘 학습한 내용을 기반으로 생성된 최대 3개의 단답형 문제를 제공한다.

사용자가 답을 제출하면:

- 정답/오답
- 대표 정답
- 해설

을 확인할 수 있다.

---

# 12. UI / UX 방향

전체 디자인 방향:

**Modern Security Knowledge Dashboard**

과도한 Cyberpunk 또는 Neon 디자인은 지양한다.

### 디자인 원칙

- Modern
- Minimal
- 높은 가독성
- 정보 중심 Dashboard
- Dark Neutral 계열 활용 검토
- 제한적인 Gradient
- 높은 Contrast의 Typography
- 카드 기반 정보 구조
- 일관된 여백과 시각적 계층

Desktop과 Mobile 모두 정상적으로 사용할 수 있는 **Responsive Web Design**을 구현한다.

레이아웃에는 CSS Grid와 Flexbox를 적극 활용한다.

---

# 13. 기술 스택

| 영역 | 기술 |
|---|---|
| Frontend | Next.js + TypeScript |
| Backend | FastAPI + Python |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| DB Migration | Alembic |
| Local LLM Runtime | Ollama |
| AI Architecture | Multi-Agent Pipeline |
| Crawling | Python 기반 HTTP/HTML Parsing |
| Version Control | Git |
| Repository | GitHub |
| CI | GitHub Actions 고려 |
| UI | Responsive Web Design |

Local LLM은 특정 모델에 강하게 종속되지 않는 구조를 지향한다.

Orca 계열 모델을 후보 중 하나로 고려하되, 실제 성능에 따라 Qwen/Llama/Gemma 등의 다른 Local LLM으로 교체할 수 있도록 설계한다.

---

# 14. 핵심 데이터 흐름

```text
boannews.com
      ↓
전날 00:00~23:59 KST 게시 기사 크롤링
      ↓
PostgreSQL 원본 저장
      ↓
News Selector Agent
      ↓
학습 가치 높은 뉴스 최대 3개
      ↓
Summary Agent
      ↓
핵심 요약 ≤ 5문장
      ↓
Security Analyst Agent
      ↓
AI Security Insight
      ↓
PostgreSQL 저장
      ↓
Quiz Agent
      ↓
단답형 최대 3문제
      ↓
PostgreSQL 저장
      ↓
FastAPI
      ↓
Next.js
      ↓
학습 / 퀴즈 / 복습
```

---

# 15. MVP 범위

초기 버전에서는 다음 기능에 집중한다.

- 보안뉴스 단일 사이트 크롤링
- 매일 08:30 KST 자동 수집
- 전날 게시 기사 AI 평가
- 뉴스 최대 3개 선정
- Local LLM 기반 기사 요약
- Local LLM 기반 Security Insight
- 단답형 퀴즈 최대 3개 자동 생성
- 자동 채점
- PostgreSQL 데이터 저장
- 오늘 뉴스 조회
- 날짜별 과거 뉴스 조회
- 퀴즈 풀이 기록
- PC / Mobile 반응형 UI

---

# 16. MVP에서 제외하는 기능

초기 구현에서는 다음 기능을 의도적으로 제외한다.

- 여러 뉴스 사이트 통합
- 사용자 회원가입
- 다중 사용자 시스템
- 소셜 로그인
- 댓글
- 뉴스 공유
- 실시간 뉴스 크롤링
- 모바일 Native App
- 서술형 AI 채점
- 객관식 퀴즈
- Vector DB
- RAG
- Knowledge Graph
- Redis
- Celery
- 과도하게 복잡한 Agent Framework

필요성이 확인될 경우 이후 버전에서 추가한다.

---

# 17. 개발 원칙

### 17.1 단순성

포트폴리오를 위한 불필요한 기술을 억지로 추가하지 않는다.

### 17.2 책임 분리

Crawler, AI Agent, Database, API, Frontend의 책임을 명확하게 분리한다.

### 17.3 AI의 선택적 사용

일반적인 프로그램 로직으로 해결할 수 있는 문제에 불필요하게 LLM을 사용하지 않는다.

### 17.4 추적 가능성

AI 결과에 사용된 모델 등의 정보를 기록하여 어떤 모델이 결과를 생성했는지 추적할 수 있도록 한다.

### 17.5 사실과 AI 추론의 구분

기사에서 직접 확인되는 사실과 LLM이 보안 지식을 바탕으로 도출한 분석을 구분한다.

### 17.6 확장 가능성

MVP는 작게 유지하되 특정 Local LLM이나 구현 방식에 과도하게 결합되지 않도록 설계한다.

---

# 18. 향후 확장 후보

MVP 완료 후 필요성이 확인되면 다음 기능을 검토한다.

- pgvector 기반 Semantic Search
- RAG 기반 과거 보안 지식 검색
- CVE 데이터베이스 연동
- MITRE ATT&CK Mapping
- 기사 및 개념 Tagging
- 반복 학습 기능
- 오답 기반 재출제
- 주간/월간 보안 지식 요약
- Local LLM 모델별 결과 비교
- AI Prompt/Model 평가 시스템
- Knowledge Graph
- 추가 보안 뉴스 소스

---

# 19. 프로젝트 핵심 정의

> **매일 08:30 KST에 보안뉴스의 전날 00:00~23:59 KST 게시 기사를 자동 수집하고, Local LLM 기반 Multi-Agent Pipeline이 학습 가치가 높은 뉴스를 최대 3개 선정하여 요약·보안 분석·퀴즈를 생성하고, 이를 PostgreSQL에 지속적으로 축적함으로써 매일 짧은 시간 안에 보안 지식을 학습하고 장기적으로 복습할 수 있도록 하는 개인용 Security Knowledge Learning System.**

---

## 문서 역할

`PROJECT.md`

> 무엇을 만들고 왜 만드는지, 어떤 기능과 범위를 갖는지를 정의한다.

`ARCHITECTURE.md`

> PROJECT.md의 요구사항을 실제 시스템으로 어떻게 구현할 것인지 기술적 구조와 설계 결정을 정의한다.

따라서 API Endpoint, Python Package 구조, FastAPI Layer, SQLAlchemy Model, Agent Interface, Scheduler 구현, Ollama Adapter, 구체적인 Crawler 구조 등은 이후 `ARCHITECTURE.md`에서 정의한다.
