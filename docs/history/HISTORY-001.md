# HISTORY-001

## 기간

- 2026-08-19

## 완료 Epic

- EPIC-001 — 개발 환경 초기화
- EPIC-002 — PostgreSQL 기반 구성
- EPIC-003 — 보안뉴스 수집 기능

## 주요 구현 내용

- Git 저장소와 `.gitignore`, `.env.example`을 구성했다.
- `backend/`에 uv 기반 Python 프로젝트와 FastAPI `src` layout, `/health` 엔드포인트, pytest 환경을 구성했다.
- `frontend/`에 Next.js와 TypeScript 기반의 최소 실행 환경을 구성했다.
- 환경설정 로딩을 중앙화하고 SQLAlchemy 2.x의 Declarative Base, Engine, Session Factory와 DB Session 관리 구조를 구성했다.
- PostgreSQL 드라이버와 Alembic을 추가하고 애플리케이션의 SQLAlchemy Metadata를 Migration 환경에 연결했다.
- Article Domain Model, `articles` SQLAlchemy Model, Alembic Migration과 Article Repository를 구현했다.
- 보안뉴스 목록·상세 Parser, DTO, 설정, 오류 정의, EUC-KR HTTP Client와 재시도·실패 처리 구조를 구현했다.
- 전날 KST 범위의 페이지 순회와 `idx` 중복 제거, 정제된 본문 수집 및 저장을 수행하는 `CollectDailyNews` Use Case를 구현했다.
- Fixture 기반 Unit Test, PostgreSQL Integration Test, 실제 보안뉴스 사이트 Smoke Test를 분리했다.

## 주요 변경 파일

- `.gitignore`, `.env.example`
- `backend/pyproject.toml`, `backend/uv.lock`
- `backend/src/security_daily/api/`
- `backend/src/security_daily/config/`
- `backend/src/security_daily/domain/`
- `backend/src/security_daily/application/collect_daily_news.py`
- `backend/src/security_daily/infrastructure/database/`
- `backend/src/security_daily/infrastructure/crawler/`
- `backend/alembic.ini`, `backend/alembic/`
- `backend/tests/`
- `frontend/`
- `docs/ARCHITECTURE.md`

## Architecture 변경

- `articles`에 `source`와 `source_article_id`를 추가했다.
- 기사 URL과 `(source, source_article_id)` 조합에 각각 UNIQUE 제약을 적용했다.
- `articles.content`에는 원문 HTML이 아닌 AI 분석용 정제 본문 텍스트를 저장하고, MVP에서는 이미지 URL을 저장하지 않도록 명시했다.
- 그 외 EPIC-001~003 범위의 Architecture 변경은 없다.

## 주요 문제와 해결

- PowerShell 실행 정책으로 `npm.ps1` 실행이 제한되어 시스템 정책을 변경하지 않고 `npm.cmd`를 사용했다.
- EPIC-002 당시 로컬 PostgreSQL이 준비되지 않아 실제 연결 테스트를 보류했으며, 사용자·Database와 `DATABASE_URL` 설정 후 Integration Test와 Alembic 연결을 다시 검증했다.
- 보안뉴스 페이지의 EUC-KR 인코딩과 복수 기사 흐름을 고려해 명시적 디코딩, 페이지 전체 기준 날짜 판단, `idx` 중복 제거를 적용했다.
- 외부 사이트 의존 테스트가 기본 테스트를 불안정하게 만들지 않도록 실제 사이트 Smoke Test를 별도 Marker와 실행 조건으로 분리했다.

## 테스트 결과

- Backend 최소 환경: FastAPI import, `/health`, pytest와 실제 uvicorn 실행을 확인했다.
- Frontend 최소 환경: 의존성 설치, ESLint와 Next.js Production Build를 통과했다.
- PostgreSQL: 실제 Database 연결과 SQLAlchemy Engine·Session 구성을 확인했다.
- 최종 Backend Unit Test: `24 passed`
- 최종 Backend 전체 기본 테스트: `27 passed, 1 skipped` — 실제 사이트 Smoke Test는 기본 실행에서 제외된다.
- 실제 사이트 Smoke Test 별도 실행: `1 passed`
- Alembic: `0001_create_articles (head)` 적용 및 `alembic check`에서 추가 Migration 차이 없음을 확인했다.

## 현재 상태

- Backend와 Frontend의 최소 개발 환경이 준비되어 있다.
- PostgreSQL 연결, ORM, Migration 기반과 `articles` 테이블이 준비되어 있다.
- 보안뉴스의 전날 기사 수집·정제·중복 제거·저장 흐름과 관련 테스트가 구현되어 있다.
- 일일 실행 Scheduler와 이후 LLM 분석·선별·퀴즈 기능은 아직 구현하지 않았다.

## 다음 작업

- 수집 Use Case를 매일 08:30 KST에 실행할 Application Runner 또는 Scheduler 연결
- 수집 결과를 사용하는 기사 선별 및 LLM Agent Epic 설계·구현
