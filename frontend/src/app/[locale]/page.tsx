import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { normalizeLocale } from '@/i18n/config';
import { isTrack, TRACK_COOKIE } from '@/tracks/config';

/**
 * `/{locale}` is a doorway, not a page.
 *
 * The dashboard belongs to a track now, so this sends the visitor to the last
 * track they used. On a first visit there is no "last track" - and inventing
 * one would start their journey on a programme nobody chose - so they land on
 * the picker instead. Keeping a dashboard here as well would mean two URLs for
 * the same screen, one of which could not say which track it was showing.
 */
export default function LocaleIndex({ params }: { params: { locale: string } }) {
  const locale = normalizeLocale(params.locale);
  const remembered = cookies().get(TRACK_COOKIE)?.value;

  if (isTrack(remembered)) {
    redirect(`/${locale}/${remembered}/dashboard`);
  }
  redirect(`/${locale}/tracks`);
}
