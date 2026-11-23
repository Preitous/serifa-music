from pathlib import Path
import random
import uuid


class PlaybackQueue:
    """Gerencia histórico, faixa atual e sequência futura."""

    def __init__(self):
        self.context_tracks = []
        self._context_entries = []

        self.current_entry = None
        self.upcoming = []
        self.history = []

        self.shuffle_enabled = False
        self.repeat_mode = "off"

        self._shuffle_order = []

    @property
    def current_track(self):
        if self.current_entry is None:
            return None
        return self.current_entry["track"]

    @staticmethod
    def _path(track):
        if not track or not track.get("path"):
            return None

        return str(Path(track["path"]).expanduser().resolve())

    @staticmethod
    def _make_entry(track):
        return {
            "id": uuid.uuid4().hex,
            "track": track,
        }

    @staticmethod
    def _copy_entry(entry):
        if entry is None:
            return None

        return {
            "id": entry["id"],
            "track": entry["track"],
        }

    def get_current_entry(self):
        return self._copy_entry(self.current_entry)

    def get_upcoming_entries(self):
        return [
            self._copy_entry(entry)
            for entry in self.upcoming
        ]

    def get_history_entries(self):
        return [
            self._copy_entry(entry)
            for entry in self.history
        ]

    def get_queue_entries(self):
        return self.get_upcoming_entries()

    def _find_context_index(self, tracks, current_track):
        for index, track in enumerate(tracks):
            if track is current_track:
                return index

        entry_id = current_track.get("playlist_entry_id")

        if entry_id is not None:
            for index, track in enumerate(tracks):
                if track.get("playlist_entry_id") == entry_id:
                    return index

        current_path = self._path(current_track)

        if current_path is not None:
            for index, track in enumerate(tracks):
                if self._path(track) == current_path:
                    return index

        return None

    def _sync_shuffle_order(self):
        if self.shuffle_enabled:
            self._shuffle_order = [
                entry["id"]
                for entry in self.upcoming
            ]

    def play_immediately(self, track):
        """Troca a faixa atual sem descartar a sequência futura."""

        if not track:
            return None

        if self.current_entry is not None:
            self.history.append(self.current_entry)

        self.current_entry = self._make_entry(track)

        self.context_tracks = [track]
        self._context_entries = [self.current_entry]

        self._sync_shuffle_order()

        return self.current_track

    def start_group(self, tracks):
        """Inicia um grupo preservando a fila futura existente."""

        tracks = list(tracks or [])

        if not tracks:
            return None

        previous_upcoming = list(self.upcoming)

        if self.current_entry is not None:
            self.history.append(self.current_entry)

        self.context_tracks = list(tracks)

        self._context_entries = [
            self._make_entry(track)
            for track in self.context_tracks
        ]

        self.current_entry = self._context_entries[0]

        self.upcoming = (
            self._context_entries[1:]
            + previous_upcoming
        )

        self._sync_shuffle_order()

        return self.current_track

    def set_context(self, tracks, current_track):
        """Inicia um novo contexto preservando o histórico de reprodução."""

        previous_entry = self._copy_entry(self.current_entry)

        self.context_tracks = list(tracks or [])

        self._context_entries = [
            self._make_entry(track)
            for track in self.context_tracks
        ]

        self.upcoming.clear()
        self._shuffle_order.clear()

        index = self._find_context_index(
            self.context_tracks,
            current_track
        )

        if index is None:
            if previous_entry is not None:
                self.history.append(previous_entry)

            self.current_entry = self._make_entry(current_track)
            self.upcoming = list(self._context_entries)

        else:
            previous_index = None

            if previous_entry is not None:
                previous_index = self._find_context_index(
                    self.context_tracks,
                    previous_entry["track"]
                )

            if (
                previous_entry is not None
                and (
                    previous_index is None
                    or previous_index >= index
                )
            ):
                self.history.append(previous_entry)

            self.history.extend(
                self._context_entries[:index]
            )

            self.current_entry = self._context_entries[index]
            self.upcoming = self._context_entries[index + 1:]

        if self.shuffle_enabled:
            self._activate_shuffle()

    def _activate_shuffle(self):
        self._shuffle_order = [
            entry["id"]
            for entry in self.upcoming
        ]

        random.shuffle(self.upcoming)

    def add_next(self, track):
        """Adiciona uma faixa no início da sequência futura."""

        if not track:
            return None

        entry = self._make_entry(track)
        self.upcoming.insert(0, entry)
        self._sync_shuffle_order()

        return entry["id"]

    def add_to_end(self, track):
        """Adiciona uma faixa ao final da sequência futura."""

        if not track:
            return None

        entry = self._make_entry(track)
        self.upcoming.append(entry)
        self._sync_shuffle_order()

        return entry["id"]

    def add_tracks(self, tracks, position=None):
        """Insere várias faixas consecutivas em uma posição."""

        entries = [
            self._make_entry(track)
            for track in (tracks or [])
            if track
        ]

        if not entries:
            return []

        if position is None:
            position = len(self.upcoming)

        position = max(
            0,
            min(int(position), len(self.upcoming))
        )

        self.upcoming[position:position] = entries
        self._sync_shuffle_order()

        return [
            entry["id"]
            for entry in entries
        ]

    def remove_entry(self, entry_id):
        """Remove uma ocorrência específica da sequência futura."""

        for index, entry in enumerate(self.upcoming):
            if entry["id"] == entry_id:
                removed = self.upcoming.pop(index)
                self._sync_shuffle_order()
                return self._copy_entry(removed)

        return None

    def move_entry(self, entry_id, new_position):
        """Move uma ocorrência dentro da sequência futura."""

        old_position = next(
            (
                index
                for index, entry in enumerate(self.upcoming)
                if entry["id"] == entry_id
            ),
            None
        )

        if old_position is None:
            return False

        entry = self.upcoming.pop(old_position)

        new_position = max(
            0,
            min(int(new_position), len(self.upcoming))
        )

        self.upcoming.insert(new_position, entry)
        self._sync_shuffle_order()

        return True

    def play_entry(self, entry_id):
        """Toca uma faixa futura e transfere as anteriores ao histórico."""

        selected_index = next(
            (
                index
                for index, entry in enumerate(self.upcoming)
                if entry["id"] == entry_id
            ),
            None
        )

        if selected_index is None:
            return None

        selected = self.upcoming[selected_index]

        skipped = self.upcoming[:selected_index]

        if self.current_entry is not None:
            self.history.append(self.current_entry)

        self.history.extend(skipped)

        self.current_entry = selected
        self.upcoming = self.upcoming[selected_index + 1:]

        self._sync_shuffle_order()

        return self.current_track

    def _refill_context(self):
        """Reconstrói o contexto preservando ocorrências duplicadas."""

        if not self._context_entries:
            return

        current_id = (
            self.current_entry["id"]
            if self.current_entry is not None
            else None
        )

        current_index = next(
            (
                index
                for index, entry in enumerate(self._context_entries)
                if entry["id"] == current_id
            ),
            None
        )

        if current_index is None:
            entries = list(self._context_entries)
        else:
            entries = (
                self._context_entries[current_index + 1:]
                + self._context_entries[:current_index]
            )

        if self.shuffle_enabled:
            self.upcoming = entries
            self._activate_shuffle()
        else:
            self.upcoming.extend(entries)

    def next_track(self, on_end=False, preferred_entry_id=None):
        """Avança para a próxima faixa, podendo respeitar uma ocorrência reservada."""

        if (
            on_end
            and self.repeat_mode == "track"
            and self.current_track
        ):
            return self.current_track

        if not self.upcoming and self.repeat_mode == "queue":
            self._refill_context()

        if not self.upcoming:
            return None

        if preferred_entry_id is not None:
            selected_index = next(
                (
                    index
                    for index, entry in enumerate(self.upcoming)
                    if entry["id"] == preferred_entry_id
                ),
                None
            )

            if selected_index is None:
                return None

            next_entry = self.upcoming.pop(selected_index)
        else:
            next_entry = self.upcoming.pop(0)

        if self.current_entry is not None:
            self.history.append(self.current_entry)

        self.current_entry = next_entry

        if self.shuffle_enabled:
            self._shuffle_order = [
                entry_id
                for entry_id in self._shuffle_order
                if entry_id != next_entry["id"]
            ]

        return self.current_track

    def previous_track(self):
        """Volta no histórico e preserva a sequência futura."""

        if not self.history:
            return None

        previous = self.history.pop()

        if self.current_entry is not None:
            self.upcoming.insert(0, self.current_entry)

        self.current_entry = previous

        if self.shuffle_enabled:
            self._shuffle_order = [
                self.current_entry["id"]
            ] + [
                entry_id
                for entry_id in self._shuffle_order
                if entry_id != self.current_entry["id"]
            ]

        return self.current_track

    def toggle_shuffle(self):
        self.shuffle_enabled = not self.shuffle_enabled

        if self.shuffle_enabled:
            self._activate_shuffle()

        elif self._shuffle_order:
            order = {
                entry_id: index
                for index, entry_id in enumerate(self._shuffle_order)
            }

            self.upcoming.sort(
                key=lambda entry: order.get(
                    entry["id"],
                    len(order)
                )
            )

            self._shuffle_order.clear()

        return self.shuffle_enabled

    def cycle_repeat(self):
        modes = ("off", "queue", "track")

        self.repeat_mode = modes[
            (modes.index(self.repeat_mode) + 1) % len(modes)
        ]

        return self.repeat_mode

    def clear(self):
        self.context_tracks.clear()
        self._context_entries.clear()

        self.current_entry = None
        self.upcoming.clear()
        self.history.clear()

        self.shuffle_enabled = False
        self.repeat_mode = "off"

        self._shuffle_order.clear()
