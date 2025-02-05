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


class PoolCapabilities:
    pool_types = [
        "dir",
        "disk",
        "fs",
        "gluster",
        "iscsi",
        "iscsi-direct",
        "logical",
        "netfs",
        "mpath",
        "rbd",
        "scsi",
        "vstorage",
        "zfs",
    ]

    pool_formats = {
        "fs": [
            "auto",
            "ext2",
            "ext3",
            "ext4",
            "ufs",
            "iso9660",
            "udf",
            "gfs",
            "gfs2",
            "vfat",
            "hfs+",
            "xfs",
            "ocfs2",
            "vmfs",
        ],
        "netfs": ["auto", "nfs", "glusterfs", "cifs"],
        "logical": ["lvm2"],
        "disk": ["dos", "dvh", "gpt", "mac", "bsd", "pc98", "sun", "lvm2"],
    }

    volume_formats = {
        "dir": [
            "raw",
            "bochs",
            "cloop",
            "cow",
            "dmg",
            "iso",
            "qcow",
            "qcow2",
            "qed",
            "vmdk",
            "vpc",
        ],
        "fs": [
            "raw",
            "bochs",
            "cloop",
            "cow",
            "dmg",
            "iso",
            "qcow",
            "qcow2",
            "qed",
            "vmdk",
            "vpc",
        ],
        "netfs": [
            "raw",
            "bochs",
            "cloop",
            "cow",
            "dmg",
            "iso",
            "qcow",
            "qcow2",
            "qed",
            "vmdk",
            "vpc",
        ],
        "logical": None,
        "disk": [
            "none",
            "linux",
            "fat16",
            "fat32",
            "linux-swap",
            "linux-lvm",
            "linux-raid",
            "extended",
        ],
        "iscsi": None,
        "iscsi-direct": None,
        "scsi": None,
        "mpath": None,
        "rbd": ["raw"],
        "gluster": [
            "raw",
            "bochs",
            "cloop",
            "cow",
            "dmg",
            "iso",
            "qcow",
            "qcow2",
            "qed",
            "vmdk",
            "vpc",
        ],
        "zfs": None,
        "vstorage": [
            "raw",
            "bochs",
            "cloop",
            "cow",
            "dmg",
            "iso",
            "qcow",
            "qcow2",
            "qed",
            "vmdk",
            "vpc",
        ],
    }

    def __init__(self, xml_tree: ET.Element):
        if xml_tree is not None:
            self.xml_tree = xml_tree

            self.pool_types = []
            self.pool_formats = {}
            self.volume_formats = {}

            for element in self.xml_tree.iter("pool"):
                if element.get("supported") == "yes":
                    self.pool_types.append(element.get("type"))

                    pool_options = element.find("poolOptions")
                    if pool_options is not None:
                        self.pool_formats[element.get("type")] = []
                        for t in pool_options.iter("value"):
                            self.pool_formats[element.get("type")].append(t.text)
                    else:
                        self.pool_formats[element.get("type")] = None

                    vol_options = element.find("volOptions")
                    if vol_options is not None:
                        self.volume_formats[element.get("type")] = []
                        for t in vol_options.iter("value"):
                            self.volume_formats[element.get("type")].append(t.text)
                    else:
                        self.volume_formats[element.get("type")] = None
