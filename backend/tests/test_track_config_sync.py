"""The frontend's routing list must match the seeded tracks.

`frontend/src/tracks/config.ts` hardcodes the track slugs because the URL carries
the track and both middleware and `generateStaticParams` need that list where the
backend is unreachable. So the same list exists twice.

This project has already been bitten twice by a value written in two places -
SEED_ON_START and DEMO_ADMIN_PASSWORD, where docker-compose.yml quietly won over
config.py. The failure mode here is worse than a wrong default: a track seeded
into the database but missing from this list has working API data and a URL that
404s, and a slug in the list but not in the database routes to a page that can
never load. Neither raises anywhere.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

SEED_FILE = Path(__file__).resolve().parents[1] / "app" / "seed_data" / "tracks.json"


def _find_frontend_config() -> Path | None:
    """The frontend is not inside the backend image, so look where it might be.

    Mirrors test_config_defaults.py: the compose file bind-mounts the repo root
    at /repo for exactly this kind of cross-cutting check.
    """
    candidates = [
        Path(__file__).resolve().parents[2] / "frontend" / "src" / "tracks" / "config.ts",
        Path("/repo/frontend/src/tracks/config.ts"),
        Path.cwd() / "frontend" / "src" / "tracks" / "config.ts",
    ]
    if env := os.environ.get("TRACK_CONFIG_PATH"):
        candidates.insert(0, Path(env))
    return next((c for c in candidates if c.is_file()), None)


FRONTEND_CONFIG = _find_frontend_config()


def _seeded_slugs() -> list[str]:
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    return [t["slug"] for t in data["tracks"]]


def _routed_slugs() -> list[str]:
    assert FRONTEND_CONFIG is not None
    body = FRONTEND_CONFIG.read_text(encoding="utf-8")
    block = re.search(r"export const TRACKS = \[(.*?)\] as const;", body, re.S)
    assert block, "TRACKS array not found - has config.ts been restructured?"
    return re.findall(r"'([a-z0-9-]+)'", block.group(1))


def test_the_seed_file_is_readable() -> None:
    assert SEED_FILE.is_file(), f"expected the seed file at {SEED_FILE}"
    assert _seeded_slugs(), "tracks.json defines no tracks"


def test_routing_list_matches_the_seeded_tracks() -> None:
    if FRONTEND_CONFIG is None:
        pytest.skip(
            "frontend/src/tracks/config.ts not reachable from here - it is outside "
            "the backend image. Run with -v $PWD:/repo or set TRACK_CONFIG_PATH."
        )

    seeded = _seeded_slugs()
    routed = _routed_slugs()

    missing = [s for s in seeded if s not in routed]
    extra = [s for s in routed if s not in seeded]

    assert not missing, (
        f"seeded but not routable: {missing}. These tracks exist in the database "
        f"and their URLs will 404. Add them to frontend/src/tracks/config.ts."
    )
    assert not extra, (
        f"routable but not seeded: {extra}. These URLs resolve to a page whose "
        f"data will never load. Remove them, or add them to tracks.json."
    )


def test_the_default_track_exists() -> None:
    if FRONTEND_CONFIG is None:
        pytest.skip("frontend config not reachable")

    body = FRONTEND_CONFIG.read_text(encoding="utf-8")
    match = re.search(r"export const DEFAULT_TRACK: TrackSlug = '([a-z0-9-]+)'", body)
    assert match, "DEFAULT_TRACK not found"
    assert match.group(1) in _seeded_slugs(), (
        f"DEFAULT_TRACK is {match.group(1)!r}, which is not a seeded track - every "
        f"unprefixed URL would land on a track that does not exist."
    )
