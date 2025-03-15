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

from realms.ui.components.bindable_entries import BindableComboRow, BindableDropDown
from realms.ui.components.common import deleteRow, iconButton

from .base_device_page import BaseDevicePage

# TODO: Timezone, variable and absolute clock modes


class TimerRow(Adw.ExpanderRow):
    """Row for a single time source."""

    def __init__(self, xml_elem: ET.Element, parent, **kwargs):
        super().__init__(
            title="Timer", show_enable_switch=False, enable_expansion=True, **kwargs
        )

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

        self.name_row = BindableDropDown(
            self.valid_names,
            "",
            vexpand=False,
            valign=Gtk.Align.CENTER,
            width_request=120,
        )
        self.name_row.bindAttr(self.xml_elem, "name", self.__onNameChanged__)
        self.add_suffix(self.name_row)

        self.track_combo = BindableComboRow(
            ["boot", "guest", "wall", "realtime"], "", title="Track"
        )
        self.add_row(self.track_combo)

        self.tickpolicy_combo = BindableComboRow(
            ["delay", "catchup", "merge", "discard"], "", title="Tick policy"
        )
        self.add_row(self.tickpolicy_combo)

        self.add_row(deleteRow(self.__onRemoveClicked__))

        self.update()

    def update(self):
        self.tickpolicy_combo.bindAttr(
            self.xml_elem, "tickpolicy", self.parent.showApply
        )

        name = self.name_row.getSelectedString()
        if name in ["rtc", "platform"]:
            self.track_combo.set_visible(True)
            self.track_combo.bindAttr(self.xml_elem, "track", self.parent.showApply)
        else:
            self.track_combo.set_visible(False)
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
        self.timer_rows.clear()

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
