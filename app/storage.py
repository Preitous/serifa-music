"""
SerifaPlayer — Gerenciamento de armazenamento.

Responsabilidades:
- Identificar partições compatíveis.
- Ignorar o NVMe do Windows.
- Ocultar partições de sistema, EFI e recuperação.
- Preservar o acesso ao /home.
- Montar discos autorizados com leitura e gravação.
- Confirmar as opções reais de montagem.

Este módulo não altera arquivos dos discos de música.
"""

import json
import os
import shutil
import subprocess

from dataclasses import dataclass
from typing import Optional


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

SYSTEM_DISK = None


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

    LSBLK_COLUMNS = (
        "NAME,PATH,TYPE,SIZE,FSTYPE,LABEL,UUID,"
        "MOUNTPOINTS,RO,MODEL,PARTLABEL,PARTTYPE,PARTFLAGS"
    )

    def __init__(self):

        self._check_dependencies()
        self._system_disk = None

    # --------------------------------------------------
    # DEPENDÊNCIAS
    # --------------------------------------------------

    def _check_dependencies(self):

        required = [
            "lsblk",
            "findmnt",
            "udisksctl",
        ]

        missing = [
            command
            for command in required
            if shutil.which(command) is None
        ]

        if missing:
            raise StorageError(
                "Dependências ausentes: "
                + ", ".join(missing)
            )

    # --------------------------------------------------
    # EXECUÇÃO DE COMANDOS
    # --------------------------------------------------

    def _run(self, command):

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

        except subprocess.TimeoutExpired:
            raise StorageError(
                "O comando demorou demais para responder."
            )

        except OSError as error:
            raise StorageError(str(error))

        if result.returncode != 0:
            message = result.stderr.strip()

            raise StorageError(
                message or "Falha ao executar comando."
            )

        return result.stdout

    # --------------------------------------------------
    # INFORMAÇÕES DE MONTAGEM
    # --------------------------------------------------

    def _mount_info(self, device):

        try:
            output = self._run([
                "findmnt",
                "--json",
                "--source",
                device,
                "--output",
                "TARGET,OPTIONS",
            ])

            data = json.loads(output)

            filesystems = data.get(
                "filesystems", []
            )

            if not filesystems:
                return None, None

            item = filesystems[0]

            target = item.get("target")
            options = item.get("options", "")

            read_only = "ro" in options.split(",")

            return target, read_only

        except (StorageError, json.JSONDecodeError):
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

        device = partition.get("path", "")

        parent = partition.get(
            "parent_device", ""
        )

        parttype = (
            partition.get("parttype") or ""
        ).lower()

        partlabel = (
            partition.get("partlabel") or ""
        ).lower()

        mountpoints = partition.get("mountpoints") or []

        # Ignora completamente o NVMe do Windows.

        if parent.startswith("/dev/nvme"):
            return True

        # Partições EFI.

        if parttype == EFI_GUID:
            return True

        if "efi" in partlabel:
            return True

        if "esp" in partlabel:
            return True

        # Partições reservadas e recuperação do Windows.

        if parttype in (
            MICROSOFT_RESERVED_GUID,
            MICROSOFT_RECOVERY_GUID,
        ):
            return True

        if "recovery" in partlabel:
            return True

        if "reserved" in partlabel:
            return True

        # A raiz do sistema nunca aparece na biblioteca.

        if "/" in mountpoints:
            return True

        # No disco do Zorin, preservamos somente o /home.

        if system_disk and parent == system_disk:

            if "/home" not in mountpoints:
                return True

        return False

    # --------------------------------------------------
    # LISTAGEM DE PARTIÇÕES
    # --------------------------------------------------

    def list_partitions(self):

        output = self._run([
            "lsblk",
            "--json",
            "--bytes",
            "--output",
            self.LSBLK_COLUMNS,
        ])

        data = json.loads(output)

        partitions = []

        def visit(node, parent=None):

            node_type = node.get("type")

            current_parent = parent

            if node_type == "disk":
                current_parent = node.get("path")

            if node_type == "part":

                partition = dict(node)

                partition["parent_device"] = current_parent

                partitions.append(partition)

            for child in node.get("children", []):

                visit(child, current_parent)

        for device in data.get("blockdevices", []):

            visit(device)

        # Identifica o disco que contém a raiz do sistema.

        system_disk = self._detect_system_disk(
            partitions
        )

        self._system_disk = system_disk

        result = []

        for partition in partitions:

            filesystem = (
                partition.get("fstype") or ""
            ).lower()

            if filesystem not in SUPPORTED_FILESYSTEMS:
                continue

            if self._is_excluded(
                partition,
                system_disk,
            ):
                continue

            device = partition.get("path")

            if not device:
                continue

            mountpoint, read_only = self._mount_info(
                device
            )

            if mountpoint:

                if read_only is True:
                    state = "mounted_ro"

                elif read_only is False:
                    state = "mounted_rw"

                else:
                    state = "mounted_unknown"

            else:
                state = "unmounted"

            result.append(
                StoragePartition(
                    device=device,
                    parent_device=partition.get(
                        "parent_device", ""
                    ),
                    model=partition.get("model") or "",
                    label=partition.get("label") or "",
                    filesystem=filesystem,
                    filesystem_name=SUPPORTED_FILESYSTEMS[
                        filesystem
                    ],
                    uuid=partition.get("uuid") or "",
                    size_bytes=int(
                        partition.get("size") or 0
                    ),
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
        """
        Localiza uma partição pelo UUID do sistema de arquivos.
        Recusa UUIDs ausentes ou duplicados.
        """

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
        """
        Identifica a partição que contém um caminho existente.
        Não depende do nome do dispositivo nem do ponto de montagem.
        """

        if not folder_path:
            raise StorageError("Caminho de pasta inválido.")

        folder_path = os.path.abspath(
            os.path.expanduser(str(folder_path))
        )

        if not os.path.exists(folder_path):
            raise StorageError(
                f"O caminho não está acessível: {folder_path}"
            )

        try:
            output = self._run([
                "findmnt",
                "--json",
                "--target",
                folder_path,
                "--output",
                "SOURCE,TARGET,OPTIONS",
            ])

            data = json.loads(output)
            filesystems = data.get("filesystems", [])

            if not filesystems:
                raise StorageError(
                    "Não foi possível identificar o volume da pasta."
                )

            mount = filesystems[0]
            source = mount.get("source") or ""
            target = mount.get("target")

            # Remove a indicação de subvolume, quando presente.
            source = source.split("[", 1)[0]

            source_real = os.path.realpath(source)

            matches = [
                partition
                for partition in self.list_partitions()
                if os.path.realpath(partition.device) == source_real
            ]

            if len(matches) != 1:
                raise StorageError(
                    "A pasta não pertence a uma partição compatível "
                    "ou sua identificação é ambígua."
                )

            return matches[0], target

        except json.JSONDecodeError as error:
            raise StorageError(
                "Resposta inválida ao identificar o volume."
            ) from error

    def mount_uuid_read_only(self, volume_uuid):
        """
        Localiza uma partição pelo UUID e solicita montagem
        somente para leitura.
        """

        partition = self.find_partition_by_uuid(volume_uuid)

        mountpoint = self.mount_read_only(partition.device)

        return partition, mountpoint

    # --------------------------------------------------
    # MONTAGEM SOMENTE PARA LEITURA
    # --------------------------------------------------

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

        self._run([
            "udisksctl",
            "mount",
            "--block-device",
            device,
            "--options",
            "ro",
        ])

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

        units = [
            "B",
            "KB",
            "MB",
            "GB",
            "TB",
        ]

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

            size = manager.format_size(
                partition.size_bytes
            )

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
