'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FieldError, Input, Label, Select, Textarea } from '@/components/ui/field';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import type { AdminQuiz, QuestionType, QuestionWrite } from '@/lib/types';

export default function AdminQuizEditorPage({ params }: { params: { id: string } }) {
  const { t, href, fill } = useI18n();
  const types: { value: QuestionType; label: string }[] = [
    { value: 'single_choice', label: t.admin.typeSingle },
    { value: 'multi_select', label: t.admin.typeMulti },
    { value: 'fill_command', label: t.admin.typeFill },
  ];
  const [quiz, setQuiz] = useState<AdminQuiz | null>(null);
  const [questions, setQuestions] = useState<QuestionWrite[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void apiFetch<AdminQuiz>(`/admin/quizzes/${params.id}`)
      .then((data) => {
        setQuiz(data);
        setQuestions(data.questions);
      })
      .catch((err) => setError(err instanceof Error ? err.message : t.admin.loadFailed));
  }, [params.id]);

  const patchQuestion = (index: number, patch: Partial<QuestionWrite>) => {
    setQuestions((prev) => prev.map((q, i) => (i === index ? { ...q, ...patch } : q)));
  };

  const addQuestion = () => {
    setQuestions((prev) => [
      ...prev,
      {
        key: `q${String(prev.length + 1).padStart(2, '0')}-${Date.now().toString(36)}`,
        type: 'single_choice',
        prompt: '',
        options: [
          { id: 'a', text: '' },
          { id: 'b', text: '' },
        ],
        correct_options: ['a'],
        accepted_answers: [],
        explanation: '',
        points: 1,
        order_index: prev.length + 1,
      },
    ]);
  };

  const removeQuestion = (index: number) => {
    setQuestions((prev) => prev.filter((_, i) => i !== index));
  };

  const save = async () => {
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      const updated = await apiFetch<AdminQuiz>(`/admin/quizzes/${params.id}`, {
        method: 'PATCH',
        body: {
          title: quiz?.title,
          description: quiz?.description,
          pass_score: quiz?.pass_score,
          is_published: quiz?.is_published,
          questions: questions.map((q, i) => ({ ...q, order_index: i + 1 })),
        },
      });
      setQuestions(updated.questions);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.profile.saveFailed);
    } finally {
      setBusy(false);
    }
  };

  if (error && !quiz) return <p className="text-sm text-[var(--critical)]">{error}</p>;
  if (!quiz) return <p className="text-sm text-ink-muted">{t.common.loading}</p>;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link href={href('/admin/quizzes')} className="text-sm text-ink-muted hover:text-ink">
          {t.admin.backToQuizzes}
        </Link>
        <div className="flex items-center gap-3">
          {saved && <span className="text-sm text-[var(--good-text)]">{t.common.saved}</span>}
          <Button onClick={save} disabled={busy}>
            {busy ? t.common.saving : t.admin.saveQuiz}
          </Button>
        </div>
      </div>

      <FieldError>{error}</FieldError>

      <Card className="mb-6">
        <CardContent className="grid gap-4 pt-5 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Label htmlFor="title">{t.admin.title}</Label>
            <Input
              id="title"
              value={quiz.title}
              onChange={(e) => setQuiz({ ...quiz, title: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2">
            <Label htmlFor="description">{t.admin.description}</Label>
            <Input
              id="description"
              value={quiz.description}
              onChange={(e) => setQuiz({ ...quiz, description: e.target.value })}
            />
          </div>
          <div>
            <Label htmlFor="pass">{t.admin.passScore}</Label>
            <Input
              id="pass"
              type="number"
              min={0}
              max={100}
              value={quiz.pass_score}
              onChange={(e) => setQuiz({ ...quiz, pass_score: Number(e.target.value) })}
            />
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 text-sm text-ink-secondary">
              <input
                type="checkbox"
                className="h-4 w-4 accent-[var(--accent)]"
                checked={quiz.is_published}
                onChange={(e) => setQuiz({ ...quiz, is_published: e.target.checked })}
              />
              {t.admin.publishedLabel}
            </label>
          </div>
        </CardContent>
      </Card>

      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="font-semibold text-ink">
          {fill(t.admin.questionsHeading, { count: questions.length })}
        </h2>
        <Button size="sm" variant="secondary" onClick={addQuestion}>
          {t.admin.addQuestion}
        </Button>
      </div>

      <p className="mb-4 text-sm text-ink-muted">{t.admin.questionsNote}</p>

      <ol className="flex flex-col gap-4">
        {questions.map((question, index) => (
          <li key={question.key}>
            <Card>
              <CardContent className="pt-5">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <span className="text-sm font-medium text-ink">
                    {fill(t.admin.question, { number: index + 1 })}
                  </span>
                  <button
                    onClick={() => removeQuestion(index)}
                    className="text-sm text-[var(--critical)] hover:underline"
                  >
                    {t.common.remove}
                  </button>
                </div>

                <div className="grid gap-4 sm:grid-cols-4">
                  <div className="sm:col-span-2">
                    <Label>{t.admin.type}</Label>
                    <Select
                      value={question.type}
                      onChange={(e) =>
                        patchQuestion(index, { type: e.target.value as QuestionType })
                      }
                    >
                      {types.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div>
                    <Label>{t.admin.pointsLabel}</Label>
                    <Input
                      type="number"
                      min={1}
                      value={question.points}
                      onChange={(e) => patchQuestion(index, { points: Number(e.target.value) })}
                    />
                  </div>
                  <div>
                    <Label>{t.admin.key}</Label>
                    <Input
                      value={question.key}
                      onChange={(e) => patchQuestion(index, { key: e.target.value })}
                    />
                  </div>

                  <div className="sm:col-span-4">
                    <Label>{t.admin.prompt}</Label>
                    <Textarea
                      className="min-h-16 font-sans"
                      value={question.prompt}
                      onChange={(e) => patchQuestion(index, { prompt: e.target.value })}
                    />
                  </div>

                  {question.type === 'fill_command' ? (
                    <div className="sm:col-span-4">
                      <Label>{t.admin.acceptedAnswers}</Label>
                      <Textarea
                        className="min-h-24"
                        value={question.accepted_answers.join('\n')}
                        onChange={(e) =>
                          patchQuestion(index, {
                            accepted_answers: e.target.value
                              .split('\n')
                              .map((s) => s.trim())
                              .filter(Boolean),
                          })
                        }
                      />
                      <p className="mt-1.5 text-xs text-ink-muted">{t.admin.acceptedHelp}</p>
                    </div>
                  ) : (
                    <div className="sm:col-span-4">
                      <Label>{t.admin.options}</Label>
                      <div className="flex flex-col gap-2">
                        {question.options.map((option, optionIndex) => (
                          <div key={option.id} className="flex items-center gap-2">
                            <label className="flex items-center gap-1.5 text-xs text-ink-muted">
                              <input
                                type={question.type === 'multi_select' ? 'checkbox' : 'radio'}
                                name={`correct-${question.key}`}
                                className="h-4 w-4 accent-[var(--accent)]"
                                checked={question.correct_options.includes(option.id)}
                                onChange={() => {
                                  const isCorrect = question.correct_options.includes(option.id);
                                  patchQuestion(index, {
                                    correct_options:
                                      question.type === 'multi_select'
                                        ? isCorrect
                                          ? question.correct_options.filter((id) => id !== option.id)
                                          : [...question.correct_options, option.id]
                                        : [option.id],
                                  });
                                }}
                              />
                              {option.id}
                            </label>
                            <Input
                              value={option.text}
                              onChange={(e) => {
                                const options = question.options.map((o, i) =>
                                  i === optionIndex ? { ...o, text: e.target.value } : o,
                                );
                                patchQuestion(index, { options });
                              }}
                            />
                            <button
                              onClick={() =>
                                patchQuestion(index, {
                                  options: question.options.filter((_, i) => i !== optionIndex),
                                  correct_options: question.correct_options.filter(
                                    (id) => id !== option.id,
                                  ),
                                })
                              }
                              className="shrink-0 px-2 text-sm text-ink-muted hover:text-[var(--critical)]"
                              aria-label={t.admin.options}
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="mt-2"
                        onClick={() => {
                          const nextId = String.fromCharCode(97 + question.options.length);
                          patchQuestion(index, {
                            options: [...question.options, { id: nextId, text: '' }],
                          });
                        }}
                      >
                        {t.admin.addOption}
                      </Button>
                      <p className="mt-1.5 text-xs text-ink-muted">{t.admin.optionsHelp}</p>
                    </div>
                  )}

                  <div className="sm:col-span-4">
                    <Label>{t.admin.explanation}</Label>
                    <Textarea
                      className="min-h-16 font-sans"
                      value={question.explanation}
                      onChange={(e) => patchQuestion(index, { explanation: e.target.value })}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </li>
        ))}
      </ol>
    </div>
  );
}
