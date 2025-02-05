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

from realms.helpers import failableAsyncJob
from realms.helpers.show_domain_video import hasDisplay, show
from realms.libvirt_wrap import Domain
from realms.libvirt_wrap.constants import *
from realms.ui.builders import (
    ActionOption,
    ApplyRow,
    XMLView,
    hspacer,
    iconButton,
    selectDialog,
)
from realms.ui.builders.domain import PerformanceBox, SnapshotBox
from realms.ui.builders.domain.pages import (
    BaseDevicePage,
    ClockPage,
    FeaturesPage,
    FirmwarePage,
    GeneralHardwarePage,
    GeneralPage,
    tagToPage,
)
from realms.ui.dialogs.add_device_dialog import AddDeviceDialog
from realms.ui.dialogs.clone_domain_dialog import CloneDomainDialog
from realms.ui.dialogs.take_snapshot_dialog import TakeSnapshotDialog

from .base_details import BaseDetailsTab


class DeviceRow:
    """Preferences row, mostly used for listing all virtual devices. Contains
    an object type for subclasses of BaseDevicePage and an xml-tree for it,
    to show that page upon row selection. For performance reasons, that page
    will only be built upon selection."""

    def __init__(
        self, parent, device_page_type: type, xml_tree: ET.Element, can_update=False
    ):
        self.parent = parent
        self.device_page_type = device_page_type
        self.xml_tree = xml_tree
        self.can_update = can_update
        self.index = 0
        self.row = None

        self.device_page = self.device_page_type(
            self.parent, self.xml_tree, can_update=self.can_update
        )

    def build(self):
        """Build the actual action row"""
        self.row = Adw.ActionRow(
            title=self.getTitle(),
            activatable=True,
            selectable=False,
        )

        main_icon = Gtk.Image.new_from_icon_name(self.device_page.getIconName())
        self.row.add_prefix(main_icon)

        open_icon = Gtk.Image.new_from_icon_name("go-next-symbolic")
        self.row.add_suffix(open_icon)

        self.row.connect("activated", self.onActivated)

    def onActivated(self, row):
        self.device_page.buildFull()
        self.parent.showNavPage(self.device_page.nav_page)

    def setIndex(self, index):
        self.index = index
        if self.row is not None:
            self.row.set_title(self.getTitle())

    def getTitle(self) -> str:
        if self.index == 0:
            return self.device_page.getTitle()
        return self.device_page.getTitle() + " " + str(self.index)


class DomainDetailsTab(BaseDetailsTab):
    """The tab showing domain details."""

    def __init__(self, domain: Domain, window: Adw.ApplicationWindow):
        super().__init__(window)

        self.domain = domain

        self.__definition_changed__ = False

        self.autostart = False

        self.stack = None
        self.toolbar_view = None

        self.apply_row = None
        self.back_btn = None
        self.start_btn = None
        self.stop_btn = None
        self.delete_btn = None
        self.pause_btn = None
        self.status_label = None
        self.open_btn = None
        self.snapshot_btn = None

        self.navigation_view = None
        self.general_group = None
        self.general_rows = []

        self.devices_group = None
        self.xml_tree = None
        self.device_rows = {}

        self.__built__ = False

        self.build()

        # Only follow the events interesting for this domain
        self.domain.register_callback_any(self.onConnectionEvent, None)

    def build(self):
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.toolbar_view = Adw.ToolbarView(hexpand=True, vexpand=True)
        self.append(self.toolbar_view)

        self.stack = Adw.ViewStack(hexpand=True, vexpand=True)
        self.toolbar_view.set_content(self.stack)

        # Apply Row
        self.apply_row = ApplyRow(
            self.onApplyClicked,
            lambda *x: self.updateData(),
            "Changes only available after restart",
        )
        self.toolbar_view.add_bottom_bar(self.apply_row)
        self.apply_row.set_visible(False)

        switcher = Adw.ViewSwitcherBar(reveal=True, stack=self.stack)
        self.toolbar_view.add_bottom_bar(switcher)

        # Control buttons
        self.buildControlRow()

        # Box with main content
        main_box = Gtk.Box(
            vexpand=True, hexpand=True, orientation=Gtk.Orientation.VERTICAL
        )
        self.stack.add_titled_with_icon(
            main_box, "settings", "Settings", "settings-symbolic"
        )

        self.navigation_view = Adw.NavigationView(animate_transitions=True)
        self.navigation_view.connect(
            "popped", lambda *x: self.back_btn.set_visible(False)
        )
        main_box.append(self.navigation_view)

        self.main_nav_page = Adw.NavigationPage(title="Devices")
        self.navigation_view.push(self.main_nav_page)

        box = Gtk.Box(vexpand=True, hexpand=True, orientation=Gtk.Orientation.VERTICAL)
        self.main_nav_page.set_child(box)

        # Containers for devices
        devices_page = Adw.PreferencesPage()
        box.append(devices_page)

        # General rows
        self.general_group = Adw.PreferencesGroup()
        devices_page.add(self.general_group)

        # Device rows
        self.devices_group = Adw.PreferencesGroup(title="Virtual devices")
        devices_page.add(self.devices_group)

        add_btn = iconButton(
            "Add device",
            "",
            self.onAddDeviceClicked,
            css_classes=["pill", "suggested-action"],
            hexpand=False,
            halign=Gtk.Align.CENTER,
            margin_top=12,
        )
        self.devices_group.add(add_btn)

        # XML
        self.xml_box = XMLView(self.onDefinitionChanged)
        self.stack.add_titled_with_icon(
            self.xml_box, "xml", "XML", "folder-code-legacy-symbolic"
        )

        # Snapshots
        self.snapshots_box = SnapshotBox(self.domain, self.window_ref)
        self.stack.add_titled_with_icon(
            self.snapshots_box, "snapshots", "Snapshots", "user-bookmarks-symbolic"
        )

        # Performance
        self.perf_box = PerformanceBox(self.domain)
        self.stack.add_titled_with_icon(
            self.perf_box, "perf", "Performance", "speedometer5-symbolic"
        )

        self.__built__ = True

        self.updateData()
        self.setStatus()

    def buildControlRow(self):
        clamp = Adw.Clamp()
        self.toolbar_view.add_top_bar(clamp)
        self.actions_box = Gtk.Box(
            spacing=6,
            margin_top=6,
            margin_bottom=6,
            margin_start=6,
            margin_end=6,
            width_request=108,
        )
        clamp.set_child(self.actions_box)

        self.back_btn = iconButton(
            "",
            "go-previous-symbolic",
            self.onBackClicked,
            css_classes=["flat"],
            visible=False,
        )
        self.actions_box.append(self.back_btn)

        self.start_btn = iconButton(
            "Start",
            "media-playback-start-symbolic",
            self.onStartClicked,
            css_classes=["suggested-action"],
        )
        self.actions_box.append(self.start_btn)

        self.resume_btn = iconButton(
            "Resume",
            "media-playback-start-symbolic",
            self.onResumeClicked,
            css_classes=["suggested-action"],
        )
        self.actions_box.append(self.resume_btn)

        self.pause_btn = iconButton(
            "Pause", "media-playback-pause-symbolic", self.onPauseClicked
        )
        self.actions_box.append(self.pause_btn)

        self.stop_btn = iconButton(
            "Stop",
            "media-playback-stop-symbolic",
            self.onStopClicked,
            css_classes=["destructive-action"],
        )
        self.actions_box.append(self.stop_btn)

        self.open_btn = iconButton(
            "Open",
            "computer-symbolic",
            lambda *b: show(self.domain, self.window_ref.window),
            css_classes=["suggested-action"],
        )
        self.actions_box.append(self.open_btn)

        self.clone_btn = iconButton(
            "", "copy-symbolic", self.onCloneClicked, tooltip_text="Clone"
        )
        self.actions_box.append(self.clone_btn)

        self.snapshot_btn = iconButton(
            "",
            "bookmark-new-symbolic",
            self.onTakeSnapshotClicked,
            tooltip_text="Snapshot",
        )
        self.actions_box.append(self.snapshot_btn)

        self.actions_box.append(hspacer())

        self.status_label = Gtk.Label(
            label="Down", css_classes=["dim-label"], margin_top=6, margin_bottom=6
        )
        self.actions_box.append(self.status_label)

    def updateData(self, reuse_tree=False) -> None:
        """Update data bindings, and try to reuse existing rows
        by just giving them fresh xml data, but not readding them.
        """
        if not self.__built__:
            return

        if not reuse_tree:
            self.xml_box.setText(self.domain.getXML())
            self.xml_tree = self.domain.getETree()
        else:
            ET.indent(self.xml_tree)
            self.xml_box.setText(ET.tostring(self.xml_tree, "unicode"))

        self.general_group.set_title("Domain: " + self.domain.getDisplayName())

        self.autostart = self.domain.getAutostart()

        for row in self.general_rows:
            self.general_group.remove(row.row)
        self.general_rows.clear()

        for row in [
            DeviceRow(self, GeneralPage, self.xml_tree),
            DeviceRow(self, FirmwarePage, self.xml_tree),
            DeviceRow(self, GeneralHardwarePage, self.xml_tree),
            DeviceRow(self, ClockPage, self.xml_tree),
            DeviceRow(self, FeaturesPage, self.xml_tree),
        ]:
            row.build()
            self.general_group.add(row.row)
            self.general_rows.append(row)

        # Virtual devices
        for row in self.device_rows.values():
            self.devices_group.remove(row.row)
        self.device_rows.clear()

        # Only show the update row in the device page if
        # the domain is active, since otherwise the configuration
        # can be applied regularly.
        domain_is_active = self.domain.isActive()

        for device_xml in self.xml_tree.find("devices"):
            page_type = tagToPage(device_xml.tag)
            if page_type is None:
                continue

            row = DeviceRow(self, page_type, device_xml, domain_is_active)
            index = 0
            while row.getTitle() in self.device_rows:
                index += 1
                row.setIndex(index)
            self.device_rows[row.getTitle()] = row
            row.build()
            self.devices_group.add(row.row)

        # Update currently visible page if possible, otherwise
        # close it. TODO
        visible_page = self.navigation_view.get_visible_page()
        if visible_page != self.main_nav_page:
            self.navigation_view.pop()

        self.apply_row.set_visible(False)
        self.__definition_changed__ = False

    def showNavPage(self, page: BaseDevicePage):
        self.navigation_view.push(page)
        self.back_btn.set_visible(True)

    def setStatus(self) -> None:
        """Update the status description."""
        if not self.__built__:
            return

        self.status_label.set_label(self.domain.getStateText())

        self.start_btn.set_visible(False)
        self.resume_btn.set_visible(False)
        self.stop_btn.set_visible(False)
        self.pause_btn.set_visible(False)
        self.open_btn.set_visible(False)

        state = self.domain.getStateID()

        if state in [
            libvirt.VIR_DOMAIN_RUNNING,
            libvirt.VIR_DOMAIN_BLOCKED,
            libvirt.VIR_DOMAIN_CRASHED,
            libvirt.VIR_DOMAIN_SHUTDOWN,
        ]:
            self.stop_btn.set_visible(True)
            self.pause_btn.set_visible(True)
            self.open_btn.set_visible(hasDisplay(self.xml_tree))
            self.setApplyWarningVisibility(True)

            for row in self.device_rows.values():
                row.device_page.setCanUpdate(True)
        elif state == libvirt.VIR_DOMAIN_PAUSED:
            self.resume_btn.set_visible(True)
            self.open_btn.set_visible(hasDisplay(self.xml_tree))
            self.setApplyWarningVisibility(True)

            for row in self.device_rows.values():
                row.device_page.setCanUpdate(True)
        else:
            self.start_btn.set_visible(True)
            self.setApplyWarningVisibility(False)

            for row in self.device_rows.values():
                row.device_page.setCanUpdate(False)

    def setApplyWarningVisibility(self, visibility: bool):
        """Whether to show the apply button on the apply row."""
        self.apply_row.setShowWarning(visibility)

    def onDefinitionChanged(self):
        self.__definition_changed__ = True
        self.apply_row.set_visible(True)

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id, opaque):
        if type_id == CALLBACK_TYPE_DOMAIN_GENERIC:
            if event_id == DOMAIN_EVENT_DELETED:
                self.window_ref.window.closeTab(self)
                return
        elif type_id == CALLBACK_TYPE_DOMAIN_LIFECYCLE:
            if event_id == libvirt.VIR_DOMAIN_EVENT_DEFINED:
                # Has to update, otherwise nothing makes sense anymore.
                self.updateData()
            # Only refresh if no changes were made. (It was only a state change event)
            elif not self.__definition_changed__:
                self.updateData()
        elif type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.window_ref.window.closeTab(self)
                return
        self.setStatus()

    def onStartClicked(self, btn):
        btn.set_sensitive(False)
        failableAsyncJob(
            self.domain.start,
            [],
            lambda e: (print(e), self.window_ref.window.pushToastText(str(e))),
            lambda r: btn.set_sensitive(True),
        )

    def onResumeClicked(self, btn):
        btn.set_sensitive(False)
        failableAsyncJob(
            self.domain.resume,
            [],
            lambda e: self.window_ref.window.pushToastText(str(e)),
            lambda r: btn.set_sensitive(True),
        )

    def onStopClicked(self, btn):
        def onResetSelected():
            self.stop_btn.set_sensitive(False)
            failableAsyncJob(
                self.domain.reset,
                [],
                lambda e: self.window_ref.window.pushToastText(str(e)),
                lambda r: self.stop_btn.set_sensitive(True),
            )

        def onKillSelected():
            self.stop_btn.set_sensitive(False)
            failableAsyncJob(
                self.domain.destroy,
                [],
                lambda e: self.window_ref.window.pushToastText(str(e)),
                lambda r: self.stop_btn.set_sensitive(True),
            )
            btn.set_sensitive(False)

        def onShutdownSelected():
            self.stop_btn.set_sensitive(False)
            failableAsyncJob(
                self.domain.shutdown,
                [],
                lambda e: self.window_ref.window.pushToastText(str(e)),
                lambda r: self.stop_btn.set_sensitive(True),
            )

        dialog = selectDialog(
            "Stopping domain",
            "Choose how to stop the domain",
            [
                ActionOption("Reset", onResetSelected),
                ActionOption(
                    "Kill",
                    onKillSelected,
                    appearance=Adw.ResponseAppearance.DESTRUCTIVE,
                ),
                ActionOption(
                    "Shut down",
                    onShutdownSelected,
                    appearance=Adw.ResponseAppearance.SUGGESTED,
                ),
            ],
        )
        dialog.present(self.window_ref.window)

    def onPauseClicked(self, btn):
        btn.set_sensitive(False)
        failableAsyncJob(
            self.domain.pause,
            [],
            lambda e: self.window_ref.window.pushToastText(str(e)),
            lambda r: btn.set_sensitive(True),
        )

    def onDeleteClicked(self, btn):
        """ "delete-domain" was clicked"""

        def onDelete():
            btn.set_sensitive(False)
            try:
                self.domain.deleteDomain()
            except Exception as e:
                self.window_ref.window.pushToastText(str(e))
            finally:
                btn.set_sensitive(True)

        dialog = selectDialog(
            "Delete domain?",
            "Deleting a domain is irreversible",
            [
                ActionOption(
                    "Delete", onDelete, appearance=Adw.ResponseAppearance.DESTRUCTIVE
                )
            ],
        )
        dialog.present(self.window_ref.window)

    def onCloneClicked(self, btn):
        CloneDomainDialog(self.window_ref.window, self.domain)

    def onMigrateClicked(self, btn):
        raise NotImplementedError

    def onTakeSnapshotClicked(self, btn):
        TakeSnapshotDialog(self.window_ref.window, self.domain)

    def onAddDeviceClicked(self, btn):
        AddDeviceDialog(
            self.window_ref.window, self.domain, self.xml_tree, self.onDeviceAdded
        )

    def onDeviceAdded(self, device_tree: ET.Element):
        """Callback from device adding dialog to create device.
        Handle the option to hotplug devices, with a fallback to just
        adding them to the regular configuration."""

        def addNormally():
            devices = self.xml_tree.find("devices")
            devices.append(device_tree)
            self.updateData(True)
            self.onDefinitionChanged()

        def hotplug():
            try:
                self.domain.attachDevice(device_tree)
                self.updateData()
            except Exception as e:
                self.window_ref.window.pushToastText(
                    str(e) + "\nDevice was added to static configuration"
                )
                addNormally()

        if self.domain.isActive():
            dialog = selectDialog(
                "Hotplug device?",
                "Try to attach device to running domain",
                [
                    ActionOption(
                        "Hotplug", hotplug, appearance=Adw.ResponseAppearance.SUGGESTED
                    ),
                    ActionOption("Add to config", addNormally),
                ],
                show_cancel=False,
            )
            dialog.present(self.window_ref.window)
        else:
            addNormally()

    def deleteDevice(self, device_page: BaseDevicePage):
        """Call from a device page that the device should be deleted.
        Handle the case of an active domain, unplugging live devices."""

        def detachNormal():
            devices = self.xml_tree.find("devices")
            devices.remove(device_page.xml_tree)
            self.updateData(True)
            self.onDefinitionChanged()

        def detachActive():
            try:
                self.domain.detachDevice(device_page.xml_tree)
                self.updateData()
            except Exception as e:
                self.window_ref.window.pushToastText(
                    str(e) + "\nDevice was removed from static configuration"
                )
                detachNormal()

        if self.domain.isActive():
            dialog = selectDialog(
                "Detach device?",
                "Try to detach device from running domain",
                [
                    ActionOption(
                        "Detach",
                        detachActive,
                        appearance=Adw.ResponseAppearance.SUGGESTED,
                    )
                ],
            )
            dialog.present(self.window_ref.window)
        else:
            detachNormal()

    def onApplyClicked(self, *args):
        """Callback when the regular apply button was clicked."""
        try:
            if self.stack.get_visible_child_name() == "xml":
                self.domain.updateDefinition(self.xml_box.getText())
            else:
                self.domain.update(self.xml_tree)
            self.domain.setAutostart(self.autostart)
            self.updateData()
        except Exception as e:
            self.window_ref.window.pushToastText(str(e))

    def onDeviceUpdate(self, device_xml: ET.Element):
        """Callback from a page, asking for the device to be updated."""
        self.domain.updateDevice(device_xml)

    def onBackClicked(self, _):
        self.navigation_view.pop()

    def end(self):
        # Unsubscribe from events
        self.perf_box.end()
        self.snapshots_box.end()
        self.domain.unregister_callback(self.onConnectionEvent)

    def getUniqueIdentifier(self) -> str:
        return self.domain.getUUID()
