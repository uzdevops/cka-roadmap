/**
 * Turning a span of time into months, weeks, days and hours.
 *
 * Kept apart from the component so it can be reasoned about - and tested -
 * without a clock ticking underneath it.
 */

export interface Breakdown {
  months: number;
  weeks: number;
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  /** True when `to` is already in the past; every field above is then the
   *  amount of time by which it has been missed. */
  overdue: boolean;
}

const HOUR = 60 * 60 * 1000;

/**
 * Whole CALENDAR months first, then what is left.
 *
 * Calendar months rather than 30-day blocks because a person reading "2 months"
 * on the 3rd of March means "until the 3rd of May", not "until the 2nd". The
 * only way to get that right is to walk the calendar, which is what the loop
 * below does - a division would drift by up to three days a year.
 */
export function breakdown(from: Date, to: Date): Breakdown {
  const overdue = to.getTime() < from.getTime();
  const start = overdue ? to : from;
  const end = overdue ? from : to;

  // Walk whole months forward from `start` without passing `end`.
  let months = 0;
  const cursor = new Date(start.getTime());
  for (;;) {
    const next = new Date(cursor.getTime());
    next.setMonth(next.getMonth() + 1);
    // setMonth clamps: 31 Jan + 1 month is 3 March, not 31 February. Pulling it
    // back to the last day of the target month is what keeps "one month" from
    // silently becoming "one month and two days".
    if (next.getDate() !== cursor.getDate()) next.setDate(0);
    if (next.getTime() > end.getTime()) break;
    cursor.setTime(next.getTime());
    months += 1;
  }

  let remainder = end.getTime() - cursor.getTime();

  const totalDays = Math.floor(remainder / (24 * HOUR));
  remainder -= totalDays * 24 * HOUR;

  const hours = Math.floor(remainder / HOUR);
  remainder -= hours * HOUR;

  const minutes = Math.floor(remainder / (60 * 1000));
  const seconds = Math.floor((remainder - minutes * 60 * 1000) / 1000);

  return {
    months,
    weeks: Math.floor(totalDays / 7),
    days: totalDays % 7,
    hours,
    minutes,
    seconds,
    overdue,
  };
}

/** "07:04" - the seconds pane, so the timer visibly moves. */
export function clockFace(b: Breakdown): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(b.minutes)}:${pad(b.seconds)}`;
}
