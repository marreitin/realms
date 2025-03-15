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
import libvirt

from .constants import *


def printEvent(conn, obj, type_id, event_id, detail_id):
    """Print event details in readable format"""
    if type_id == CALLBACK_TYPE_CONNECTION_GENERIC:
        if event_id == CONNECTION_EVENT_CONNECTED:
            print("Connection connected", conn, obj, type_id, event_id, detail_id)
        elif event_id == CONNECTION_EVENT_ATTEMPT_CONNECT:
            print("Connection attempted", conn, obj, type_id, event_id, detail_id)
        elif event_id == CONNECTION_EVENT_DISCONNECTED:
            print("Connection disconnected", conn, obj, type_id, event_id, detail_id)
        elif event_id == CONNECTION_EVENT_DELETED:
            print("Connection deleted", conn, obj, type_id, event_id, detail_id)
        elif event_id == CONNECTION_EVENT_SETTINGS_CHANGED:
            print(
                "Connection settings changed", conn, obj, type_id, event_id, detail_id
            )
        elif event_id == CONNECTION_EVENT_CONNECTION_FAILED:
            print(
                "Connection failed to connect", conn, obj, type_id, event_id, detail_id
            )
        else:
            raise ValueError(
                "This should not be reached - unknown generic connection event_id"
            )
    elif type_id == CALLBACK_TYPE_DOMAIN_LIFECYCLE:
        if event_id == libvirt.VIR_DOMAIN_EVENT_DEFINED:
            print("Domain defined", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_DOMAIN_EVENT_UNDEFINED:
            print("Domain undefined", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_DOMAIN_EVENT_STARTED:
            print("Domain started", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_DOMAIN_EVENT_SUSPENDED:
            print("Domain suspended", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_DOMAIN_EVENT_RESUMED:
            print("Domain resumed", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_DOMAIN_EVENT_STOPPED:
            print("Domain stopped", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_DOMAIN_EVENT_SHUTDOWN:
            print("Domain shutdown", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_DOMAIN_EVENT_PMSUSPENDED:
            print("Domain pmsuspended", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_DOMAIN_EVENT_CRASHED:
            print("Domain crashed", conn, obj, type_id, event_id, detail_id)
        else:
            raise ValueError(
                "This should not be reached - unknown domain event_id",
                conn,
                obj,
                type_id,
                event_id,
                detail_id,
            )
    elif type_id == CALLBACK_TYPE_DOMAIN_GENERIC:
        if event_id == DOMAIN_EVENT_DELETED:
            print("Domain deleted", conn, obj, type_id, event_id, detail_id)
        elif event_id == DOMAIN_EVENT_ADDED:
            print("Domain added", conn, obj, type_id, event_id, detail_id)
        elif event_id == DOMAIN_EVENT_SNAPSHOT_TAKEN:
            print("Domain snapshot taken", conn, obj, type_id, event_id, detail_id)
        elif event_id == DOMAIN_EVENT_SNAPSHOT_DELETED:
            print("Domain snapshot deleted", conn, obj, type_id, event_id, detail_id)
        else:
            raise ValueError(
                "This should not be reached - unknown generic domain event_id"
            )
    elif type_id == CALLBACK_TYPE_POOL_LIFECYCLE:
        if event_id == libvirt.VIR_STORAGE_POOL_EVENT_DEFINED:
            print("Pool defined", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_STORAGE_POOL_EVENT_UNDEFINED:
            print("Pool undefined", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_STORAGE_POOL_EVENT_STARTED:
            print("Pool started", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_STORAGE_POOL_EVENT_STOPPED:
            print("Pool stopped", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_STORAGE_POOL_EVENT_CREATED:
            print("Pool created", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_STORAGE_POOL_EVENT_DELETED:
            print("Pool deleted", conn, obj, type_id, event_id, detail_id)
        else:
            raise ValueError(
                "This should not be reached - unknown pool lifecycle event_id"
            )
    elif type_id == CALLBACK_TYPE_POOL_GENERIC:
        if event_id == POOL_EVENT_DELETED:
            print("Pool deleted", conn, obj, type_id, event_id, detail_id)
        elif event_id == POOL_EVENT_ADDED:
            print("Pool added", conn, obj, type_id, event_id, detail_id)
        elif event_id == POOL_EVENT_VOLUME_ADDED:
            print("Pool volume added", conn, obj, type_id, event_id, detail_id)
        elif event_id == POOL_EVENT_VOLUME_DELETED:
            print("Pool volume deleted", conn, obj, type_id, event_id, detail_id)
        else:
            raise ValueError(
                "This should not be reached - unknown generic pool event_id"
            )
    elif type_id == CALLBACK_TYPE_NETWORK_LIFECYCLE:
        if event_id == libvirt.VIR_NETWORK_EVENT_DEFINED:
            print("Network defined", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_NETWORK_EVENT_UNDEFINED:
            print("Network undefined", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_NETWORK_EVENT_STARTED:
            print("Network started", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_NETWORK_EVENT_STOPPED:
            print("Network stopped", conn, obj, type_id, event_id, detail_id)
        else:
            raise ValueError(
                "This should not be reached - unknown network lifecycle event_id"
            )
    elif type_id == CALLBACK_TYPE_NETWORK_GENERIC:
        if event_id == NETWORK_EVENT_DELETED:
            print("Network deleted", conn, obj, type_id, event_id, detail_id)
        elif event_id == NETWORK_EVENT_ADDED:
            print("Network added", conn, obj, type_id, event_id, detail_id)
        else:
            raise ValueError(
                "This should not be reached - unknown generic network event_id"
            )
    elif type_id == CALLBACK_TYPE_SECRET_LIFECYCLE:
        if event_id == libvirt.VIR_SECRET_EVENT_DEFINED:
            print("Secret defined", conn, obj, type_id, event_id, detail_id)
        elif event_id == libvirt.VIR_SECRET_EVENT_UNDEFINED:
            print("Secret undefined", conn, obj, type_id, event_id, detail_id)
        else:
            raise ValueError(
                "This should not be reached - unknown secret lifecycle event_id"
            )
    elif type_id == CALLBACK_TYPE_SECRET_GENERIC:
        if event_id == SECRET_EVENT_ADDED:
            print("Secret added", conn, obj, type_id, event_id, detail_id)
        elif event_id == SECRET_EVENT_DELETED:
            print("Secret deleted", conn, obj, type_id, event_id, detail_id)
        else:
            raise ValueError(
                "This should not be reached - unknown secret generic event_id"
            )
    else:
        raise ValueError(
            "This should not be reached - unknown type_id",
            conn,
            obj,
            type_id,
            event_id,
            detail_id,
        )


def libvirtVersionToString(version: int) -> str:
    """Transform a libvirt version encoded as int to str.

    Args:
        version (int): Version

    Returns:
        str: Formatted version string: major.minor.release
    """
    if version == -1:
        return "unknown"
    release = int(version % 1000)
    minor = int(((version - release) % 1000000) / 1000)
    major = int((version - minor * 1000 - release) / 1000000)
    return f"{major}.{minor}.{release}"
