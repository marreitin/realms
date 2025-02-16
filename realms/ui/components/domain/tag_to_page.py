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
from .audio_page import AudioPage
from .character_page import CharacterPage
from .controller_page import ControllerPage
from .crypto_page import CryptoPage
from .disk_page import DiskPage
from .filesystem_page import FilesystemPage
from .graphics_page import GraphicsPage
from .hostdev_page import HostdevPage
from .hub_page import HubPage
from .input_page import InputPage
from .interface_page import InterfacePage
from .iommu_page import IOMMUPage
from .lease_page import LeasePage
from .mem_page import MemPage
from .memballoon_page import MemballoonPage
from .panic_page import PanicPage
from .pstore_page import PstorePage
from .redirdev_page import RedirdevPage
from .redirfilter_page import RedirfilterPage
from .rng_page import RNGPage
from .shmem_page import SHMemPage
from .smartcard_page import SmartcardPage
from .sound_page import SoundPage
from .tpm_page import TPMPage
from .video_page import VideoPage
from .vsock_page import VSockPage
from .watchdog_page import WatchdogPage


def tagToPage(tag: str) -> type:
    """Get the device page type depending on the tag as found in xml."""
    page_type = None
    if tag == "audio":
        page_type = AudioPage
    elif tag in ["parallel", "serial", "console", "channel"]:
        page_type = CharacterPage
    elif tag == "controller":
        page_type = ControllerPage
    elif tag == "crypto":
        page_type = CryptoPage
    elif tag == "disk":
        page_type = DiskPage
    elif tag == "filesystem":
        page_type = FilesystemPage
    elif tag == "graphics":
        page_type = GraphicsPage
    elif tag == "hostdev":
        page_type = HostdevPage
    elif tag == "hub":
        page_type = HubPage
    elif tag == "input":
        page_type = InputPage
    elif tag == "interface":
        page_type = InterfacePage
    elif tag == "iommu":
        page_type = IOMMUPage
    elif tag == "lease":
        page_type = LeasePage
    elif tag == "memory":
        page_type = MemPage
    elif tag == "memballoon":
        page_type = MemballoonPage
    elif tag == "panic":
        page_type = PanicPage
    elif tag == "pstore":
        page_type = PstorePage
    elif tag == "redirdev":
        page_type = RedirdevPage
    elif tag == "redirfilter":
        page_type = RedirfilterPage
    elif tag == "rng":
        page_type = RNGPage
    elif tag == "shmem":
        page_type = SHMemPage
    elif tag == "smartcard":
        page_type = SmartcardPage
    elif tag == "sound":
        page_type = SoundPage
    elif tag == "tpm":
        page_type = TPMPage
    elif tag == "video":
        page_type = VideoPage
    elif tag == "vsock":
        page_type = VSockPage
    elif tag == "watchdog":
        page_type = WatchdogPage
    elif tag == "emulator":
        pass  # Is handled in the general page
    else:
        print("Unknown device", tag)
    return page_type
