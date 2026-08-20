import { redirect } from 'next/navigation';

import { normalizeLocale } from '@/i18n/config';

/**
 * `/{locale}` is a doorway, not a page.
 *
 * It opens onto the track grid - every programme as a card, with where you
 * stand in each - because that is where a journey is chosen or resumed. The
 * dashboard belongs to a track, and the rail remembers which one you were in,
 * so there is no need to guess here.
 */
export default function LocaleIndex({ params }: { params: { locale: string } }) {
  redirect(`/${normalizeLocale(params.locale)}/tracks`);
}
