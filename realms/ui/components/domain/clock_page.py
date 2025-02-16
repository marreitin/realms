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

from gi.repository import Adw, Gtk

from realms.ui.components import iconButton
from realms.ui.components.bindable_entries import BindableComboRow, BindableDropDown
from realms.ui.components.generic_preferences_row import GenericPreferencesRow

from .base_device_page import BaseDevicePage

# TODO: Timezone, variable and absolute clock modes


class TimerRow(GenericPreferencesRow):
    """Row for a single time source."""

    def __init__(self, xml_elem: ET.Element, parent, **kwargs):
        super().__init__(**kwargs)

        self.xml_elem = xml_elem
        self.parent = parent

        self.valid_names = [
            "hpet",
            "kvmclock",
            "pit",
            "rtc",
            "tsc",
            "hypervclock",
            "armvtimer",
            "platform",
        ]
        name_box = Gtk.Box(spacing=6)
        self.addChild(name_box)
        self.name_row = BindableDropDown(self.valid_names, "", hexpand=True)
        self.name_row.bindAttr(self.xml_elem, "name", self.__onNameChanged__)
        name_box.append(self.name_row)

        remove = iconButton(
            "Remove",
            "user-trash-symbolic",
            self.__onRemoveClicked__,
            css_classes=["flat"],
            hexpand=False,
        )
        name_box.append(remove)

        self.track_box = Gtk.Box(spacing=6, margin_start=18)
        self.addChild(self.track_box)
        self.track_box.append(
            Gtk.Label(label="track", hexpand=True, halign=Gtk.Align.START)
        )
        self.track_combo = BindableDropDown(
            ["boot", "guest", "wall", "realtime"],
            "",
            css_classes=["flat"],
            tooltip_text="What the timer tracks",
        )
        self.track_box.append(self.track_combo)

        tickpolicy_box = Gtk.Box(spacing=6, margin_start=18)
        tickpolicy_box.append(
            Gtk.Label(label="Tick Policy", halign=Gtk.Align.START, hexpand=True)
        )
        self.tickpolicy_combo = BindableDropDown(
            ["delay", "catchup", "merge", "discard"], "", css_classes=["flat"]
        )
        tickpolicy_box.append(self.tickpolicy_combo)
        self.addChild(tickpolicy_box)

        self.update()

    def update(self):
        self.tickpolicy_combo.bindAttr(
            self.xml_elem, "tickpolicy", self.parent.showApply
        )

        name = self.name_row.getSelectedString()
        if name in ["rtc", "platform"]:
            self.track_box.set_visible(True)
            self.track_combo.bindAttr(self.xml_elem, "track", self.parent.showApply)
        else:
            self.track_box.set_visible(False)
            if self.xml_elem.get("track") is not None:
                del self.xml_elem.attrib["track"]

    def __onNameChanged__(self):
        self.xml_elem.clear()
        self.xml_elem.set("name", self.name_row.getSelectedString())

        self.update()
        self.parent.showApply()

    def __onRemoveClicked__(self, btn):
        self.parent.onRemoveTimerRow(self)


class ClockPage(BaseDevicePage):
    """Clock Page, one of the always-present settings."""

    def __init__(
        self, parent, xml_tree: ET.Element, use_for_adding=False, can_update=False
    ):
        super().__init__(parent, xml_tree, use_for_adding, can_update)

        self.timer_rows = []

    def build(self):
        self.general_group = Adw.PreferencesGroup(title="Clock")
        self.prefs_page.add(self.general_group)

        self.offset_row = BindableComboRow(["utc", "localtime"], title="Clock offset")
        self.general_group.add(self.offset_row)

        self.timer_group = Adw.PreferencesGroup(title="Timers")
        self.prefs_page.add(self.timer_group)

        add_timer = iconButton(
            "",
            "list-add-symbolic",
            self.__onAddTimerClicked__,
            tooltip_text="Add timer",
            css_classes=["flat"],
        )
        self.timer_group.set_header_suffix(add_timer)

        self.updateData()

    def updateData(self):
        clock = self.xml_tree.find("clock")
        self.offset_row.bindAttr(clock, "offset", self.showApply)
        for row in self.timer_rows.copy():
            self.__removeTimerRow__(row)
        for t in clock.findall("timer"):
            row = TimerRow(t, self)
            self.timer_group.add(row)
            self.timer_rows.append(row)

    def getTitle(self) -> str:
        if self.use_for_adding:
            return ""
        return "Clock"

    def getDescription(self) -> str:
        return "Hardware clock"

    def getIconName(self) -> str:
        return "clock-alt-symbolic"

    def __onAddTimerClicked__(self, btn):
        clock = self.xml_tree.find("clock")
        timer = ET.SubElement(clock, "timer")
        row = TimerRow(timer, self)
        self.timer_group.add(row)
        self.timer_rows.append(row)
        self.showApply()

    def __removeTimerRow__(self, row: TimerRow):
        clock = self.xml_tree.find("clock")
        if row.xml_elem in clock:
            clock.remove(row.xml_elem)
        self.timer_group.remove(row)
        self.timer_rows.remove(row)

    def __onRemoveTimerRow__(self, row: TimerRow):
        self.__removeTimerRow__(row)
        self.showApply()
