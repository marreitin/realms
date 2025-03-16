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
from gi.repository import Adw, GLib, Gtk

from realms.libvirt_wrap import Pool, Volume
from realms.ui.components.common import iconButton
from realms.ui.dialogs.add_volume_dialog import AddVolumeDialog
from realms.ui.window_reference import WindowReference

from .pool_volume_row import PoolVolumeRow


class VolumesGroup(Adw.PreferencesGroup):
    """Preferences group containing all volume rows in the pool details tab."""

    def __init__(
        self, pool: Pool, show_apply_cb: callable, window_ref: WindowReference
    ):
        super().__init__()

        self.pool = pool
        self.show_apply_cb = show_apply_cb
        self.window_ref = window_ref
        self.vol_refresh_btn = None

        self.rows = []

        self.build()

    def build(self):
        self.set_title("Volumes")

        box = Gtk.Box(spacing=6)
        add_vol_btn = iconButton(
            "",
            "list-add-symbolic",
            self.onAddClicked,
            css_classes=["flat"],
            tooltip_text="Add Volume",
        )
        box.append(add_vol_btn)

        self.vol_refresh_btn = iconButton(
            "",
            "update-symbolic",
            self.onRefreshClicked,
            css_classes=["flat"],
            tooltip_text="Refresh Volume List",
        )
        box.append(self.vol_refresh_btn)

        self.set_header_suffix(box)

    def onAddClicked(self, *args):
        AddVolumeDialog(self.window_ref.window, self.pool)

    def onRefreshClicked(self, *args, refresh=True):
        """Refresh the list of volumes and display it."""
        for row in self.rows:
            self.remove(row)
        self.rows.clear()

        def finish(vir_volumes):
            vir_volumes = sorted(vir_volumes, key=lambda el: el.name())
            for vir_volume in vir_volumes:
                vol = Volume(self.pool, vir_volume)
                row = PoolVolumeRow(vol, self.window_ref)
                self.add(row)
                self.rows.append(row)

            self.vol_refresh_btn.set_sensitive(True)

        self.vol_refresh_btn.set_sensitive(False)

        self.pool.listVolumes(finish, refresh=refresh)
