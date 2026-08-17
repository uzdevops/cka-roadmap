'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FieldError, Input, Label, Select } from '@/components/ui/field';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import type { AdminLesson, StructurePhase } from '@/lib/types';

export default function AdminLessonsPage() {
  const { t, href, fill } = useI18n();
  const [lessons, setLessons] = useState<AdminLesson[]>([]);
  const [structure, setStructure] = useState<StructurePhase[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const [form, setForm] = useState({
    week_id: '',
    slug: '',
    title: '',
    summary: '',
    estimated_minutes: 30,
  });

  const load = async () => {
    try {
      const [lessonList, phaseList] = await Promise.all([
        apiFetch<AdminLesson[]>('/admin/lessons'),
        apiFetch<StructurePhase[]>('/admin/structure'),
      ]);
      setLessons(lessonList);
      setStructure(phaseList);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.admin.loadFailed);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const create = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      const lesson = await apiFetch<AdminLesson>('/admin/lessons', {
        method: 'POST',
        body: {
          week_id: Number(form.week_id),
          slug: form.slug,
          title: form.title,
          summary: form.summary,
          content: `## ${form.title}\n\nWrite the lesson here.\n`,
          estimated_minutes: Number(form.estimated_minutes),
        },
      });
      setCreating(false);
      setForm({ week_id: '', slug: '', title: '', summary: '', estimated_minutes: 30 });
      await load();
      window.location.href = href(`/admin/lessons/${lesson.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.admin.createFailed);
    }
  };

  const remove = async (lesson: AdminLesson) => {
    if (!window.confirm(fill(t.admin.deleteConfirm, { title: lesson.title }))) {
      return;
    }
    try {
      await apiFetch(`/admin/lessons/${lesson.id}`, { method: 'DELETE' });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.admin.deleteFailed);
    }
  };

  const weekLabel = (weekId: number) => {
    for (const phase of structure) {
      const week = phase.weeks.find((w) => w.id === weekId);
      if (week) return `W${week.number}`;
    }
    return '-';
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between gap-3">
        <p className="text-sm text-ink-secondary">{fill(t.admin.lessonsCount, { count: lessons.length })}</p>
        <Button size="sm" onClick={() => setCreating((v) => !v)}>
          {creating ? t.common.cancel : t.admin.newLesson}
        </Button>
      </div>

      <FieldError>{error}</FieldError>

      {creating && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{t.admin.newLesson}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={create} className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="week">{t.admin.colWeek}</Label>
                <Select
                  id="week"
                  required
                  value={form.week_id}
                  onChange={(e) => setForm({ ...form, week_id: e.target.value })}
                >
                  <option value="">{t.admin.selectWeek}</option>
                  {structure.map((phase) => (
                    <optgroup key={phase.id} label={phase.title}>
                      {phase.weeks.map((week) => (
                        <option key={week.id} value={week.id}>
                          Week {week.number} - {week.title}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </Select>
              </div>

              <div>
                <Label htmlFor="slug">{t.admin.slug}</Label>
                <Input
                  id="slug"
                  required
                  pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
                  placeholder="pod-security-standards"
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                />
              </div>

              <div className="sm:col-span-2">
                <Label htmlFor="title">{t.admin.title}</Label>
                <Input
                  id="title"
                  required
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                />
              </div>

              <div className="sm:col-span-2">
                <Label htmlFor="summary">{t.admin.summary}</Label>
                <Input
                  id="summary"
                  value={form.summary}
                  onChange={(e) => setForm({ ...form, summary: e.target.value })}
                />
              </div>

              <div>
                <Label htmlFor="minutes">{t.admin.estimatedMinutes}</Label>
                <Input
                  id="minutes"
                  type="number"
                  min={5}
                  value={form.estimated_minutes}
                  onChange={(e) =>
                    setForm({ ...form, estimated_minutes: Number(e.target.value) })
                  }
                />
              </div>

              <div className="flex items-end">
                <Button type="submit">{t.admin.createAndEdit}</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="overflow-x-auto rounded-card border border-line bg-surface">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-axis text-left text-xs uppercase tracking-wide text-ink-muted">
              <th className="px-4 py-2.5 font-medium">{t.admin.colWeek}</th>
              <th className="px-4 py-2.5 font-medium">{t.admin.colTitle}</th>
              <th className="px-4 py-2.5 font-medium">{t.admin.colSlug}</th>
              <th className="px-4 py-2.5 font-medium">{t.admin.colState}</th>
              <th className="px-4 py-2.5 text-right font-medium">{t.admin.colActions}</th>
            </tr>
          </thead>
          <tbody>
            {lessons.map((lesson) => (
              <tr key={lesson.id} className="border-b border-line last:border-0">
                <td className="px-4 py-2.5 tabular-nums text-ink-muted">
                  {weekLabel(lesson.week_id)}
                </td>
                <td className="px-4 py-2.5 text-ink">{lesson.title}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-ink-muted">{lesson.slug}</td>
                <td className="px-4 py-2.5">
                  {lesson.is_placeholder ? (
                    <Badge variant="outline">{t.common.draft}</Badge>
                  ) : lesson.is_published ? (
                    <Badge variant="good">{t.common.published}</Badge>
                  ) : (
                    <Badge variant="warning">{t.common.hidden}</Badge>
                  )}
                </td>
                <td className="px-4 py-2.5 text-right">
                  <Link
                    href={href(`/admin/lessons/${lesson.id}`)}
                    className="mr-3 text-[var(--accent)] hover:underline"
                  >
                    {t.common.edit}
                  </Link>
                  <button
                    onClick={() => remove(lesson)}
                    className="text-[var(--critical)] hover:underline"
                  >
                    {t.common.delete}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
