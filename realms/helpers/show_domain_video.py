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
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from gi.repository import Adw

from realms.libvirt_wrap import Domain
from realms.ui.components.common import simpleErrorDialog


def getDisplay(domain_xml: ET.Element) -> ET.Element | None:
    """Retrieve the first display device that could be opened

    Args:
        domain_xml (ET.Element): Domain xml

    Returns:
        ET.Element: None or found graphics_xml
    """
    displays = domain_xml.findall(".//graphics")
    for d in displays:
        if d.get("type") not in ["sdl", "desktop", "egl-headless"]:
            return d
    return None


def hasDisplay(domain_xml: ET.Element):
    return getDisplay(domain_xml) is not None


def show(domain: Domain, window: Adw.ApplicationWindow):
    "Open a remote viewer window and display the domain"
    conn_url = domain.connection.getURLCurr()
    parsed_url = urlparse(conn_url)

    hostname = parsed_url.hostname

    xml = domain.getETree()

    display = getDisplay(xml)

    if display is None:
        simpleErrorDialog("No Display", "The domain doesn't have any display.", window)
        return

    spice_cmd = []

    graphics_type = display.get("type")
    if graphics_type == "spice":
        listen_type = display.find("listen")
        if listen_type is not None and listen_type.get("type") == "socket":
            path = listen_type.get("socket")
            spice_cmd = ["remote-viewer", f"spice+unix://{ path }"]
        elif (
            listen_type is not None and listen_type.get("type") == "address"
        ) or listen_type is None:
            graphics_port = display.get("port")

            if hostname is not None:
                display_url = f"{ graphics_type }://{ hostname }:{ graphics_port if graphics_port is not None else '5900' }"
            else:
                display_url = f"{ graphics_type }://localhost:{ graphics_port if graphics_port is not None else '5900' }"

            spice_cmd = ["remote-viewer", display_url]
        else:
            simpleErrorDialog("Unknown Display Type", "", window)
            raise NotImplementedError
    else:
        simpleErrorDialog("Unknown Graphics Type", "", window)
        raise NotImplementedError

    print(spice_cmd)
    try:
        subprocess.Popen(spice_cmd)
    except Exception as e:
        simpleErrorDialog("Failed to open display", str(e), window)
        return
