"""Leitura e indexação local da biblioteca musical do SerifaPlayer."""

from __future__ import annotations

import base64
import hashlib
import os
import sqlite3
import uuid
from datetime import datetime
import shutil
from PIL import Image, ImageOps
from io import BytesIO
from pathlib import Path
from typing import Callable

from mutagen import File as MutagenFile
from mutagen.flac import Picture


AUDIO_EXTENSIONS = {
    ".mp3", ".flac", ".m4a", ".mp4", ".aac", ".ogg", ".oga",
    ".opus", ".wav", ".aiff", ".aif", ".wma", ".ape", ".wv",
}

COVER_NAMES = (
    "cover.jpg", "cover.jpeg",
    "folder.jpg", "folder.jpeg",
    "front.jpg", "front.jpeg",
    "album.jpg", "album.jpeg",
    "cover.png", "folder.png",
    "front.png", "album.png",
)


class LibraryScanner:

    def __init__(self, database_path: str | Path, covers_dir: str | Path):
        self.database_path = Path(database_path)
        self.covers_dir = Path(covers_dir)

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.covers_dir.mkdir(parents=True, exist_ok=True)

        self._initialize_database()

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_database(self):
        with self._connect() as db:

            db.execute("""
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    album TEXT NOT NULL,
                    album_artist TEXT NOT NULL,
                    track_number TEXT,
                    disc_number TEXT,
                    year TEXT,
                    genre TEXT,
                    duration REAL NOT NULL DEFAULT 0,
                    format TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    modified_time REAL NOT NULL DEFAULT 0,
                    cover_path TEXT,
                    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            columns = {
                row["name"]
                for row in db.execute(
                    "PRAGMA table_info(tracks)"
                ).fetchall()
            }

            if "is_favorite" not in columns:
                db.execute("""
                    ALTER TABLE tracks
                    ADD COLUMN is_favorite INTEGER NOT NULL DEFAULT 0
                """)

            if "favorited_at" not in columns:
                db.execute("""
                    ALTER TABLE tracks
                    ADD COLUMN favorited_at TEXT
                """)

            db.execute("""
                UPDATE tracks
                SET favorited_at = imported_at
                WHERE is_favorite = 1
                  AND favorited_at IS NULL
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tracks_artist
                ON tracks(artist)
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tracks_album
                ON tracks(album)
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS track_stats (
                    track_id INTEGER PRIMARY KEY,
                    play_count INTEGER NOT NULL DEFAULT 0,
                    last_played_at TEXT,

                    FOREIGN KEY (track_id)
                        REFERENCES tracks(id)
                        ON DELETE CASCADE
                )
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_track_stats_play_count
                ON track_stats(play_count DESC)
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS play_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id INTEGER,
                    track_path TEXT,
                    title TEXT NOT NULL DEFAULT 'Desconhecida',
                    artist TEXT NOT NULL DEFAULT 'Artista desconhecido',
                    album TEXT NOT NULL DEFAULT '',
                    started_at TEXT NOT NULL,
                    listened_seconds REAL NOT NULL DEFAULT 0,
                    duration_seconds REAL NOT NULL DEFAULT 0,
                    qualified INTEGER NOT NULL DEFAULT 0,
                    finished INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_play_history_started
                ON play_history(started_at)
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_play_history_track
                ON play_history(track_id)
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_play_history_qualified
                ON play_history(qualified, started_at)
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS playlist_folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            playlist_columns = {
                row["name"]
                for row in db.execute(
                    "PRAGMA table_info(playlists)"
                ).fetchall()
            }

            if "cover_path" not in playlist_columns:
                db.execute("""
                    ALTER TABLE playlists
                    ADD COLUMN cover_path TEXT
                """)

            if "folder_id" not in playlist_columns:
                db.execute("""
                    ALTER TABLE playlists
                    ADD COLUMN folder_id INTEGER
                    REFERENCES playlist_folders(id)
                    ON DELETE SET NULL
                """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_playlists_folder
                ON playlists(folder_id)
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS entity_covers (
                    entity_type TEXT NOT NULL,
                    entity_key TEXT NOT NULL,
                    cover_path TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (entity_type, entity_key)
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS playlist_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER NOT NULL,
                    track_id INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (playlist_id)
                        REFERENCES playlists(id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (track_id)
                        REFERENCES tracks(id)
                        ON DELETE CASCADE
                )
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_playlist_tracks_order
                ON playlist_tracks(playlist_id, position)
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_playlist_tracks_track
                ON playlist_tracks(track_id)
            """)

    def start_play_session(self, track):
        if not isinstance(track, dict):
            return None

        try:
            track_id = int(track.get("id") or 0) or None
        except (TypeError, ValueError):
            track_id = None

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        values = (
            track_id,
            str(track.get("path") or ""),
            str(track.get("title") or "Desconhecida"),
            str(track.get("artist") or "Artista desconhecido"),
            str(track.get("album") or ""),
            now,
            max(0.0, float(track.get("duration") or 0)),
            now
        )

        with self._connect() as db:
            cursor = db.execute("""
                INSERT INTO play_history (
                    track_id, track_path, title, artist, album,
                    started_at, duration_seconds, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, values)

            return cursor.lastrowid

    def update_play_session(
        self,
        session_id,
        listened_seconds,
        duration_seconds=None,
        qualified=False,
        finished=False
    ):
        try:
            session_id = int(session_id)
            listened_seconds = max(0.0, float(listened_seconds))
        except (TypeError, ValueError):
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._connect() as db:
            row = db.execute("""
                SELECT track_id, qualified
                FROM play_history
                WHERE id = ?
            """, (session_id,)).fetchone()

            if row is None:
                return False

            new_qualified = bool(row["qualified"] or qualified)

            if duration_seconds is None:
                db.execute("""
                    UPDATE play_history
                    SET listened_seconds = ?,
                        qualified = ?,
                        finished = MAX(finished, ?),
                        updated_at = ?
                    WHERE id = ?
                """, (
                    listened_seconds,
                    int(new_qualified),
                    int(bool(finished)),
                    now,
                    session_id
                ))
            else:
                db.execute("""
                    UPDATE play_history
                    SET listened_seconds = ?,
                        duration_seconds = ?,
                        qualified = ?,
                        finished = MAX(finished, ?),
                        updated_at = ?
                    WHERE id = ?
                """, (
                    listened_seconds,
                    max(0.0, float(duration_seconds)),
                    int(new_qualified),
                    int(bool(finished)),
                    now,
                    session_id
                ))

            if new_qualified and not row["qualified"] and row["track_id"]:
                exists = db.execute("""
                    SELECT 1 FROM tracks WHERE id = ?
                """, (row["track_id"],)).fetchone()

                if exists:
                    db.execute("""
                        INSERT INTO track_stats (
                            track_id, play_count, last_played_at
                        )
                        VALUES (?, 1, ?)
                        ON CONFLICT(track_id)
                        DO UPDATE SET
                            play_count = track_stats.play_count + 1,
                            last_played_at = excluded.last_played_at
                    """, (row["track_id"], now))

        return True

    def get_usage_summary(self, start_at, end_at):
        with self._connect() as db:
            totals = db.execute("""
                SELECT
                    COALESCE(SUM(listened_seconds), 0) AS listened_seconds,
                    COUNT(*) AS sessions,
                    SUM(qualified) AS qualified_plays
                FROM play_history
                WHERE started_at >= ? AND started_at < ?
            """, (start_at, end_at)).fetchone()

            top_track = db.execute("""
                SELECT
                    h.title,
                    h.artist,
                    h.album,
                    h.track_path,
                    MAX(t.cover_path) AS cover_path,
                    COUNT(*) AS play_count,
                    SUM(h.listened_seconds) AS listened_seconds
                FROM play_history h
                LEFT JOIN tracks t ON t.id = h.track_id
                WHERE h.started_at >= ?
                  AND h.started_at < ?
                  AND h.qualified = 1
                GROUP BY h.title, h.artist, h.album
                ORDER BY play_count DESC, listened_seconds DESC
                LIMIT 1
            """, (start_at, end_at)).fetchone()

            top_artist = db.execute("""
                SELECT
                    h.artist,
                    MAX(t.cover_path) AS cover_path,
                    COUNT(*) AS play_count,
                    SUM(h.listened_seconds) AS listened_seconds
                FROM play_history h
                LEFT JOIN tracks t ON t.id = h.track_id
                WHERE h.started_at >= ?
                  AND h.started_at < ?
                  AND h.qualified = 1
                GROUP BY h.artist COLLATE NOCASE
                ORDER BY play_count DESC, listened_seconds DESC
                LIMIT 1
            """, (start_at, end_at)).fetchone()

            return {
                "listened_seconds": float(totals["listened_seconds"] or 0),
                "sessions": int(totals["sessions"] or 0),
                "qualified_plays": int(totals["qualified_plays"] or 0),
                "top_track": dict(top_track) if top_track else None,
                "top_artist": dict(top_artist) if top_artist else None
            }


    def get_usage_top_tracks(self, start_at, end_at, limit=100):
        limit = max(1, min(int(limit), 1000))

        with self._connect() as db:
            rows = db.execute("""
                SELECT
                    track_id,
                    title,
                    artist,
                    album,
                    track_path,
                    COUNT(*) AS play_count,
                    SUM(listened_seconds) AS listened_seconds
                FROM play_history
                WHERE started_at >= ?
                  AND started_at < ?
                  AND qualified = 1
                GROUP BY
                    track_id, title, artist, album, track_path
                ORDER BY
                    play_count DESC,
                    listened_seconds DESC,
                    title COLLATE NOCASE
                LIMIT ?
            """, (start_at, end_at, limit)).fetchall()

            return [dict(row) for row in rows]

    def get_usage_top_artists(self, start_at, end_at, limit=10):
        limit = max(1, min(int(limit), 100))

        with self._connect() as db:
            rows = db.execute("""
                SELECT
                    artist,
                    COUNT(*) AS play_count,
                    SUM(listened_seconds) AS listened_seconds
                FROM play_history
                WHERE started_at >= ?
                  AND started_at < ?
                  AND qualified = 1
                GROUP BY artist COLLATE NOCASE
                ORDER BY
                    play_count DESC,
                    listened_seconds DESC,
                    artist COLLATE NOCASE
                LIMIT ?
            """, (start_at, end_at, limit)).fetchall()

            return [dict(row) for row in rows]

    def get_usage_months(self):
        with self._connect() as db:
            rows = db.execute("""
                SELECT
                    substr(started_at, 1, 7) AS month,
                    COUNT(*) AS sessions,
                    SUM(qualified) AS qualified_plays,
                    SUM(listened_seconds) AS listened_seconds
                FROM play_history
                GROUP BY substr(started_at, 1, 7)
                ORDER BY month DESC
            """).fetchall()

            return [dict(row) for row in rows]

    @staticmethod
    def _tag_value(tags, *names, default=""):

        if not tags:
            return default

        wanted = {name.casefold() for name in names}

        try:
            keys = list(tags.keys())
        except Exception:
            return default

        for key in keys:

            if str(key).casefold() not in wanted:
                continue

            value = tags.get(key)

            if isinstance(value, (list, tuple)):
                value = value[0] if value else ""

            if value is None:
                continue

            if hasattr(value, "text"):
                value = value.text

                if isinstance(value, (list, tuple)):
                    value = value[0] if value else ""

            if isinstance(value, bytes):
                try:
                    value = value.decode("utf-8", errors="replace")
                except Exception:
                    continue

            text = str(value).strip()

            if text:
                return text

        return default

    @staticmethod
    def _extract_embedded_cover(audio):

        tags = getattr(audio, "tags", None)

        if not tags:
            return None

        # Capas ID3: MP3 e alguns arquivos AIFF.
        try:
            for frame in tags.values():

                if getattr(frame, "FrameID", "") == "APIC":

                    data = getattr(frame, "data", None)

                    if data:
                        return bytes(data)

        except Exception:
            pass

        # Capas FLAC.
        pictures = getattr(audio, "pictures", None)

        if pictures:
            try:
                return bytes(pictures[0].data)
            except Exception:
                pass

        # Capas MP4 e M4A.
        try:
            for key in ("covr", "©covr"):

                values = tags.get(key)

                if values:
                    return bytes(values[0])

        except Exception:
            pass

        # Vorbis comments: METADATA_BLOCK_PICTURE.
        try:
            encoded = tags.get("metadata_block_picture")

            if encoded:

                raw = base64.b64decode(encoded[0])
                picture = Picture(raw)

                if picture.data:
                    return bytes(picture.data)

        except Exception:
            pass

        return None

    def _store_webp_cover(self, image_data):
        if not image_data:
            return None

        digest = hashlib.sha256(image_data).hexdigest()
        destination = self.covers_dir / f"{digest}.webp"

        if destination.is_file():
            return str(destination)

        temporary = destination.with_suffix(".webp.tmp")

        try:
            with Image.open(BytesIO(image_data)) as source:
                source.draft("RGB", (1200, 1200))

                image = ImageOps.exif_transpose(source)

                image.thumbnail(
                    (1200, 1200),
                    Image.Resampling.LANCZOS
                )

                if (
                    image.mode in ("RGBA", "LA")
                    or "transparency" in image.info
                ):
                    image = image.convert("RGBA")
                else:
                    image = image.convert("RGB")

                image.save(
                    temporary,
                    format="WEBP",
                    quality=82,
                    method=4
                )

            temporary.replace(destination)
            return str(destination)

        except Exception:
            temporary.unlink(missing_ok=True)
            return None

    def _cover_for_file(self, file_path: Path, audio):

        folder = file_path.parent

        # Primeiro procura capas externas na pasta do álbum.
        for name in COVER_NAMES:

            candidate = folder / name

            if candidate.is_file():

                try:
                    image_data = candidate.read_bytes()
                    result = self._store_webp_cover(image_data)

                    if result:
                        return result

                except OSError:
                    pass

        # Depois procura capas incorporadas no próprio áudio.
        image_data = self._extract_embedded_cover(audio)

        if not image_data:
            return None

        return self._store_webp_cover(image_data)

    def _read_track(self, file_path: Path):

        audio = MutagenFile(str(file_path), easy=False)

        if audio is None:
            return None

        tags = getattr(audio, "tags", None)

        duration = float(
            getattr(
                getattr(audio, "info", None),
                "length",
                0
            ) or 0
        )

        title = self._tag_value(
            tags,
            "title",
            "TIT2",
            default=file_path.stem
        )

        artist = self._tag_value(
            tags,
            "artist",
            "TPE1",
            "©ART",
            default="Artista desconhecido"
        )

        album = self._tag_value(
            tags,
            "album",
            "TALB",
            "©alb",
            default=file_path.parent.name
        )

        album_artist = self._tag_value(
            tags,
            "albumartist",
            "album artist",
            "TPE2",
            "aART",
            default=artist
        )

        track_number = self._tag_value(
            tags,
            "tracknumber",
            "TRCK",
            "trkn"
        )

        disc_number = self._tag_value(
            tags,
            "discnumber",
            "TPOS",
            "disk"
        )

        year = self._tag_value(
            tags,
            "date",
            "year",
            "TDRC",
            "TYER",
            "©day"
        )

        genre = self._tag_value(
            tags,
            "genre",
            "TCON",
            "©gen"
        )

        stat = file_path.stat()

        cover_path = self._cover_for_file(
            file_path,
            audio
        )

        return {
            "path": str(file_path),
            "title": title,
            "artist": artist,
            "album": album,
            "album_artist": album_artist,
            "track_number": track_number,
            "disc_number": disc_number,
            "year": year,
            "genre": genre,
            "duration": duration,
            "format": file_path.suffix.lower().lstrip("."),
            "file_size": stat.st_size,
            "modified_time": stat.st_mtime,
            "cover_path": cover_path,
        }

    def scan(
        self,
        folders,
        progress: Callable[[str], None] | None = None
    ):

        found_paths = set()
        stats = {
            "errors": 0,
            "imported": 0,
            "updated": 0,
        }

        db = self._connect()

        try:
            existing_paths = {
                row["path"]
                for row in db.execute(
                    "SELECT path FROM tracks"
                ).fetchall()
            }

            columns = (
                "path",
                "title",
                "artist",
                "album",
                "album_artist",
                "track_number",
                "disc_number",
                "year",
                "genre",
                "duration",
                "format",
                "file_size",
                "modified_time",
                "cover_path",
            )

            column_sql = ", ".join(columns)
            placeholders = ", ".join("?" for _ in columns)

            updates = ", ".join(
                f"{column}=excluded.{column}"
                for column in columns
                if column != "path"
            )

            upsert_sql = f"""
                INSERT INTO tracks ({column_sql})
                VALUES ({placeholders})
                ON CONFLICT(path)
                DO UPDATE SET {updates}
            """

            batch = []

            def flush_batch():
                if not batch:
                    return

                with db:
                    for record, was_existing in batch:
                        try:
                            db.execute(
                                upsert_sql,
                                tuple(record[column] for column in columns)
                            )

                            existing_paths.add(record["path"])

                            if was_existing:
                                stats["updated"] += 1
                            else:
                                stats["imported"] += 1

                        except Exception:
                            stats["errors"] += 1

                batch.clear()

            for folder in folders:
                root = Path(folder)

                if not root.is_dir():
                    continue

                for current, dirnames, filenames in os.walk(
                    root,
                    followlinks=False
                ):
                    dirnames[:] = [
                        name
                        for name in dirnames
                        if not name.startswith(".")
                    ]

                    for filename in filenames:
                        path = Path(current) / filename

                        if path.is_symlink():
                            continue

                        if path.suffix.lower() not in AUDIO_EXTENSIONS:
                            continue

                        try:
                            resolved = str(path.resolve(strict=True))

                            if resolved in found_paths:
                                continue

                            found_paths.add(resolved)

                            if progress:
                                progress(path.name)

                            record = self._read_track(
                                Path(resolved)
                            )

                            if record is None:
                                stats["errors"] += 1
                                continue

                            was_existing = record["path"] in existing_paths

                            batch.append((record, was_existing))

                            if len(batch) >= 50:
                                flush_batch()

                        except (
                            OSError,
                            ValueError,
                            TypeError,
                            RuntimeError
                        ):
                            stats["errors"] += 1

                        except Exception:
                            stats["errors"] += 1

            flush_batch()

            total = db.execute(
                "SELECT COUNT(*) FROM tracks"
            ).fetchone()[0]

            return {
                "imported": stats["imported"],
                "updated": stats["updated"],
                "errors": stats["errors"],
                "found": len(found_paths),
                "total": int(total),
            }

        finally:
            db.close()

    def list_albums(self):

        with self._connect() as db:

            rows = db.execute(
                """
                SELECT
                    album,
                    COALESCE(
                        NULLIF(album_artist, ''),
                        NULLIF(artist, ''),
                        'Artista desconhecido'
                    ) AS artist,
                    MAX(NULLIF(cover_path, '')) AS cover_path,
                    COUNT(*) AS track_count

                FROM tracks

                WHERE TRIM(album) != ''

                GROUP BY
                    album COLLATE NOCASE,
                    COALESCE(
                        NULLIF(album_artist, ''),
                        NULLIF(artist, ''),
                        'Artista desconhecido'
                    ) COLLATE NOCASE

                ORDER BY
                    album COLLATE NOCASE,
                    artist COLLATE NOCASE
                """
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]


    # --------------------------------------------------
    # PLAYLISTS
    # --------------------------------------------------

    def create_playlist(self, name):
        name = str(name or "").strip()

        if not name:
            raise ValueError("O nome da playlist não pode ficar vazio.")

        with self._connect() as db:
            cursor = db.execute(
                """
                INSERT INTO playlists (name)
                VALUES (?)
                """,
                (name,)
            )

            playlist_id = cursor.lastrowid

            row = db.execute(
                "SELECT * FROM playlists WHERE id = ?",
                (playlist_id,)
            ).fetchone()

            return dict(row)

    def list_playlists(self):
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT
                    playlists.*,
                    COUNT(playlist_tracks.id) AS track_count
                FROM playlists
                LEFT JOIN playlist_tracks
                    ON playlist_tracks.playlist_id = playlists.id
                GROUP BY playlists.id
                ORDER BY playlists.name COLLATE NOCASE
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def create_playlist_folder(self, name):
        name = str(name or "").strip()

        if not name:
            raise ValueError("O nome da pasta não pode ficar vazio.")

        with self._connect() as db:
            existing = db.execute(
                """
                SELECT id
                FROM playlist_folders
                WHERE name = ? COLLATE NOCASE
                """,
                (name,)
            ).fetchone()

            if existing:
                raise ValueError("Já existe uma pasta com esse nome.")

            cursor = db.execute(
                """
                INSERT INTO playlist_folders (name)
                VALUES (?)
                """,
                (name,)
            )

            row = db.execute(
                """
                SELECT *
                FROM playlist_folders
                WHERE id = ?
                """,
                (cursor.lastrowid,)
            ).fetchone()

            return dict(row)

    def list_playlist_folders(self):
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT
                    playlist_folders.*,
                    COUNT(playlists.id) AS playlist_count
                FROM playlist_folders
                LEFT JOIN playlists
                    ON playlists.folder_id = playlist_folders.id
                GROUP BY playlist_folders.id
                ORDER BY playlist_folders.name COLLATE NOCASE
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def rename_playlist_folder(self, folder_id, new_name):
        new_name = str(new_name or "").strip()

        if not new_name:
            raise ValueError("O nome da pasta não pode ficar vazio.")

        with self._connect() as db:
            existing = db.execute(
                """
                SELECT id
                FROM playlist_folders
                WHERE name = ? COLLATE NOCASE
                  AND id != ?
                """,
                (new_name, folder_id)
            ).fetchone()

            if existing:
                raise ValueError("Já existe uma pasta com esse nome.")

            cursor = db.execute(
                """
                UPDATE playlist_folders
                SET name = ?
                WHERE id = ?
                """,
                (new_name, folder_id)
            )

            return cursor.rowcount > 0

    def delete_playlist_folder(self, folder_id):
        with self._connect() as db:
            db.execute(
                """
                UPDATE playlists
                SET folder_id = NULL
                WHERE folder_id = ?
                """,
                (folder_id,)
            )

            cursor = db.execute(
                """
                DELETE FROM playlist_folders
                WHERE id = ?
                """,
                (folder_id,)
            )

            return cursor.rowcount > 0

    def move_playlist_to_folder(self, playlist_id, folder_id=None):
        with self._connect() as db:
            playlist = db.execute(
                """
                SELECT id
                FROM playlists
                WHERE id = ?
                """,
                (playlist_id,)
            ).fetchone()

            if playlist is None:
                raise ValueError("Playlist não encontrada.")

            if folder_id is not None:
                folder = db.execute(
                    """
                    SELECT id
                    FROM playlist_folders
                    WHERE id = ?
                    """,
                    (folder_id,)
                ).fetchone()

                if folder is None:
                    raise ValueError("Pasta não encontrada.")

            cursor = db.execute(
                """
                UPDATE playlists
                SET folder_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (folder_id, playlist_id)
            )

            return cursor.rowcount > 0

    def get_playlist(self, playlist_id):
        with self._connect() as db:
            row = db.execute(
                """
                SELECT *
                FROM playlists
                WHERE id = ?
                """,
                (playlist_id,)
            ).fetchone()

            return dict(row) if row else None

    def list_playlist_tracks(self, playlist_id):
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT
                    tracks.*,
                    playlist_tracks.id AS playlist_entry_id,
                    playlist_tracks.position AS playlist_position,
                    playlist_tracks.added_at AS playlist_added_at
                FROM playlist_tracks
                INNER JOIN tracks
                    ON tracks.id = playlist_tracks.track_id
                WHERE playlist_tracks.playlist_id = ?
                ORDER BY
                    playlist_tracks.position,
                    playlist_tracks.id
                """,
                (playlist_id,)
            ).fetchall()

            return [dict(row) for row in rows]

    def rename_playlist(self, playlist_id, new_name):
        new_name = str(new_name or "").strip()

        if not new_name:
            raise ValueError("O nome da playlist não pode ficar vazio.")

        with self._connect() as db:
            cursor = db.execute(
                """
                UPDATE playlists
                SET name = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_name, playlist_id)
            )

            return cursor.rowcount > 0

    def get_entity_cover(self, entity_type, entity_key):
        entity_type = str(entity_type).strip().casefold()
        entity_key = str(entity_key).strip()

        if entity_type not in {"artist", "album"} or not entity_key:
            return None

        with self._connect() as db:
            row = db.execute(
                """
                SELECT cover_path
                FROM entity_covers
                WHERE entity_type = ? AND entity_key = ?
                """,
                (entity_type, entity_key)
            ).fetchone()

        if row and row["cover_path"] and Path(row["cover_path"]).is_file():
            return row["cover_path"]

        return None

    def _remove_managed_entity_cover(self, cover_path):
        if not cover_path:
            return

        try:
            covers_root = Path(self.covers_dir)

            if covers_root.is_symlink():
                return

            covers_root = covers_root.resolve()
            candidate = Path(cover_path)

            if candidate.is_symlink():
                return

            resolved = candidate.resolve(strict=True)

            if resolved.parent != covers_root:
                return

            with self._connect() as db:
                row = db.execute(
                    """
                    SELECT
                        (SELECT COUNT(*) FROM entity_covers
                         WHERE cover_path = ?) +
                        (SELECT COUNT(*) FROM playlists
                         WHERE cover_path = ?) AS total
                    """,
                    (str(candidate), str(candidate))
                ).fetchone()

            if row and int(row["total"]) == 0:
                resolved.unlink(missing_ok=True)

        except (OSError, RuntimeError, ValueError):
            return

    def set_entity_cover(self, entity_type, entity_key, source_path):
        entity_type = str(entity_type).strip().casefold()
        entity_key = str(entity_key).strip()

        if entity_type not in {"artist", "album"} or not entity_key:
            raise ValueError("Identidade de artista ou álbum inválida.")

        source = Path(source_path).expanduser().resolve(strict=True)

        if not source.is_file():
            raise ValueError("O arquivo selecionado não existe.")

        allowed_extensions = {
            ".png", ".jpg", ".jpeg", ".webp", ".bmp"
        }
        extension = source.suffix.lower()

        if extension not in allowed_extensions:
            raise ValueError("Formato de imagem não suportado.")

        self.covers_dir.mkdir(parents=True, exist_ok=True)

        destination = (
            Path(self.covers_dir)
            / f"entity_{entity_type}_{uuid.uuid4().hex}{extension}"
        )

        with self._connect() as db:
            row = db.execute(
                """
                SELECT cover_path
                FROM entity_covers
                WHERE entity_type = ? AND entity_key = ?
                """,
                (entity_type, entity_key)
            ).fetchone()

            old_cover = row["cover_path"] if row else None

            try:
                shutil.copy2(source, destination)

                db.execute(
                    """
                    INSERT INTO entity_covers (
                        entity_type,
                        entity_key,
                        cover_path,
                        updated_at
                    )
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(entity_type, entity_key)
                    DO UPDATE SET
                        cover_path = excluded.cover_path,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (entity_type, entity_key, str(destination))
                )

            except Exception:
                destination.unlink(missing_ok=True)
                raise

        if old_cover:
            self._remove_managed_entity_cover(old_cover)

        return str(destination)

    def reset_entity_cover(self, entity_type, entity_key):
        entity_type = str(entity_type).strip().casefold()
        entity_key = str(entity_key).strip()

        if entity_type not in {"artist", "album"} or not entity_key:
            return False

        with self._connect() as db:
            row = db.execute(
                """
                SELECT cover_path
                FROM entity_covers
                WHERE entity_type = ? AND entity_key = ?
                """,
                (entity_type, entity_key)
            ).fetchone()

            if row is None:
                return False

            old_cover = row["cover_path"]

            db.execute(
                """
                DELETE FROM entity_covers
                WHERE entity_type = ? AND entity_key = ?
                """,
                (entity_type, entity_key)
            )

        if old_cover:
            self._remove_managed_entity_cover(old_cover)

        return True

    def _remove_managed_playlist_cover(
        self,
        cover_path,
        playlist_id=None
    ):
        if not cover_path:
            return

        try:
            covers_root = Path(self.covers_dir)

            if covers_root.is_symlink():
                return

            covers_root = covers_root.resolve()
            candidate = Path(cover_path)

            if candidate.is_symlink():
                return

            resolved = candidate.resolve(strict=True)

            if resolved.parent != covers_root:
                return

            with self._connect() as db:
                if playlist_id is None:
                    row = db.execute(
                        """
                        SELECT COUNT(*) AS total
                        FROM playlists
                        WHERE cover_path = ?
                        """,
                        (str(candidate),)
                    ).fetchone()
                else:
                    row = db.execute(
                        """
                        SELECT COUNT(*) AS total
                        FROM playlists
                        WHERE cover_path = ?
                          AND id != ?
                        """,
                        (str(candidate), playlist_id)
                    ).fetchone()

            if row and int(row["total"]) == 0:
                resolved.unlink(missing_ok=True)

        except (OSError, RuntimeError, ValueError):
            return

    def set_playlist_cover(self, playlist_id, source_path):
        playlist_id = int(playlist_id)
        source = Path(source_path).expanduser().resolve(strict=True)

        if not source.is_file():
            raise ValueError("O arquivo selecionado não existe.")

        allowed_extensions = {
            ".png", ".jpg", ".jpeg", ".webp", ".bmp"
        }

        extension = source.suffix.lower()

        if extension not in allowed_extensions:
            raise ValueError("Formato de imagem não suportado.")

        self.covers_dir.mkdir(parents=True, exist_ok=True)

        destination = (
            Path(self.covers_dir)
            / f"playlist_{playlist_id}_{uuid.uuid4().hex}{extension}"
        )

        with self._connect() as db:
            row = db.execute(
                """
                SELECT cover_path
                FROM playlists
                WHERE id = ?
                """,
                (playlist_id,)
            ).fetchone()

            if row is None:
                raise ValueError("Playlist não encontrada.")

            old_cover = row["cover_path"]

            try:
                shutil.copy2(source, destination)

                db.execute(
                    """
                    UPDATE playlists
                    SET cover_path = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (str(destination), playlist_id)
                )

            except Exception:
                destination.unlink(missing_ok=True)
                raise

        if old_cover:
            self._remove_managed_playlist_cover(
                old_cover,
                playlist_id
            )

        return str(destination)

    def reset_playlist_cover(self, playlist_id):
        playlist_id = int(playlist_id)

        with self._connect() as db:
            row = db.execute(
                """
                SELECT cover_path
                FROM playlists
                WHERE id = ?
                """,
                (playlist_id,)
            ).fetchone()

            if row is None:
                return False

            old_cover = row["cover_path"]

            db.execute(
                """
                UPDATE playlists
                SET cover_path = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (playlist_id,)
            )

        if old_cover:
            self._remove_managed_playlist_cover(
                old_cover,
                playlist_id
            )

        return True

    def delete_playlist(self, playlist_id):
        with self._connect() as db:
            row = db.execute(
                """
                SELECT cover_path
                FROM playlists
                WHERE id = ?
                """,
                (playlist_id,)
            ).fetchone()

            if row is None:
                return False

            old_cover = row["cover_path"]

            cursor = db.execute(
                """
                DELETE FROM playlists
                WHERE id = ?
                """,
                (playlist_id,)
            )

            deleted = cursor.rowcount > 0

        if deleted and old_cover:
            self._remove_managed_playlist_cover(
                old_cover,
                playlist_id
            )

        return deleted

    def add_tracks_to_playlist(
        self,
        playlist_id,
        track_ids,
        position=None
    ):
        track_ids = list(track_ids or [])

        if not track_ids:
            return 0

        track_ids = [int(track_id) for track_id in track_ids]

        with self._connect() as db:
            playlist = db.execute(
                "SELECT id FROM playlists WHERE id = ?",
                (playlist_id,)
            ).fetchone()

            if playlist is None:
                raise ValueError("Playlist não encontrada.")

            unique_ids = set(track_ids)
            placeholders = ",".join("?" for _ in unique_ids)

            existing = db.execute(
                f"""
                SELECT id
                FROM tracks
                WHERE id IN ({placeholders})
                """,
                tuple(unique_ids)
            ).fetchall()

            existing_ids = {row["id"] for row in existing}
            missing_ids = unique_ids - existing_ids

            if missing_ids:
                raise ValueError(
                    "Uma ou mais músicas não existem na biblioteca."
                )

            row = db.execute(
                """
                SELECT COUNT(*) AS total,
                       COALESCE(MAX(position), -1) AS last_position
                FROM playlist_tracks
                WHERE playlist_id = ?
                """,
                (playlist_id,)
            ).fetchone()

            total = row["total"]

            if position is None:
                position = row["last_position"] + 1
            else:
                position = max(0, min(int(position), total))

            db.execute(
                """
                UPDATE playlist_tracks
                SET position = position + ?
                WHERE playlist_id = ?
                  AND position >= ?
                """,
                (len(track_ids), playlist_id, position)
            )

            db.executemany(
                """
                INSERT INTO playlist_tracks (
                    playlist_id,
                    track_id,
                    position
                )
                VALUES (?, ?, ?)
                """,
                [
                    (playlist_id, track_id, position + index)
                    for index, track_id in enumerate(track_ids)
                ]
            )

            db.execute(
                """
                UPDATE playlists
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (playlist_id,)
            )

            return len(track_ids)


    def replace_playlist_tracks(self, playlist_id, track_ids):
        ordered_ids = []
        seen = set()

        for value in track_ids or []:
            track_id = int(value)
            if track_id not in seen:
                seen.add(track_id)
                ordered_ids.append(track_id)

        with self._connect() as db:
            playlist = db.execute(
                "SELECT id FROM playlists WHERE id = ?",
                (playlist_id,)
            ).fetchone()

            if playlist is None:
                raise ValueError("Playlist não encontrada.")

            if ordered_ids:
                placeholders = ",".join(
                    "?" for _ in ordered_ids
                )
                rows = db.execute(
                    f"SELECT id FROM tracks WHERE id IN ({placeholders})",
                    tuple(ordered_ids)
                ).fetchall()
                valid_ids = {row["id"] for row in rows}
                ordered_ids = [
                    item for item in ordered_ids
                    if item in valid_ids
                ]

            db.execute(
                "DELETE FROM playlist_tracks WHERE playlist_id = ?",
                (playlist_id,)
            )

            db.executemany(
                """
                INSERT INTO playlist_tracks (
                    playlist_id, track_id, position
                )
                VALUES (?, ?, ?)
                """,
                [
                    (playlist_id, track_id, index)
                    for index, track_id in enumerate(ordered_ids)
                ]
            )

            db.execute(
                """
                UPDATE playlists
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (playlist_id,)
            )

            return len(ordered_ids)

    def remove_playlist_track(self, entry_id):
        with self._connect() as db:
            entry = db.execute(
                """
                SELECT playlist_id, position
                FROM playlist_tracks
                WHERE id = ?
                """,
                (entry_id,)
            ).fetchone()

            if entry is None:
                return False

            playlist_id = entry["playlist_id"]
            position = entry["position"]

            db.execute(
                "DELETE FROM playlist_tracks WHERE id = ?",
                (entry_id,)
            )

            db.execute(
                """
                UPDATE playlist_tracks
                SET position = position - 1
                WHERE playlist_id = ?
                  AND position > ?
                """,
                (playlist_id, position)
            )

            db.execute(
                """
                UPDATE playlists
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (playlist_id,)
            )

            return True

    def move_playlist_track(
        self,
        playlist_id,
        entry_id,
        new_position
    ):
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT id
                FROM playlist_tracks
                WHERE playlist_id = ?
                ORDER BY position, id
                """,
                (playlist_id,)
            ).fetchall()

            entry_ids = [row["id"] for row in rows]

            if entry_id not in entry_ids:
                return False

            old_position = entry_ids.index(entry_id)
            entry_ids.pop(old_position)

            new_position = max(
                0,
                min(int(new_position), len(entry_ids))
            )

            entry_ids.insert(new_position, entry_id)

            for position, current_entry_id in enumerate(entry_ids):
                db.execute(
                    """
                    UPDATE playlist_tracks
                    SET position = ?
                    WHERE id = ?
                      AND playlist_id = ?
                    """,
                    (position, current_entry_id, playlist_id)
                )

            db.execute(
                """
                UPDATE playlists
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (playlist_id,)
            )

            return True

    def set_playlist_track_order(self, playlist_id, entry_ids):
        entry_ids = list(entry_ids or [])

        if len(entry_ids) != len(set(entry_ids)):
            raise ValueError("A ordem contém entradas repetidas.")

        with self._connect() as db:
            rows = db.execute(
                """
                SELECT id
                FROM playlist_tracks
                WHERE playlist_id = ?
                """,
                (playlist_id,)
            ).fetchall()

            existing_ids = {row["id"] for row in rows}

            if set(entry_ids) != existing_ids:
                raise ValueError(
                    "A lista enviada não corresponde às entradas da playlist."
                )

            for position, entry_id in enumerate(entry_ids):
                db.execute(
                    """
                    UPDATE playlist_tracks
                    SET position = ?
                    WHERE id = ?
                      AND playlist_id = ?
                    """,
                    (position, entry_id, playlist_id)
                )

            db.execute(
                """
                UPDATE playlists
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (playlist_id,)
            )

            return True

    def count_tracks(self):

        with self._connect() as db:

            row = db.execute(
                "SELECT COUNT(*) AS total FROM tracks"
            ).fetchone()

            return int(row["total"])

    def remove_folder(self, folder_path, protected_folders=None):
        """
        Remove do banco as faixas pertencentes à pasta informada.
        Nenhum arquivo físico é apagado.
        """

        return self.remove_folders(
            [folder_path],
            protected_folders=protected_folders
        )

    def remove_folders(self, folder_paths, protected_folders=None):
        """
        Remove faixas de várias pastas em uma única transação.

        Pastas cadastradas que continuem na biblioteca são preservadas.
        Nenhum arquivo físico é apagado.
        """

        roots = [
            Path(folder).expanduser().resolve()
            for folder in folder_paths
        ]

        protected_roots = [
            Path(folder).expanduser().resolve()
            for folder in (protected_folders or [])
        ]

        def belongs_to(path, directory):
            try:
                path.relative_to(directory)
                return True
            except ValueError:
                return False

        with self._connect() as db:

            rows = db.execute(
                "SELECT path FROM tracks"
            ).fetchall()

            paths_to_remove = []

            for row in rows:

                track_path = Path(row["path"]).resolve()

                belongs_to_removed_folder = any(
                    belongs_to(track_path, root)
                    for root in roots
                )

                if not belongs_to_removed_folder:
                    continue

                is_protected = any(
                    belongs_to(track_path, protected)
                    for protected in protected_roots
                )

                if not is_protected:
                    paths_to_remove.append(row["path"])

            if paths_to_remove:

                db.executemany(
                    "DELETE FROM tracks WHERE path = ?",
                    ((path,) for path in paths_to_remove)
                )

        return len(paths_to_remove)

    def remap_volume_paths(self, old_root, new_root):
        """
        Atualiza os caminhos das faixas quando um volume muda
        de ponto de montagem.

        Preserva os registros e metadados existentes.
        Nenhum arquivo físico é movido ou alterado.
        """

        old_root = Path(old_root).expanduser().resolve()
        new_root = Path(new_root).expanduser().resolve()

        if old_root == Path("/") or new_root == Path("/"):
            raise ValueError(
                "A raiz do sistema não pode ser usada "
                "como ponto de remapeamento."
            )

        if old_root == new_root:
            return 0

        with self._connect() as db:
            rows = db.execute(
                "SELECT path FROM tracks"
            ).fetchall()

            existing_paths = {
                str(Path(row["path"]).expanduser().resolve())
                for row in rows
            }

            changes = []

            for row in rows:
                original_path = row["path"]
                normalized_path = Path(
                    original_path
                ).expanduser().resolve()

                try:
                    relative_path = normalized_path.relative_to(old_root)
                except ValueError:
                    continue

                destination = str(
                    (new_root / relative_path).resolve()
                )

                changes.append((
                    original_path,
                    str(normalized_path),
                    destination
                ))

            if not changes:
                return 0

            source_paths = {
                normalized
                for _, normalized, _ in changes
            }

            destinations = [
                destination
                for _, _, destination in changes
            ]

            if len(destinations) != len(set(destinations)):
                raise ValueError(
                    "O remapeamento produziria caminhos duplicados."
                )

            conflicts = [
                path
                for path in destinations
                if path in existing_paths
                and path not in source_paths
            ]

            if conflicts:
                raise ValueError(
                    "Já existem músicas cadastradas nos novos caminhos. "
                    "O remapeamento foi cancelado para preservar os dados."
                )

            temporary_paths = []

            for _ in changes:
                temporary = str(
                    old_root / f".serifaplayer-remap-{uuid.uuid4().hex}"
                )
                temporary_paths.append(temporary)

            for (original, _, _), temporary in zip(
                changes, temporary_paths
            ):
                db.execute(
                    "UPDATE tracks SET path = ? WHERE path = ?",
                    (temporary, original)
                )

            for temporary, (_, _, destination) in zip(
                temporary_paths, changes
            ):
                db.execute(
                    "UPDATE tracks SET path = ? WHERE path = ?",
                    (destination, temporary)
                )

        return len(changes)

    def remap_volume_paths_batch(self, root_pairs):
        """
        Remapeia várias raízes em uma única transação SQLite.
        Qualquer falha cancela todas as alterações.
        """

        normalized_pairs = []

        for old_root, new_root in root_pairs:
            old_root = Path(old_root).expanduser().resolve()
            new_root = Path(new_root).expanduser().resolve()

            if old_root == Path("/") or new_root == Path("/"):
                raise ValueError(
                    "A raiz do sistema não pode ser usada "
                    "como ponto de remapeamento."
                )

            if old_root != new_root:
                normalized_pairs.append((old_root, new_root))

        if not normalized_pairs:
            return 0

        old_roots = [old for old, _ in normalized_pairs]

        for index, root in enumerate(old_roots):
            for other in old_roots[index + 1:]:
                if root.is_relative_to(other) or other.is_relative_to(root):
                    raise ValueError(
                        "As raízes de origem dos remapeamentos "
                        "se sobrepõem."
                    )

        with self._connect() as db:
            rows = db.execute(
                "SELECT path FROM tracks"
            ).fetchall()

            existing_paths = {
                str(Path(row["path"]).expanduser().resolve())
                for row in rows
            }

            changes = []

            for row in rows:
                original = row["path"]
                normalized = Path(original).expanduser().resolve()

                matching = [
                    (old, new)
                    for old, new in normalized_pairs
                    if normalized.is_relative_to(old)
                ]

                if not matching:
                    continue

                if len(matching) != 1:
                    raise ValueError(
                        "Uma faixa corresponde a mais de uma "
                        "raiz de origem."
                    )

                old_root, new_root = matching[0]
                relative = normalized.relative_to(old_root)
                destination = str((new_root / relative).resolve())

                changes.append((
                    original,
                    str(normalized),
                    destination
                ))

            if not changes:
                return 0

            source_paths = {
                normalized
                for _, normalized, _ in changes
            }

            destinations = [
                destination
                for _, _, destination in changes
            ]

            if len(destinations) != len(set(destinations)):
                raise ValueError(
                    "Os remapeamentos produziriam caminhos duplicados."
                )

            conflicts = [
                path
                for path in destinations
                if path in existing_paths
                and path not in source_paths
            ]

            if conflicts:
                raise ValueError(
                    "Já existem músicas cadastradas em um ou mais "
                    "destinos. Todos os remapeamentos foram cancelados."
                )

            temporary_paths = [
                str(
                    Path(original).expanduser().resolve().parent
                    / f".serifaplayer-remap-{uuid.uuid4().hex}"
                )
                for original, _, _ in changes
            ]

            for (original, _, _), temporary in zip(
                changes, temporary_paths
            ):
                db.execute(
                    "UPDATE tracks SET path = ? WHERE path = ?",
                    (temporary, original)
                )

            for temporary, (_, _, destination) in zip(
                temporary_paths, changes
            ):
                db.execute(
                    "UPDATE tracks SET path = ? WHERE path = ?",
                    (destination, temporary)
                )

        return len(changes)

    def set_track_favorite(self, track_id, is_favorite):
        with self._connect() as db:
            favorite_value = 1 if is_favorite else 0

            cursor = db.execute(
                """
                UPDATE tracks
                SET
                    favorited_at = CASE
                        WHEN ? = 1 THEN
                            CASE
                                WHEN is_favorite = 0
                                    THEN CURRENT_TIMESTAMP
                                ELSE COALESCE(
                                    favorited_at,
                                    CURRENT_TIMESTAMP
                                )
                            END
                        ELSE NULL
                    END,
                    is_favorite = ?
                WHERE id = ?
                """,
                (favorite_value, favorite_value, track_id)
            )

            return cursor.rowcount > 0

    def get_track_by_id(self, track_id):
        with self._connect() as db:
            row = db.execute(
                """
                SELECT *
                FROM tracks
                WHERE id = ?
                """,
                (track_id,)
            ).fetchone()

            return dict(row) if row else None

    def is_track_favorite(self, track_id):
        with self._connect() as db:
            row = db.execute(
                """
                SELECT is_favorite
                FROM tracks
                WHERE id = ?
                """,
                (track_id,)
            ).fetchone()

            return bool(row["is_favorite"]) if row else False

    def list_favorite_tracks(self):
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT *
                FROM tracks
                WHERE is_favorite = 1
                ORDER BY
                    artist COLLATE NOCASE,
                    album COLLATE NOCASE,
                    title COLLATE NOCASE
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def record_play(self, track_id):
        try:
            track_id = int(track_id)
        except (TypeError, ValueError):
            return False

        if track_id <= 0:
            return False

        with self._connect() as db:
            exists = db.execute(
                "SELECT 1 FROM tracks WHERE id = ?",
                (track_id,)
            ).fetchone()

            if not exists:
                return False

            db.execute("""
                INSERT INTO track_stats (
                    track_id,
                    play_count,
                    last_played_at
                )
                VALUES (?, 1, CURRENT_TIMESTAMP)

                ON CONFLICT(track_id)
                DO UPDATE SET
                    play_count = track_stats.play_count + 1,
                    last_played_at = CURRENT_TIMESTAMP
            """, (track_id,))

        return True

    def list_most_played_tracks(self, limit=6):
        limit = max(1, int(limit))

        with self._connect() as db:
            rows = db.execute("""
                SELECT
                    tracks.*,
                    track_stats.play_count,
                    track_stats.last_played_at

                FROM track_stats

                INNER JOIN tracks
                    ON tracks.id = track_stats.track_id

                WHERE track_stats.play_count > 0

                ORDER BY
                    track_stats.play_count DESC,
                    track_stats.last_played_at DESC,
                    tracks.title COLLATE NOCASE

                LIMIT ?
            """, (limit,)).fetchall()

            return [dict(row) for row in rows]

    def list_recent_tracks(self, limit=3):
        limit = max(1, int(limit))

        with self._connect() as db:
            rows = db.execute("""
                SELECT *
                FROM tracks

                ORDER BY
                    imported_at DESC,
                    id DESC

                LIMIT ?
            """, (limit,)).fetchall()

            return [dict(row) for row in rows]


    def list_most_played_albums(self, limit=8):
        limit = max(1, int(limit))

        with self._connect() as db:
            rows = db.execute("""
                SELECT
                    tracks.album,
                    COALESCE(
                        NULLIF(TRIM(tracks.album_artist), ''),
                        NULLIF(TRIM(tracks.artist), ''),
                        'Artista desconhecido'
                    ) AS artist,
                    MAX(NULLIF(tracks.cover_path, '')) AS cover_path,
                    COUNT(DISTINCT tracks.id) AS track_count,
                    SUM(track_stats.play_count) AS play_count,
                    MAX(track_stats.last_played_at) AS last_played_at

                FROM tracks

                INNER JOIN track_stats
                    ON track_stats.track_id = tracks.id

                WHERE
                    TRIM(tracks.album) != ''
                    AND track_stats.play_count > 0

                GROUP BY
                    tracks.album COLLATE NOCASE,
                    COALESCE(
                        NULLIF(TRIM(tracks.album_artist), ''),
                        NULLIF(TRIM(tracks.artist), ''),
                        'Artista desconhecido'
                    ) COLLATE NOCASE

                ORDER BY
                    play_count DESC,
                    last_played_at DESC,
                    tracks.album COLLATE NOCASE

                LIMIT ?
            """, (limit,)).fetchall()

            return [dict(row) for row in rows]

    def list_most_played_artists(self, limit=8):
        limit = max(1, int(limit))

        with self._connect() as db:
            rows = db.execute("""
                SELECT
                    COALESCE(
                        NULLIF(TRIM(tracks.artist), ''),
                        NULLIF(TRIM(tracks.album_artist), ''),
                        'Artista desconhecido'
                    ) AS name,
                    MAX(NULLIF(tracks.cover_path, '')) AS cover_path,
                    COUNT(DISTINCT tracks.id) AS track_count,
                    SUM(track_stats.play_count) AS play_count,
                    MAX(track_stats.last_played_at) AS last_played_at

                FROM tracks

                INNER JOIN track_stats
                    ON track_stats.track_id = tracks.id

                WHERE track_stats.play_count > 0

                GROUP BY
                    COALESCE(
                        NULLIF(TRIM(tracks.artist), ''),
                        NULLIF(TRIM(tracks.album_artist), ''),
                        'Artista desconhecido'
                    ) COLLATE NOCASE

                ORDER BY
                    play_count DESC,
                    last_played_at DESC,
                    name COLLATE NOCASE

                LIMIT ?
            """, (limit,)).fetchall()

            return [dict(row) for row in rows]

    def list_recent_albums(self, limit=3):
        limit = max(1, int(limit))

        with self._connect() as db:
            rows = db.execute("""
                SELECT
                    tracks.album,
                    COALESCE(
                        NULLIF(TRIM(tracks.album_artist), ''),
                        NULLIF(TRIM(tracks.artist), ''),
                        'Artista desconhecido'
                    ) AS artist,
                    MAX(NULLIF(tracks.cover_path, '')) AS cover_path,
                    COUNT(*) AS track_count,
                    MAX(tracks.imported_at) AS imported_at

                FROM tracks

                WHERE TRIM(tracks.album) != ''

                GROUP BY
                    tracks.album COLLATE NOCASE,
                    COALESCE(
                        NULLIF(TRIM(tracks.album_artist), ''),
                        NULLIF(TRIM(tracks.artist), ''),
                        'Artista desconhecido'
                    ) COLLATE NOCASE

                ORDER BY
                    imported_at DESC,
                    tracks.album COLLATE NOCASE

                LIMIT ?
            """, (limit,)).fetchall()

            return [dict(row) for row in rows]

    def list_tracks(self, limit=500):

        with self._connect() as db:

            query = """
                SELECT *
                FROM tracks
                ORDER BY
                    artist COLLATE NOCASE,
                    album COLLATE NOCASE,
                    title COLLATE NOCASE
            """

            if limit is not None:
                query += " LIMIT ?"
                rows = db.execute(query, (limit,)).fetchall()
            else:
                rows = db.execute(query).fetchall()

            return [
                dict(row)
                for row in rows
            ]