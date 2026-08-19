import Link from "next/link";
import type { NewsBriefing, NewsDate, Quiz } from "@/lib/types";
import { formatDate } from "@/lib/format";
import { NewsCard } from "./NewsCard";
import { QuizCard } from "./QuizCard";
import { EmptyState, ErrorState } from "./SectionState";
import styles from "./dashboard.module.css";

type DataResult<T> = { data: T | null; error: boolean };

export function Dashboard({
  morning, dates, archive, quizzes, archiveDate, quizDate,
}: {
  morning: DataResult<NewsBriefing>;
  dates: DataResult<NewsDate[]>;
  archive: DataResult<NewsBriefing>;
  quizzes: DataResult<Quiz[]>;
  archiveDate: string | null;
  quizDate: string | null;
}) {
  const displayDate = morning.data?.date;
  const quizLabel = quizDate ? `${formatDate(quizDate)} Quiz` : "오늘의 Quiz";
  return <div className={styles.shell}>
    <header className={styles.header}>
      <div className={styles.headerInner}>
        <a className={styles.brand} href="#top" aria-label="Security Daily 처음으로">
          <span className={styles.brandMark}>SD</span>
          <span><strong>Security Daily</strong><small>Security Knowledge Briefing</small></span>
        </a>
        <nav aria-label="주요 섹션">
          <a href="#briefing">오늘의 브리핑</a><a href="#archive">지난 뉴스</a><a href="#quiz">오늘의 Quiz</a>
        </nav>
        {displayDate && <div className={styles.headerDate}><span>BRIEFING DATE</span><time dateTime={displayDate}>{formatDate(displayDate)}</time></div>}
      </div>
    </header>

    <main id="top" className={styles.main}>
      <section id="briefing" className={styles.section}>
        <div className={styles.sectionHeader}>
          <div><span className={styles.eyebrow}>MORNING SECURITY BRIEFING</span><h1>오늘 알아야 할 보안 이슈</h1><p>수집된 보안뉴스에서 학습 가치가 높은 이슈를 선별하고 분석했습니다.</p></div>
          {morning.data && <div className={styles.count}><strong>{morning.data.count}</strong><span>SELECTED<br />ARTICLES</span></div>}
        </div>
        {morning.error ? <ErrorState title="오늘의 브리핑을 불러오지 못했습니다." /> : morning.data?.articles.length ? (
          <div className={styles.morningGrid}>{morning.data.articles.map((item) => <NewsCard key={item.id} article={item} />)}</div>
        ) : <EmptyState title="아직 오늘의 브리핑이 준비되지 않았습니다." description="Daily Pipeline 완료 후 다시 확인해 주세요." />}
      </section>

      <section id="archive" className={styles.section}>
        <div className={styles.sectionHeader}><div><span className={styles.eyebrow}>NEWS ARCHIVE</span><h2>지난 뉴스</h2><p>날짜별로 축적된 보안 이슈와 분석을 다시 확인하세요.</p></div></div>
        <div className={styles.archiveLayout}>
          <aside className={styles.datePanel} aria-label="뉴스 날짜 선택">
            <h3>날짜 선택</h3>
            {dates.error ? <p className={styles.smallError}>날짜를 불러오지 못했습니다.</p> : dates.data?.length ? (
              <div className={styles.dateList}>{dates.data.map((item) => (
                <Link key={item.date} href={`/?date=${item.date}#archive`} className={item.date === archiveDate ? styles.activeDate : ""} aria-current={item.date === archiveDate ? "date" : undefined}>
                  <time dateTime={item.date}>{formatDate(item.date)}</time><span>{item.article_count}건</span>
                </Link>
              ))}</div>
            ) : <p className={styles.muted}>저장된 지난 뉴스가 없습니다.</p>}
          </aside>
          <div className={styles.archiveContent}>
            {archive.data && <div className={styles.archiveHeading}><h3>{formatDate(archive.data.date)}</h3><span>{archive.data.count}개의 선정 뉴스</span></div>}
            {archive.error ? <ErrorState title="선택한 날짜의 뉴스를 불러오지 못했습니다." /> : archive.data?.articles.length ? (
              <div className={styles.archiveList}>{archive.data.articles.map((item) => <NewsCard key={item.id} article={item} compact />)}</div>
            ) : <EmptyState title="이 날짜에 선정된 뉴스가 없습니다." description="다른 날짜를 선택해 주세요." />}
          </div>
        </div>
      </section>

      <section id="quiz" className={styles.section}>
        <div className={styles.sectionHeader}><div><span className={styles.eyebrow}>KNOWLEDGE CHECK</span><h2>{quizLabel}</h2><p>오늘 학습한 핵심 개념을 단답형 문제로 확인해 보세요.</p></div>{quizzes.data && <div className={styles.count}><strong>{quizzes.data.length}</strong><span>QUIZ<br />QUESTIONS</span></div>}</div>
        {quizzes.error ? <ErrorState title="Quiz를 불러오지 못했습니다." /> : quizzes.data?.length ? (
          <div className={styles.quizGrid}>{quizzes.data.map((quiz, index) => <QuizCard key={quiz.id} quiz={quiz} index={index} />)}</div>
        ) : <EmptyState title="오늘 생성된 Quiz가 없습니다." description="분석 결과가 준비되면 Quiz가 제공됩니다." />}
      </section>
    </main>
    <footer className={styles.footer}><div><span>Security Daily</span><p>보안뉴스 원문과 Local AI 분석을 기반으로 한 개인 학습 Dashboard</p></div><a href="#top">맨 위로 ↑</a></footer>
  </div>;
}
