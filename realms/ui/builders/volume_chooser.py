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

import libvirt
from gi.repository import Adw, Gtk

from realms.libvirt_wrap.connection import Connection
from realms.libvirt_wrap.pool import Pool
from realms.ui.builders.common import iconButton
from realms.ui.dialogs.add_volume_dialog import AddVolumeDialog


class VolumeChooser(Gtk.Box):
    """A widget with two dropdowns to selected a storage
    pool and a volume therein."""

    def __init__(
        self,
        window: Adw.ApplicationWindow,
        connection: Connection,
        on_changed_cb: callable,
    ):
        super().__init__(
            hexpand=True, orientation=Gtk.Orientation.HORIZONTAL, css_classes=["linked"]
        )

        self.__window__ = window
        self.__connection__ = connection
        self.__on_changed_cb__ = on_changed_cb

        self.__pools__ = None
        self.__volumes__ = None
        self.__pool__ = None

        self.__build__()

    def __build__(self):
        """Build self."""
        self.__pool_combo__ = Gtk.DropDown(tooltip_text="Pool", hexpand=True)
        self.__pool_combo__.connect("notify::selected", self.__onPoolSelected__)
        self.append(self.__pool_combo__)

        self.__volume_combo__ = Gtk.DropDown(tooltip_text="Volume", hexpand=True)
        self.__volume_combo__.connect("notify::selected", self.__onVolumeSelected__)
        self.append(self.__volume_combo__)

        self.__create_btn__ = iconButton(
            "",
            "list-add-symbolic",
            self.__onCreateVolClicked__,
            sensitive=False,
            tooltip_text="Create",
        )
        self.append(self.__create_btn__)

        self.__connection__.listStoragePools(self.__setPools__)

    def __setPools__(self, vir_pools: list[libvirt.virStoragePool]):
        """List available pools."""
        self.__pools__ = vir_pools
        self.__pools__.sort(key=lambda k: k.name())
        pool_names = [p.name() for p in self.__pools__]
        pool_names.sort()
        self.__pool_combo__.set_model(Gtk.StringList(strings=pool_names))

    def __onPoolSelected__(self, *_):
        """A pool was chosen."""
        self.__volume_combo__.set_model(Gtk.StringList(strings=[]))

        def listVolumes(vir_vols: list[libvirt.virStorageVol]):
            self.__volumes__ = None
            volume_names = [v.name() for v in vir_vols]
            volume_names.sort()
            self.__volume_combo__.set_model(Gtk.StringList(strings=volume_names))
            self.__volumes__ = vir_vols

        self.__pool__ = Pool(
            self.__connection__, self.__pools__[self.__pool_combo__.get_selected()]
        )
        self.__pool__.listVolumes(listVolumes)

        self.__create_btn__.set_sensitive(True)

    def __onVolumeSelected__(self, *_):
        """A volume was chosen."""
        if self.__volumes__ is not None:
            self.__on_changed_cb__()

    def __onCreateVolClicked__(self, _):
        """Show Dialog to create a volume."""

        def onVolCreated(vir_vol: libvirt.virStorageVol):
            # Don't refresh volumes here to prevent race-condition.
            if vir_vol not in self.__volumes__:
                self.__volumes__.append(vir_vol)

            volume_names = [v.name() for v in self.__volumes__]
            volume_names.sort()
            self.__volume_combo__.set_model(Gtk.StringList(strings=volume_names))
            self.__volume_combo__.set_selected(volume_names.index(vir_vol.name()))

        AddVolumeDialog(self.__window__, self.__pool__, onVolCreated)

    def connectOnChanged(self, on_changed_cb: callable):
        """Add a callback to call when the selected volume changed."""
        self.__on_changed_cb__ = on_changed_cb

    def getPool(self) -> libvirt.virStoragePool:
        """Get the currently selected pool."""
        return self.__pools__[self.__pool_combo__.get_selected()]

    def getVolume(self) -> libvirt.virStorageVol:
        """Get the currently selected volume."""
        return self.__volumes__[self.__volume_combo__.get_selected()]
