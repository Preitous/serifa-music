import asyncio
import threading

from dbus_next.aio import MessageBus
from dbus_next.constants import PropertyAccess
from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next import Variant

from PySide6.QtCore import QObject, Signal


class MprisBridge(QObject):
    play_pause = Signal()
    play = Signal()
    pause = Signal()
    stop = Signal()
    next_track = Signal()
    previous_track = Signal()
    seek_relative = Signal(int)
    seek_absolute = Signal(int)
    set_volume = Signal(float)


class MprisRoot(ServiceInterface):
    def __init__(self):
        super().__init__("org.mpris.MediaPlayer2")

    @dbus_property(access=PropertyAccess.READ)
    def Identity(self) -> "s":
        return "Serifa Music"

    @dbus_property(access=PropertyAccess.READ)
    def DesktopEntry(self) -> "s":
        return "serifamusic"

    @dbus_property(access=PropertyAccess.READ)
    def CanQuit(self) -> "b":
        return False

    @dbus_property(access=PropertyAccess.READ)
    def CanRaise(self) -> "b":
        return True

    @dbus_property(access=PropertyAccess.READ)
    def HasTrackList(self) -> "b":
        return False

    @dbus_property(access=PropertyAccess.READ)
    def SupportedUriSchemes(self) -> "as":
        return []

    @dbus_property(access=PropertyAccess.READ)
    def SupportedMimeTypes(self) -> "as":
        return []

    @method()
    def Raise(self):
        pass

    @method()
    def Quit(self):
        pass


class MprisPlayer(ServiceInterface):
    def __init__(self, bridge):
        super().__init__("org.mpris.MediaPlayer2.Player")
        self.bridge = bridge
        self.status = "Stopped"
        self.metadata = {}
        self.position = 0
        self.volume = 1.0
        self.can_next = False
        self.can_previous = False

    @dbus_property(access=PropertyAccess.READ)
    def PlaybackStatus(self) -> "s":
        return self.status

    @dbus_property(access=PropertyAccess.READ)
    def LoopStatus(self) -> "s":
        return "None"

    @dbus_property(access=PropertyAccess.READ)
    def Rate(self) -> "d":
        return 1.0

    @dbus_property(access=PropertyAccess.READ)
    def Shuffle(self) -> "b":
        return False

    @dbus_property(access=PropertyAccess.READ)
    def Metadata(self) -> "a{sv}":
        return self.metadata

    @dbus_property(access=PropertyAccess.READ)
    def Position(self) -> "x":
        return self.position

    @dbus_property(access=PropertyAccess.READ)
    def MinimumRate(self) -> "d":
        return 1.0

    @dbus_property(access=PropertyAccess.READ)
    def MaximumRate(self) -> "d":
        return 1.0

    @dbus_property(access=PropertyAccess.READ)
    def CanGoNext(self) -> "b":
        return self.can_next

    @dbus_property(access=PropertyAccess.READ)
    def CanGoPrevious(self) -> "b":
        return self.can_previous

    @dbus_property(access=PropertyAccess.READ)
    def CanPlay(self) -> "b":
        return bool(self.metadata)

    @dbus_property(access=PropertyAccess.READ)
    def CanPause(self) -> "b":
        return bool(self.metadata)

    @dbus_property(access=PropertyAccess.READ)
    def CanSeek(self) -> "b":
        return bool(self.metadata)

    @dbus_property(access=PropertyAccess.READ)
    def CanControl(self) -> "b":
        return True

    @dbus_property(access=PropertyAccess.READ)
    def Volume(self) -> "d":
        return self.volume

    @Volume.setter
    def Volume(self, value: "d"):
        self.bridge.set_volume.emit(max(0.0, min(1.0, value)))

    @method()
    def Next(self):
        self.bridge.next_track.emit()

    @method()
    def Previous(self):
        self.bridge.previous_track.emit()

    @method()
    def Pause(self):
        self.bridge.pause.emit()

    @method()
    def PlayPause(self):
        self.bridge.play_pause.emit()

    @method()
    def Stop(self):
        self.bridge.stop.emit()

    @method()
    def Play(self):
        self.bridge.play.emit()

    @method()
    def Seek(self, Offset: "x"):
        self.bridge.seek_relative.emit(Offset)

    @method()
    def SetPosition(self, TrackId: "o", Position: "x"):
        self.bridge.seek_absolute.emit(Position)

    @method()
    def OpenUri(self, Uri: "s"):
        pass


class MprisService:
    BUS_NAME = "org.mpris.MediaPlayer2.serifamusic"
    OBJECT_PATH = "/org/mpris/MediaPlayer2"

    def __init__(self, bridge):
        self.bridge = bridge
        self.loop = None
        self.bus = None
        self.player = MprisPlayer(bridge)
        self._shutdown_event = None
        self._stop_requested = threading.Event()
        self.thread = threading.Thread(
            target=self._thread_main,
            daemon=True
        )

    def start(self):
        self.thread.start()

    def _thread_main(self):
        asyncio.run(self._run())

    async def _run(self):
        self.loop = asyncio.get_running_loop()

        try:
            self.bus = await MessageBus().connect()
            await self.bus.request_name(self.BUS_NAME)

            self.bus.export(
                self.OBJECT_PATH,
                MprisRoot()
            )
            self.bus.export(
                self.OBJECT_PATH,
                self.player
            )

            self._shutdown_event = asyncio.Event()

            if self._stop_requested.is_set():
                self._shutdown_event.set()

            await self._shutdown_event.wait()

        except asyncio.CancelledError:
            pass
        except Exception as error:
            print(f"[MPRIS] Erro no serviço: {error}", flush=True)
        finally:
            if self.bus:
                self.bus.disconnect()

    def update(self, track, status, position, volume,
               can_next=False, can_previous=False):
        if not self.loop or not self.loop.is_running():
            return

        self.loop.call_soon_threadsafe(
            self._apply_update,
            track,
            status,
            position,
            volume,
            can_next,
            can_previous
        )

    def _apply_update(self, track, status, position, volume,
                      can_next, can_previous):
        metadata = {}

        if track:
            title = str(track.get("title") or "Faixa desconhecida")
            artist = str(
                track.get("artist")
                or track.get("album_artist")
                or "Artista desconhecido"
            )
            album = str(track.get("album") or "")
            path = str(track.get("path") or "")
            track_id = str(abs(hash(path)) or 1)

            metadata = {
                "mpris:trackid": Variant(
                    "o",
                    f"/org/serifamusic/track/{track_id}"
                ),
                "xesam:title": Variant("s", title),
                "xesam:artist": Variant("as", [artist]),
            }

            if album:
                metadata["xesam:album"] = Variant("s", album)

            duration = float(track.get("duration") or 0)
            if duration > 0:
                metadata["mpris:length"] = Variant(
                    "x",
                    int(duration * 1_000_000)
                )

            cover = track.get("cover_path")
            if cover:
                metadata["mpris:artUrl"] = Variant(
                    "s",
                    f"file://{cover}"
                )

        changed = {}

        if self.player.status != status:
            self.player.status = status
            changed["PlaybackStatus"] = status

        if self.player.metadata != metadata:
            self.player.metadata = metadata
            changed["Metadata"] = metadata

        new_position = max(0, int(position * 1_000_000))
        if self.player.position != new_position:
            self.player.position = new_position

        new_volume = max(0.0, min(1.0, float(volume)))
        if self.player.volume != new_volume:
            self.player.volume = new_volume
            changed["Volume"] = new_volume

        if self.player.can_next != can_next:
            self.player.can_next = can_next
            changed["CanGoNext"] = can_next

        if self.player.can_previous != can_previous:
            self.player.can_previous = can_previous
            changed["CanGoPrevious"] = can_previous

        if changed:
            self.player.emit_properties_changed(changed)

    def stop(self):
        self._stop_requested.set()

        if (
            self.loop
            and self.loop.is_running()
            and self._shutdown_event is not None
        ):
            self.loop.call_soon_threadsafe(
                self._shutdown_event.set
            )

        if self.thread.is_alive():
            self.thread.join(timeout=2)
