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
import xml.etree.ElementTree as ET

import libvirt
from gi.repository import Adw, Gtk

from realms.helpers import ResultWrapper, failableAsyncJob, getETText, prettyTime
from realms.libvirt_wrap import Domain
from realms.libvirt_wrap.constants import *
from realms.ui.components import ActionOption, iconButton, selectDialog
from realms.ui.components.preference_widgets import RealmsPreferencesPage
from realms.ui.dialogs.inspect_snapshot_dialog import InspectSnapshotDialog
from realms.ui.dialogs.take_snapshot_dialog import TakeSnapshotDialog
from realms.ui.window_reference import WindowReference


class SnapshotRow(Adw.ActionRow):
    def __init__(
        self, parent, domain: Domain, snapshot: libvirt.virDomainSnapshot, **kwargs
    ):
        super().__init__(use_markup=False, **kwargs)

        self.parent = parent
        self.domain = domain
        self.snapshot = snapshot
        self.set_title(self.snapshot.getName())

        self.is_current_icon = Gtk.Image.new_from_icon_name("play-symbolic")
        self.is_current_icon.set_tooltip_text("Current snapshot")
        self.add_prefix(self.is_current_icon)

        self.created_label = Gtk.Label(css_classes=["caption", "dim-label"])
        self.add_suffix(self.created_label)

        self.add_suffix(
            iconButton(
                "",
                "step-back-symbolic",
                self.onPlayClicked,
                css_classes=["flat"],
                tooltip_text="Revert to snapshot",
            )
        )

        self.add_suffix(
            iconButton(
                "",
                "folder-code-legacy-symbolic",
                self.onXMLClicked,
                css_classes=["flat"],
                tooltip_text="Inspect xml",
            )
        )

        self.add_suffix(
            iconButton(
                "",
                "user-trash-symbolic",
                self.onDeleteClicked,
                css_classes=["flat"],
                tooltip_text="Delete",
            )
        )

        self.update()

    def update(self):
        self.is_current_icon.set_visible(self.snapshot.isCurrent())

        xml = self.snapshot.getXMLDesc()
        self.xml_tree = ET.fromstring(xml)

        created = self.xml_tree.find("creationTime")
        self.created_label.set_label(prettyTime(getETText(created)))

        self.set_subtitle(getETText(self.xml_tree.find("state")))

    def onPlayClicked(self, btn):
        def onRevert():
            btn.set_sensitive(False)

            def onDone(res: ResultWrapper):
                btn.set_sensitive(True)
                if not res.failed:
                    self.parent.window_ref.window.pushToastText(
                        "Reverted domain to snapshot"
                    )

            failableAsyncJob(
                self.domain.revertToSnapshot,
                [self.snapshot],
                lambda e: self.parent.window_ref.window.pushToastText(str(e)),
                onDone,
            )

        dialog = selectDialog(
            "Revert snapshot?",
            "Reverting a snapshot can lead to data loss",
            [
                ActionOption(
                    "Revert", onRevert, appearance=Adw.ResponseAppearance.DESTRUCTIVE
                )
            ],
        )
        dialog.present(self.parent.window_ref.window)

    def onXMLClicked(self, btn):
        InspectSnapshotDialog(self.parent.window_ref.window, self.domain, self.snapshot)

    def onDeleteClicked(self, btn):
        def onDeleteSelected():
            self.set_sensitive(False)
            self.parent.onDeleteSnapshot(self)

        dialog = selectDialog(
            "Delete snapshot?",
            "Snapshot data cannot be recovered",
            [
                ActionOption(
                    "Delete",
                    onDeleteSelected,
                    appearance=Adw.ResponseAppearance.DESTRUCTIVE,
                )
            ],
        )
        dialog.present(self.parent.window_ref.window)


class SnapshotBox(Gtk.Box):
    def __init__(self, domain: Domain, window_ref: WindowReference):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.domain = domain
        self.window_ref = window_ref
        self.snapshot_rows = []

        self.build()

        self.domain.register_callback_any(self.onConnectionEvent)

    def build(self):
        self.snapshot_overlay = Gtk.Overlay(vexpand=True)
        self.append(self.snapshot_overlay)

        self.no_snapshots_status = Adw.StatusPage(
            title="No snapshots",
            icon_name="library-symbolic",
            vexpand=True,
            child=iconButton(
                "Take snapshot",
                "",
                self.onTakeClicked,
                halign=Gtk.Align.CENTER,
                css_classes=["pill", "suggested-action"],
            ),
        )
        self.snapshot_overlay.add_overlay(self.no_snapshots_status)

        self.prefs_page = RealmsPreferencesPage()
        self.snapshot_overlay.set_child(self.prefs_page)

        self.group = Adw.PreferencesGroup(title="Snapshots")
        self.prefs_page.add(self.group)

        self.snapshot_btn = iconButton(
            "Take snapshot",
            "",
            self.onTakeClicked,
            halign=Gtk.Align.CENTER,
            css_classes=["pill", "suggested-action"],
            margin_top=12,
        )
        self.group.add(self.snapshot_btn)

        self.updateData()

    def updateData(self):
        for row in self.snapshot_rows:
            self.group.remove(row)
        self.snapshot_rows.clear()

        def addSnapshots(vir_snapshots: list[libvirt.virDomainSnapshot]):
            if len(vir_snapshots) != 0:
                self.group.remove(self.snapshot_btn)

                self.prefs_page.set_visible(True)
                self.no_snapshots_status.set_visible(False)
                for s in vir_snapshots:
                    self.addSnapshot(s)

                self.group.add(self.snapshot_btn)
            else:
                self.prefs_page.set_visible(False)
                self.no_snapshots_status.set_visible(True)

        self.domain.listSnapshots(addSnapshots)

    def onDeleteSnapshot(self, row: SnapshotRow):
        # Handling the deleted row is not necessary anymore, since the
        # event is being broadcasted by the domain.
        failableAsyncJob(
            self.domain.deleteSnapshot,
            [row.snapshot],
            lambda e: self.window_ref.window.pushToastText(str(e)),
            lambda *x: None,
        )

    def addSnapshot(self, vir_snapshot: libvirt.virDomainSnapshot):
        row = SnapshotRow(self, self.domain, vir_snapshot)
        self.group.add(row)
        self.snapshot_rows.append(row)

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id):
        if type_id == CALLBACK_TYPE_DOMAIN_GENERIC:
            if event_id in [DOMAIN_EVENT_SNAPSHOT_TAKEN, DOMAIN_EVENT_SNAPSHOT_DELETED]:
                self.updateData()
        elif type_id == CALLBACK_TYPE_DOMAIN_LIFECYCLE:
            if event_id == libvirt.VIR_DOMAIN_EVENT_DEFINED:
                self.updateData()

    def onTakeClicked(self, *args):
        TakeSnapshotDialog(self.window_ref.window, self.domain)

    def end(self):
        self.domain.unregister_callback(self.onConnectionEvent)
