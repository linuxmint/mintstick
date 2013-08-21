#!/usr/bin/python


import commands
from subprocess import Popen,PIPE,call,STDOUT
import os
import signal
import re
import gettext
from gettext import gettext as _
import gtk
import gtk.glade      
import gobject
import sys
import getopt
import threading
import dbus
import gobject
from dbus.mainloop.glib import DBusGMainLoop


class MintStick:
    def __init__(self, iso_path=None, usb_path=None, filesystem=None, mode=None, debug=False):
               
        self.debug = debug

        def device_added_callback(device):
            #self.logger(_('Device %s was added' % (device))
            self.get_devices()

        def device_removed_callback(device):
            #self.logger(_('Device %s has been removed' % (device))  
            self.get_devices()
                
        proxy = bus.get_object("org.freedesktop.UDisks", 
                       "/org/freedesktop/UDisks")
        self.iface = dbus.Interface(proxy, "org.freedesktop.UDisks")
                
        self.iface.connect_to_signal('DeviceAdded', device_added_callback)
        self.iface.connect_to_signal('DeviceRemoved', device_removed_callback)
        
        APP="mintstick"
        DIR="/usr/share/linuxmint/locale"
        gettext.bindtextdomain(APP, DIR)
        gettext.textdomain(APP)
        gtk.glade.bindtextdomain(APP, DIR)
        gtk.glade.textdomain(APP)

        # get glade tree      
        self.gladefile = "/usr/share/mintstick/mintstick.glade"        
        self.wTree = gtk.glade.XML(self.gladefile)                   
        self.ddpid = 0    
        
        self.emergency_dialog = self.wTree.get_widget("emergency_dialog")  
        self.confirm_dialog =  self.wTree.get_widget("confirm_dialog")
        self.success_dialog = self.wTree.get_widget("success_dialog")
        
        
        if mode == "iso":
            self.mode = "normal"
            self.devicelist = self.wTree.get_widget("device_combobox")
            self.label = self.wTree.get_widget("to_label")
            self.expander = self.wTree.get_widget("detail_expander")
            self.go_button = self.wTree.get_widget("write_button")
            self.logview = self.wTree.get_widget("detail_text") 
            self.progress = self.wTree.get_widget("progressbar")
            self.chooser = self.wTree.get_widget("filechooserbutton")
            
            self.get_devices()
            # get globally needed widgets
            self.window = self.wTree.get_widget("main_dialog")

            # set default file filter to *.img
            
            filt = gtk.FileFilter()
            filt.add_pattern("*.img")
            filt.add_pattern("*.iso")
            self.chooser.set_filter(filt)

            # set callbacks
            dict = { "on_main_dialog_destroy" : self.close,
                    "on_cancel_button_clicked" : self.close,
                    "on_emergency_button_clicked" : self.emergency_ok,                    
                    "on_success_button_clicked" : self.success_ok,
                    "on_filechooserbutton_file_set" : self.file_selected,
                    "on_detail_expander_activate" : self.expander_control,
                    "on_device_combobox_changed" : self.device_selected,
                    "on_confirm_cancel_button_clicked" : self.confirm_cancel,
                    "on_write_button_clicked" : self.do_write}
            self.wTree.signal_autoconnect(dict)
        
            if iso_path:
                if os.path.exists(iso_path):                    
                    self.chooser.set_filename(iso_path)  
                    self.file_selected(self.chooser)                
                    
        if mode == "format":
            self.mode="format"
            self.devicelist = self.wTree.get_widget("formatdevice_combobox")
            self.label = self.wTree.get_widget("formatdevice_label")
            self.expander = self.wTree.get_widget("formatdetail_expander")
            self.go_button = self.wTree.get_widget("format_formatbutton")
            self.logview = self.wTree.get_widget("format_detail_text")  
            
            self.window = self.wTree.get_widget("format_window")   
            self.spinner = self.wTree.get_widget("format_spinner")
            self.filesystemlist = self.wTree.get_widget("filesystem_combobox")
            # set callbacks
            dict = { "on_format_window_destroy" : self.close,
                    "on_cancel_button_clicked" : self.close,
                    "on_emergency_button_clicked" : self.emergency_ok,                    
                    "on_success_button_clicked" : self.success_ok,
                    "on_filesystem_combobox_changed" : self.filesystem_selected,
                    "on_formatdetail_expander_activate" : self.expander_control,
                    "on_formatdevice_combobox_changed" : self.device_selected,                    
                    "on_confirm_cancel_button_clicked" : self.confirm_cancel,
                    "on_format_formatbutton_clicked" : self.do_format}
            self.wTree.signal_autoconnect(dict)

            # Devicelist model
            self.devicemodel = gtk.ListStore(str, str)

            # Renderer
            renderer_text = gtk.CellRendererText()
            self.devicelist.pack_start(renderer_text, True)           
            self.devicelist.add_attribute(renderer_text, "text", 1)                 
            
            # Filesystemlist
            model = gtk.ListStore(str, str)            
            model.append(["fat32", "FAT32"])
            model.append(["ntfs", "NTFS"])
            model.append(["ext4", "EXT4"])
            self.filesystemlist.set_model(model)
            
            # Renderer
            renderer_text = gtk.CellRendererText()
            self.filesystemlist.pack_start(renderer_text, True)           
            self.filesystemlist.add_attribute(renderer_text, "text", 1)
            
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
            self.spinner.hide()
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
                and (str(dev.Get('', 'DeviceIsRemovable')) == "1") \
                and (str(dev.Get('', 'DeviceSize')) != "0") \
                and (str(dev.Get('', 'DeviceIsOpticalDisc')) == "0"):
                    name = str(dev.Get('', 'DeviceFile'))
                    drivemodel = str(dev.Get('', 'DriveModel'))
                    name = ''.join([i for i in name if not i.isdigit()])                        
                    size = float(dev.Get('', 'DeviceSize')) / 1000000000
                    if size >= 1:                        
                        size = "%.0fGB" % round(size)
                    else:
                        size = "%.0fMB" % round(size * 1000)

                    item = "%s (%s) - %s" % (drivemodel, name, size)
                    if item not in dct:
                       dct.append(item)
                       self.devicemodel.append([name, item])
        self.devicelist.set_model(self.devicemodel)                     
                
    def device_selected(self, widget):        
        if self.devicelist.get_active_text() is not None:
            self.dev = self.devicelist.get_active_text()
            self.go_button.set_sensitive(True)
            
    def filesystem_selected(self, widget):
        self.filesystem = self.filesystemlist.get_active_text()              
        self.activate_devicelist()       
        
    def file_selected(self, widget):
        self.img_name = self.chooser.get_filename()
        self.activate_devicelist()        
    
    def do_format(self, widget):
        if self.debug:
            print "DEBUG: Format %s as %s" % (self.dev, self.filesystem)
            return

        self.devicelist.set_sensitive(False)
        self.filesystemlist.set_sensitive(False)
        self.go_button.set_sensitive(False)          

        label = self.wTree.get_widget("volume_label_entry").get_text()

        if os.geteuid() > 0:
            self.raw_format(self.dev, self.filesystem, label)
        else:
                # We are root, display confirmation dialog
                resp = self.confirm_dialog.run()
                if resp == gtk.RESPONSE_OK:                    
                    self.confirm_dialog.hide()
                    while gtk.events_pending():
                        gtk.main_iteration(True)
                    self.raw_format(self.dev, self.filesystem, label)
                else:
                    self.confirm_dialog.hide()
                    self.set_format_sensitive()
                    
    def raw_format(self, usb_path, fstype, label):
        #self.logger(_('Going to format ') + usb_path+ _(' with ')+ fstype + _(' filesystem') )
        def thread_run():
                        
            self.spinner.show()
            self.spinner.start()
        
            if os.geteuid() > 0:
                launcher='pkexec'
                output = Popen([launcher,'/usr/bin/python', '/usr/lib/mintstick/raw_format.py','-d',usb_path,'-f',fstype, '-l', label], shell=False, stdout=PIPE)   
            else:
                output = Popen(['/usr/bin/python', '/usr/lib/mintstick/raw_format.py','-d',usb_path,'-f',fstype, '-l', label], shell=False, stdout=PIPE)                
            output.communicate()[0]
            self.rc = output.returncode              
        t = threading.Thread(group=None,target=thread_run)
        t.start()
        while t.isAlive():
            while gtk.events_pending():
                gtk.main_iteration(True)             
        self.spinner.stop()
        self.spinner.hide()        
        if self.rc == 0:
            message = _('The USB stick was formatted successfully.')
            self.logger(message)
            self.success(_('The USB stick was formatted successfully.'))
            return True
        elif self.rc == 5:
            message = _("Can't create partition on %s.") % usb_path
        elif self.rc == 127:
            message = _('Authentication Error.')      
        else:
            message = _('An error occurred.') 
        self.logger(message)
        self.emergency(message)
        self.set_format_sensitive()
        
        return False
    
    def do_write(self, widget):
        if self.debug:
            print "DEBUG: Write %s to %s" % (source, self.dev)
            return

        self.go_button.set_sensitive(False)
        self.devicelist.set_sensitive(False)
        self.chooser.set_sensitive(False)
        source = self.img_name
        target = self.dev
        self.logger(_('Image:') + ' ' + source)
        self.logger(_('Target Device:')+ ' ' + self.dev)
        
        if os.geteuid() > 0:
	      self.raw_write(source, target)
        else:
            # We are root, display confirmation dialog
            resp = self.confirm_dialog.run()
            if resp == gtk.RESPONSE_OK:
                self.confirm_dialog.hide()
                while gtk.events_pending():
                    gtk.main_iteration(True)
                self.raw_write(source, target)
            else:
                self.confirm_dialog.hide()
                self.set_iso_sensitive()
 

    def raw_write(self, source, target):   
        
        self.progress.set_sensitive(True)
        self.progress.set_text(_('Writing %(A)s to %(B)s') % {'A': source.split('/')[-1], 'B': self.dev})
        self.logger(_('Starting copy from %(A)s to %(B)s') % {'A':source, 'B':target})
        def thread_run():           
            # Add launcher string, only when not root
            launcher = ''
            size=''
            flag = True

            if os.geteuid() > 0:
                launcher='pkexec'
                output = Popen([launcher,'/usr/bin/python', '/usr/lib/mintstick/raw_write.py','-s',source,'-t',target], shell=False, stdout=PIPE)
            else:
                output = Popen(['/usr/bin/python', '/usr/lib/mintstick/raw_write.py','-s',source,'-t',target], shell=False, stdout=PIPE)                    
            while flag == True:
                try:                
                    size = float(output.stdout.readline().strip())                    
                    flag = True
                except:
                    flag = False
                if flag:
                    self.progress.set_fraction(size)
                    self.progress.set_text("%3.0f%%" % (float(size)*100))            
            output.communicate()[0]
            self.rc = output.returncode            
            
        t = threading.Thread(group=None,target=thread_run)
        t.start()
        while t.isAlive():           
            while gtk.events_pending():
                gtk.main_iteration(True)     
        
        # Process return code
        if  self.rc == 0:
            message = _('The image was successfully written.')
            self.logger(message)            
            self.success(_('The image was successfully written.'))
            return True
        elif self.rc == 3:
            message = _('Not enough space on the device.')
        elif self.rc == 4:
            message = _('An error occured while copying the image.')
        elif self.rc == 127:
            message = _('Authentication Error.')
        else:
            message = _('An error occurred.') 
        self.logger(message)
        self.emergency(message)
        return False

           
    def success(self,message):
        label = self.wTree.get_widget("label5")
        label.set_text(message)
        if self.mode == "normal":
            self.final_unsensitive()
        resp = self.success_dialog.run()
        if resp == gtk.RESPONSE_OK:
            self.success_dialog.hide()

    def emergency(self, message):
        if self.mode == "normal":
            self.final_unsensitive()    
        label = self.wTree.get_widget("label6")        
        label.set_text(message)
        #self.expander.set_expanded(True)
        mark = self.log.create_mark("end", self.log.get_end_iter(), False)
        self.logview.scroll_to_mark(mark, 0.05, True, 0.0, 1.0)
        resp = self.emergency_dialog.run()
        if resp == gtk.RESPONSE_OK:
            self.emergency_dialog.hide()

    def final_unsensitive(self):
        self.chooser.set_sensitive(False)
        self.devicelist.set_sensitive(False)        
        self.go_button.set_sensitive(False)
        self.progress = self.wTree.get_widget("progressbar")
        self.progress.set_sensitive(False)

    def close(self, widget):
        self.write_logfile()
        if self.ddpid > 0:
            try:
                os.killpg(os.getpgid(self.ddpid), signal.SIGKILL)
            except:
                mainloop.quit()
        else:
            mainloop.quit()

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
        if self.mode == "normal": self.set_iso_sensitive()
        if self.mode == "format": 
            self.set_format_sensitive()
            self.go_button.set_sensitive(False)
        
    def set_iso_sensitive(self):
        self.chooser.set_sensitive(True)
        self.devicelist.set_sensitive(True)        
        self.go_button.set_sensitive(True)
        self.progress.set_text("")
        self.progress.set_fraction(0.0)
        
    def set_format_sensitive(self):
        self.filesystemlist.set_sensitive(True)
        self.devicelist.set_sensitive(True)        
        self.go_button.set_sensitive(True)        
    
    def expander_control(self, widget):
        # this is darn ugly but still better than the UI behavior of
        # the unexpanded expander which doesnt reset the window size
        if widget.get_expanded():
            gobject.timeout_add(130, lambda: self.window.reshow_with_initial_size())

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
    mainloop = gobject.MainLoop()
    mainloop.run()
