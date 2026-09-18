"""Raw snapshot store for the trust pipeline (see docs/TRUST_PIPELINE.md).

Content-addressed on disk (dedup by sha256), with one RawSnapshot row per fetch
event so freshness can be tracked even when content is unchanged. The fetch
layer (Phase 2) is the only intended writer; the extractor (Phase 3) reads by
following RawSnapshot.raw_snapshot_path.
"""

import hashlib
from datetime import datetime
from pathlib import Path

from app.config import settings
from db.models import RawSnapshot
from extraction.schema import html_to_text
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]


def _snapshot_root() -> Path:
    root = Path(settings.raw_snapshot_dir)
    if not root.is_absolute():
        root = ROOT / root
    return root


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def normalized_content_hash(content: bytes) -> str:
    """Hash of tag-stripped, whitespace-collapsed text — see RawSnapshot.normalized_hash."""
    text = html_to_text(content.decode("utf-8", errors="replace"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def save_snapshot(
    db: Session,
    *,
    source_url: str,
    content: bytes,
    source_type: str | None = None,
    http_status: int | None = None,
    scheme_pk: str | None = None,
    fetched_at: datetime | None = None,
) -> RawSnapshot:
    """Persist a fetched page to the content-addressed snapshot store and record
    the fetch event. Safe to call repeatedly with identical content — the file is
    written once and reused, but a new RawSnapshot row is still recorded so the
    watcher (Phase 6) can see that a fetch happened at this time."""
    digest = content_hash(content)
    root = _snapshot_root()
    shard_dir = root / digest[:2]
    shard_dir.mkdir(parents=True, exist_ok=True)
    file_path = shard_dir / f"{digest}.html"
    if not file_path.exists():
        file_path.write_bytes(content)

    snapshot = RawSnapshot(
        scheme_pk=scheme_pk,
        source_url=source_url,
        source_type=source_type,
        http_status=http_status,
        content_hash=digest,
        normalized_hash=normalized_content_hash(content),
        raw_snapshot_path=str(file_path),
        fetched_at=fetched_at or datetime.utcnow(),
    )
    db.add(snapshot)
    db.flush()
    return snapshot


def latest_snapshot(db: Session, source_url: str) -> RawSnapshot | None:
    return (
        db.query(RawSnapshot)
        .filter(RawSnapshot.source_url == source_url)
        .order_by(RawSnapshot.fetched_at.desc())
        .first()
    )


def read_snapshot_content(snapshot: RawSnapshot) -> bytes:
    return Path(snapshot.raw_snapshot_path).read_bytes()
