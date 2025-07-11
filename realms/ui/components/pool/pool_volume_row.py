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

from realms.helpers import asyncJob, bytesToString, failableAsyncJob, stringToBytes
from realms.helpers.async_jobs import ResultWrapper
from realms.libvirt_wrap import Volume
from realms.ui.components import ActionOption, selectDialog

# from ..bindable_entries import
from realms.ui.components.common import deleteButton, iconButton, propertyRow
from realms.ui.components.generic_preferences_row import GenericPreferencesRow
from realms.ui.dialogs.download_volume_dialog import DownloadVolumeDialog
from realms.ui.window_reference import WindowReference

from .pool_permissions_box import PoolPermissionsBox


class PoolVolumeRow(Adw.ExpanderRow):
    """Represent a volume row for the pool details page."""

    def __init__(
        self,
        volume: Volume,
        window_ref: WindowReference,
    ):
        super().__init__(title=volume.getName())

        self.volume = volume
        self.window_ref = window_ref
        self.volume_tree = None

        self.usage_progress = None

        self.capacity_row = None
        self.action_row = None

        self.__build__()

    def __build__(self):
        self.volume_tree = self.volume.getETree()
        self.usage_progress = Gtk.ProgressBar(
            vexpand=True,
            valign=Gtk.Align.BASELINE_CENTER,
            show_text=True,
        )
        self.add_suffix(self.usage_progress)

        name_row = propertyRow("Name")
        name_row.set_subtitle(self.volume.getName())
        self.add_row(name_row)

        self.capacity_row = Adw.EntryRow(title="Capacity", show_apply_button=False)
        self.capacity_row.connect(
            "changed", lambda *_: self.capacity_row.set_show_apply_button(True)
        )
        self.capacity_row.connect("apply", self.__applyCapacityChange__)
        self.add_row(self.capacity_row)

        type_row = propertyRow("Type")
        type_row.set_subtitle(self.volume.getType())
        self.add_row(type_row)

        target = self.volume_tree.find("target")
        f = target.find("format")
        if f is not None:
            format_row = propertyRow("Format")
            format_row.set_subtitle(f.get("type"))
            self.add_row(format_row)

        permissions = target.find("permissions")
        if permissions is not None:
            perms_row = GenericPreferencesRow()
            perms_row.addChild(Gtk.Label(label="Permissions", halign=Gtk.Align.START))
            perms_box = PoolPermissionsBox(lambda *x: None, sensitive=False)
            perms_box.connectData(permissions)
            perms_row.addChild(perms_box)
            self.add_row(perms_row)

        self.action_row = Adw.ActionRow()
        self.add_row(self.action_row)

        wipe_btn = iconButton(
            "Wipe", "eraser-symbolic", self.__onWipeClicked__, css_classes=["flat"]
        )
        self.action_row.add_prefix(wipe_btn)

        self.action_row.add_prefix(deleteButton(self.__onDeleteClicked__))

        download_btn = iconButton(
            "Download",
            "folder-download-symbolic",
            self.__onDownloadClicked__,
            css_classes=["flat"],
        )
        self.action_row.add_suffix(download_btn)

        self.__loadUsageStats__()

    def __loadUsageStats__(self):
        """Show the usage of the volume."""

        def loadStats():
            capacity = self.volume.getCapacity()
            allocated = self.volume.getAllocation()

            fill_fraction = 0
            if capacity > 0:
                fill_fraction = allocated / capacity

            text = f"{ bytesToString(allocated)} / { bytesToString(capacity) }"
            return (fill_fraction, text, capacity)

        def showStats(res):
            self.usage_progress.set_fraction(min(1, res[0]))
            self.usage_progress.set_text(res[1])

            self.capacity_row.set_text(bytesToString(res[2]))
            self.capacity_row.set_show_apply_button(False)

        asyncJob(loadStats, [], showStats)

    def __applyCapacityChange__(self, *_):
        """As the capacity is the only parameter to be changed for a volume,
        this handler handles the entry changing directly.
        """
        description = self.capacity_row.get_text()
        try:
            b = stringToBytes(description)
            self.volume.setCapacity(b)
        except Exception as e:
            self.window_ref.window.pushToastText(str(e))

        self.capacity_row.set_text(bytesToString(self.volume.getCapacity()))
        self.capacity_row.set_show_apply_button(False)

        self.__loadUsageStats__()

    def __onDeleteClicked__(self, btn):
        """Delete this volume."""

        def finish(res: ResultWrapper):
            btn.set_sensitive(True)

            if not res.failed:
                self.window_ref.window.pushToastText("Volume was deleted")

        def delete():
            btn.set_sensitive(False)

            failableAsyncJob(
                self.volume.delete,
                [],
                lambda e: self.window_ref.window.pushToastText(str(e)),
                finish,
            )

        dialog = selectDialog(
            f'Delete "{ self.volume.getName() }"?',
            "The volume will be deleted permanently",
            [
                ActionOption(
                    "Delete",
                    delete,
                    appearance=Adw.ResponseAppearance.DESTRUCTIVE,
                )
            ],
        )
        dialog.present(self.window_ref.window)

    def __onWipeClicked__(self, btn):
        """Erase this volume."""

        def finish(res: ResultWrapper):
            btn.set_sensitive(True)

            self.window_ref.window.pushToastText(
                "Volume was wiped" if not res.failed else "Wiping volume failed"
            )

        def wipe():
            btn.set_sensitive(False)
            failableAsyncJob(
                self.volume.wipe,
                [],
                lambda e: self.window_ref.window.pushToastText(str(e)),
                finish,
            )

        dialog = selectDialog(
            f'Wipe volume "{ self.volume.getName() }"?',
            "The volume's contents will be erased permanently",
            [
                ActionOption(
                    "Erase",
                    wipe,
                    appearance=Adw.ResponseAppearance.DESTRUCTIVE,
                )
            ],
        )
        dialog.present(self.window_ref.window)

    def __onDownloadClicked__(self, _):
        """Download this volume."""
        DownloadVolumeDialog(self.window_ref.window, self.volume)
