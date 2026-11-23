from pathlib import Path
import time

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst


class AudioPlayer:

    def __init__(self):
        Gst.init(None)

        self.players = []
        self.buses = []
        self.filters = []

        self.active_deck = 0
        self.current_path = None
        self.is_playing = False
        self.is_paused = False

        self.master_volume = 0.7
        self.deck_gains = [1.0, 0.0]

        self.crossfade_active = False
        self.crossfade_start = 0.0
        self.crossfade_paused_at = None
        self.crossfade_duration = 5.0
        self.crossfade_from = 0
        self.crossfade_to = 1
        self.crossfade_outgoing_finished = False

        self.eq_enabled = False
        self.eq_mode = "basic"
        self.eq_preamp = 0.0

        self.eq_basic_gains = [0.0] * 10
        self.eq_advanced_gains = [0.0] * 25

        self.eq_basic_frequencies = [
            29, 59, 119, 237, 474,
            947, 1889, 3770, 7523, 15011
        ]

        self.eq_advanced_frequencies = []

        for index in range(2):
            player = Gst.ElementFactory.make(
                "playbin",
                f"serifa-deck-{index}"
            )

            if player is None:
                raise RuntimeError(
                    f"Não foi possível criar o deck de áudio {index + 1}."
                )

            audio_filter = self._build_audio_filter(index)

            player.set_property("audio-filter", audio_filter)
            player.set_property("volume", 0.0 if index == 1 else self.master_volume)

            self.players.append(player)
            self.buses.append(player.get_bus())
            self.filters.append(audio_filter)

        self.player = self.players[0]
        self.bus = self.buses[0]

        self._apply_equalizer()

    def _build_audio_filter(self, deck_index):
        audio_filter = Gst.Bin.new(
            f"serifa-audio-filter-{deck_index}"
        )

        if audio_filter is None:
            raise RuntimeError(
                "Não foi possível criar o filtro de áudio."
            )

        preamp = Gst.ElementFactory.make(
            "volume",
            f"serifa-preamp-{deck_index}"
        )

        eq_basic = Gst.ElementFactory.make(
            "equalizer-10bands",
            f"serifa-eq-basic-{deck_index}"
        )

        eq_advanced = Gst.ElementFactory.make(
            "equalizer-nbands",
            f"serifa-eq-advanced-{deck_index}"
        )

        if any(
            element is None
            for element in (preamp, eq_basic, eq_advanced)
        ):
            raise RuntimeError(
                "Não foi possível criar os elementos do equalizador."
            )

        eq_advanced.set_property("num-bands", 25)

        if deck_index == 0:
            for index in range(25):
                band = eq_advanced.get_child_by_name(
                    f"band{index}"
                )
                self.eq_advanced_frequencies.append(
                    band.get_property("freq")
                )

        audio_filter.add(preamp)
        audio_filter.add(eq_basic)
        audio_filter.add(eq_advanced)

        if not preamp.link(eq_basic):
            raise RuntimeError(
                "Falha ao conectar o preamp ao EQ básico."
            )

        if not eq_basic.link(eq_advanced):
            raise RuntimeError(
                "Falha ao conectar os equalizadores."
            )

        ghost_sink = Gst.GhostPad.new(
            "sink",
            preamp.get_static_pad("sink")
        )

        ghost_src = Gst.GhostPad.new(
            "src",
            eq_advanced.get_static_pad("src")
        )

        if not audio_filter.add_pad(ghost_sink):
            raise RuntimeError(
                "Falha ao criar a entrada do filtro de áudio."
            )

        if not audio_filter.add_pad(ghost_src):
            raise RuntimeError(
                "Falha ao criar a saída do filtro de áudio."
            )

        if deck_index == 0:
            self.preamp = preamp
            self.eq_basic = eq_basic
            self.eq_advanced = eq_advanced

        return audio_filter

    def _apply_equalizer(self):
        basic_active = (
            self.eq_enabled and self.eq_mode == "basic"
        )

        advanced_active = (
            self.eq_enabled and self.eq_mode == "advanced"
        )

        preamp_db = self.eq_preamp if self.eq_enabled else 0.0
        preamp_value = 10 ** (preamp_db / 20.0)

        for audio_filter in self.filters:
            preamp = audio_filter.get_by_name(
                audio_filter.get_name().replace(
                    "serifa-audio-filter",
                    "serifa-preamp"
                )
            )

            eq_basic = audio_filter.get_by_name(
                audio_filter.get_name().replace(
                    "serifa-audio-filter",
                    "serifa-eq-basic"
                )
            )

            eq_advanced = audio_filter.get_by_name(
                audio_filter.get_name().replace(
                    "serifa-audio-filter",
                    "serifa-eq-advanced"
                )
            )

            preamp.set_property("volume", preamp_value)

            for index, gain in enumerate(self.eq_basic_gains):
                eq_basic.set_property(
                    f"band{index}",
                    gain if basic_active else 0.0
                )

            for index, gain in enumerate(self.eq_advanced_gains):
                band = eq_advanced.get_child_by_name(
                    f"band{index}"
                )
                band.set_property(
                    "gain",
                    gain if advanced_active else 0.0
                )

    def set_eq_enabled(self, enabled):
        self.eq_enabled = bool(enabled)
        self._apply_equalizer()

    def set_eq_mode(self, mode):
        if mode not in ("basic", "advanced"):
            raise ValueError(
                "Modo inválido. Utilize 'basic' ou 'advanced'."
            )

        self.eq_mode = mode
        self._apply_equalizer()

    def set_eq_preamp(self, value):
        self.eq_preamp = max(
            -12.0,
            min(12.0, float(value))
        )
        self._apply_equalizer()

    def set_eq_band_gain(self, index, value, mode=None):
        mode = mode or self.eq_mode
        value = max(-24.0, min(12.0, float(value)))

        if mode == "basic":
            if not 0 <= index < 10:
                raise IndexError(
                    "Índice de banda básica inválido."
                )
            self.eq_basic_gains[index] = value

        elif mode == "advanced":
            if not 0 <= index < 25:
                raise IndexError(
                    "Índice de banda avançada inválido."
                )
            self.eq_advanced_gains[index] = value

        else:
            raise ValueError("Modo inválido.")

        self._apply_equalizer()

    def get_eq_band_frequencies(self, mode=None):
        mode = mode or self.eq_mode

        if mode == "basic":
            return list(self.eq_basic_frequencies)

        if mode == "advanced":
            return list(self.eq_advanced_frequencies)

        raise ValueError("Modo inválido.")

    def get_eq_gains(self, mode=None):
        mode = mode or self.eq_mode

        if mode == "basic":
            return list(self.eq_basic_gains)

        if mode == "advanced":
            return list(self.eq_advanced_gains)

        raise ValueError("Modo inválido.")

    def set_eq_settings(
        self,
        enabled=None,
        mode=None,
        preamp=None,
        basic_gains=None,
        advanced_gains=None
    ):
        if mode is not None and mode not in ("basic", "advanced"):
            raise ValueError("Modo inválido.")

        if basic_gains is not None and len(basic_gains) != 10:
            raise ValueError("O EQ básico precisa de 10 ganhos.")

        if advanced_gains is not None and len(advanced_gains) != 25:
            raise ValueError("O EQ avançado precisa de 25 ganhos.")

        if mode is not None:
            self.eq_mode = mode

        if enabled is not None:
            self.eq_enabled = bool(enabled)

        if preamp is not None:
            self.eq_preamp = max(
                -12.0,
                min(12.0, float(preamp))
            )

        if basic_gains is not None:
            self.eq_basic_gains = [
                max(-24.0, min(12.0, float(value)))
                for value in basic_gains
            ]

        if advanced_gains is not None:
            self.eq_advanced_gains = [
                max(-24.0, min(12.0, float(value)))
                for value in advanced_gains
            ]

        self._apply_equalizer()

    def _set_deck_volume(self, index):
        started = time.perf_counter()

        gain = max(0.0, min(1.0, self.deck_gains[index]))
        self.players[index].set_property(
            "volume",
            self.master_volume * gain
        )

        elapsed = (time.perf_counter() - started) * 1000.0
        if elapsed >= 5.0:
            print(
                f"[Crossfade Detail] set volume deck {index}: "
                f"{elapsed:.1f} ms",
                flush=True
            )

    def _stop_deck(self, index):
        started = time.perf_counter()

        result = self.players[index].set_state(Gst.State.NULL)

        elapsed = (time.perf_counter() - started) * 1000.0

        if elapsed >= 10.0:
            print(
                f"[GStreamer] _stop_deck({index}): "
                f"{elapsed:.1f} ms | resultado: {result}",
                flush=True
            )

        self.deck_gains[index] = 0.0
        self._set_deck_volume(index)

    def _stop_crossfade(self):
        if not self.crossfade_active:
            return

        self._stop_deck(self.crossfade_from)
        self.crossfade_active = False
        self.crossfade_outgoing_finished = False

    def play(self, file_path):
        path = Path(file_path).expanduser().resolve()

        if not path.is_file():
            raise FileNotFoundError(
                f"Arquivo de áudio não encontrado: {path}"
            )

        self.stop()

        index = self.active_deck
        player = self.players[index]

        self.deck_gains = [0.0, 0.0]
        self.deck_gains[index] = 1.0
        self._set_deck_volume(index)

        self.current_path = path
        player.set_property("uri", path.as_uri())

        result = player.set_state(Gst.State.PLAYING)

        if result == Gst.StateChangeReturn.FAILURE:
            self.current_path = None
            raise RuntimeError(
                "O GStreamer não conseguiu iniciar a reprodução."
            )

        self.is_playing = True
        self.is_paused = False

    def load_paused(self, file_path):
        path = Path(file_path).expanduser().resolve()

        if not path.is_file():
            raise FileNotFoundError(
                f"Arquivo de áudio não encontrado: {path}"
            )

        self.stop()

        index = self.active_deck
        player = self.players[index]

        self.deck_gains = [0.0, 0.0]
        self.deck_gains[index] = 1.0
        self._set_deck_volume(index)

        self.current_path = path
        player.set_property("uri", path.as_uri())

        result = player.set_state(Gst.State.PAUSED)

        if result == Gst.StateChangeReturn.FAILURE:
            self.current_path = None
            raise RuntimeError(
                "O GStreamer não conseguiu carregar a faixa pausada."
            )

        self.is_playing = False
        self.is_paused = True

    def start_crossfade(self, file_path, duration_seconds=5.0):
        path = Path(file_path).expanduser().resolve()

        if not path.is_file():
            raise FileNotFoundError(
                f"Arquivo de áudio não encontrado: {path}"
            )

        if not self.is_playing or self.is_paused:
            return False

        if self.crossfade_active:
            return False

        started = time.perf_counter()

        incoming = 1 - self.active_deck
        outgoing = self.active_deck

        step_started = time.perf_counter()
        self._stop_deck(incoming)
        elapsed = (time.perf_counter() - step_started) * 1000.0
        if elapsed >= 5.0:
            print(
                f"[Crossfade Detail] prepare deck: {elapsed:.1f} ms",
                flush=True
            )

        step_started = time.perf_counter()
        self.players[incoming].set_property(
            "uri",
            path.as_uri()
        )
        elapsed = (time.perf_counter() - step_started) * 1000.0
        if elapsed >= 5.0:
            print(
                f"[Crossfade Detail] set URI: {elapsed:.1f} ms",
                flush=True
            )

        self.deck_gains[incoming] = 0.0
        self._set_deck_volume(incoming)

        step_started = time.perf_counter()
        result = self.players[incoming].set_state(
            Gst.State.PLAYING
        )
        elapsed = (time.perf_counter() - step_started) * 1000.0
        if elapsed >= 5.0:
            print(
                f"[Crossfade Detail] start incoming deck: "
                f"{elapsed:.1f} ms | resultado: {result}",
                flush=True
            )

        if result == Gst.StateChangeReturn.FAILURE:
            self._stop_deck(incoming)
            raise RuntimeError(
                "Não foi possível iniciar a próxima faixa."
            )

        self.crossfade_from = outgoing
        self.crossfade_to = incoming
        self.crossfade_duration = max(
            1.0,
            min(12.0, float(duration_seconds))
        )
        self.crossfade_start = time.monotonic()
        self.crossfade_active = True
        self.crossfade_outgoing_finished = False

        self.active_deck = incoming
        self.current_path = path

        elapsed = (time.perf_counter() - started) * 1000.0
        if elapsed >= 10.0:
            print(
                f"[Crossfade Detail] start_crossfade total: "
                f"{elapsed:.1f} ms",
                flush=True
            )

        return True

    def update_crossfade(self):
        if not self.crossfade_active:
            return False

        if self.is_paused or not self.is_playing:
            return False

        update_started = time.perf_counter()
        elapsed = time.monotonic() - self.crossfade_start

        outgoing_duration = max(
            0.5,
            self.crossfade_duration / 2.0
        )

        outgoing_progress = min(
            1.0,
            elapsed / outgoing_duration
        )

        incoming_progress = min(
            1.0,
            elapsed / self.crossfade_duration
        )

        outgoing = self.crossfade_from
        incoming = self.crossfade_to

        self.deck_gains[outgoing] = 1.0 - outgoing_progress
        self.deck_gains[incoming] = incoming_progress

        self._set_deck_volume(outgoing)
        self._set_deck_volume(incoming)

        if incoming_progress >= 1.0:
            self._stop_deck(outgoing)
            self.deck_gains[incoming] = 1.0
            self._set_deck_volume(incoming)
            self.crossfade_active = False
            self.crossfade_paused_at = None
            self.crossfade_outgoing_finished = False

        update_elapsed = (
            time.perf_counter() - update_started
        ) * 1000.0

        if update_elapsed >= 10.0:
            print(
                f"[Crossfade Detail] update_crossfade total: "
                f"{update_elapsed:.1f} ms",
                flush=True
            )

        return True


    def pause(self):
        if not self.is_playing:
            return

        if self.crossfade_active:
            self.crossfade_paused_at = time.monotonic()

        for player in self.players:
            player.set_state(Gst.State.PAUSED)

        self.is_playing = False
        self.is_paused = True


    def resume(self):
        if not self.is_paused:
            return

        if (
            self.crossfade_active
            and self.crossfade_paused_at is not None
        ):
            paused_duration = (
                time.monotonic() - self.crossfade_paused_at
            )

            self.crossfade_start += paused_duration
            self.crossfade_paused_at = None

        for player in self.players:
            if player.current_state != Gst.State.NULL:
                player.set_state(Gst.State.PLAYING)

        self.is_playing = True
        self.is_paused = False


    def toggle_pause(self):
        if self.is_playing:
            self.pause()
        elif self.is_paused:
            self.resume()

    def stop(self):
        for index in range(2):
            self.players[index].set_state(Gst.State.NULL)

        self.deck_gains = [0.0, 0.0]
        self.crossfade_active = False
        self.crossfade_paused_at = None
        self.crossfade_outgoing_finished = False
        self.current_path = None
        self.is_playing = False
        self.is_paused = False

        for index in range(2):
            self._set_deck_volume(index)

    def set_volume(self, value):
        self.master_volume = max(
            0.0,
            min(100.0, float(value))
        ) / 100.0

        for index in range(2):
            self._set_deck_volume(index)

    def get_position(self, deck=None):
        deck_index = (
            self.active_deck if deck is None else deck
        )

        success, position = self.players[
            deck_index
        ].query_position(Gst.Format.TIME)

        if success:
            return position / Gst.SECOND

        return 0

    def get_duration(self, deck=None):
        deck_index = (
            self.active_deck if deck is None else deck
        )

        success, duration = self.players[
            deck_index
        ].query_duration(Gst.Format.TIME)

        if success:
            return duration / Gst.SECOND

        return 0

    def seek(self, position_seconds):
        player = self.players[self.active_deck]

        success, duration = player.query_duration(
            Gst.Format.TIME
        )

        if not success or duration <= 0:
            return False

        position = max(
            0.0,
            min(float(position_seconds), duration / Gst.SECOND)
        )

        return player.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            int(position * Gst.SECOND)
        )

    def poll_bus(self):
        messages = []

        for index, bus in enumerate(self.buses):
            while True:
                message = bus.pop_filtered(
                    Gst.MessageType.ERROR |
                    Gst.MessageType.EOS
                )

                if message is None:
                    break

                if message.type == Gst.MessageType.ERROR:
                    error, debug = message.parse_error()

                    if index == self.crossfade_from and self.crossfade_active:
                        self.crossfade_outgoing_finished = True
                        self._stop_deck(index)
                        continue

                    self.is_playing = False
                    self.is_paused = False

                    messages.append({
                        "type": "error",
                        "message": str(error),
                        "debug": debug
                    })

                elif message.type == Gst.MessageType.EOS:
                    if (
                        self.crossfade_active
                        and index == self.crossfade_from
                    ):
                        self.crossfade_outgoing_finished = True
                        self._stop_deck(index)
                        continue

                    if index != self.active_deck:
                        continue

                    self.is_playing = False
                    self.is_paused = False

                    messages.append({
                        "type": "eos"
                    })

        return messages
