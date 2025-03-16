# Realms, a libadwaita libvirt client.
# Copyright (C) 2025
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Module to manage domain templates.
There are two template locations:
    - Default templates somewhere hidden inside flatpak
    - User templates anywhere
"""
from os import listdir, path

import yaml
from config import *  # pylint: disable=import-error

from realms.helpers.settings import Settings


class TemplateFile:
    def __init__(self, path: str, exists: bool, is_default: bool):
        self.path = path
        self.exists = exists
        self.is_default = is_default

        self.is_valid = True
        self.invalid_error = None
        self.__validate__()

    def getName(self) -> str:
        """Retrieve the display name for this file.

        Returns:
            str: Name
        """
        if self.is_default:
            return path.basename(self.path)
        return self.path

    def __validate__(self):
        try:
            for t in TemplateManager.listTemplatesInFile(self):
                if "name" not in t:
                    raise ValueError("Template is missing a name")
                if "template" not in t:
                    raise ValueError("Template is missing a template")

                self.__validate_settings__(t)

        except ValueError as e:
            self.is_valid = False
            self.invalid_error = f"Template error: { e }"
        except Exception as e:
            self.is_valid = False
            self.invalid_error = f"Template file error: { e }"

    def __validate_settings__(self, t: dict):
        if "settings" not in t:
            return

        for s in t["settings"]:
            if "name" not in s:
                raise ValueError("Setting is missing a name")
            if "type" not in s:
                raise ValueError("Setting is missing a type")


class TemplateManager:
    @classmethod
    def listTemplateFilesCustom(cls, list_invalid: bool = False) -> list[TemplateFile]:
        """List all registered paths to custom template files

        Args:
            list_invalid (bool, optional): List files that do not exist or are not valid. Defaults to False.

        Returns:
            list[TemplateFile]: Return list of templates
        """
        template_paths = Settings.get("templates")
        if template_paths is None:
            template_paths = []

        template_files = [
            TemplateFile(p, path.exists(p), False) for p in template_paths
        ]

        if not list_invalid:
            template_files = filter(lambda t: t.exists and t.is_valid, template_files)

        return template_files

    @classmethod
    def listTemplateFilesDefault(cls) -> list[TemplateFile]:
        """List all template files in default template directory.

        Returns:
            list[TemplateFile]: List of files.
        """
        templates_dir = path.join(
            pkgdatadir, "realms", "templates"  # pylint: disable=undefined-variable
        )

        template_files = [
            TemplateFile(path.join(templates_dir, p), True, True)
            for p in listdir(templates_dir)
        ]

        template_files = filter(
            lambda t: ".yml" in t.path or ".yaml" in t.path, template_files
        )
        return template_files

    @classmethod
    def listTemplatesInFile(cls, file: TemplateFile) -> list[dict]:
        """List all templates inside the given file.

        Args:
            file (TemplateFile): File

        Raises:
            ValueError: If file doesn't exist
        """
        if not file.exists:
            raise ValueError("File doesn't exist")

        if not file.is_valid:
            raise ValueError("File is marked invalid")

        templates = []
        with open(file.path, "r") as f:
            data = yaml.safe_load(f)

        if data is not None and "templates" in data:
            for template in data["templates"]:
                templates.append(template)

        return templates

    @classmethod
    def listTemplatesAll(cls) -> list[dict]:
        """List all templates as list of dictionaries.

        Returns:
            list[dict]: Templates
        """
        templates = cls.listTemplatesDefault()
        templates.extend(cls.listTemplatesCustom())

        templates.sort(key=lambda x: x["name"])

        return templates

    @classmethod
    def listTemplatesCustom(cls) -> list[dict]:
        """List custom templates.

        Returns:
            list[dict]: List of template dictionaries.
        """
        templates = []

        for t in cls.listTemplateFilesCustom(False):
            templates.extend(cls.listTemplatesInFile(t))

        templates.sort(key=lambda x: x["name"])

        return templates

    @classmethod
    def listTemplatesDefault(cls) -> list[dict]:
        """List default templates.

        Returns:
            list[dict]: List of template dictionaries.
        """
        templates = []

        for t in cls.listTemplateFilesDefault():
            templates.extend(cls.listTemplatesInFile(t))

        templates.sort(key=lambda x: x["name"])

        return templates

    @classmethod
    def addTemplateFile(cls, path: str):
        """Add a new custom template file.

        Args:
            path (str): Path to template file
        """
        templates = Settings.get("templates")
        if templates is None:
            templates = []
        templates.append(path)
        Settings.put("templates", templates)

    @classmethod
    def removeTemplateFile(cls, path: str):
        """Remove a custom template file.

        Args:
            path (str): Path to file

        Raises:
            ValueError: If file wasn't registered
        """
        templates: list | None = Settings.get("templates")
        if templates is None:
            raise ValueError("path doesn't exist.")
        templates.remove(path)
        Settings.put("templates", templates)
