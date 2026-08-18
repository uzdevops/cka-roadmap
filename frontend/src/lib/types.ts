/** Mirrors the backend Pydantic schemas. */

export type Role = 'student' | 'admin';

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: Role;
  is_active: boolean;
  target_exam_date: string | null;
  daily_study_minutes: number;
  avatar_url: string | null;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthConfig {
  google_oauth_enabled: boolean;
  registration_enabled: boolean;
  phase_unlock_enforced: boolean;
}

export interface LessonSummary {
  id: number;
  slug: string;
  title: string;
  summary: string;
  order_index: number;
  estimated_minutes: number;
  day_of_week: number | null;
  is_placeholder: boolean;
  completed: boolean;
}

export interface LessonDetail extends LessonSummary {
  content: string;
  /** A YouTube link, shown as a player above the prose. Null for most lessons. */
  video_url?: string | null;
  week_id: number;
  week_number: number | null;
  week_title: string | null;
  phase_slug: string | null;
  phase_title: string | null;
  prev_slug: string | null;
  next_slug: string | null;
  content_translated: boolean;
  quiz_slug: string | null;
  quiz_pass_score: number | null;
  quiz_best_score: number | null;
  quiz_passed: boolean;
  quiz_attempts: number;
  references: { title: string; url: string }[];
}

export interface Week {
  id: number;
  number: number;
  title: string;
  description: string;
  order_index: number;
  lessons: LessonSummary[];
  completed_lessons: number;
  total_lessons: number;
}

export interface PhaseSummary {
  id: number;
  slug: string;
  title: string;
  description: string;
  order_index: number;
  exam_domain: string | null;
  exam_weight: number;
  week_start: number;
  week_end: number;
  color: string;
  total_lessons: number;
  completed_lessons: number;
  progress_percent: number;
  locked: boolean;
}

export interface PhaseDetail extends PhaseSummary {
  weeks: Week[];
  quizzes: QuizSummary[];
  labs: LabSummary[];
}

export interface QuestionOption {
  id: string;
  text: string;
}

export type QuestionType = 'single_choice' | 'multi_select' | 'fill_command';

export interface QuestionPublic {
  id: number;
  type: QuestionType;
  prompt: string;
  options: QuestionOption[];
  points: number;
  order_index: number;
}

export interface QuizSummary {
  id: number;
  slug: string;
  title: string;
  description: string;
  pass_score: number;
  time_limit_minutes: number | null;
  order_index: number;
  question_count: number;
  phase_slug: string | null;
  best_score: number | null;
  attempt_count: number;
  locked: boolean;
}

export interface QuizDetail extends QuizSummary {
  questions: QuestionPublic[];
}

export interface AnswerResult {
  question_id: number;
  prompt: string;
  type: QuestionType;
  is_correct: boolean;
  points_earned: number;
  points_possible: number;
  given: string[];
  correct: string[];
  explanation: string;
}

export interface QuizResult {
  attempt_id: number;
  quiz_slug: string;
  quiz_title: string;
  score: number;
  passed: boolean;
  correct_count: number;
  question_count: number;
  earned_points: number;
  total_points: number;
  results: AnswerResult[];
  completed_at: string | null;
}

export interface AttemptSummary {
  id: number;
  quiz_id: number;
  quiz_slug: string | null;
  quiz_title: string | null;
  score: number;
  passed: boolean;
  correct_count: number;
  question_count: number;
  completed_at: string | null;
}

export type LabStatus = 'not_started' | 'in_progress' | 'completed';

export interface LabSummary {
  id: number;
  slug: string;
  title: string;
  description: string;
  difficulty: string;
  estimated_minutes: number;
  order_index: number;
  phase_slug: string | null;
  status: LabStatus;
}

export interface LabTask {
  title: string;
  instructions: string;
  solution: string;
  verification: string;
}

export interface LabDetail extends LabSummary {
  scenario: string;
  environment_setup: string;
  cleanup: string;
  tasks: LabTask[];
}

export interface StreakInfo {
  current_streak: number;
  longest_streak: number;
  active_days: number;
  last_active: string | null;
}

export interface PhaseProgress {
  phase_slug: string;
  phase_title: string;
  order_index: number;
  exam_weight: number;
  color: string;
  total_lessons: number;
  completed_lessons: number;
  progress_percent: number;
  quiz_average: number | null;
}

export interface QuizScorePoint {
  attempt_id: number;
  quiz_slug: string;
  quiz_title: string;
  score: number;
  completed_at: string | null;
}

export interface ReadinessBreakdown {
  domain: string;
  weight: number;
  score: number | null;
  contribution: number;
}

export interface ExamReadiness {
  score: number;
  covered_weight: number;
  breakdown: ReadinessBreakdown[];
  verdict: string;
}

export interface Dashboard {
  total_lessons: number;
  completed_lessons: number;
  overall_percent: number;
  total_labs: number;
  completed_labs: number;
  total_quizzes: number;
  attempted_quizzes: number;
  quiz_average: number | null;
  streak: StreakInfo;
  phases: PhaseProgress[];
  recent_scores: QuizScorePoint[];
  readiness: ExamReadiness;
  target_exam_date: string | null;
  days_until_exam: number | null;
  daily_study_minutes: number;
}

export interface WeeklyScheduleDay {
  day: number;
  label: string;
  kind: 'lesson' | 'lab' | 'review';
  items: Record<string, unknown>[];
}

export interface WeeklySchedule {
  week_number: number;
  week_title: string;
  phase_slug: string;
  days: WeeklyScheduleDay[];
}

/* --- Admin --------------------------------------------------------------- */

export interface AdminStats {
  users: number;
  students: number;
  admins: number;
  phases: number;
  weeks: number;
  lessons: number;
  quizzes: number;
  questions: number;
  labs: number;
  quiz_attempts: number;
  completed_lessons: number;
}

/** { "uz": { title, summary, content } } - English lives in the base fields. */
export type Translations = Record<string, Record<string, unknown>>;

export interface AdminLesson {
  id: number;
  week_id: number;
  slug: string;
  title: string;
  summary: string;
  content: string;
  video_url?: string | null;
  order_index: number;
  estimated_minutes: number;
  day_of_week: number | null;
  is_published: boolean;
  is_placeholder: boolean;
  translations: Translations;
}

export interface QuestionWrite {
  key: string;
  type: QuestionType;
  prompt: string;
  options: QuestionOption[];
  correct_options: string[];
  accepted_answers: string[];
  explanation: string;
  points: number;
  order_index: number;
  translations?: Translations;
}

export interface AdminQuiz {
  id: number;
  phase_id: number;
  week_id: number | null;
  slug: string;
  title: string;
  description: string;
  pass_score: number;
  time_limit_minutes: number | null;
  order_index: number;
  is_published: boolean;
  translations: Translations;
  questions: QuestionWrite[];
}

export interface AdminLab {
  id: number;
  phase_id: number;
  week_id: number | null;
  slug: string;
  title: string;
  description: string;
  scenario: string;
  difficulty: string;
  estimated_minutes: number;
  environment_setup: string;
  cleanup: string;
  tasks: LabTask[];
  order_index: number;
  is_published: boolean;
  translations: Translations;
}

export interface StructurePhase {
  id: number;
  slug: string;
  title: string;
  order_index: number;
  weeks: { id: number; number: number; title: string }[];
}

export interface AdminUser {
  id: number;
  email: string;
  full_name: string | null;
  role: Role;
  is_active: boolean;
  created_at: string;
  last_active: string | null;
  completed_lessons: number;
  total_lessons: number;
  progress_percent: number;
  quiz_attempts: number;
  quiz_average: number | null;
  completed_labs: number;
  current_streak: number;
}

export interface AdminUserCreate {
  email: string;
  password: string;
  full_name?: string | null;
  role?: Role;
}
