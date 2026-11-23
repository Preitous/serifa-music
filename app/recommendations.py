
import math
import re
import unicodedata
from pathlib import Path

from difflib import SequenceMatcher
from datetime import datetime


class RecommendationEngine:
    """
    Motor local de recomendações do SerifaPlayer.

    Trabalha exclusivamente com os metadados recebidos.
    Não altera o banco de dados nem os arquivos musicais.
    """

    UNKNOWN_ARTISTS = {
        "",
        "artista desconhecido",
        "unknown",
        "unknown artist",
        "various artists",
        "various",
        "desconhecido",
    }

    COLLABORATION_MARKERS = (
        r"\s*\(\s*feat(?:uring)?\.?\s+.*$",
        r"\s*\[\s*feat(?:uring)?\.?\s+.*$",
        r"\s+\bfeat(?:uring)?\.?\s+.*$",
        r"\s+\bft\.?\s+.*$",
        r"\s+\bwith\s+.*$",
    )

    GENRE_RULES = (
        ("symphonic", "symphonic", 1.0),
        ("sympho", "symphonic", 1.0),
        ("simpho", "symphonic", 1.0),
        ("gothic", "gothic", 1.0),
        ("alternative", "alternative", 1.0),
        ("alt.", "alternative", 1.0),
        ("metalcore", "metalcore", 1.0),
        ("nu metal", "nu_metal", 1.0),
        ("nu-metal", "nu_metal", 1.0),
        ("hard rock", "hard_rock", 1.0),
        ("heavy metal", "heavy_metal", 1.0),
        ("power metal", "power_metal", 1.0),
        ("progressive", "progressive", 1.0),
        ("death metal", "death_metal", 1.0),
        ("neo classical", "neo_classical", 1.0),
        ("neo-classical", "neo_classical", 1.0),
        ("pop rock", "pop_rock", 1.0),
        ("industrial", "industrial", 1.0),
        ("female vocal", "female_vocals", 0.3),
        ("female vocals", "female_vocals", 0.3),
        ("metal", "metal", 0.45),
        ("rock", "rock", 0.45),
    )

    EDITION_SUFFIXES = (
        r"\s*[\[(]\s*japanese(?:\s+limited)?(?:\s+deluxe)?(?:\s+edition)?\s*[\])]\s*$",
        r"\s*[\[(]\s*japan(?:\s+\d{4})?\s*[\])]\s*$",
        r"\s*[\[(]\s*limited(?:\s+edition)?\s*[\])]\s*$",
        r"\s*[\[(]\s*deluxe(?:\s+edition)?\s*[\])]\s*$",
        r"\s*[\[(]\s*tour\s+edition\s*[\])]\s*$",
        r"\s*[\[(]\s*black\s+edition\s*[\])]\s*$",
        r"\s*[\[(]\s*bonus\s+cd\s*[\])]\s*$",
        r"\s*[\[(]\s*(?:with\s+)?bonus\s+track\s*[\])]\s*$",
        r"\s*[\[(]\s*walmart\s+exclusive\s*[\])]\s*$",
        r"\s*[\[(]\s*wpcr-\d+\s*[\])]\s*$",
    )

    def __init__(self, tracks, now=None, artist_aliases=None):
        self.tracks = [
            dict(track)
            for track in tracks
            if isinstance(track, dict)
        ]

        self.now = now or datetime.now()
        self.explicit_artist_aliases = dict(artist_aliases or {})

        self._prepare_artist_identity()
        self._prepare_data()

    @staticmethod
    def _text(value):
        return str(value or "").strip()

    @staticmethod
    def _normalize(value):
        value = unicodedata.normalize(
            "NFKD",
            str(value or "")
        )

        value = "".join(
            char for char in value
            if not unicodedata.combining(char)
        )

        return value.casefold().strip()

    @classmethod
    def _artist_token(cls, value):
        value = cls._normalize(value)
        value = re.sub(r"[^\w\s]", " ", value)
        return " ".join(value.split())

    @staticmethod
    def track_key(track):
        if not track:
            return None

        path = track.get("path")

        if path:
            return str(path).strip().casefold()

        track_id = track.get("id")

        if track_id is not None:
            return f"id:{track_id}"

        return None

    @classmethod
    def artist_name(cls, track):
        if not track:
            return "Artista desconhecido"

        artist = cls._text(track.get("artist"))
        album_artist = cls._text(track.get("album_artist"))

        if artist.casefold() in cls.UNKNOWN_ARTISTS:
            artist = ""

        if album_artist.casefold() in cls.UNKNOWN_ARTISTS:
            album_artist = ""

        if album_artist:
            return cls._clean_artist_name(album_artist)

        if artist:
            return cls._clean_artist_name(artist)

        return "Artista desconhecido"

    @classmethod
    def _clean_artist_name(cls, value):
        value = cls._text(value)

        if not value:
            return "Artista desconhecido"

        for pattern in cls.COLLABORATION_MARKERS:
            value = re.sub(
                pattern,
                "",
                value,
                flags=re.IGNORECASE
            )

        value = value.strip(" ,;/&")

        if not value:
            return "Artista desconhecido"

        return value

    @classmethod
    def album_name(cls, track):
        return cls._text(track.get("album"))

    @classmethod
    def _album_identity(cls, album):
        value = cls._normalize(album)

        changed = True

        while changed:
            changed = False

            for pattern in cls.EDITION_SUFFIXES:
                updated = re.sub(
                    pattern,
                    "",
                    value
                ).strip()

                if updated != value:
                    value = updated
                    changed = True
                    break

        value = re.sub(r"[^\w\s]", " ", value)

        return " ".join(value.split())

    @classmethod
    def _raw_album_key(cls, track):
        album = cls._album_identity(
            cls.album_name(track)
        )

        if not album:
            return None

        return album

    def _prepare_artist_identity(self):
        self.artist_aliases = {}
        self.artist_display = {}

        known_names = {}

        for track in self.tracks:
            artist = self._text(track.get("artist"))
            album_artist = self._text(track.get("album_artist"))

            artist_unknown = artist.casefold() in self.UNKNOWN_ARTISTS
            album_unknown = album_artist.casefold() in self.UNKNOWN_ARTISTS

            comma_guest = (
                not artist_unknown
                and not album_unknown
                and artist.casefold().startswith(
                    album_artist.casefold() + ","
                )
            )

            values = []

            if not artist_unknown and not comma_guest:
                values.append(artist)

            if not album_unknown and "&" not in album_artist:
                values.append(album_artist)

            for value in values:
                clean = self._clean_artist_name(value)

                if clean.casefold() in self.UNKNOWN_ARTISTS:
                    continue

                token = self._artist_token(clean)

                if token:
                    known_names.setdefault(token, clean)

        self._known_artist_tokens = set(known_names)

        for token, display in known_names.items():
            self.artist_aliases[token] = token
            self.artist_display[token] = display

        self._build_conservative_aliases(known_names)

        for alias, canonical in self.explicit_artist_aliases.items():
            alias_token = self._artist_token(alias)
            canonical_token = self._artist_token(canonical)

            canonical_token = self.artist_aliases.get(
                canonical_token,
                canonical_token
            )

            if not alias_token or not canonical_token:
                continue

            if canonical_token not in self.artist_display:
                raise ValueError(
                    f"Artista canônico não encontrado: {canonical}"
                )

            self.artist_aliases[alias_token] = canonical_token

        self._inferred_album_artists = {}
        album_artists = {}

        for track in self.tracks:
            artist = self._artist_for_track(track)
            album = self._raw_album_key(track)

            if not album or not artist:
                continue

            album_artists.setdefault(album, set()).add(artist)

        self._inferred_album_artists = {
            album: next(iter(artists))
            for album, artists in album_artists.items()
            if len(artists) == 1
        }



    def _build_conservative_aliases(self, known_names):
        tokens = list(known_names)

        for token in tokens:
            if not token:
                continue

            matches = []

            for candidate in tokens:
                if candidate == token:
                    continue

                similarity = SequenceMatcher(
                    None,
                    token,
                    candidate
                ).ratio()

                if similarity >= 0.94:
                    matches.append((similarity, candidate))

            matches.sort(reverse=True)

            if not matches:
                continue

            best_score, best_token = matches[0]

            if len(matches) > 1:
                second_score = matches[1][0]

                if best_score - second_score < 0.035:
                    continue

            self.artist_aliases[token] = best_token

    def _canonical_artist_text(self, value):
        clean = self._clean_artist_name(value)
        token = self._artist_token(clean)

        if token in self.artist_aliases:
            return self.artist_aliases[token]

        return token

    def _artist_from_path(self, track):
        raw_path = self._text(track.get("path"))

        if not raw_path:
            return None

        try:
            folders = Path(raw_path).parents
        except (TypeError, ValueError, OSError):
            return None

        for folder in folders:
            token = self._artist_token(folder.name)
            canonical = self.artist_aliases.get(token)

            if canonical in self.artist_display:
                return canonical

        return None

    def _known_artist_group(self, value):
        parts = [
            part.strip()
            for part in self._text(value).split("&")
        ]

        if len(parts) < 2:
            return []

        canonical = []

        for part in parts:
            token = self._canonical_artist_text(part)

            if token not in self.artist_display:
                return []

            if token not in canonical:
                canonical.append(token)

        return canonical if len(canonical) >= 2 else []

    def _extract_feature_names(self, value):
        text = self._text(value)

        match = re.search(
            r"(?:\(|\[)?\s*(?:feat(?:uring)?\.?|ft\.?)\s+"
            r"(.+?)\s*(?:\)|\])?$",
            text,
            flags=re.IGNORECASE
        )

        if not match:
            return []

        names = re.split(
            r"\s*(?:&|,|\band\b)\s*",
            match.group(1),
            flags=re.IGNORECASE
        )

        result = []

        for name in names:
            token = self._canonical_artist_text(name)

            if (
                token in self.artist_display
                and token not in result
            ):
                result.append(token)

        return result

    def _artist_collaborators_for_track(self, track):
        primary = self._artist_for_track(track)
        collaborators = []

        def add(name):
            token = self._canonical_artist_text(name)

            if (
                token
                and token != primary
                and token in self.artist_display
                and token not in collaborators
            ):
                collaborators.append(token)

        artist = self._text(track.get("artist"))
        album_artist = self._text(track.get("album_artist"))

        for field in (artist, album_artist, self._text(track.get("title"))):
            for guest in self._extract_feature_names(field):
                add(guest)

        for name in self._known_artist_group(album_artist):
            add(name)

        if (
            artist
            and album_artist
            and "&" not in album_artist
            and artist.casefold().startswith(
                album_artist.casefold() + ","
            )
        ):
            guest = artist[len(album_artist) + 1:].strip()

            if guest:
                add(guest)

        return collaborators

    def _artist_for_track(self, track):
        artist = self._text(track.get("artist"))
        album_artist = self._text(track.get("album_artist"))

        group = self._known_artist_group(album_artist)

        if group:
            if artist.casefold() not in self.UNKNOWN_ARTISTS:
                candidate = self._canonical_artist_text(artist)

                if candidate in group:
                    return candidate

            return group[0]

        if album_artist.casefold() not in self.UNKNOWN_ARTISTS:
            return self._canonical_artist_text(album_artist)

        if artist.casefold() not in self.UNKNOWN_ARTISTS:
            return self._canonical_artist_text(artist)

        path_artist = self._artist_from_path(track)

        if path_artist:
            return path_artist

        album = self._raw_album_key(track)

        if album and album in self._inferred_album_artists:
            return self._inferred_album_artists[album]

        title = self._text(track.get("title"))

        if " - " in title:
            prefix = title.split(" - ", 1)[0].strip()
            prefix_token = self._artist_token(prefix)

            if prefix_token in self.artist_aliases:
                return self.artist_aliases[prefix_token]

        return "artista desconhecido"


    def _artist_display_name(self, artist_key):
        if not artist_key:
            return "Artista desconhecido"

        return self.artist_display.get(
            artist_key,
            artist_key.title()
        )

    def album_key(self, track):
        album = self._raw_album_key(track)
        artist = self._artist_for_track(track)

        if not album:
            return None

        return artist, album

    @classmethod
    def genre_features(cls, genre):
        raw = cls._normalize(genre)
        features = {}

        if not raw:
            return features

        for pattern, feature, weight in cls.GENRE_RULES:
            if pattern in raw:
                features[feature] = max(
                    features.get(feature, 0.0),
                    weight
                )

        return features

    @staticmethod
    def _genre_similarity(first, second):
        if not first or not second:
            return 0.0

        keys = set(first) | set(second)

        intersection = sum(
            min(
                first.get(key, 0.0),
                second.get(key, 0.0)
            )
            for key in keys
        )

        union = sum(
            max(
                first.get(key, 0.0),
                second.get(key, 0.0)
            )
            for key in keys
        )

        return intersection / union if union else 0.0

    @staticmethod
    def _number(value):
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_date(value):
        if not value:
            return None

        try:
            parsed = datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )

            if parsed.tzinfo is not None:
                parsed = parsed.replace(tzinfo=None)

            return parsed

        except (TypeError, ValueError):
            return None

    def _recency_penalty(self, track):
        played_at = self._parse_date(
            track.get("last_played_at")
        )

        if played_at is None:
            return 0.0

        age = (
            self.now - played_at
        ).total_seconds() / 86400

        if age < 0 or age >= 14:
            return 0.0

        return 0.16 * (1.0 - age / 14.0)

    def _prepare_data(self):
        self.artist_tracks = {}
        self.album_tracks = {}

        self.artist_plays = {}
        self.album_plays = {}
        self.artist_collaborations = {}

        self.max_track_plays = max(
            (
                self._number(track.get("play_count"))
                for track in self.tracks
            ),
            default=0
        )

        for track in self.tracks:
            artist = self._artist_for_track(track)
            album_key = self.album_key(track)

            track["_recommendation_artist"] = artist

            collaborators = self._artist_collaborators_for_track(track)
            track["_recommendation_collaborators"] = collaborators

            plays = self._number(track.get("play_count"))

            self.artist_tracks.setdefault(
                artist,
                []
            ).append(track)

            self.artist_plays[artist] = (
                self.artist_plays.get(artist, 0) + plays
            )

            if album_key:
                self.album_tracks.setdefault(
                    album_key,
                    []
                ).append(track)

                self.album_plays[album_key] = (
                    self.album_plays.get(album_key, 0) + plays
                )

            for collaborator in collaborators:
                relations = self.artist_collaborations.setdefault(
                    artist,
                    {}
                )

                relations[collaborator] = (
                    relations.get(collaborator, 0) + 1
                )

                reverse = self.artist_collaborations.setdefault(
                    collaborator,
                    {}
                )

                reverse[artist] = reverse.get(artist, 0) + 1

        self.max_artist_plays = max(
            self.artist_plays.values(),
            default=0
        )

        self.max_album_plays = max(
            self.album_plays.values(),
            default=0
        )

        self.genre_profile = self._build_genre_profile()


    def _build_genre_profile(self):
        profile = {}
        total_weight = 0.0

        has_personal_data = any(
            self._number(track.get("play_count")) > 0
            or bool(self._number(track.get("is_favorite")))
            for track in self.tracks
        )

        for track in self.tracks:
            plays = self._number(
                track.get("play_count")
            )

            favorite = bool(
                self._number(track.get("is_favorite"))
            )

            weight = (
                math.log1p(plays)
                + (1.5 if favorite else 0.0)
                if has_personal_data
                else 1.0
            )

            if weight <= 0:
                continue

            features = self.genre_features(
                track.get("genre")
            )

            for feature, value in features.items():
                profile[feature] = (
                    profile.get(feature, 0.0)
                    + value * weight
                )

            total_weight += weight

        if total_weight:
            profile = {
                key: value / total_weight
                for key, value in profile.items()
            }

        return profile

    def _personal_score(self, track):
        plays = self._number(
            track.get("play_count")
        )

        artist = self._artist_for_track(track)
        album = self.album_key(track)

        track_score = (
            math.log1p(plays)
            / math.log1p(self.max_track_plays)
            if self.max_track_plays else 0.0
        )

        artist_plays = self.artist_plays.get(
            artist,
            0
        )

        artist_score = (
            math.log1p(artist_plays)
            / math.log1p(self.max_artist_plays)
            if self.max_artist_plays else 0.0
        )

        album_plays = self.album_plays.get(
            album,
            0
        )

        album_score = (
            math.log1p(album_plays)
            / math.log1p(self.max_album_plays)
            if self.max_album_plays else 0.0
        )

        favorite_score = (
            1.0
            if self._number(track.get("is_favorite"))
            else 0.0
        )

        return min(
            1.0,
            track_score * 0.45
            + artist_score * 0.25
            + album_score * 0.10
            + favorite_score * 0.20
        )

    def _track_score(self, track, seed_track=None):
        personal = self._personal_score(track)

        genres = self.genre_features(
            track.get("genre")
        )

        profile_affinity = self._genre_similarity(
            genres,
            self.genre_profile
        )

        if seed_track:
            seed_genres = self.genre_features(
                seed_track.get("genre")
            )

            similarity = self._genre_similarity(
                genres,
                seed_genres
            )

            score = (
                similarity * 0.65
                + personal * 0.25
                + profile_affinity * 0.10
            )
        else:
            score = (
                personal * 0.55
                + profile_affinity * 0.35
                + (
                    0.10
                    if self._number(track.get("is_favorite"))
                    else 0.0
                )
            )

        score -= self._recency_penalty(track)

        return max(0.0, score)

    def _select_diverse(self, scored_tracks, limit):
        selected = []
        artist_counts = {}
        album_counts = {}
        remaining = list(scored_tracks)

        while remaining and len(selected) < limit:
            best_index = None
            best_score = float("-inf")

            for index, (base_score, track) in enumerate(remaining):
                artist = self._artist_for_track(track)
                album = self.album_key(track)

                penalty = (
                    artist_counts.get(artist, 0) * 0.17
                    + album_counts.get(album, 0) * 0.10
                )

                adjusted = base_score - penalty

                if adjusted > best_score:
                    best_score = adjusted
                    best_index = index

            _, chosen = remaining.pop(best_index)
            selected.append(chosen)

            artist = self._artist_for_track(chosen)
            album = self.album_key(chosen)

            artist_counts[artist] = (
                artist_counts.get(artist, 0) + 1
            )

            if album:
                album_counts[album] = (
                    album_counts.get(album, 0) + 1
                )

        return selected

    def recommend_tracks(
        self,
        limit=10,
        seed_track=None,
        exclude_keys=None,
        exclude_artists=None,
    ):
        limit = max(0, int(limit))

        excluded_keys = {
            str(key).casefold()
            for key in (exclude_keys or [])
        }

        excluded_artists = {
            self._canonical_artist_text(name)
            for name in (exclude_artists or [])
        }

        seed_key = self.track_key(seed_track)

        if seed_key:
            excluded_keys.add(seed_key)

        scored = []

        for track in self.tracks:
            key = self.track_key(track)

            if key and key in excluded_keys:
                continue

            artist = self._artist_for_track(track)

            if artist in excluded_artists:
                continue

            score = self._track_score(
                track,
                seed_track=seed_track
            )

            scored.append((score, track))

        scored.sort(
            key=lambda item: item[0],
            reverse=True
        )

        return self._select_diverse(
            scored,
            limit
        )

    def recommend_next_track(
        self,
        current_track,
        exclude_keys=None,
        recent_artists=None,
        artist_cooldown=5,
    ):
        if not current_track:
            return None

        excluded_keys = {
            str(key).casefold()
            for key in (exclude_keys or [])
        }

        current_key = self.track_key(current_track)

        if current_key:
            excluded_keys.add(current_key)

        current_artist = self._artist_for_track(
            current_track
        )

        current_album = self.album_key(
            current_track
        )

        recent = []
        seen_artists = set()

        for name in [current_artist] + list(recent_artists or []):
            artist = self._canonical_artist_text(name)

            if artist and artist not in seen_artists:
                recent.append(artist)
                seen_artists.add(artist)

        cooldown = max(1, int(artist_cooldown))
        recent = recent[:cooldown]

        candidates = []

        for track in self.tracks:
            key = self.track_key(track)

            if key and key in excluded_keys:
                continue

            score = self._track_score(
                track,
                seed_track=current_track
            )

            if score <= 0:
                continue

            artist = self._artist_for_track(track)
            album = self.album_key(track)

            candidates.append({
                "track": track,
                "score": score,
                "artist": artist,
                "same_artist": artist == current_artist,
                "same_album": album == current_album,
            })

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        best_score = candidates[0]["score"]

        outside_cooldown = [
            item for item in candidates
            if item["artist"] not in recent
        ]

        if outside_cooldown:
            alternative = outside_cooldown[0]

            if alternative["score"] >= max(
                0.08,
                best_score * 0.35
            ):
                return alternative["track"]

        other_artists = [
            item for item in candidates
            if not item["same_artist"]
        ]

        if other_artists:
            alternative = other_artists[0]

            if alternative["score"] >= max(
                0.08,
                best_score * 0.20
            ):
                return alternative["track"]

        same_artist_other_album = [
            item for item in candidates
            if item["same_artist"]
            and not item["same_album"]
        ]

        if same_artist_other_album:
            return same_artist_other_album[0]["track"]

        return candidates[0]["track"]

    def _aggregate_genres(self, tracks):
        profile = {}

        for track in tracks:
            for feature, weight in self.genre_features(
                track.get("genre")
            ).items():
                profile[feature] = (
                    profile.get(feature, 0.0) + weight
                )

        return profile

    def recommend_artists(self, artist_name, limit=8):
        target = self._canonical_artist_text(artist_name)

        target_tracks = self.artist_tracks.get(target, [])

        if not target_tracks:
            return []

        target_genres = self._aggregate_genres(target_tracks)

        relationships = self.artist_collaborations.get(target, {})

        max_collaborations = max(
            relationships.values(),
            default=0
        )

        results = []

        for key, tracks in self.artist_tracks.items():
            if key == target:
                continue

            if key == "artista desconhecido":
                continue

            genres = self._aggregate_genres(tracks)

            similarity = self._genre_similarity(
                target_genres,
                genres
            )

            personal = (
                math.log1p(self.artist_plays.get(key, 0))
                / math.log1p(self.max_artist_plays)
                if self.max_artist_plays else 0.0
            )

            collaboration_count = relationships.get(key, 0)

            collaboration = (
                math.log1p(collaboration_count)
                / math.log1p(max_collaborations)
                if max_collaborations else 0.0
            )

            if max_collaborations:
                score = (
                    similarity * 0.70
                    + personal * 0.15
                    + collaboration * 0.15
                )
            else:
                score = similarity * 0.80 + personal * 0.20

            if score <= 0:
                continue

            results.append({
                "name": self._artist_display_name(key),
                "cover_path": next(
                    (
                        track.get("cover_path")
                        for track in tracks
                        if track.get("cover_path")
                    ),
                    None
                ),
                "track_count": len(tracks),
                "play_count": self.artist_plays.get(key, 0),
                "score": score,
            })

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results[:max(0, int(limit))]


    def recommend_albums(
        self,
        album_name,
        artist_name=None,
        limit=8
    ):
        target_album = self._album_identity(
            album_name
        )

        target_artist = (
            self._canonical_artist_text(artist_name)
            if artist_name
            else None
        )

        target_key = None

        for key in self.album_tracks:
            if key[1] != target_album:
                continue

            if target_artist and key[0] != target_artist:
                continue

            target_key = key
            break

        if target_key is None:
            return []

        target_tracks = self.album_tracks[target_key]

        target_genres = self._aggregate_genres(
            target_tracks
        )

        results = []

        for key, tracks in self.album_tracks.items():
            if key[0] == target_key[0]:
                continue

            if key[0] == "artista desconhecido":
                continue

            genres = self._aggregate_genres(tracks)

            similarity = self._genre_similarity(
                target_genres,
                genres
            )

            personal = (
                math.log1p(self.album_plays.get(key, 0))
                / math.log1p(self.max_album_plays)
                if self.max_album_plays else 0.0
            )

            score = similarity * 0.85 + personal * 0.15

            if score <= 0:
                continue

            album_names = [
                self.album_name(track)
                for track in tracks
                if self.album_name(track)
            ]

            display_album = min(
                album_names,
                key=lambda name: (
                    len(name),
                    self._normalize(name)
                )
            ) if album_names else ""

            track_titles = {
                self._normalize(track.get("title"))
                for track in tracks
                if self._normalize(track.get("title"))
            }

            results.append({
                "album": display_album,
                "artist": self._artist_display_name(key[0]),
                "cover_path": next(
                    (
                        track.get("cover_path")
                        for track in tracks
                        if track.get("cover_path")
                    ),
                    None
                ),
                "track_count": len(track_titles) or len(tracks),
                "play_count": self.album_plays.get(key, 0),
                "score": score,
            })

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results[:max(0, int(limit))]
