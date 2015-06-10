#!/usr/bin/python2

import commands
from subprocess import Popen,PIPE,call,STDOUT
import os
import signal
import re
import gettext
import locale
from gi.repository import GObject, Gio, Polkit, Gtk, GLib
import sys
import getopt
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import time

APP = 'mintstick'
LOCALE_DIR = "/usr/share/linuxmint/locale"
locale.bindtextdomain(APP, LOCALE_DIR)
gettext.bindtextdomain(APP, LOCALE_DIR)
gettext.textdomain(APP)
_ = gettext.gettext

GObject.threads_init()

def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0)
        return res
    return wrapper

class MintStick:
    def __init__(self, iso_path=None, usb_path=None, filesystem=None, mode=None, debug=False):

        self.debug = debug

        def device_added_callback(device):
            #self.logger(_('Device %s was added' % (device))
            self.get_devices()

        def device_removed_callback(device):
            #self.logger(_('Device %s has been removed' % (device))
            self.get_devices()

        proxy = bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks")
        self.iface = dbus.Interface(proxy, "org.freedesktop.UDisks")

        self.iface.connect_to_signal('DeviceAdded', device_added_callback)
        self.iface.connect_to_signal('DeviceRemoved', device_removed_callback)

        # get glade tree
        self.gladefile = "/usr/share/mintstick/mintstick.ui"
        self.wTree = Gtk.Builder()

        self.process = None
        self.source_id = None

        self.wTree.set_translation_domain(APP)

        self.wTree.add_from_file(self.gladefile)

        self.ddpid = 0

        self.emergency_dialog = self.wTree.get_object("emergency_dialog")
        self.confirm_dialog =  self.wTree.get_object("confirm_dialog")
        self.success_dialog = self.wTree.get_object("success_dialog")

        if mode == "iso":
            self.mode = "normal"
            self.devicelist = self.wTree.get_object("device_combobox")
            self.label = self.wTree.get_object("to_label")
            self.expander = self.wTree.get_object("detail_expander")
            self.go_button = self.wTree.get_object("write_button")
            self.go_button.set_label(_("Write"))
            self.logview = self.wTree.get_object("detail_text")
            self.progress = self.wTree.get_object("progressbar")
            self.chooser = self.wTree.get_object("filechooserbutton")

            # Devicelist model
            self.devicemodel = Gtk.ListStore(str, str)

            # Renderer
            renderer_text = Gtk.CellRendererText()
            self.devicelist.pack_start(renderer_text, True)
            self.devicelist.add_attribute(renderer_text, "text", 1)

            self.get_devices()
            # get globally needed widgets
            self.window = self.wTree.get_object("main_dialog")
            self.window.connect("destroy", self.close)

            # set default file filter to *.img

            filt = Gtk.FileFilter()
            filt.add_pattern("*.img")
            filt.add_pattern("*.iso")
            self.chooser.set_filter(filt)

            # set callbacks

            dict = {
                    "on_cancel_button_clicked" : self.close,
                    "on_emergency_button_clicked" : self.emergency_ok,
                    "on_success_button_clicked" : self.success_ok,
                    "on_confirm_cancel_button_clicked" : self.confirm_cancel}
            self.wTree.connect_signals(dict)

            self.devicelist.connect("changed", self.device_selected)
            self.go_button.connect("clicked", self.do_write)
            self.chooser.connect("file-set", self.file_selected)

            if iso_path:
                if os.path.exists(iso_path):
                    self.chooser.set_filename(iso_path)
                    self.file_selected(self.chooser)

        if mode == "format":
            self.mode="format"
            self.devicelist = self.wTree.get_object("formatdevice_combobox")
            self.label = self.wTree.get_object("formatdevice_label")
            self.expander = self.wTree.get_object("formatdetail_expander")
            self.go_button = self.wTree.get_object("format_formatbutton")
            self.go_button.set_label(_("Format"))
            self.logview = self.wTree.get_object("format_detail_text")

            self.window = self.wTree.get_object("format_window")
            self.window.connect("destroy", self.close)

            self.format_progressbar = self.wTree.get_object("format_progressbar")
            self.filesystemlist = self.wTree.get_object("filesystem_combobox")
            # set callbacks
            dict = {
                    "on_cancel_button_clicked" : self.close,
                    "on_emergency_button_clicked" : self.emergency_ok,
                    "on_success_button_clicked" : self.success_ok,
                    "on_confirm_cancel_button_clicked" : self.confirm_cancel}
            self.wTree.connect_signals(dict)

            self.go_button.connect("clicked", self.do_format)
            self.filesystemlist.connect("changed", self.filesystem_selected)
            self.devicelist.connect("changed", self.device_selected)

            # Filesystemlist
            self.fsmodel = Gtk.ListStore(str, str)
            self.fsmodel.append(["fat32", "FAT32"])
            self.fsmodel.append(["ntfs", "NTFS"])
            self.fsmodel.append(["ext4", "EXT4"])
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
            if filesystem is not None:
                iter = model.get_iter_first()
                while iter is not None:
                    value = model.get_value(iter, 0)
                    if value == filesystem:
                        self.filesystemlist.set_active_iter(iter)
                    iter = model.iter_next(iter)

            self.filesystem_selected(self.filesystemlist)
            self.get_devices()

            if usb_path is not None:
                iter = self.devicemodel.get_iter_first()
                while iter is not None:
                    value = self.devicemodel.get_value(iter, 0)
                    if usb_path in value:
                        self.devicelist.set_active_iter(iter)
                    iter = self.devicemodel.iter_next(iter)

        self.window.show_all()
        if self.mode=="format":
            self.expander.hide()
        self.log = self.logview.get_buffer()

    def get_devices(self):
        devices = self.iface.get_dbus_method('EnumerateDevices')()
        self.go_button.set_sensitive(False)
        self.devicemodel.clear()
        dct = []
        self.dev = None
        # Building device list from UDisk
        for dev in devices:
            dev_obj = bus.get_object("org.freedesktop.UDisks", dev)
            dev = dbus.Interface(dev_obj, "org.freedesktop.DBus.Properties")
            if (str(dev.Get('', 'DriveConnectionInterface')) == 'usb') \
                and (str(dev.Get('', 'DeviceIsDrive')) == "1") \
                and (str(dev.Get('', 'DeviceSize')) != "0") \
                and (str(dev.Get('', 'DeviceIsOpticalDisc')) == "0"):
                    name = str(dev.Get('', 'DeviceFile'))
                    driveVendor = str(dev.Get('', 'DriveVendor'))
                    driveModel = str(dev.Get('', 'DriveModel'))
                    if driveVendor.strip() != "":
                        driveModel = "%s %s" % (driveVendor, driveModel)
                    name = ''.join([i for i in name if not i.isdigit()])
                    size = float(dev.Get('', 'DeviceSize'))
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

                    item = "%s (%s) - %s" % (driveModel, name, size)
                    if item not in dct:
                       dct.append(item)
                       self.devicemodel.append([name, item])
        self.devicelist.set_model(self.devicemodel)

    def device_selected(self, widget):
        iter = self.devicelist.get_active_iter()
        if iter is not None:
            self.dev = self.devicemodel.get_value(iter, 0)
            self.go_button.set_sensitive(True)

    def filesystem_selected(self, widget):
        iter = self.filesystemlist.get_active_iter()
        if iter is not None:
            self.filesystem = self.fsmodel.get_value(iter, 0)
            self.activate_devicelist()

    def file_selected(self, widget):
        self.activate_devicelist()

    def do_format(self, widget):
        if self.debug:
            print "DEBUG: Format %s as %s" % (self.dev, self.filesystem)
            return

        self.devicelist.set_sensitive(False)
        self.filesystemlist.set_sensitive(False)
        self.go_button.set_sensitive(False)

        label = self.wTree.get_object("volume_label_entry").get_text()

        if os.geteuid() > 0:
            self.raw_format(self.dev, self.filesystem, label)
        else:
            # We are root, display confirmation dialog
            resp = self.confirm_dialog.run()
            if resp == Gtk.ResponseType.OK:
                self.confirm_dialog.hide()
                self.raw_format(self.dev, self.filesystem, label)
            else:
                self.confirm_dialog.hide()
                self.set_format_sensitive()

    def check_format_job(self):
        self.process.poll()
        if self.process.returncode is None:
            self.format_progressbar.pulse()
            return True
        else:
            GObject.idle_add(self.format_job_done, self.process.returncode)
            self.process = None
            return False

    def raw_format(self, usb_path, fstype, label):
        if os.geteuid() > 0:
            launcher='pkexec'
            self.process = Popen([launcher,'/usr/bin/python2', '-u', '/usr/lib/mintstick/raw_format.py','-d',usb_path,'-f',fstype, '-l', label, '-u', str(os.geteuid()), '-g', str(os.getgid())], shell=False, stdout=PIPE,  preexec_fn=os.setsid)
        else:
            self.process = Popen(['/usr/bin/python2', '-u', '/usr/lib/mintstick/raw_format.py','-d',usb_path,'-f',fstype, '-l', label, '-u', str(os.geteuid()), '-g', str(os.getgid())], shell=False, stdout=PIPE,  preexec_fn=os.setsid)

        self.format_progressbar.show()
        self.format_progressbar.pulse()

        GObject.timeout_add(500, self.check_format_job)

    def format_job_done(self, rc):
        self.format_progressbar.set_fraction(1.0)
        if rc == 0:
            message = _('The USB stick was formatted successfully.')
            self.logger(message)
            self.success(_('The USB stick was formatted successfully.'))
            return False
        elif rc == 5:
            message = _("An error occured while creating a partition on %s.") % usb_path
        elif rc == 127:
            message = _('Authentication Error.')
        else:
            message = _('An error occurred.')
        self.logger(message)
        self.emergency(message)
        self.set_format_sensitive()
        return False

    def do_write(self, widget):
        if self.debug:
            print "DEBUG: Write %s to %s" % (self.chooser.get_filename(), self.dev)
            return

        self.go_button.set_sensitive(False)
        self.devicelist.set_sensitive(False)
        self.chooser.set_sensitive(False)
        source = self.chooser.get_filename()
        target = self.dev
        self.logger(_('Image:') + ' ' + source)
        self.logger(_('USB stick:')+ ' ' + self.dev)

        if os.geteuid() > 0:
            self.raw_write(source, target)
        else:
            # We are root, display confirmation dialog
            resp = self.confirm_dialog.run()
            if resp == Gtk.ResponseType.OK:
                self.confirm_dialog.hide()
                self.raw_write(source, target)
            else:
                self.confirm_dialog.hide()
                self.set_iso_sensitive()

    def set_progress_bar_fraction(self, size):
        self.progress.set_fraction(size)
        str_progress = "%3.0f%%" % (float(size)*100)
        self.progress.set_text(str_progress)
        self.window.set_title("%s - %s" % (str_progress, _("USB Image Writer")))

    def update_progress(self, fd, condition):
        if condition  is GLib.IO_IN:
            line = fd.readline()
            try:
                size = float(line.strip())
                progress = round(size * 100)
                if progress > self.write_progress:
                    self.write_progress = progress
                    GObject.idle_add(self.set_progress_bar_fraction, size)
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
            GObject.idle_add(self.write_job_done, self.process.returncode)
            self.process = None
            return False

    def raw_write(self, source, target):
        self.progress.set_sensitive(True)
        self.progress.set_text(_('Writing %(VAR_FILE)s to %(VAR_DEV)s') % {'VAR_FILE': source.split('/')[-1], 'VAR_DEV': self.dev})
        self.logger(_('Starting copy from %(VAR_SOURCE)s to %(VAR_TARGET)s') % {'VAR_SOURCE':source, 'VAR_TARGET':target})

        if os.geteuid() > 0:
            launcher='pkexec'
            self.process = Popen([launcher,'/usr/bin/python2', '-u', '/usr/lib/mintstick/raw_write.py','-s',source,'-t',target], shell=False, stdout=PIPE, preexec_fn=os.setsid)
        else:
            self.process = Popen(['/usr/bin/python2', '-u', '/usr/lib/mintstick/raw_write.py','-s',source,'-t',target], shell=False, stdout=PIPE, preexec_fn=os.setsid)

        self.write_progress = 0
        self.source_id = GLib.io_add_watch(self.process.stdout, GLib.IO_IN|GLib.IO_HUP, self.update_progress)
        GObject.timeout_add(500, self.check_write_job)

    def write_job_done(self, rc):
        if rc == 0:
            message = _('The image was successfully written.')
            self.set_progress_bar_fraction(1.0)
            self.logger(message)
            self.success(_('The image was successfully written.'))
            return False
        elif rc == 3:
            message = _('Not enough space on the USB stick.')
        elif rc == 4:
            message = _('An error occured while copying the image.')
        elif rc == 127:
            message = _('Authentication Error.')
        else:
            message = _('An error occurred.')
        self.logger(message)
        self.emergency(message)
        return False

    def success(self,message):
        label = self.wTree.get_object("label5")
        label.set_text(message)
        if self.mode == "normal":
            self.final_unsensitive()
        resp = self.success_dialog.run()
        if resp == Gtk.ResponseType.OK:
            self.success_dialog.hide()

    def emergency(self, message):
        if self.mode == "normal":
            self.final_unsensitive()
        label = self.wTree.get_object("label6")
        label.set_text(message)
        #self.expander.set_expanded(True)
        mark = self.log.create_mark("end", self.log.get_end_iter(), False)
        self.logview.scroll_to_mark(mark, 0.05, True, 0.0, 1.0)
        resp = self.emergency_dialog.run()
        if resp == Gtk.ResponseType.OK:
            self.emergency_dialog.hide()

    def final_unsensitive(self):
        self.chooser.set_sensitive(False)
        self.devicelist.set_sensitive(False)
        self.go_button.set_sensitive(False)
        self.progress = self.wTree.get_object("progressbar")
        self.progress.set_sensitive(False)
        self.window.set_title(_("USB Image Writer"))

    def close(self, widget):
        self.write_logfile()
        if self.process is not None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except:
                pass
            finally:
                Gtk.main_quit()
        else:
            Gtk.main_quit()

    def write_logfile(self):
        start = self.log.get_start_iter()
        end = self.log.get_end_iter()
        print self.log.get_text(start, end, False)

    def logger(self, text):
        self.log.insert_at_cursor(text+"\n")

    def activate_devicelist(self):
        self.devicelist.set_sensitive(True)
        self.expander.set_sensitive(True)
        self.label.set_sensitive(True)

    def confirm_cancel(self,widget):
        self.confirm_dialog.hide()
        if self.mode == "normal": self.set_iso_sensitive()
        if self.mode == "format": self.set_format_sensitive()

    def emergency_ok(self,widget):
        self.emergency_dialog.hide()
        if self.mode == "normal": self.set_iso_sensitive()
        if self.mode == "format":
            self.set_format_sensitive()
            self.go_button.set_sensitive(False)

    def success_ok(self,widget):
        self.success_dialog.hide()
        if self.mode == "normal":
            self.set_iso_sensitive()
        if self.mode == "format":
            self.set_format_sensitive()
            self.go_button.set_sensitive(False)

    def set_iso_sensitive(self):
        self.chooser.set_sensitive(True)
        self.devicelist.set_sensitive(True)
        self.go_button.set_sensitive(True)

    def set_format_sensitive(self):
        self.filesystemlist.set_sensitive(True)
        self.devicelist.set_sensitive(True)
        self.go_button.set_sensitive(True)

if __name__ == "__main__":

    usb_path=None
    iso_path=None
    filesystem=None
    mode=None

    def usage():
        print "Usage: mintstick [--debug] -m [format|iso]              : mode (format usb stick or burn iso image)"
        print "       mintstick [--debug] -m iso [-i|--iso] iso_path"
        print "       mintstick [--debug] -m format [-u|--usb] usb_device "
        print "                           [-f|--filesystem] filesystem"
        exit (0)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hm:i:u:f:", ["debug", "help", "mode=", "iso=","usb=","filesystem="])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)

    debug = False
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-i", "--iso"):
            iso_path = a
        elif o in ("-u", "--usb"):
            # hack. KDE Solid application gives partition name not device name. Need to remove extra digit from the string.
            # ie. /dev/sdj1 -> /dev/sdj
            usb_path = ''.join([i for i in a if not i.isdigit()])
        elif o in ("-f", "--filesystem"):
            filesystem = a
        elif o in ("-m", "--mode"):
            mode=a
        elif o in ("--debug"):
            debug = True

    argc = len(sys.argv)
    if argc > 8:
        print "Too many arguments"
        print "for help use --help"
        exit(2)

    # Mandatory argument
    if (mode is None) or ((mode != "format") and (mode != "iso")):
        usage()

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    MintStick(iso_path, usb_path, filesystem, mode, debug)

    #start the main loop
    #mainloop = GObject.MainLoop()
    #mainloop.run()
    Gtk.main()
