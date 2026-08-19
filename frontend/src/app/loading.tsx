import styles from "@/components/dashboard.module.css";

export default function Loading() {
  return <main className={styles.loadingShell} aria-label="Dashboard를 불러오는 중"><div className={styles.loadingHeader} />{[1,2,3].map((section) => <section className={styles.loadingSection} key={section}><div className={styles.loadingTitle} /><div className={styles.loadingGrid}><div className={styles.skeleton} /><div className={styles.skeleton} /></div></section>)}</main>;
}
