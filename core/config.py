import shutil
from pathlib import Path
from typing import Any

import tomlkit
from dotenv import load_dotenv
from tomlkit.toml_document import TOMLDocument

from core.logger import LogLevel
from core.utils.working_dir import CONFIG_DIR

load_dotenv()


class Config:
    """Configuration manager using TOML for persistence"""

    # increment when breaking changes are made
    CONFIG_VERSION = 1

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or CONFIG_DIR / "config.toml"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config: TOMLDocument = self._load()

    def _load(self) -> TOMLDocument:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                doc = tomlkit.load(f)

            # check config version compatibility
            config_version = doc.get("general", {}).get("config_version", 0)
            if config_version != self.CONFIG_VERSION:
                # version mismatch - backup old config and create new one
                backup_path = self.config_path.with_suffix(
                    f".toml.v{config_version}.bak"
                )
                self.config_path.rename(backup_path)
                return self._create_default()

            return doc
        return self._create_default()

    def _create_default(self) -> TOMLDocument:
        """Create default configuration"""
        doc = tomlkit.document()
        doc.add(tomlkit.comment("MP4 Mux Tool Configuration"))
        doc.add(tomlkit.nl())

        # general settings
        general = tomlkit.table()
        general.add("config_version", self.CONFIG_VERSION)
        general.add("log_level", "INFO")
        general.add("theme", "Auto")
        general.add("mp4box_path", "")

        doc.add("general", general)

        return doc

    def save(self) -> None:
        """Save configuration to file"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            tomlkit.dump(self._config, f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value from general section"""
        return self._config.get("general", {}).get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value in general section"""
        if "general" not in self._config:
            self._config["general"] = tomlkit.table()
        self._config["general"][key] = value  # pyright: ignore[reportIndexIssue]

    @property
    def log_level(self) -> LogLevel:
        """Get log level as enum"""
        level_str = self.get("log_level", "INFO")
        try:
            return LogLevel[level_str.upper()]
        except KeyError:
            return LogLevel.INFO

    @log_level.setter
    def log_level(self, value: LogLevel) -> None:
        """Set log level from enum"""
        self.set("log_level", str(value))

    @property
    def theme(self) -> str:
        """Get theme setting"""
        return self.get("theme", "Auto")

    @theme.setter
    def theme(self, value: str) -> None:
        """Set theme setting"""
        self.set("theme", value)

    @property
    def mp4box_path(self) -> str:
        """Get MP4Box executable path"""
        stored_path = self.get("mp4box_path", "")

        # if empty or doesn't exist, try to auto-detect
        if not stored_path or not Path(stored_path).exists():
            detected = shutil.which("mp4box")
            if detected:
                # cache the detected path
                self.set("mp4box_path", detected)
                return detected
            return "mp4box"  # fallback to hoping it's in PATH

        return stored_path

    @mp4box_path.setter
    def mp4box_path(self, value: str) -> None:
        """Set MP4Box executable path"""
        self.set("mp4box_path", value)


Conf = Config()
