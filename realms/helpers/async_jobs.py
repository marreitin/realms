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
import threading
import traceback

from gi.repository import GLib


def asyncJob(f: callable, args: any, cb: callable):
    """Generic job that runs asynchronously and then calls back with the result

    Args:
        f (callable): Function to run asynchronously
        args (any): Arguments for f
        cb (callable): Callback, will be called with results from f
    """

    def run(args):
        ret = f(*args)
        GLib.idle_add(cb, ret)

    thread = threading.Thread(target=run, args=[args])
    thread.start()


class ResultWrapper:
    def __init__(self, data: any, failed: bool):
        self.data = data
        self.failed = failed


def failableAsyncJob(f: callable, args: any, except_cb: callable, finally_cb: callable):
    """Generic job that runs asynchronously and calls back upon failure, then calls back
    again with a ResultWrapper as argument

    Args:
        f (callable): Function to run asynchronously
        args (any): Arguments for f
        except_cb (callable): Callback on failure, called with exception
        finally_cb (callable): Final callback with ResultWrapper for data
    """

    def onExcept(e: Exception):
        except_cb(e)
        finally_cb(ResultWrapper(None, True))

    def run(args):
        try:
            res = f(*args)
            GLib.idle_add(finally_cb, ResultWrapper(res, False))
        except Exception as e:
            traceback.print_exc()
            GLib.idle_add(onExcept, e)

    thread = threading.Thread(target=run, args=[args])
    thread.start()


class RepeatJob:
    def __init__(self, f: callable, args: any, cb: callable, interval: int):
        """Generic job that runs asynchronously and then calls back with the result repeatedly after <interval> seconds

        Args:
            f (callable): Function to run asynchronously
            args (any): Arguments for f
            cb (callable): Callback, will be called with results from f
            interval (int): Seconds at which to repeat task
        """
        self.f = f
        self.args = args
        self.cb = cb
        self.stop_flag = threading.Event()

        GLib.timeout_add(interval * 1000, self.onTimeout)
        self.onTimeout()

    def onTimeout(self):
        if self.stop_flag.is_set():
            self.stop_flag.clear()
            return False  # Cancel timeout
        thread = threading.Thread(target=self.run, args=[self.args])
        thread.start()
        return True

    def run(self, args):
        ret = self.f(*args)
        GLib.idle_add(self.cb, ret)

    def stopTask(self):
        """Stop the repeated task, a running task will however not be killed."""
        self.stop_flag.set()
