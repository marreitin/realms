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
    if hostname is None:
        hostname = "localhost"

    xml = domain.getETree()

    display = getDisplay(xml)

    if display is None:
        simpleErrorDialog("No Display", "The domain doesn't have any display.", window)
        return

    remote_viewer_cmd = []

    graphics_type = display.get("type")

    if graphics_type in ["spice", "vnc"]:
        listen = display.find("listen")

        if listen is not None and listen.get("type") == "socket":
            path = listen.get("socket")
            remote_viewer_cmd = ["remote-viewer", f"{ graphics_type }+unix://{ path }"]
        elif (listen is not None and listen.get("type") == "address") or listen is None:
            graphics_port = display.get("port")

            display_url = f"{ graphics_type }://{ hostname }:{ graphics_port if graphics_port is not None else '5900' }"

            remote_viewer_cmd = ["remote-viewer", display_url]
        elif (listen is not None and listen.get("type") == "network") or listen is None:
            graphics_port = display.get("port")
            hostname = listen.get("address", "localhost")
            display_url = f"{ graphics_type }://{ hostname }:{ graphics_port if graphics_port is not None else '5900' }"

            remote_viewer_cmd = ["remote-viewer", display_url]
        else:
            simpleErrorDialog(
                "Configuration Unsupported",
                f"Unknown listen type for { graphics_type } graphics",
                window,
            )
            raise NotImplementedError

    else:
        simpleErrorDialog("Unknown Graphics Type", "Use either VNC or SPICE", window)
        raise NotImplementedError

    print(remote_viewer_cmd)
    try:
        subprocess.Popen(remote_viewer_cmd)
    except Exception as e:
        simpleErrorDialog("Failed to Open Remote Viewer", str(e), window)
        return
