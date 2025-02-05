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


class DomainCapabilities:
    emulator_path = "Unknown"
    domain = "Unknown"
    machine = "Unknown"
    arch = "Unknown"
    vcpu = 0

    os = {
        "firmware": ["bios", "efi"],
        "loader": {
            "values": ["/some/loader", "/another/loader"],
            "type": ["rom", "pflash"],
            "readonly": ["yes", "no"],
            "secure": ["yes", "no"],
        },
    }

    cpu_modes = ["host-passthrough"]
    custom_cpu_models = ["Haswell"]
    iothreads = True

    devices = {
        "disk": {
            "diskDevice": ["disk", "cdrom"],
            "bus": ["sata"],
            "model": ["virtio"],
        },
        "graphics": {"type": ["sdl", "vnc", "spice", "egl-headless", "dbus"]},
        "video": {"modelType": ["vga", "cirrus"]},
        "hostdev": {
            "mode": ["subsystem"],
            "startupPolicy": ["default", "mandatory", "requisite", "optional"],
            "subsysType": ["usb", "pci", "scsi"],
            "capsType": [],
            "pciBackend": ["default", "vfio"],
        },
        "rng": {
            "model": ["virtio", "virtio-transitional", "virtio-non-transitional"],
            "backendModel": ["random", "egd", "builtin"],
        },
        "filesystem": {"driverType": ["path", "handle", "virtiofs"]},
        "tpm": {
            "model": ["tpm-tis", "tpm-crb"],
            "backendModel": ["passthrough", "emulator", "external"],
            "backendVersion": ["1.2", "2.0"],
        },
        "redirdev": {"bus": ["usb"]},
        "channel": {"type": ["pty", "unix", "spicevmc"]},
        "crypto": {"model": ["virtio"], "type": ["qemu"], "backendModel": ["builtin"]},
    }

    def __init__(self, xml_tree: ET.Element):
        if xml_tree is not None:
            self.xml_tree = xml_tree

            # General
            self.emulator_path = self.xml_tree.find("path").text
            self.domain = self.xml_tree.find("domain").text
            self.machine = self.xml_tree.find("machine").text
            self.arch = self.xml_tree.find("arch").text
            self.vcpu = int(self.xml_tree.find("vcpu").get("max"))

            # OS
            self.os = {}

            self.os["firmware"] = [
                e.text for e in self.xml_tree.find("os").find("enum").iter("value")
            ]

            loader = self.xml_tree.find("os").find("loader")
            if loader.get("supported") == "yes":
                self.os["loader"] = {}
                self.os["loader"]["values"] = [e.text for e in loader.findall("value")]
                for enum in loader.iter("enum"):
                    self.os["loader"][enum.get("name")] = [
                        e.text for e in enum.iter("value")
                    ]
            else:
                self.os["loader"] = None

            cpu = self.xml_tree.find("cpu")
            self.cpu_modes = []
            self.custom_cpu_models = []
            for mode in cpu.findall("mode"):
                if mode.get("supported") == "yes":
                    self.cpu_modes.append(mode.get("name"))
                if mode.get("name") == "custom":
                    for model in mode.findall("model"):
                        if model.get("usable") == "yes":
                            self.custom_cpu_models.append(model.text)

            self.iothreads = self.xml_tree.find("iothreads").get("supported") == "yes"

            # Devices
            devices = self.xml_tree.find("devices")
            self.devices = {}
            for dev in devices:
                if dev.get("supported") == "yes":
                    self.devices[dev.tag] = {}
                    for enum in dev.findall("enum"):
                        self.devices[dev.tag][enum.get("name")] = [
                            e.text for e in enum.findall("value")
                        ]
