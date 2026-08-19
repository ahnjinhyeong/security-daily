import { formatPublishedAt } from "@/lib/format";
import type { NewsArticle } from "@/lib/types";
import styles from "./dashboard.module.css";

function hasAnalysis(article: NewsArticle): boolean {
  const insight = article.insight;
  return Boolean(
    article.summary || insight.importance || insight.attack_scenario ||
      insight.security_actions?.length || insight.key_concepts?.length ||
      insight.related_security_info?.length,
  );
}

export function NewsCard({ article, compact = false }: { article: NewsArticle; compact?: boolean }) {
  const insight = article.insight;
  return (
    <article className={`${styles.newsCard} ${compact ? styles.newsCardCompact : ""}`}>
      <header className={styles.cardHeader}>
        <span className={styles.rank}>NEWS {String(article.rank).padStart(2, "0")}</span>
        <time dateTime={article.published_at}>{formatPublishedAt(article.published_at)}</time>
      </header>
      <h3>{article.title}</h3>
      {article.summary && (
        <div className={styles.summary}>
          <span className={styles.eyebrow}>핵심 요약</span>
          <p>{article.summary}</p>
        </div>
      )}

      {hasAnalysis(article) ? (
        <div className={styles.insight}>
          <div className={styles.insightTitle}>
            <span className={styles.signal} aria-hidden="true" />
            <h4>AI Security Insight</h4>
          </div>
          {insight.importance && (
            <section className={styles.insightBlock}>
              <h5>왜 중요한가?</h5><p>{insight.importance}</p>
            </section>
          )}
          {insight.attack_scenario && (
            <section className={styles.insightBlock}>
              <h5>실제 공격에서는 어떻게 활용되는가?</h5><p>{insight.attack_scenario}</p>
            </section>
          )}
          {!!insight.security_actions?.length && (
            <section className={styles.insightBlock}>
              <h5>보안 담당자가 확인해야 할 것은?</h5>
              <ul className={styles.checklist}>
                {insight.security_actions.map((action) => <li key={action}>{action}</li>)}
              </ul>
            </section>
          )}
          {!!insight.key_concepts?.length && (
            <section className={styles.insightBlock}>
              <h5>기억해야 할 핵심 개념</h5>
              <dl className={styles.concepts}>
                {insight.key_concepts.map((concept, index) => (
                  <div key={`${concept.name ?? "concept"}-${index}`}>
                    <dt>{concept.name ?? "핵심 개념"}</dt>
                    <dd>{concept.description ?? Object.values(concept).filter(Boolean).join(" · ")}</dd>
                  </div>
                ))}
              </dl>
            </section>
          )}
          {!!insight.related_security_info?.length && (
            <section className={styles.insightBlock}>
              <h5>관련 기술 / 취약점 / CVE</h5>
              <div className={styles.tags}>
                {insight.related_security_info.map((item, index) => (
                  <span key={`${item.type}-${item.value}-${index}`}>
                    {item.type && <small>{item.type}</small>}{item.value ?? Object.values(item).filter(Boolean).join(" · ")}
                  </span>
                ))}
              </div>
            </section>
          )}
        </div>
      ) : (
        <div className={styles.pending}>AI 분석이 아직 완료되지 않았습니다.</div>
      )}
      <a className={styles.sourceLink} href={article.url} target="_blank" rel="noopener noreferrer">
        보안뉴스 원문 보기 <span aria-hidden="true">↗</span>
        <span className={styles.srOnly}>(새 창)</span>
      </a>
    </article>
  );
}
