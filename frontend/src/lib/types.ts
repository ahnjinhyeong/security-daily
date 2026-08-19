export type KeyConcept = {
  name?: string;
  description?: string;
  [key: string]: string | undefined;
};

export type RelatedSecurityInfo = {
  type?: string;
  value?: string;
  [key: string]: string | undefined;
};

export type NewsInsight = {
  importance: string | null;
  attack_scenario: string | null;
  security_actions: string[] | null;
  key_concepts: KeyConcept[] | null;
  related_security_info: RelatedSecurityInfo[] | null;
};

export type NewsArticle = {
  id: number;
  rank: number;
  title: string;
  url: string;
  published_at: string;
  summary: string | null;
  insight: NewsInsight;
};

export type NewsBriefing = {
  date: string;
  count: number;
  articles: NewsArticle[];
};

export type NewsDate = {
  date: string;
  article_count: number;
};

export type Quiz = {
  id: number;
  article_id: number;
  question: string;
};

export type QuizAnswerResult = {
  correct: boolean;
  correct_answer: string;
  explanation: string;
};
