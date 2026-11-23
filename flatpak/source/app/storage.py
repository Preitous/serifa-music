"""
SerifaPlayer — Gerenciamento de armazenamento via UDisks2.

Identifica partições compatíveis e monta volumes externos
com acesso somente para leitura.
"""

import os

from dataclasses import dataclass
from typing import Optional

from gi.repository import Gio, GLib


SUPPORTED_FILESYSTEMS = {
    "ntfs": "NTFS",
    "vfat": "FAT",
    "fat": "FAT",
    "exfat": "exFAT",
    "ext4": "EXT4",
}

EFI_GUID = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
MICROSOFT_RESERVED_GUID = "e3c9e316-0b5c-4db8-817d-f92df00215ae"
MICROSOFT_RECOVERY_GUID = "de94bba4-06d1-4d40-a16a-bfd50179d6ac"

UDISKS_DESTINATION = "org.freedesktop.UDisks2"
UDISKS_ROOT = "/org/freedesktop/UDisks2"

OBJECT_MANAGER = "org.freedesktop.DBus.ObjectManager"
BLOCK_INTERFACE = "org.freedesktop.UDisks2.Block"
PARTITION_INTERFACE = "org.freedesktop.UDisks2.Partition"
FILESYSTEM_INTERFACE = "org.freedesktop.UDisks2.Filesystem"
DRIVE_INTERFACE = "org.freedesktop.UDisks2.Drive"


class StorageError(Exception):
    """Erro relacionado ao armazenamento."""


@dataclass(frozen=True)
class StoragePartition:
    device: str
    parent_device: str
    model: str
    label: str
    filesystem: str
    filesystem_name: str
    uuid: str
    size_bytes: int
    mountpoint: Optional[str]
    state: str
    read_only: Optional[bool]

    @property
    def is_mounted(self):
        return self.mountpoint is not None

    @property
    def display_name(self):
        if self.label:
            return self.label

        if self.mountpoint == "/home":
            return "SSD 720GB — /home"

        return self.model or self.device


class StorageManager:

    def __init__(self):
        try:
            self._bus = Gio.bus_get_sync(
                Gio.BusType.SYSTEM,
                None,
            )
        except GLib.Error as error:
            raise StorageError(
                f"Não foi possível acessar o barramento do sistema: {error}"
            ) from error

        self._system_disk = None

    # --------------------------------------------------
    # COMUNICAÇÃO COM UDISKS2
    # --------------------------------------------------

    @staticmethod
    def _decode(value):
        if isinstance(value, (bytes, bytearray)):
            return bytes(value).rstrip(b"\0").decode(
                "utf-8",
                errors="replace",
            )

        if isinstance(value, (list, tuple)):
            try:
                return bytes(value).rstrip(b"\0").decode(
                    "utf-8",
                    errors="replace",
                )
            except (ValueError, TypeError):
                return ""

        return str(value) if value is not None else ""

    def _get_managed_objects(self):
        try:
            result = self._bus.call_sync(
                UDISKS_DESTINATION,
                UDISKS_ROOT,
                OBJECT_MANAGER,
                "GetManagedObjects",
                None,
                GLib.VariantType("(a{oa{sa{sv}}})"),
                Gio.DBusCallFlags.NONE,
                10000,
                None,
            )

            return result.unpack()[0]

        except GLib.Error as error:
            raise StorageError(
                f"Falha ao consultar o UDisks2: {error}"
            ) from error

    @staticmethod
    def _property(interfaces, interface, name, default=None):
        properties = interfaces.get(interface, {})
        return properties.get(name, default)

    def _decode_mountpoints(self, values):
        return [
            self._decode(value)
            for value in (values or [])
            if self._decode(value)
        ]

    def _mount_info(self, device):
        objects = self._get_managed_objects()

        for interfaces in objects.values():
            block_device = self._decode(
                self._property(
                    interfaces,
                    BLOCK_INTERFACE,
                    "Device",
                    [],
                )
            )

            if block_device != device:
                continue

            mountpoints = self._decode_mountpoints(
                self._property(
                    interfaces,
                    FILESYSTEM_INTERFACE,
                    "MountPoints",
                    [],
                )
            )

            if not mountpoints:
                return None, None

            mountpoint = mountpoints[0]

            try:
                flags = os.statvfs(mountpoint).f_flag
                read_only = bool(flags & os.ST_RDONLY)
            except OSError:
                read_only = None

            return mountpoint, read_only

        return None, None

    # --------------------------------------------------
    # DETECÇÃO DO DISCO DO SISTEMA
    # --------------------------------------------------

    def _detect_system_disk(self, devices):
        for device in devices:
            mountpoints = device.get("mountpoints") or []

            if "/" in mountpoints:
                return device.get("parent_device")

        return None

    # --------------------------------------------------
    # FILTROS DE PARTIÇÕES
    # --------------------------------------------------

    def _is_excluded(self, partition, system_disk):
        parent = partition.get("parent_device", "")

        parttype = (
            partition.get("parttype") or ""
        ).lower()

        partlabel = (
            partition.get("partlabel") or ""
        ).lower()

        mountpoints = partition.get("mountpoints") or []

        if parent.startswith("/dev/nvme"):
            return True

        if parttype == EFI_GUID:
            return True

        if "efi" in partlabel or "esp" in partlabel:
            return True

        if parttype in (
            MICROSOFT_RESERVED_GUID,
            MICROSOFT_RECOVERY_GUID,
        ):
            return True

        if "recovery" in partlabel:
            return True

        if "reserved" in partlabel:
            return True

        if "/" in mountpoints:
            return True

        if system_disk and parent == system_disk:
            if "/home" not in mountpoints:
                return True

        return False

    # --------------------------------------------------
    # LISTAGEM DE PARTIÇÕES
    # --------------------------------------------------

    def list_partitions(self):
        objects = self._get_managed_objects()
        raw_partitions = []

        for object_path, interfaces in objects.items():
            if PARTITION_INTERFACE not in interfaces:
                continue

            block = interfaces.get(BLOCK_INTERFACE)
            if block is None:
                continue

            device = self._decode(block.get("Device", []))
            filesystem = self._decode(
                block.get("IdType", "")
            ).lower()

            label = self._decode(block.get("IdLabel", ""))
            volume_uuid = self._decode(
                block.get("IdUUID", "")
            )

            size = int(block.get("Size", 0))

            partition_info = interfaces[PARTITION_INTERFACE]

            table_path = partition_info.get("Table", "")
            parent_interfaces = objects.get(table_path, {})
            parent_block = parent_interfaces.get(BLOCK_INTERFACE, {})

            parent_device = self._decode(
                parent_block.get("Device", [])
            )

            drive_path = block.get("Drive", "")
            drive_interfaces = objects.get(drive_path, {})
            drive_info = drive_interfaces.get(DRIVE_INTERFACE, {})

            model = self._decode(
                drive_info.get("Model", "")
            ).strip()

            parttype = self._decode(
                partition_info.get("Type", "")
            ).lower()

            partlabel = self._decode(
                partition_info.get("Name", "")
            )

            mountpoints = self._decode_mountpoints(
                interfaces.get(
                    FILESYSTEM_INTERFACE, {}
                ).get("MountPoints", [])
            )

            raw_partitions.append({
                "path": device,
                "parent_device": parent_device,
                "model": model,
                "label": label,
                "fstype": filesystem,
                "uuid": volume_uuid,
                "size": size,
                "parttype": parttype,
                "partlabel": partlabel,
                "mountpoints": mountpoints,
            })

        system_disk = self._detect_system_disk(raw_partitions)
        self._system_disk = system_disk

        result = []

        for partition in raw_partitions:
            filesystem = partition["fstype"]

            if filesystem not in SUPPORTED_FILESYSTEMS:
                continue

            if self._is_excluded(partition, system_disk):
                continue

            device = partition["path"]
            if not device:
                continue

            mountpoints = partition["mountpoints"]
            mountpoint = mountpoints[0] if mountpoints else None

            if mountpoint:
                try:
                    flags = os.statvfs(mountpoint).f_flag
                    read_only = bool(flags & os.ST_RDONLY)
                except OSError:
                    read_only = None

                if read_only is True:
                    state = "mounted_ro"
                elif read_only is False:
                    state = "mounted_rw"
                else:
                    state = "mounted_unknown"
            else:
                read_only = None
                state = "unmounted"

            result.append(
                StoragePartition(
                    device=device,
                    parent_device=partition["parent_device"],
                    model=partition["model"],
                    label=partition["label"],
                    filesystem=filesystem,
                    filesystem_name=SUPPORTED_FILESYSTEMS[filesystem],
                    uuid=partition["uuid"],
                    size_bytes=partition["size"],
                    mountpoint=mountpoint,
                    state=state,
                    read_only=read_only,
                )
            )

        return result

    # --------------------------------------------------
    # IDENTIFICAÇÃO ESTÁVEL DE VOLUMES
    # --------------------------------------------------

    def find_partition_by_uuid(self, volume_uuid):
        if not volume_uuid:
            raise StorageError("UUID de volume inválido.")

        matches = [
            partition
            for partition in self.list_partitions()
            if partition.uuid == volume_uuid
        ]

        if not matches:
            raise StorageError(
                f"Nenhuma partição compatível encontrada para o UUID {volume_uuid}."
            )

        if len(matches) > 1:
            raise StorageError(
                f"O UUID {volume_uuid} aparece em mais de uma partição. "
                "A montagem automática foi bloqueada por segurança."
            )

        return matches[0]

    def find_partition_for_path(self, folder_path):
        if not folder_path:
            raise StorageError("Caminho de pasta inválido.")

        folder_path = os.path.realpath(
            os.path.expanduser(str(folder_path))
        )

        if not os.path.exists(folder_path):
            raise StorageError(
                f"O caminho não está acessível: {folder_path}"
            )

        matches = []

        for partition in self.list_partitions():
            mountpoint = partition.mountpoint

            if not mountpoint:
                continue

            mountpoint = os.path.realpath(mountpoint)

            try:
                if os.path.commonpath(
                    [folder_path, mountpoint]
                ) == mountpoint:
                    matches.append((partition, mountpoint))
            except ValueError:
                continue

        if not matches:
            raise StorageError(
                "A pasta não pertence a uma partição compatível "
                "ou sua identificação é ambígua."
            )

        matches.sort(
            key=lambda item: len(item[1]),
            reverse=True,
        )

        return matches[0]

    # --------------------------------------------------
    # MONTAGEM SOMENTE PARA LEITURA
    # --------------------------------------------------

    def mount_uuid_read_only(self, volume_uuid):
        partition = self.find_partition_by_uuid(volume_uuid)
        mountpoint = self.mount_read_only(partition.device)
        partition = self.find_partition_by_uuid(volume_uuid)

        return partition, mountpoint

    def mount_read_only(self, device):
        if not isinstance(device, str):
            raise StorageError("Dispositivo inválido.")

        available = {
            partition.device: partition
            for partition in self.list_partitions()
        }

        partition = available.get(device)

        if partition is None:
            raise StorageError(
                "Partição não autorizada para montagem."
            )

        if partition.mountpoint == "/home":
            raise StorageError(
                "A partição /home já está disponível."
            )

        if (
            self._system_disk
            and partition.parent_device == self._system_disk
        ):
            raise StorageError(
                "Partição pertencente ao disco do sistema."
            )

        if partition.is_mounted:
            if partition.read_only is True:
                return partition.mountpoint

            if partition.read_only is False:
                raise StorageError(
                    "A partição já está montada com leitura e gravação. "
                    "Desmonte-a pelo sistema e tente novamente."
                )

            raise StorageError(
                "Não foi possível confirmar as permissões da montagem."
            )

        objects = self._get_managed_objects()
        object_path = None

        for path, interfaces in objects.items():
            if BLOCK_INTERFACE not in interfaces:
                continue

            current_device = self._decode(
                interfaces[BLOCK_INTERFACE].get("Device", [])
            )

            if current_device == device:
                if FILESYSTEM_INTERFACE in interfaces:
                    object_path = path
                    break

        if object_path is None:
            raise StorageError(
                "Não foi possível localizar o dispositivo no UDisks2."
            )

        parameters = GLib.Variant(
            "(a{sv})",
            ({
                "options": GLib.Variant("s", "ro"),
            },),
        )

        try:
            self._bus.call_sync(
                UDISKS_DESTINATION,
                object_path,
                FILESYSTEM_INTERFACE,
                "Mount",
                parameters,
                GLib.VariantType("(s)"),
                Gio.DBusCallFlags.NONE,
                120000,
                None,
            )

        except GLib.Error as error:
            raise StorageError(
                f"Falha ao montar {device}: {error}"
            ) from error

        mountpoint, read_only = self._mount_info(device)

        if not mountpoint or read_only is not True:
            raise StorageError(
                "A montagem não foi confirmada como somente leitura."
            )

        return mountpoint

    # --------------------------------------------------
    # INFORMAÇÕES DE TAMANHO
    # --------------------------------------------------

    @staticmethod
    def format_size(size_bytes):
        size = float(size_bytes)

        units = ["B", "KB", "MB", "GB", "TB"]

        for unit in units:
            if size < 1024 or unit == "TB":
                return f"{size:.1f} {unit}"

            size /= 1024

        return f"{size:.1f} TB"


# --------------------------------------------------
# TESTE PELO TERMINAL
# --------------------------------------------------

if __name__ == "__main__":
    try:
        manager = StorageManager()
        partitions = manager.list_partitions()

        if not partitions:
            print("Nenhuma partição compatível encontrada.")

        for partition in partitions:
            size = manager.format_size(partition.size_bytes)

            if partition.state == "mounted_ro":
                status = "Montada • somente leitura"
            elif partition.state == "mounted_rw":
                status = "Montada • leitura e escrita"
            elif partition.state == "mounted_unknown":
                status = "Montada • estado desconhecido"
            else:
                status = "Desmontada"

            print(
                f"{partition.display_name} | "
                f"{partition.device} | "
                f"{partition.filesystem_name} | "
                f"{size} | "
                f"{status}"
            )

    except StorageError as error:
        print(f"ERRO: {error}")
