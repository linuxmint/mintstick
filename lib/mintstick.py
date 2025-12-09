#!/usr/bin/python3

from unidecode import unidecode
from subprocess import Popen, PIPE
import dbus
import getopt
import gettext
import gi
import locale
import os
import signal
import subprocess
import sys

gi.require_version('Polkit', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('UDisks', '2.0')
gi.require_version('XApp', '1.0')

from gi.repository import Polkit, Gtk, GLib, UDisks, XApp

try:
    gi.require_version('Unity', '7.0')
    from gi.repository import Unity
    Using_Unity = True
except Exception:
    Using_Unity = False

if Using_Unity:
    launcher = Unity.LauncherEntry.get_for_desktop_id("mintstick.desktop")

APP = 'mintstick'
LOCALE_DIR = "/usr/share/linuxmint/locale"
locale.bindtextdomain(APP, LOCALE_DIR)
gettext.bindtextdomain(APP, LOCALE_DIR)
gettext.textdomain(APP)
_ = gettext.gettext

# https://technet.microsoft.com/en-us/library/bb490925.aspx
FORBIDDEN_CHARS = ["*", "?", "/", "\\", "|", ".", ",", ";", ":", "+", "=", "[", "]", "<", ">", "\""]

RELEVANT_UDISK_PROPERTIES = ['connection-bus', 'ejectable', 'id', \
'media-available', 'media-compatibility', 'media-removable', \
'model', 'vendor', 'optical', 'removable', 'size']

# noinspection PyUnusedLocal
class MintStick:
    def __init__(self, iso_path_arg=None, usb_path_arg=None, filesystem_arg=None, mode_arg=None, debug_arg=False):

        self.debug = debug_arg
        self.filesystem = filesystem_arg

        def devices_changed_callback(client):
            self.get_devices()

        self.udisks_client = UDisks.Client.new_sync()
        self.udisk_listener_id = self.udisks_client.connect("changed", devices_changed_callback)

        self.wTree = Gtk.Builder()
        self.wTree.set_translation_domain(APP)
        self.wTree.add_from_file("/usr/share/mintstick/mintstick.ui")

        self.process = None
        self.source_id = None
        self.dev = None
        self.write_progress = None

        if mode_arg == "iso":
            self.mode = "normal"
            self.devicelist = self.wTree.get_object("device_combobox")
            self.go_button = self.wTree.get_object("write_button")
            self.verify_button = self.wTree.get_object("verify_button")
            self.progressbar = self.wTree.get_object("progressbar")
            self.chooser = self.wTree.get_object("filechooserbutton")

            # Making file chooser accessible for users with screen reader
            label = self.wTree.get_object("label_write_image")
            button = self.chooser.get_children()[0]
            label.set_mnemonic_widget(button)

            # Devicelist model
            self.devicemodel = Gtk.ListStore(str, str)

            # Renderer
            renderer_text = Gtk.CellRendererText()
            self.devicelist.pack_start(renderer_text, True)
            self.devicelist.add_attribute(renderer_text, "text", 1)

            self.get_devices()
            # get globally needed widgets
            self.window = self.wTree.get_object("main_window")
            self.window.connect("destroy", self.close)

            # set default file filter to *.iso/*.img
            filt = Gtk.FileFilter()
            filt.add_pattern("*.[iI][mM][gG]")
            filt.add_pattern("*.[iI][sS][oO]")
            self.chooser.set_filter(filt)

            self.devicelist.connect("changed", self.device_selected)
            self.go_button.connect("clicked", self.do_write)
            self.verify_button.connect("clicked", self.verify)
            self.chooser.connect("file-set", self.file_selected)

            if iso_path_arg:
                if os.path.exists(iso_path_arg):
                    self.chooser.set_filename(iso_path_arg)
                    self.file_selected(self.chooser)
                    self.verify_button.set_sensitive(True)

        if mode_arg == "format":
            self.mode = "format"
            self.devicelist = self.wTree.get_object("formatdevice_combobox")
            self.go_button = self.wTree.get_object("format_formatbutton")
            self.label_entry = self.wTree.get_object("volume_label_entry")
            try:
                self.label_entry.set_text(unidecode(self.label_entry.get_text()))
            except:
                self.label_entry.set_text("USB STICK")
            self.label_entry_changed_id = self.label_entry.connect("changed", self.on_label_entry_text_changed)

            self.window = self.wTree.get_object("format_window")
            self.window.connect("destroy", self.close)

            self.progressbar = self.wTree.get_object("format_progressbar")
            self.filesystemlist = self.wTree.get_object("filesystem_combobox")

            self.go_button.connect("clicked", self.do_format)
            self.filesystemlist.connect("changed", self.filesystem_selected)
            self.devicelist.connect("changed", self.device_selected)

            self.label_entry.connect("changed", lambda *_: self.update_format_button())
            self.filesystemlist.connect("changed", lambda *_: self.update_format_button())
            self.devicelist.connect("changed", lambda *_: self.update_format_button())

            # Filesystemlist
            self.fsmodel = Gtk.ListStore(str, str, int, bool, bool)
            #                     id       label    max-length force-upper-case   force-alpha-numeric
            self.fsmodel.append(["fat32", "FAT32", 11, True, True])
            self.fsmodel.append(["exfat", "exFAT", 15, False, False])
            self.fsmodel.append(["ntfs", "NTFS", 32, False, False])
            self.fsmodel.append(["ext4", "EXT4", 16, False, False])
            self.filesystemlist.set_model(self.fsmodel)

            # Renderer
            renderer_text = Gtk.CellRendererText()
            self.filesystemlist.pack_start(renderer_text, True)
            self.filesystemlist.add_attribute(renderer_text, "text", 1)

            # Devicelist model
            self.devicemodel = Gtk.ListStore(str, str)

            # Renderer
            renderer_text = Gtk.CellRendererText()
            self.devicelist.pack_start(renderer_text, True)
            self.devicelist.add_attribute(renderer_text, "text", 1)

            self.filesystemlist.set_sensitive(True)
            # Default's to fat32
            self.filesystemlist.set_active(0)
            if filesystem_arg is not None:
                fs_iter = self.fsmodel.get_iter_first()
                while fs_iter is not None:
                    value = self.fsmodel.get_value(fs_iter, 0)
                    if value == filesystem_arg:
                        self.filesystemlist.set_active_iter(fs_iter)
                    fs_iter = self.fsmodel.iter_next(fs_iter)

            self.get_devices()
            self.select_device(usb_path_arg)

        self.window.show()

    def select_device(self, usb_path=None):
        if usb_path is not None:
            device_iter = self.devicemodel.get_iter_first()
            while device_iter is not None:
                value = self.devicemodel.get_value(device_iter, 0)
                if usb_path in value:
                    self.devicelist.set_active_iter(device_iter)
                    return
                device_iter = self.devicemodel.iter_next(device_iter)
            return

        device_iter = self.devicemodel.get_iter_first()
        if device_iter is not None:
            self.devicelist.set_active_iter(device_iter)

    def verify(self, button):
        subprocess.Popen(["mint-iso-verify", self.chooser.get_filename()])

    def print_drive(self, drive):
        # print drive info to stdout
        # this is done for debugging purposes
        try:
            for prop in drive.list_properties():
                name = prop.name
                if name in RELEVANT_UDISK_PROPERTIES:
                    print(f"    {prop.name}: {drive.get_property(prop.name)}")
            print()
        except Exception as e:
            print(e)

    def get_devices(self):
        self.go_button.set_sensitive(False)
        self.devicemodel.clear()
        detected_drives = []
        self.dev = None

        manager = self.udisks_client.get_object_manager()

        for obj in manager.get_objects():
            if obj is not None:
                block = obj.get_block()
                if block is not None:
                    drive = self.udisks_client.get_drive_for_block(block)
                    if drive is not None:
                        drive_id = drive.get_property('id')
                        if drive_id in detected_drives:
                            continue
                        self.print_drive(drive)
                        is_usb = str(drive.get_property('connection-bus')) in ['usb', 'cpio', 'sdio']
                        size = int(drive.get_property('size'))
                        optical = bool(drive.get_property('optical'))
                        removable = bool(drive.get_property('removable'))

                        if is_usb and size > 0 and removable and not optical:
                            name = block.get_property('device')
                            name = ''.join([i for i in name if not i.isdigit()])

                            drive_vendor = str(drive.get_property('vendor'))
                            drive_model = str(drive.get_property('model'))

                            if drive_vendor.strip() != "":
                                drive_model = "%s %s" % (drive_vendor, drive_model)

                            if size >= 1000000000000:
                                size = "%.0fTB" % round(size / 1000000000000)
                            elif size >= 1000000000:
                                size = "%.0fGB" % round(size / 1000000000)
                            elif size >= 1000000:
                                size = "%.0fMB" % round(size / 1000000)
                            elif size >= 1000:
                                size = "%.0fkB" % round(size / 1000)
                            else:
                                size = "%.0fB" % round(size)

                            item = "%s (%s) - %s" % (drive_model, name, size)

                            detected_drives.append(drive_id)
                            self.devicemodel.append([name, item])

        self.devicelist.set_model(self.devicemodel)

    def device_selected(self, widget):
        iterator = self.devicelist.get_active_iter()
        if iterator is not None:
            self.dev = self.devicemodel.get_value(iterator, 0)
            self.go_button.set_sensitive(True)

    def filesystem_selected(self, widget):
        fs_iter = self.filesystemlist.get_active_iter()
        if fs_iter is not None:
            self.filesystem = self.fsmodel.get_value(fs_iter, 0)
            self.activate_devicelist()

            self.label_entry.set_max_length(self.fsmodel.get_value(fs_iter, 2))
            self.on_label_entry_text_changed(self, self.label_entry)

    def file_selected(self, widget):
        self.activate_devicelist()
        filename = self.chooser.get_filename()
        if filename is not None and os.path.exists(filename):
            self.verify_button.set_sensitive(True)
        else:
            self.verify_button.set_sensitive(False)

    def fix_label_entry_text(self, should_block_handler):
        if should_block_handler:
            self.label_entry.handler_block(self.label_entry_changed_id)

        active_iter = self.filesystemlist.get_active_iter()
        text = self.label_entry.get_text()

        if self.fsmodel.get_value(active_iter, 3):
            text = text.upper()

        if self.fsmodel.get_value(active_iter, 4):
            for char in FORBIDDEN_CHARS:
                text = text.replace(char, "")

        try:
            text = unidecode(text)
        except Exception as e:
            print(f"Exception in sanitizing the label {text}")
            print(str(e))
            text = "USB STICK"

        self.label_entry.set_text(text)

        if should_block_handler:
            self.label_entry.handler_unblock(self.label_entry_changed_id)

    def on_label_entry_text_changed(self, widget, data=None):
        self.fix_label_entry_text(True)

    def update_format_button(self):
        has_valid_device = self.devicelist.get_active_iter() is not None
        has_valid_fs = self.filesystemlist.get_active_iter() is not None
        is_enough_length = self.label_entry.get_buffer().get_length() > 0

        if has_valid_device and has_valid_fs and is_enough_length:
            self.go_button.set_sensitive(True)
        else:
            self.go_button.set_sensitive(False)

    def has_polkit_rule_format(self):
        return self.check_polkit_permission('com.linuxmint.mintstick-format')

    def has_polkit_rule_write(self):
        return self.check_polkit_permission('com.linuxmint.mintstick-write')

    def check_polkit_permission(self, action_id):
        try:
            bus = dbus.SystemBus()
            polkit = bus.get_object('org.freedesktop.PolicyKit1',
                                '/org/freedesktop/PolicyKit1/Authority')
            authority = dbus.Interface(polkit, 'org.freedesktop.PolicyKit1.Authority')

            subject = ('unix-process', {
                'pid': dbus.UInt32(os.getpid()),
                'start-time': dbus.UInt64(0)
            })

            granted, _, _ = authority.CheckAuthorization(
                subject,
                action_id,
                {},
                0,
                ''
            )
            return granted
        except:
            return False

    def confirm_action(self, title, question):
        dialog = Gtk.MessageDialog(
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            message_format=f"{title}\n\n{question}"
        )

        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.YES


    def do_format(self, widget):
        if self.has_polkit_rule_format():
            if not self.confirm_action(
                "Confirm formatting",
                "Do you really want to format the device?"
            ):
                return
        if self.debug:
            print("DEBUG: Format %s as %s" % (self.dev, self.filesystem))
            return
        self.udisks_client.handler_block(self.udisk_listener_id)
        self.devicelist.set_sensitive(False)
        self.filesystemlist.set_sensitive(False)
        self.go_button.set_sensitive(False)
        self.label_entry.set_sensitive(False)
        label = self.label_entry.get_text()
        self.raw_format(self.dev, self.filesystem, label)


    def check_format_job(self):
        self.process.poll()
        if self.process.returncode is None:
            self.pulse_progress()
            return True
        else:
            GLib.idle_add(self.format_job_done, self.process.returncode)
            self.process = None
            return False

    def raw_format(self, usb_path_arg, fstype, label):
        if os.geteuid() > 0:
            polkit_exec = 'pkexec'
            self.process = Popen(
                [polkit_exec, '/usr/bin/mint-stick-format', '-d', usb_path_arg,
                 '-f', fstype, '-u', str(os.geteuid()), '-g', str(os.getgid()), '--', label],
                shell=False, stdout=PIPE, preexec_fn=os.setsid)
        else:
            self.process = Popen(
                ['/usr/bin/mint-stick-format', '-d', usb_path_arg,
                 '-f', fstype, '-u', str(os.geteuid()), '-g', str(os.getgid()), "--", label],
                shell=False, stdout=PIPE, preexec_fn=os.setsid)

        self.progressbar.show()
        self.pulse_progress()

        GLib.timeout_add(500, self.check_format_job)

    def format_job_done(self, rc):
        if rc == 0:
            self.show_format_result("dialog-information", _('The USB stick was formatted successfully.'))
            return False
        elif rc == 5:
            message = _("An error occured while creating a partition on %s.") % usb_path
        elif rc == 127:
            message = _('Authentication Error.')
        elif rc == 126:  # Cancelled by the user.
            self.clear_progress()
            message = None
        else:
            message = _('An error occurred.')

        if message is not None:
            self.show_format_result("dialog-error", message)
        self.set_format_sensitive(False)
        self.udisks_client.handler_unblock(self.udisk_listener_id)
        return False

    def do_write(self, widget):
        if self.has_polkit_rule_write():
            if not self.confirm_action(
                "Confirm ISO-writing",
                "Do you really want to write the ISO to the device?"
            ):
                return
        if self.debug:
            print("DEBUG: Write %s to %s" % (self.chooser.get_filename(), self.dev))
            return

        source = self.chooser.get_filename()
        target = self.dev
        filename = os.path.basename(source).lower()
        # Don't write Windows ISO
        for keyword in ["windows", "win7", "win8", "win10", "winxp"]:
            if keyword in filename:
                self.wTree.get_object("stack").set_visible_child_name("windows_page")
                return

        self.udisks_client.handler_block(self.udisk_listener_id)
        self.go_button.set_sensitive(False)
        self.verify_button.set_sensitive(False)
        self.devicelist.set_sensitive(False)
        self.chooser.set_sensitive(False)
        self.progressbar.show()
        self.raw_write(source, target)

    def set_progress(self, size):
        self.progressbar.set_fraction(size)
        str_progress = "%3.0f%%" % (float(size) * 100)
        int_progress = int(float(size) * 100)
        self.progressbar.set_text(str_progress)
        XApp.set_window_progress_pulse(self.window, False)
        XApp.set_window_progress(self.window, int_progress)

    def clear_progress(self):
        self.progressbar.hide()
        XApp.set_window_progress_pulse(self.window, False)

    def pulse_progress(self):
        self.progressbar.pulse()
        XApp.set_window_progress_pulse(self.window, True)

    def update_progress(self, fd, condition):
        if Using_Unity:
            launcher.set_property("progress_visible", True)
        if condition is GLib.IO_IN:
            line = fd.readline()
            # noinspection PyBroadException
            try:
                size = float(line.strip())
                progress = round(size * 100)
                if progress > self.write_progress:
                    self.write_progress = progress
                    GLib.idle_add(self.set_progress, size)
                    if Using_Unity:
                        launcher.set_property("progress", size)
            except:
                pass
            return True
        else:
            GLib.source_remove(self.source_id)
            return False

    def check_write_job(self):
        self.process.poll()
        if self.process.returncode is None:
            return True
        else:
            GLib.idle_add(self.write_job_done, self.process.returncode)
            self.process = None
            return False

    def raw_write(self, source, target):
        if os.geteuid() > 0:
            polkit_exec = 'pkexec'
            self.process = Popen(
                [polkit_exec, '/usr/bin/mint-stick-write', '-s', source, '-t', target],
                shell=False, stdout=PIPE, preexec_fn=os.setsid)
        else:
            self.process = Popen(
                ['/usr/bin/mint-stick-write', '-s', source, '-t', target],
                shell=False, stdout=PIPE, preexec_fn=os.setsid)

        self.write_progress = 0
        self.source_id = GLib.io_add_watch(self.process.stdout, GLib.IO_IN | GLib.IO_HUP, self.update_progress)
        GLib.timeout_add(500, self.check_write_job)

    def write_job_done(self, rc):
        self.udisks_client.handler_unblock(self.udisk_listener_id)
        if rc == 0:
            if Using_Unity:
                launcher.set_property("progress_visible", False)
                launcher.set_property("urgent", True)
            self.set_progress(1.0)
            self.show_result("dialog-information", _('The image was successfully written.'))
            return False
        elif rc == 3:
            message = _('Not enough space on the USB stick.')
        elif rc == 4:
            message = _('An error occured while copying the image.')
        elif rc == 127:
            message = _('Authentication Error.')
        elif rc == 126:  # Cancelled by the user.
            self.clear_progress()
            self.set_iso_sensitive()
            message = None
        else:
            message = _('An error occurred.')
        if message is not None:
            self.show_format_result("dialog-error", message)

        return False

    def show_format_result(self, icon_name, text):
        self.wTree.get_object("format_stack").set_visible_child_name("format_result_page")
        self.wTree.get_object("format_result_image").set_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        self.wTree.get_object("format_result_label").set_text(text)

    def show_result(self, icon_name, text):
        self.wTree.get_object("stack").set_visible_child_name("result_page")
        self.wTree.get_object("result_image").set_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        self.wTree.get_object("result_label").set_text(text)

    def close(self, widget):
        if self.process is not None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except:
                pass
            finally:
                Gtk.main_quit()
        else:
            Gtk.main_quit()

    def activate_devicelist(self):
        self.devicelist.set_sensitive(True)

    def set_iso_sensitive(self):
        self.chooser.set_sensitive(True)
        self.devicelist.set_sensitive(True)
        self.go_button.set_sensitive(True)
        self.verify_button.set_sensitive(True)

    def set_format_sensitive(self, reset=True):
        if reset:
            self.get_devices()
        self.filesystemlist.set_sensitive(True)
        self.devicelist.set_sensitive(True)
        self.label_entry.set_sensitive(True)
        self.go_button.set_sensitive(True)

if __name__ == "__main__":
    usb_path = None
    iso_path = None
    filesystem = None
    mode = None

    def usage():
        print("Usage: mintstick [--debug] -m [format|iso]              : mode (format usb stick or burn iso image)")
        print("       mintstick [--debug] -m iso [-i|--iso] iso_path")
        print("       mintstick [--debug] -m format [-u|--usb] usb_device ")
        print("                           [-f|--filesystem] filesystem")
        exit(0)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hm:i:u:f:", ["debug", "help", "mode=", "iso=", "usb=", "filesystem="])
    except getopt.error as msg:
        print(msg)
        print("for help use --help")
        sys.exit(2)

    debug = False
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-i", "--iso"):
            iso_path = a
        elif o in ("-u", "--usb"):
            # hack. KDE Solid application gives partition name not device name.
            # Need to remove extra digit from the string.
            # ie. /dev/sdj1 -> /dev/sdj
            usb_path = ''.join([i for i in a if not i.isdigit()])
        elif o in ("-f", "--filesystem"):
            filesystem = a
        elif o in ("-m", "--mode"):
            mode = a
        elif o == "--debug":
            debug = True

    argc = len(sys.argv)
    if argc > 8:
        print("Too many arguments")
        print("for help use --help")
        exit(2)

    # Mandatory argument
    if (mode is None) or ((mode != "format") and (mode != "iso")):
        usage()

    MintStick(iso_path, usb_path, filesystem, mode, debug)
    Gtk.main()
