import json
import tomllib
import hashlib
import re
import tempfile

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication


SVG_ICON_SCALE = 1.00




def get_theme_color(section, name, default=None):
    """Consulta uma cor na paleta externa do Serifa Music."""
    app = QApplication.instance()
    manager = (
        app.property("serifa_appearance_manager")
        if app is not None else None
    )

    if manager is None:
        return default

    return manager.get_color(section, name, default)


def get_theme_value(configuration, section, name, default=None):
    """Consulta dimensões e valores nas configurações externas."""
    app = QApplication.instance()
    manager = (
        app.property("serifa_appearance_manager")
        if app is not None else None
    )

    if manager is None:
        return default

    return manager.get_value(
        configuration,
        section,
        name,
        default
    )


class IconManager:
    """Gerencia os ícones externos e seus estados visuais."""

    VALID_STATES = {
        "normal",
        "hover",
        "active",
        "pressed",
        "disabled",
    }

    def __init__(self, icons_directory, configuration):
        self.icons_directory = Path(icons_directory).resolve()
        self.configuration = configuration
        self.entries = configuration.get("icons", {})

    def identifiers(self):
        return list(self.entries.keys())

    def has_icon(self, identifier):
        return identifier in self.entries

    def _entry(self, identifier):
        return self.entries.get(identifier, {})

    def _state_entry(self, identifier, state):
        if state not in self.VALID_STATES:
            raise ValueError(
                f"Estado de ícone inválido: {state}"
            )

        entry = self._entry(identifier)
        states = entry.get("states", {})

        return states.get(state, {})

    def fallback(self, identifier, state="normal"):
        state_data = self._state_entry(identifier, state)

        value = state_data.get("fallback")

        if value is not None:
            return str(value)

        normal_data = self._state_entry(
            identifier,
            "normal"
        )

        return str(normal_data.get("fallback", ""))

    def _resolve_file(self, relative_path):
        if not relative_path:
            return None

        candidate = (
            self.icons_directory / str(relative_path)
        ).resolve()

        try:
            candidate.relative_to(self.icons_directory)
        except ValueError:
            return None

        if not candidate.is_file():
            return None

        return candidate

    def _scaled_svg_path(self, path, scale=None):
        """Gera uma cópia temporária do SVG com escala visual configurável."""

        if scale is None:
            scale = SVG_ICON_SCALE

        try:
            scale = float(scale)
        except (TypeError, ValueError):
            scale = SVG_ICON_SCALE

        if not 0 < scale <= 2:
            scale = SVG_ICON_SCALE

        if path.suffix.lower() != ".svg":
            return path

        content = path.read_text(encoding="utf-8")

        match = re.search(
            r"""viewBox\s*=\s*(['"])(.*?)\1""",
            content,
            re.DOTALL
        )

        if match is None:
            return path

        values = re.split(r"[\s,]+", match.group(2).strip())

        if len(values) != 4:
            return path

        try:
            x, y, width, height = map(float, values)
        except ValueError:
            return path

        if width <= 0 or height <= 0:
            return path

        new_width = width / scale
        new_height = height / scale

        new_x = x - (new_width - width) / 2
        new_y = y - (new_height - height) / 2

        new_viewbox = (
            f"{new_x:.6f} {new_y:.6f} "
            f"{new_width:.6f} {new_height:.6f}"
        )

        digest = hashlib.sha256(
            (content + str(scale)).encode("utf-8")
        ).hexdigest()[:20]

        cache_directory = (
            Path(tempfile.gettempdir()) / "serifa_music_svg_icons"
        )
        cache_directory.mkdir(parents=True, exist_ok=True)

        cached_path = cache_directory / f"{digest}.svg"

        if not cached_path.exists():
            scaled_content = (
                content[:match.start(2)]
                + new_viewbox
                + content[match.end(2):]
            )
            cached_path.write_text(scaled_content, encoding="utf-8")

        return cached_path

    def icon(self, identifier, state="normal", size=None):
        """Retorna um QIcon. Sem arquivo disponível, retorna QIcon vazio."""

        if state not in self.VALID_STATES:
            raise ValueError(
                f"Estado de ícone inválido: {state}"
            )

        state_data = self._state_entry(identifier, state)

        path = self._resolve_file(
            state_data.get("file")
        )

        if path is None and state != "normal":
            normal_data = self._state_entry(
                identifier,
                "normal"
            )

            path = self._resolve_file(
                normal_data.get("file")
            )

        if path is None:
            return QIcon()

        result = QIcon(str(self._scaled_svg_path(path, self._entry(identifier).get("scale"))))

        if result.isNull():
            return QIcon()

        if size is not None:
            result.actualSize(QSize(size, size))

        return result

    def resolve(self, identifier, state="normal"):
        """Retorna o ícone e o fallback textual correspondente."""

        return (
            self.icon(identifier, state),
            self.fallback(identifier, state)
        )


class AppearanceManager:
    """Carrega os arquivos externos de personalização."""

    CONFIGURATION_FILES = {
        "colors": "colors.toml",
        "typography": "typography.toml",
        "components": "components.toml",
        "layout": "layout.toml",
        "splash": "splash.toml",
    }

    def __init__(self, customization_directory=None):
        project_root = Path(__file__).resolve().parent.parent

        if customization_directory is None:
            customization_directory = (
                project_root / "customization"
            )

        self.root = Path(
            customization_directory
        ).resolve()

        self.colors = {}
        self.typography = {}
        self.components = {}
        self.layout = {}
        self.splash = {}
        self.stylesheet = ""
        self.icon_manager = None

        self.reload()

    def _load_toml(self, filename):
        path = self.root / filename

        if not path.is_file():
            raise FileNotFoundError(
                f"Arquivo de configuração ausente: {path}"
            )

        try:
            with path.open("rb") as stream:
                data = tomllib.load(stream)
        except Exception as error:
            raise ValueError(
                f"Erro ao ler {filename}: {error}"
            ) from error

        if not isinstance(data, dict):
            raise ValueError(
                f"Configuração inválida em {filename}."
            )

        return data

    def _load_json(self, filename):
        path = self.root / filename

        if not path.is_file():
            raise FileNotFoundError(
                f"Arquivo de configuração ausente: {path}"
            )

        try:
            with path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
        except Exception as error:
            raise ValueError(
                f"Erro ao ler {filename}: {error}"
            ) from error

        if not isinstance(data, dict):
            raise ValueError(
                f"Configuração inválida em {filename}."
            )

        return data

    def reload(self):
        """Relê todas as configurações do disco."""

        loaded = {}

        for key, filename in self.CONFIGURATION_FILES.items():
            loaded[key] = self._load_toml(filename)

        icon_configuration = self._load_json(
            "icons.json"
        )

        icons_directory = self.root / "icons"

        if not icons_directory.is_dir():
            raise FileNotFoundError(
                f"Pasta de ícones ausente: {icons_directory}"
            )

        stylesheet_path = self.root / "theme.qss"

        if not stylesheet_path.is_file():
            raise FileNotFoundError(
                f"Arquivo de tema ausente: {stylesheet_path}"
            )

        stylesheet = stylesheet_path.read_text(
            encoding="utf-8"
        )

        icon_manager = IconManager(
            icons_directory,
            icon_configuration
        )

        self.colors = loaded["colors"]
        self.typography = loaded["typography"]
        self.components = loaded["components"]
        self.layout = loaded["layout"]
        self.splash = loaded["splash"]
        self.stylesheet = stylesheet
        self.icon_manager = icon_manager

    def get_color(self, section, name, default=None):
        return self.colors.get(
            section,
            {}
        ).get(name, default)

    def get_value(self, configuration, section, name, default=None):
        data = getattr(self, configuration, None)

        if not isinstance(data, dict):
            return default

        return data.get(
            section,
            {}
        ).get(name, default)
