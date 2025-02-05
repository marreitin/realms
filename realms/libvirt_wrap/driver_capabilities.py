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

from realms.helpers import getETText


class DriverCapabilities:
    cpu = {
        "arch": "unknown",
        "model": "unknown",
        "vendor": "unknown",
    }

    os_types = ["hvm"]
    guest_types = {
        "hvm": {
            "i686": {
                "hypervisors": ["qemu", "kvm"],
                "machines": ["pc-abc", "pc-xyz"],
                "emulator": "/bin/emulator",
            }
        }
    }

    def __init__(self, xml_tree: ET.Element):
        if xml_tree is not None:
            self.xml_tree = xml_tree

            host = self.xml_tree.find("host")

            cpu_data = host.find("cpu")

            self.cpu = {
                "arch": getETText(cpu_data.find("arch")),
                "model": getETText(cpu_data.find("model")),
                "vendor": getETText(cpu_data.find("vendor")),
            }

            guests = self.xml_tree.findall("guest")

            self.os_types = []
            self.guest_types = {}

            for e in guests:
                os_type = getETText(e.find("os_type"))
                self.os_types.append(os_type)

                if os_type not in self.guest_types:
                    self.guest_types[os_type] = {}

                arch = e.find("arch")
                arch_data = {}

                arch_data["machines"] = [m.text for m in arch.findall("machine")]
                arch_data["hypervisors"] = [
                    d.get("type") for d in arch.findall("domain")
                ]
                arch_data["emulator"] = arch.find("emulator").text

                self.guest_types[os_type][arch.get("name")] = arch_data

            self.os_types = list(set(self.os_types))
