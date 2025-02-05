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
import re


def transformUnitsAuto(
    bytes_vol: int, base_unit: str = None, target_unit: str = None
) -> tuple[float, str]:
    """Transform an amount of bytes into something reasonable and a unit

    Args:
        bytes_vol (int): Volume
        base_unit: If bytes is not in bytes but a larger volume

    Returns:
        tuple: Amount transformed to unit and unit
    """
    units = ["B", "KB", "MB", "GB", "TB", "PT", "EB", "ZB", "YB", "RB", "QB"]
    if base_unit is not None:
        bytes_vol = stringToBytes(f"{ bytes_vol }{ base_unit }")
    for unit in units:
        if bytes_vol >= 10**3:
            bytes_vol /= 10**3
        else:
            return (bytes_vol, unit)


def bytesToString(bytes_vol: int | str, base_unit: str = None) -> str:
    """Transform bytes into a nice description string

    Args:
        bytes_vol (int|str): bytes
        base_unit: If bytes is not in bytes but a larger volume

    Returns:
        str: Nice description
    """
    if base_unit is not None and len(base_unit) == 1 and base_unit.upper() != "B":
        base_unit += "iB"  # Transform i.e. M to MiB

    if type(bytes_vol) is str:
        if bytes_vol == "":
            return ""
        else:
            bytes_vol = int(bytes_vol)
    amount, unit = transformUnitsAuto(bytes_vol, base_unit)
    amount = round(amount, 1)
    return f"{ amount } { unit }"


def stringToBytes(string: str, target_unit: str = None) -> int:
    """Transform size describing string to bytes

    Args:
        string (str): Input
        target_unit: If the target are not bytes

    Returns:
        int: Bytes
    """
    if string.isdigit():
        return int(string)

    if target_unit is not None and len(target_unit) == 1 and target_unit.upper() != "B":
        target_unit += "iB"  # Transform i.e. M to MiB

    try:
        if not re.match(r"^[\d\.]+\s*\wi?\w?$", string):
            raise ValueError("invalid format")
        string = string.upper().strip().replace(" ", "")

        num_end_index = 0
        while string[num_end_index] in "0123456789.":
            num_end_index += 1

        num = float(string[0:num_end_index])
        unit = string[num_end_index:]

        bytes = 0
        if "I" in unit:
            units = [
                "B",
                "KIB",
                "MIB",
                "GIB",
                "TIB",
                "PIT",
                "EIB",
                "ZIB",
                "YIB",
                "RIB",
                "QIB",
            ]
            bytes = int(num * 1024 ** units.index(unit))
        else:
            units = ["B", "KB", "MB", "GB", "TB", "PT", "EB", "ZB", "YB", "RB", "QB"]
            bytes = int(num * 1000 ** units.index(unit))

        if target_unit is not None:
            if "I" in target_unit.upper():
                units = [
                    "B",
                    "KIB",
                    "MIB",
                    "GIB",
                    "TIB",
                    "PIT",
                    "EIB",
                    "ZIB",
                    "YIB",
                    "RIB",
                    "QIB",
                ]
                bytes /= 1024 ** units.index(target_unit.upper())
            else:
                units = [
                    "B",
                    "KB",
                    "MB",
                    "GB",
                    "TB",
                    "PT",
                    "EB",
                    "ZB",
                    "YB",
                    "RB",
                    "QB",
                ]
                bytes /= 1024 ** units.index(target_unit.upper())
        return int(bytes)

    except Exception as e:
        raise ValueError(e)
