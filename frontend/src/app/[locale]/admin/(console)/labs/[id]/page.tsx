'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FieldError, Input, Label, Select, Textarea } from '@/components/ui/field';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import type { AdminLab, LabTask } from '@/lib/types';

export default function AdminLabEditorPage({ params }: { params: { id: string } }) {
  const { t, href, fill } = useI18n();
  const [lab, setLab] = useState<AdminLab | null>(null);
  const [tasks, setTasks] = useState<LabTask[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void apiFetch<AdminLab>(`/admin/labs/${params.id}`)
      .then((data) => {
        setLab(data);
        setTasks(data.tasks ?? []);
      })
      .catch((err) => setError(err instanceof Error ? err.message : t.admin.loadFailed));
  }, [params.id]);

  const patchTask = (index: number, patch: Partial<LabTask>) => {
    setTasks((prev) => prev.map((task, i) => (i === index ? { ...task, ...patch } : task)));
  };

  const save = async () => {
    if (!lab) return;
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      await apiFetch(`/admin/labs/${params.id}`, {
        method: 'PATCH',
        body: {
          title: lab.title,
          description: lab.description,
          scenario: lab.scenario,
          difficulty: lab.difficulty,
          estimated_minutes: lab.estimated_minutes,
          environment_setup: lab.environment_setup,
          cleanup: lab.cleanup,
          tasks,
          is_published: lab.is_published,
        },
      });
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.profile.saveFailed);
    } finally {
      setBusy(false);
    }
  };

  if (error && !lab) return <p className="text-sm text-[var(--critical)]">{error}</p>;
  if (!lab) return <p className="text-sm text-ink-muted">{t.common.loading}</p>;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link href={href('/admin/labs')} className="text-sm text-ink-muted hover:text-ink">
          {t.admin.backToLabs}
        </Link>
        <div className="flex items-center gap-3">
          {saved && <span className="text-sm text-[var(--good-text)]">{t.common.saved}</span>}
          <Link
            href={href(`/labs/${lab.slug}`)}
            target="_blank"
            className="text-sm text-[var(--accent)] underline decoration-[var(--accent)]/40 underline-offset-2 hover:decoration-[var(--accent)]"
          >
            {t.admin.viewLive}
          </Link>
          <Button onClick={save} disabled={busy}>
            {busy ? t.common.saving : t.admin.saveLab}
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
              value={lab.title}
              onChange={(e) => setLab({ ...lab, title: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2">
            <Label htmlFor="description">{t.admin.description}</Label>
            <Input
              id="description"
              value={lab.description}
              onChange={(e) => setLab({ ...lab, description: e.target.value })}
            />
          </div>
          <div>
            <Label htmlFor="difficulty">{t.admin.colDifficulty}</Label>
            <Select
              id="difficulty"
              value={lab.difficulty}
              onChange={(e) => setLab({ ...lab, difficulty: e.target.value })}
            >
              <option value="beginner">{t.labs.difficulty.beginner}</option>
              <option value="intermediate">{t.labs.difficulty.intermediate}</option>
              <option value="advanced">{t.labs.difficulty.advanced}</option>
            </Select>
          </div>
          <div>
            <Label htmlFor="minutes">{t.admin.estimatedMinutes}</Label>
            <Input
              id="minutes"
              type="number"
              min={5}
              value={lab.estimated_minutes}
              onChange={(e) => setLab({ ...lab, estimated_minutes: Number(e.target.value) })}
            />
          </div>
          <div className="sm:col-span-2">
            <Label htmlFor="scenario">{t.admin.scenario}</Label>
            <Textarea
              id="scenario"
              className="min-h-32 font-sans"
              value={lab.scenario}
              onChange={(e) => setLab({ ...lab, scenario: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2">
            <Label htmlFor="setup">{t.admin.setupShell}</Label>
            <Textarea
              id="setup"
              className="min-h-40"
              spellCheck={false}
              value={lab.environment_setup}
              onChange={(e) => setLab({ ...lab, environment_setup: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2">
            <Label htmlFor="cleanup">{t.admin.cleanupShell}</Label>
            <Textarea
              id="cleanup"
              className="min-h-20"
              spellCheck={false}
              value={lab.cleanup}
              onChange={(e) => setLab({ ...lab, cleanup: e.target.value })}
            />
          </div>
          <div>
            <label className="flex items-center gap-2 text-sm text-ink-secondary">
              <input
                type="checkbox"
                className="h-4 w-4 accent-[var(--accent)]"
                checked={lab.is_published}
                onChange={(e) => setLab({ ...lab, is_published: e.target.checked })}
              />
              {t.admin.publishedLabel}
            </label>
          </div>
        </CardContent>
      </Card>

      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="font-semibold text-ink">
          {fill(t.admin.tasksHeading, { count: tasks.length })}
        </h2>
        <Button
          size="sm"
          variant="secondary"
          onClick={() =>
            setTasks((prev) => [
              ...prev,
              {
                title: `Task ${prev.length + 1} - `,
                instructions: '',
                solution: '',
                verification: '',
              },
            ])
          }
        >
          {t.admin.addTask}
        </Button>
      </div>

      <ol className="flex flex-col gap-4">
        {tasks.map((task, index) => (
          <li key={index}>
            <Card>
              <CardContent className="pt-5">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <span className="text-sm font-medium text-ink">
                    {fill(t.admin.task, { number: index + 1 })}
                  </span>
                  <button
                    onClick={() => setTasks((prev) => prev.filter((_, i) => i !== index))}
                    className="text-sm text-[var(--critical)] hover:underline"
                  >
                    {t.common.remove}
                  </button>
                </div>

                <div className="grid gap-4">
                  <div>
                    <Label>{t.admin.title}</Label>
                    <Input
                      value={task.title}
                      onChange={(e) => patchTask(index, { title: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>{t.admin.instructions}</Label>
                    <Textarea
                      className="min-h-24 font-sans"
                      value={task.instructions}
                      onChange={(e) => patchTask(index, { instructions: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>{t.admin.solution}</Label>
                    <Textarea
                      className="min-h-32"
                      spellCheck={false}
                      value={task.solution}
                      onChange={(e) => patchTask(index, { solution: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>{t.admin.verification}</Label>
                    <Textarea
                      className="min-h-20"
                      spellCheck={false}
                      value={task.verification}
                      onChange={(e) => patchTask(index, { verification: e.target.value })}
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
