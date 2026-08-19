import styles from "./dashboard.module.css";

export function EmptyState({ title, description }: { title: string; description: string }) {
  return <div className={styles.sectionState}><span aria-hidden="true">—</span><h3>{title}</h3><p>{description}</p></div>;
}

export function ErrorState({ title }: { title: string }) {
  return <div className={`${styles.sectionState} ${styles.errorState}`} role="alert"><span aria-hidden="true">!</span><h3>{title}</h3><p>잠시 후 페이지를 새로고침해 주세요.</p></div>;
}
