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
from gi.repository import Adw, Gtk

from realms.helpers.templates import TemplateFile, TemplateManager
from realms.ui.components.common import iconButton
from realms.ui.components.preference_widgets import RealmsPreferencesPage

from .base_details import *


class TemplateFileRow(Adw.ExpanderRow):
    def __init__(self, parent, file: TemplateFile):
        super().__init__(title=file.getName(), title_lines=1, subtitle_lines=1)

        self.parent = parent
        self.file = file

        self.status_icon = None

        if not file.is_default:
            self.delete_btn = iconButton(
                "",
                "user-trash-symbolic",
                lambda *_: self.parent.onDeleteCustomClicked(self),
                css_classes=["flat"],
            )
            self.add_suffix(self.delete_btn)

        self.__list_templates__()

    def __list_templates__(self):
        if not self.file.exists:
            self.__set_status__(False, "File doesn't exist")
            return

        if not self.file.is_valid:
            self.__set_status__(False, self.file.invalid_error)
            return

        try:
            for t in TemplateManager.listTemplatesInFile(self.file):
                name = t["name"]
                desc = ""
                if "description" in t:
                    desc = t["description"]

                self.add_row(Adw.ActionRow(title=name, subtitle=desc))

            self.__set_status__(True)
        except Exception as e:
            self.__set_status__(False, str(e))

    def __set_status__(self, success: bool, error: str = ""):
        if self.status_icon is not None:
            self.remove(self.status_icon)
            self.status_icon = None

        self.set_subtitle(error)

        if success and not self.file.is_default:
            self.status_icon = Gtk.Image(
                icon_name="check-round-outline-symbolic", css_classes=["success"]
            )

            self.add_prefix(self.status_icon)
        elif not success:
            self.status_icon = Gtk.Image(
                icon_name="cross-large-circle-outline-symbolic", css_classes=["error"]
            )
            self.set_enable_expansion(False)

            self.add_prefix(self.status_icon)


class EditTemplatesTab(BaseDetailsTab):
    """Class providing an editing tab for a libvirt connection."""

    def __init__(self, window: Adw.ApplicationWindow):
        super().__init__(window)

        self.save_btn = None

        self.toolbar_view = None
        self.navigation_view = None
        self.main_nav_page = None
        self.prefs_page = None
        self.default_group = None
        self.custom_group = None

        self.default_rows = []
        self.custom_rows = []

        self.__build__()

    def __build__(self):
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.title_widget = Adw.WindowTitle(title="Templates")

        self.update_btn = iconButton(
            "", "update-symbolic", self.__update__, tooltip_text="Refresh"
        )

        self.toolbar_view = Adw.ToolbarView(hexpand=True, vexpand=True)
        self.append(self.toolbar_view)

        self.navigation_view = Adw.NavigationView(animate_transitions=True)
        self.toolbar_view.set_content(self.navigation_view)

        self.main_nav_page = Adw.NavigationPage(title="Main")
        self.navigation_view.push(self.main_nav_page)

        box = Gtk.Box(vexpand=True, hexpand=True, orientation=Gtk.Orientation.VERTICAL)
        self.main_nav_page.set_child(box)

        self.prefs_page = RealmsPreferencesPage()
        box.append(self.prefs_page)

        self.default_group = Adw.PreferencesGroup(title="Default Templates")
        self.prefs_page.add(self.default_group)

        self.custom_group = Adw.PreferencesGroup(title="Custom Templates")
        self.prefs_page.add(self.custom_group)

        add_btn = iconButton(
            "",
            "list-add-symbolic",
            self.__onAddCustomClicked__,
            css_classes=["flat"],
            tooltip_text="Add",
        )
        self.custom_group.set_header_suffix(add_btn)

        self.__update__()

    def __update__(self, *_):
        for row in self.default_rows:
            self.default_group.remove(row)
        self.default_rows.clear()

        for file in TemplateManager.listTemplateFilesDefault():
            row = TemplateFileRow(self, file)
            self.default_group.add(row)
            self.default_rows.append(row)

        for row in self.custom_rows:
            self.custom_group.remove(row)
        self.custom_rows.clear()

        for file in TemplateManager.listTemplateFilesCustom(True):
            row = TemplateFileRow(self, file)
            self.custom_group.add(row)
            self.custom_rows.append(row)

    def __onAddCustomClicked__(self, *_):
        def onOpen(dialog, result):
            try:
                file = dialog.open_finish(result)

                if file is None:
                    return

                path = file.get_path()

                TemplateManager.addTemplateFile(path)

                self.__update__()
            except Exception as e:
                self.window_ref.window.push_toast_text(f"Error: { e }")
                return

        dialog = Gtk.FileDialog(title="Template File")
        dialog.open(None, None, onOpen)

    def onDeleteCustomClicked(self, row: TemplateFileRow):
        """Row requested deletion of this template."""
        TemplateManager.removeTemplateFile(row.file.path)

        self.custom_group.remove(row)
        self.custom_rows.remove(row)

    def end(self):
        # No resources are held.
        pass

    def getUniqueIdentifier(self) -> str:
        return "edit-templates"

    def setWindowHeader(self, window):
        window.headerSetTitleWidget(self.title_widget)
        window.headerPackEnd(self.update_btn)
