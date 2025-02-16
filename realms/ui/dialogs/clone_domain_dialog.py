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

from realms.helpers.async_jobs import ResultWrapper, failableAsyncJob
from realms.libvirt_wrap import Domain, Volume
from realms.libvirt_wrap.constants import *
from realms.ui.components import GenericPreferencesRow, hspacer
from realms.ui.components.common import simpleErrorDialog
from realms.ui.components.preference_widgets import RealmsPreferencesPage


class CloneVolumeBox(GenericPreferencesRow):
    def __init__(self, volume: Volume):
        super().__init__()
        self.volume = volume

        self.switch = None
        self.entry = None

        self.build()

    def build(self):
        box = Gtk.Box(spacing=6)
        box.append(
            Gtk.Label(
                label=f"{ self.volume.pool.getDisplayName() }/{ self.volume.getName() }",
                css_classes=["heading"],
            )
        )
        box.append(hspacer())
        self.switch = Gtk.Switch(active=True)
        box.append(self.switch)
        self.addChild(box)

        self.entry = Gtk.Entry(
            placeholder_text="New name", text=f"{ self.volume.getName() }-clone"
        )
        self.addChild(self.entry)

    def shouldClone(self) -> bool:
        return self.switch.get_active()

    def getNewName(self) -> str:
        return self.entry.get_text()


class CloneParam:
    def __init__(self, volume: Volume, new_name: str):
        self.volume = volume
        self.new_name = new_name


class CloneVolumesPage(Adw.NavigationPage):
    def __init__(self, window: Adw.ApplicationWindow, domain: Domain):
        super().__init__(title="post-actions")

        self.domain = domain
        self.volume_boxes = []

        self.build()

    def build(self):
        self.prefs_page = RealmsPreferencesPage(clamp=False)
        self.set_child(self.prefs_page)

        self.prefs_group = Adw.PreferencesGroup(
            title="Cloned volumes", description="Select volumes that will be cloned"
        )
        self.prefs_page.add(self.prefs_group)

        for vol in self.domain.getAttachedStorageVolumes():
            box = CloneVolumeBox(vol)
            self.prefs_group.add(box)
            self.volume_boxes.append(box)

    def finalize(self) -> list[CloneParam]:
        to_clone = []
        for box in self.volume_boxes:
            if box.shouldClone():
                to_clone.append(CloneParam(box.volume, box.getNewName()))

        return to_clone


class CloneDomainDialog:
    def __init__(self, window: Adw.ApplicationWindow, domain: Domain):
        super().__init__()

        self.window = window
        self.domain = domain

        self.current_page = 0
        self.total_pages = 2

        self.volumes_page = None

        self.domain.register_callback_any(self.onConnectionEvent, None)

        self.build()

    def build(self):
        # Create a Builder
        self.builder = Gtk.Builder.new_from_resource(
            "/com/github/marreitin/realms/gtk/clonedom.ui"
        )

        # Obtain and show the main window
        self.dialog = self.obj("main-dialog")
        self.dialog.connect("closed", self.onDialogClosed)
        self.dialog.present(self.window)

        self.obj("btn-next").connect("clicked", self.onNextClicked)
        self.obj("btn-back").connect("clicked", self.onBackClicked)
        self.obj("btn-finish").connect("clicked", self.onApplyClicked)

        self.obj("nav-view").connect("popped", self.onNavPopped)

        self.setControlButtonStates()

        self.obj("new_name").grab_focus()

    def setControlButtonStates(self):
        self.obj("btn-back").set_visible(False)
        self.obj("btn-finish").set_visible(False)
        self.obj("btn-next").set_visible(False)

        if self.current_page == 0:
            self.obj("btn-next").set_visible(True)
        elif self.current_page == 1:
            self.obj("btn-back").set_visible(True)
            self.obj("btn-finish").set_visible(True)

    def onNextClicked(self, _):
        visible_page = self.obj("nav-view").get_visible_page()

        self.current_page += 1
        if visible_page == self.obj("template-nav-page"):
            # Showing volume options
            if self.volumes_page is None:
                self.volumes_page = CloneVolumesPage(self.window, self.domain)

            self.obj("nav-view").push(self.volumes_page)
        else:
            raise Exception("this should not be reached")
        self.setControlButtonStates()

    def onBackClicked(self, *_):
        self.obj("nav-view").pop()

    def onNavPopped(self, *_):
        self.current_page -= 1
        self.setControlButtonStates()

    def cloneDomain(self):
        # Prepare domain xml
        domain_xml = self.domain.getETree()
        domain_xml.find("name").text = self.obj("new_name").get_text()
        title = domain_xml.find("title")
        if title is not None:
            title.text = self.obj("new_name").get_text()
        domain_xml.find("uuid").text = ""

        # Clone volumes.
        clone_params = self.volumes_page.finalize()

        for p in clone_params:
            for device_xml in domain_xml.find("devices"):
                if device_xml.tag == "disk" and device_xml.get("type", "") == "volume":
                    source_xml = device_xml.find("source")
                    if source_xml is None:
                        continue

                    pool_name = source_xml.get("pool", "")
                    vol_name = source_xml.get("volume", "")

                    if not pool_name or not vol_name:
                        continue

                    if pool_name != p.volume.pool.getDisplayName():
                        continue

                    if vol_name != p.volume.getName():
                        continue

                    source_xml.set("volume", p.new_name)
                    p.volume.clone(p.new_name)

        # Finally clone the domain.
        new_xml = ET.tostring(domain_xml, encoding="unicode")
        print(new_xml)
        self.domain.connection.addDomain(new_xml)

    def onApplyClicked(self, _):
        def onFail(e: Exception):
            simpleErrorDialog("Invalid settings", str(e), self.window)

        def onDone(res: ResultWrapper):
            self.dialog.set_can_close(True)
            self.obj("main-stack").set_visible_child_name("main-page")

            if not res.failed:
                self.dialog.close()

        spinner = Adw.SpinnerPaintable(widget=self.obj("cloning-status"))
        self.obj("cloning-status").set_paintable(spinner)
        self.obj("main-stack").set_visible_child_name("spinner-page")

        self.dialog.set_can_close(False)
        failableAsyncJob(self.cloneDomain, [], onFail, onDone)

    def onStackChanged(self, *_):
        # XML preview is not really possible
        self.setControlButtonStates()

    def obj(self, name: str):
        o = self.builder.get_object(name)
        if o is None:
            raise NotImplementedError(f"Object { name } could not be found!")
        return o

    def onConnectionEvent(self, conn, obj, type_id, event_id, detail_id, opaque):
        if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
            if event_id in [CONNECTION_EVENT_DISCONNECTED, CONNECTION_EVENT_DELETED]:
                self.dialog.close()
        elif type_id == CALLBACK_TYPE_DOMAIN_GENERIC:
            if event_id == DOMAIN_EVENT_DELETED:
                self.dialog.close()
        elif type_id == CALLBACK_TYPE_DOMAIN_LIFECYCLE:
            if event_id == libvirt.VIR_DOMAIN_EVENT_DEFINED:
                self.dialog.close()

    def onDialogClosed(self, *_):
        self.domain.unregister_callback(self.onConnectionEvent)
