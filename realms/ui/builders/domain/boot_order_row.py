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


class BootOrderRow(Adw.ActionRow):
    """Row to add and set the <boot> element of a device's xml definition"""

    def __init__(self, device_xml: ET.Element, show_apply_cb: callable, **kwargs):
        super().__init__(
            title="Make device bootable",
            subtitle="Make device bootable and set it's boot priority",
            **kwargs
        )

        self.device_xml = device_xml
        self.show_apply_cb = show_apply_cb

        self.spinner = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(lower=1, upper=16, step_increment=1, value=1),
            digits=0,
            css_classes=["flat"],
            tooltip_text="Lower values go first",
        )
        self.add_suffix(self.spinner)

        self.switch = Gtk.Switch(vexpand=False, valign=Gtk.Align.BASELINE_CENTER)
        self.add_suffix(self.switch)

        self.switch.connect("notify::active", self.onSwitchChanged)
        self.spinner.connect("value-changed", self.onSpinnerChanged)

        self.updateData()

    def updateData(self):
        """Refresh all states according to the stored xml."""
        self.switch.disconnect_by_func(self.onSwitchChanged)
        self.spinner.disconnect_by_func(self.onSpinnerChanged)
        boot = self.device_xml.find("boot")
        if boot is None:
            self.spinner.set_sensitive(False)
            self.switch.set_active(False)
        else:
            self.spinner.set_sensitive(True)
            self.spinner.set_value(int(boot.get("order", "1")))
            self.switch.set_active(True)
        self.switch.connect("notify::active", self.onSwitchChanged)
        self.spinner.connect("value-changed", self.onSpinnerChanged)

    def setXML(self, xml_tree: ET.Element):
        """Update self with the new xml."""
        self.device_xml = xml_tree
        self.updateData()

    def onSwitchChanged(self, switch, *_):
        """The state of the switch changed."""
        boot = self.device_xml.find("boot")
        if switch.get_active():
            if boot is None:
                boot = ET.SubElement(
                    self.device_xml,
                    "boot",
                    attrib={"order": str(int(self.spinner.get_value()))},
                )
            self.spinner.set_sensitive(True)
        else:
            if boot is not None:
                self.device_xml.remove(boot)
            self.spinner.set_sensitive(False)
        self.show_apply_cb()

    def onSpinnerChanged(self, spinner, *_):
        """The spinner was changed."""
        boot = self.device_xml.find("boot")
        boot.set("order", str(int(spinner.get_value())))
        self.show_apply_cb()
