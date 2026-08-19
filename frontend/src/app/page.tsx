import { Dashboard } from "@/components/Dashboard";
import { getNewsByDate, getNewsDates, getQuizzesByDate, getTodayNews, getTodayQuizzes } from "@/lib/api";
import { isIsoDate } from "@/lib/format";

export const dynamic = "force-dynamic";
type PageProps = { searchParams: Promise<{ date?: string }> };

function result<T>(settled: PromiseSettledResult<T>): { data: T | null; error: boolean } {
  return settled.status === "fulfilled" ? { data: settled.value, error: false } : { data: null, error: true };
}

export default async function Home({ searchParams }: PageProps) {
  const requestedDate = (await searchParams).date;
  const selectedDate = isIsoDate(requestedDate) ? requestedDate : null;
  const [morningResult, datesResult, quizResult] = await Promise.allSettled([
    getTodayNews(), getNewsDates(), selectedDate ? getQuizzesByDate(selectedDate) : getTodayQuizzes(),
  ]);
  const dates = result(datesResult);
  const archiveDate = selectedDate ?? dates.data?.[0]?.date ?? null;
  const archiveResult = archiveDate ? await Promise.allSettled([getNewsByDate(archiveDate)]) : null;
  const archive = archiveResult ? result(archiveResult[0]) : { data: null, error: dates.error };

  return <Dashboard morning={result(morningResult)} dates={dates} archive={archive} quizzes={result(quizResult)} archiveDate={archiveDate} quizDate={selectedDate} />;
}
