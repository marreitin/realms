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

from realms.helpers import RepeatJob, bytesToString, failableAsyncJob
from realms.libvirt_wrap import Pool
from realms.libvirt_wrap.constants import *
from realms.ui.components import ActionOption, ApplyRow, XMLView, selectDialog
from realms.ui.components.common import iconButton
from realms.ui.components.pool.pool_prefs_group import PoolPreferencesGroup
from realms.ui.components.pool.pool_volumes_group import VolumesGroup
from realms.ui.components.preference_widgets import RealmsPreferencesPage

from .base_details import BaseDetailsTab


class PoolDetailsTab(BaseDetailsTab):
    """Tab page for a storage pool."""

    def __init__(self, pool: Pool, window: Adw.ApplicationWindow):
        super().__init__(window)

        self.pool = pool
        self.xml_tree = None

        self.stack = None

        self.usage_task = None

        # Action group
        self.prefs_page = None
        self.title_widget = None
        self.start_btn = None
        self.stop_btn = None
        self.delete_btn = None
        self.fill_progress = None
        self.apply_row = None

        # General preferences
        self.pool_prefs_group = None

        # Volumes
        self.volume_page = None
        self.volume_stack_page = None
        self.volume_group = None

        self.build()

        # Only follow the events interesting for this pool
        self.pool.registerCallback(self.onConnectionEvent)

    def build(self):
        self.set_hexpand(True)
        self.set_vexpand(True)

        toolbar_view = Adw.ToolbarView(hexpand=True, vexpand=True)
        self.append(toolbar_view)

        self.apply_row = ApplyRow(
            self.onApplyClicked,
            self.onCancelClicked,
            "Changes only available after restart",
        )
        toolbar_view.add_bottom_bar(self.apply_row)

        self.stack = Adw.ViewStack(hexpand=True, vexpand=True)
        toolbar_view.set_content(self.stack)

        switcher = Adw.ViewSwitcherBar(reveal=True, stack=self.stack)
        toolbar_view.add_bottom_bar(switcher)

        # Settings stack page
        prefs_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True
        )
        self.stack.add_titled_with_icon(
            prefs_box, "settings", "Settings", "settings-symbolic"
        )

        self.prefs_page = RealmsPreferencesPage()
        prefs_box.append(self.prefs_page)

        # Top group with buttons
        self.title_widget = Adw.WindowTitle(title=self.pool.getDisplayName())
        self.start_btn = iconButton(
            "",
            "play-symbolic",
            self.onStartClicked,
            css_classes=["suggested-action"],
            tooltip_text="Start",
        )
        self.stop_btn = iconButton(
            "",
            "stop-symbolic",
            self.onStopClicked,
            css_classes=["destructive-action"],
            tooltip_text="Stop",
        )

        # Group with general pool settings
        fill_group = Adw.PreferencesGroup()
        self.prefs_page.add(fill_group)

        self.fill_progress = Gtk.ProgressBar(margin_top=6, show_text=True)
        fill_group.add(self.fill_progress)

        self.pool_prefs_group = PoolPreferencesGroup(
            self.pool.pool_capabilities,
            False,
            self.window_ref,
            self.showApply,
            self.onDeleteClicked,
        )
        self.prefs_page.add(self.pool_prefs_group)

        # Volume group
        self.volume_page = RealmsPreferencesPage()
        self.volume_stack_page = self.stack.add_titled_with_icon(
            self.volume_page, "volumes", "Volumes", "drive-multidisk-symbolic"
        )
        self.volume_group = VolumesGroup(self.pool, self.showApply, self.window_ref)
        self.volume_page.add(self.volume_group)

        # XML
        self.xml_view = XMLView(self.showApply)
        self.stack.add_titled_with_icon(
            self.xml_view, "xml", "XML", "folder-code-legacy-symbolic"
        )

        self.updateData()
        self.setStatus()
        GLib.idle_add(lambda *x: self.presentUsage())

    def presentUsage(self):
        """Show the usage of the pool with the progress bar."""

        def gatherUsage():
            allocated = self.pool.getAllocation()
            capacity = self.pool.getCapacity()
            return [allocated, capacity]

        def showUsage(res):
            allocated, capacity = res
            fill_fraction = 0
            if capacity > 0:
                fill_fraction = allocated / capacity

            self.fill_progress.set_fraction(min(1, fill_fraction))
            self.fill_progress.set_text(
                f"{ bytesToString(allocated) } / { bytesToString(capacity) } - { int(fill_fraction*100) }%"
            )

        if self.usage_task is None:
            self.usage_task = RepeatJob(gatherUsage, [], showUsage, 30)

    def updateData(self) -> None:
        """Reload XML tree and update all elements accordingly."""
        self.xml_tree = self.pool.getETree()

        self.pool_prefs_group.updateBindings(self.xml_tree, self.pool.getAutostart())

        self.xml_view.setText(self.pool.getXML())

        self.apply_row.set_visible(False)

    def setStatus(self) -> None:
        """Update the status description."""
        if self.pool.isActive():
            self.start_btn.set_visible(False)
            self.stop_btn.set_visible(True)

            self.title_widget.set_subtitle("active")

            self.apply_row.setShowWarning(True)
            self.volume_stack_page.set_visible(True)
            self.volume_group.onRefreshClicked(True)
        else:
            self.start_btn.set_visible(True)
            self.stop_btn.set_visible(False)

            self.title_widget.set_subtitle("inactive")

            self.apply_row.setShowWarning(False)

            self.volume_stack_page.set_visible(False)

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id):
        if type_id == CALLBACK_TYPE_POOL_GENERIC:
            if event_id == POOL_EVENT_DELETED:
                self.window_ref.window.closeTab(self)
                return
            elif event_id == POOL_EVENT_VOLUME_ADDED:
                self.volume_group.onRefreshClicked()
            elif event_id == POOL_EVENT_VOLUME_DELETED:
                self.volume_group.onRefreshClicked()
        elif type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.window_ref.window.closeTab(self)
                return

        self.setStatus()

        if not self.apply_row.get_visible():
            self.updateData()

    def onStartClicked(self, btn):
        self.start_btn.set_sensitive(False)
        failableAsyncJob(
            self.pool.start,
            [],
            lambda e: self.window_ref.window.pushToastText(str(e)),
            lambda r: self.start_btn.set_sensitive(True),
        )

    def onStopClicked(self, btn):
        self.stop_btn.set_sensitive(False)
        failableAsyncJob(
            self.pool.stop,
            [],
            lambda e: self.window_ref.window.pushToastText(str(e)),
            lambda r: self.stop_btn.set_sensitive(True),
        )

    def onDeleteClicked(self, btn):
        def onDelete():
            btn.set_sensitive(False)
            try:
                self.pool.deletePool()
            except Exception as e:
                self.window_ref.window.pushToastText(str(e))
            finally:
                btn.set_sensitive(True)

        dialog = selectDialog(
            "Delete storage pool?",
            "Deleting a storage pool is irreversible",
            [
                ActionOption(
                    "Delete", onDelete, appearance=Adw.ResponseAppearance.DESTRUCTIVE
                )
            ],
        )
        dialog.present(self.window_ref.window)

    def onApplyClicked(self, btn):
        self.pool.setAutostart(self.pool_prefs_group.getAutostart())
        try:
            if self.stack.get_visible_child_name() == "xml":
                self.pool.updateDefinition(self.xml_view.getText())
            else:
                self.pool.update(self.xml_tree)
            self.updateData()
        except Exception as e:
            self.window_ref.window.pushToastText(str(e))

    def onCancelClicked(self, btn):
        self.updateData()

    def showApply(self, *args):
        self.apply_row.set_visible(True)

    def end(self):
        # Unsubscribe from events
        self.pool.unregisterCallback(self.onConnectionEvent)
        if self.usage_task is not None:
            self.usage_task.stopTask()

    def getUniqueIdentifier(self) -> str:
        return self.pool.getUUID()

    def setWindowHeader(self, window):
        window.headerSetTitleWidget(self.title_widget)
        window.headerPackStart(self.start_btn)
        window.headerPackStart(self.stop_btn)
