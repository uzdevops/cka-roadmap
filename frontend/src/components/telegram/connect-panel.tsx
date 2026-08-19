'use client';

import { QRCodeSVG } from 'qrcode.react';
import { useCallback, useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';

interface TelegramStatus {
  enabled: boolean;
  linked: boolean;
  username: string | null;
  linked_at: string | null;
}

interface LinkOffer {
  url: string;
  expires_at: string;
  ttl_minutes: number;
}

/**
 * Connecting the reminder bot, from the site.
 *
 * The whole thing is optional and says so. A deep link rather than a code to
 * copy: pressing the button opens Telegram with `/start <token>` already typed,
 * which is the difference between a flow people finish and one they abandon
 * halfway between two apps.
 *
 * Renders nothing at all when the deployment has no bot configured - offering a
 * button that cannot work is worse than offering nothing.
 */
export function ConnectPanel({ compact = false }: { compact?: boolean }) {
  const { t, fill } = useI18n();
  const [status, setStatus] = useState<TelegramStatus | null>(null);
  const [offer, setOffer] = useState<LinkOffer | null>(null);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setStatus(await apiFetch<TelegramStatus>('/telegram/status'));
    } catch {
      setStatus(null);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // The link expires; showing it without saying so leaves somebody pressing a
  // dead button and blaming the bot.
  useEffect(() => {
    if (!offer) return;
    const tick = () => {
      const left = Math.max(
        0,
        Math.round((new Date(offer.expires_at).getTime() - Date.now()) / 1000),
      );
      setSecondsLeft(left);
      if (left === 0) setOffer(null);
    };
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [offer]);

  if (!status?.enabled) return null;

  const request = async () => {
    setBusy(true);
    setError(null);
    try {
      setOffer(await apiFetch<LinkOffer>('/telegram/link-token', { method: 'POST' }));
    } catch {
      setError(t.telegram.failed);
    } finally {
      setBusy(false);
    }
  };

  const disconnect = async () => {
    setBusy(true);
    setError(null);
    try {
      setStatus(await apiFetch<TelegramStatus>('/telegram/link', { method: 'DELETE' }));
      setOffer(null);
    } catch {
      setError(t.telegram.failed);
    } finally {
      setBusy(false);
    }
  };

  if (status.linked) {
    return (
      <div className="tg-panel">
        <div className="tg-head">
          <span className="tech-label">{t.telegram.label}</span>
          {/* A word, not just a green dot: state is never carried by colour
              alone anywhere else here either. */}
          <span className="tg-connected">{t.telegram.connected}</span>
        </div>
        <p className="tg-body">
          {status.username
            ? fill(t.telegram.connectedAs, { username: status.username })
            : t.telegram.connectedNoName}
        </p>
        <Button variant="secondary" size="sm" onClick={disconnect} disabled={busy}>
          {t.telegram.disconnect}
        </Button>
        {error && (
          <p role="alert" className="tg-error">
            {error}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="tg-panel">
      <div className="tg-head">
        <span className="tech-label">{t.telegram.label}</span>
        <span className="tg-optional">{t.telegram.optional}</span>
      </div>
      <p className="tg-body">{compact ? t.telegram.offerShort : t.telegram.offer}</p>

      {!offer ? (
        <Button variant="secondary" size="sm" onClick={request} disabled={busy}>
          {busy ? t.common.loading : t.telegram.connect}
        </Button>
      ) : (
        <div className="tg-offer">
          {/* Two ways in, because the person may be on the machine showing this
              or on a different phone. */}
          <a href={offer.url} target="_blank" rel="noopener noreferrer" className="tg-open">
            {t.telegram.openTelegram}
          </a>

          <div className="tg-qr">
            <QRCodeSVG
              value={offer.url}
              size={132}
              // White quiet zone regardless of theme: a scanner needs the
              // contrast, and a dark-on-dark QR simply does not read.
              bgColor="#ffffff"
              fgColor="#0b1020"
              includeMargin
              // An <svg role="img"> with no name is a WCAG failure, and here it
              // would be a screen reader announcing "image" for the only way in
              // from a second device.
              title={t.telegram.scan}
            />
            <p className="tg-qr-hint">{t.telegram.scan}</p>
          </div>

          <p className="tg-expiry">
            {secondsLeft > 0
              ? fill(t.telegram.expiresIn, {
                  time: `${Math.floor(secondsLeft / 60)}:${String(secondsLeft % 60).padStart(2, '0')}`,
                })
              : t.telegram.expired}
          </p>
          <button type="button" className="tg-again" onClick={request} disabled={busy}>
            {t.telegram.newLink}
          </button>
        </div>
      )}

      {error && (
        <p role="alert" className="tg-error">
          {error}
        </p>
      )}
    </div>
  );
}
