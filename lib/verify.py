#!/usr/bin/python3

import gettext
import gi
import gnupg
import locale
import os
import requests
import subprocess
import sys
import threading

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

APP = 'mintstick'
LOCALE_DIR = "/usr/share/linuxmint/locale"
locale.bindtextdomain(APP, LOCALE_DIR)
gettext.bindtextdomain(APP, LOCALE_DIR)
gettext.textdomain(APP)
_ = gettext.gettext

TRUSTED_SIGNATURES = {}
TRUSTED_SIGNATURES["27DEB15644C6B3CF3BD7D291300F846BA25BAE09"] = "Linux Mint"
TRUSTED_SIGNATURES["C5986B4F1257FFA86632CBA746181433FBB75451"] = "Ubuntu"
TRUSTED_SIGNATURES["843938DF228D22F7B3742BC0D94AA3F0EFE21092"] = "Ubuntu"
TRUSTED_SIGNATURES["10460DAD76165AD81FBC0CE9988021A964E6EA7D"] = "Debian"
TRUSTED_SIGNATURES["DF9B9C49EAA9298432589D76DA87E80D6294BE9B"] = "Debian"
TRUSTED_SIGNATURES["F41D30342F3546695F65C66942468F4009EA8AC3"] = "Debian"

MINT_MIRROR = "https://ftp.heanet.ie/mirrors/linuxmint.com/"

CACHE_DIR = os.path.expanduser("~/.cache/mintstick")
subprocess.call(["mkdir", "-p", CACHE_DIR])
PATH_SUMS = os.path.join(CACHE_DIR, "sha256sum.txt")
PATH_GPG = os.path.join(CACHE_DIR, "sha256sum.txt.gpg")

# Used as a decorator to run things in the background
def async_function(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

# Used as a decorator to run things in the main loop, from another thread
def idle_function(func):
    def wrapper(*args):
        GLib.idle_add(func, *args)
    return wrapper

# Converts bytes to readable size
def convert_bytes(num):
    for x in [_('bytes'), _('KB'), _('MB'), _('GB'), _('TB')]:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

class App():

    def __init__(self, iso_path_arg=None):
        self.gpg = gnupg.GPG()
        self.sha256sum = None # the sum of the ISO
        self.path = None # path of the ISO
        self.filename = None # filename of the ISO
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(APP)
        self.builder.add_from_file("/usr/share/mintstick/verify.ui")
        self.window = self.builder.get_object("main_window")
        self.window.connect("destroy", self.quit)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.show()
        self.filechooser = self.builder.get_object("filechooser")
        if iso_path_arg != None and os.path.isfile(iso_path_arg):
            self.filechooser.set_filename(iso_path_arg)
            self.file_selected()

        self.filechooser.connect("file-set", self.file_selected)
        self.builder.get_object("verify_url_button").connect("clicked", self.verify_url)
        self.builder.get_object("verify_files_button").connect("clicked", self.verify_files)
        self.builder.get_object("verify_checksum_button").connect("clicked", self.verify_checksum)
        self.builder.get_object("back_button").connect("clicked", self.go_back)
        self.builder.get_object("stack_checksum").connect("notify::visible-child-name", self.update_verify_button)

        # filechooser filters
        file_filter = Gtk.FileFilter()
        file_filter.set_name(_("ISO images"))
        file_filter.add_mime_type("application/x-cd-image")
        self.filechooser.add_filter(file_filter)
        file_filter = Gtk.FileFilter()
        file_filter.set_name(_("Checksum files"))
        file_filter.add_mime_type("text/plain")
        self.builder.get_object("filechooser_sums").add_filter(file_filter)
        file_filter = Gtk.FileFilter()
        file_filter.set_name(_("GPG signatures"))
        file_filter.add_mime_type("application/pgp-encrypted")
        file_filter.add_mime_type("application/pgp-signature")
        file_filter.add_mime_type("application/pgp-keys")
        self.builder.get_object("filechooser_gpg").add_filter(file_filter)


    def file_selected(self, widget=None):
        self.path = None
        self.filename = None
        self.sha256sum = None
        path = self.filechooser.get_filename()
        self.builder.get_object("size_label").set_text(_("Calculating..."))
        self.builder.get_object("volume_label").set_text(_("Calculating..."))
        self.builder.get_object("checksum_label").set_text(_("Calculating..."))
        self.builder.get_object("headerbar").set_subtitle(path)
        self.builder.get_object("verify_url_button").set_sensitive(False)
        self.builder.get_object("verify_files_button").set_sensitive(False)
        self.builder.get_object("verify_checksum_button").set_sensitive(False)
        if path != None and os.path.isfile(path):
            self.path = path
            self.filename = os.path.basename(path)
            self.guess_urls()
            self.calculate_size()
            self.calculate_volume()
            self.calculate_checksum()

    def guess_urls(self):
        # guess the SUMS/GPG URL based on the ISO name
        try:
            sums = ""
            gpg = ""
            if self.filename.startswith("linuxmint-"):
                if self.filename.endswith("-beta.iso"):
                    sums = f"{MINT_MIRROR}/testing/sha256sum.txt"
                elif self.filename.endswith(".iso"):
                    # extract version number
                    version = self.filename.split("-")[1]
                    sums = f"{MINT_MIRROR}/stable/{version}/sha256sum.txt"
                gpg = sums + ".gpg"
            elif self.filename.startswith("lmde-"):
                if self.filename.endswith("-beta.iso"):
                    sums = f"{MINT_MIRROR}/testing/sha256sum.txt"
                elif self.filename.endswith(".iso"):
                    # extract version number
                    version = self.filename.split("-")[1]
                    sums = f"{MINT_MIRROR}/debian/sha256sum.txt"
                gpg = sums + ".gpg"
            elif self.filename.startswith("ubuntu-"):
                version = self.filename.split("-")[1]
                # remove point version from version
                major = version.split(".")[0]
                minor = version.split(".")[1]
                version = f"{major}.{minor}"
                sums = f"http://releases.ubuntu.com/{version}/SHA256SUMS"
                gpg = sums + ".gpg"
            self.builder.get_object("entry_url_sums").set_text(sums)
            self.builder.get_object("entry_url_gpg").set_text(gpg)
        except Exception as e:
            # best effort
            print(e)
            pass

    @async_function
    def calculate_size(self):
        file_info = os.stat(self.path)
        text = convert_bytes(file_info.st_size)
        self.set_label("size_label", text)

    @async_function
    def calculate_volume(self):
        volume_id = _("No volume ID found")
        stdout = subprocess.check_output(["isoinfo", "-d", "-i", self.path]).decode("UTF-8")
        for line in stdout.split("\n"):
            if "volume id:" in line.lower():
                volume_id = line.split(":")[1].strip()
        self.set_label("volume_label", volume_id)

    @async_function
    def calculate_checksum(self):
        print("Checking ", self.path)
        checksum = subprocess.getoutput(f"sha256sum -b '{self.path}'")
        checksum = checksum.replace(self.path, "").replace("*", "").strip()
        self.set_label("checksum_label", checksum)
        self.sha256sum = checksum

    def update_verify_button(self, *args):
        self.builder.get_object("verify_files_button").set_sensitive(False)
        self.builder.get_object("verify_checksum_button").set_sensitive(False)

        if self.sha256sum == None:
            return

        current_page = self.builder.get_object("stack_checksum").get_visible_child_name()

        if current_page == "page_url":
            if self.builder.get_object("entry_url_sums").get_text() != "" and self.builder.get_object("entry_url_gpg").get_text() != "":
                self.builder.get_object("verify_url_button").set_sensitive(True)
        elif current_page == "page_files":
            if self.builder.get_object("filechooser_sums").get_filename() is not None and self.builder.get_object("filechooser_gpg").get_filename() is not None:
                self.builder.get_object("verify_files_button").set_sensitive(True)
        elif current_page == "page_sum_manual":
            if (self.builder.get_object("entry_sum").get_text() != ""):
                self.builder.get_object("verify_checksum_button").set_sensitive(True)

    @idle_function
    def set_label(self, label, text):
        self.builder.get_object(label).set_text(text)
        self.update_verify_button()

    def verify_checksum(self, button):
        if self.builder.get_object("entry_sum").get_text() == self.sha256sum:
            self.show_result("dialog-warning", _("The checksum is correct"),
                    summary=_("The checksum is correct but the authenticity of the sum was not verified."))
        else:
            self.show_result("dialog-error", _("Checksum mismatch"),
                    summary=_("Download the ISO image again. Its checksum does not match."))

    def verify_url(self, button):
        # Download files
        try:
            with open(PATH_SUMS, "wb") as file:
                url = self.builder.get_object("entry_url_sums").get_text()
                response = requests.get(url)
                response.raise_for_status()
                file.write(response.content)
        except:
            self.dialog(_("The sums file could not be downloaded. Check the URL."))
            return
        try:
            with open(PATH_GPG, "wb") as file:
                url = self.builder.get_object("entry_url_gpg").get_text()
                response = requests.get(url)
                response.raise_for_status()
                file.write(response.content)
        except:
            self.dialog(_("The gpg file could not be downloaded. Check the URL."))
            return
        self.verify()

    def verify_files(self, button):
        # Copy files
        try:
            with open(PATH_SUMS, "wb") as file:
                path = self.builder.get_object("filechooser_sums").get_filename()
                subprocess.call(["cp", path, PATH_SUMS])
        except:
            self.dialog(_("The sums file could not be checked."))
            return
        try:
            with open(PATH_GPG, "wb") as file:
                path = self.builder.get_object("filechooser_gpg").get_filename()
                subprocess.call(["cp", path, PATH_GPG])
        except:
            self.dialog(_("The gpg file could not be checked."))
            return
        self.verify()

    def verify(self):
        details = []
        try:
            integrity_ok, explanation = self.check_integrity()
            if not integrity_ok:
                # Incorrect SUM
                self.show_result("dialog-error", _("Integrity check failed"),
                    summary=explanation)
                return

            # note: verify_file automatically closes the file handle
            verified = self.gpg.verify_file(open(PATH_GPG, "rb"), PATH_SUMS)

            if verified.fingerprint == None:
                # The GPG file is not signed
                self.show_result("dialog-error", _("The SHA256 sums file is not signed."))
                return

            fingerprint = verified.fingerprint
            details.append(_("Signed by: %s") % fingerprint)

            if not verified.valid:
                # The key isn't in the keyring, download it from the keyserver
                print("Importing", fingerprint)
                # re-verify
                self.gpg.recv_keys('hkp://keyserver.ubuntu.com', fingerprint)
                verified = self.gpg.verify_file(open(PATH_GPG, "rb"), sums_path)
                # Remove it from the keyring
                print("Deleting", fingerprint)
                self.gpg.delete_keys(fingerprint)

            if not verified.valid:
                # The key still isn't in the keyring
                self.show_result("dialog-warning", _("Unknown signature"),
                    summary=_("Key not found on keyserver."),
                    details=details)
                return

            if verified.username != None:
                details.append(verified.username)

            if verified.fingerprint in TRUSTED_SIGNATURES.keys():
                name = TRUSTED_SIGNATURES[verified.fingerprint]
                logo_name = name.replace(" ", "").lower().strip()
                logo_name = f"mintstick-logo-{logo_name}"
                self.show_result(logo_name, _("Everything looks good!"),
                    summary=_("This is an official ISO image."),
                    details=details)
                return

            if verified.trust_level != None and verified.trust_level >= verified.TRUST_FULLY:
                self.show_result("application-certificate", _("Everything looks good!"),
                    summary=_("This ISO image is verified by a trusted signature."),
                    details=details)
            else:
                details.append(_("If you trust the signature you can trust the ISO."))
                self.show_result("dialog-warning", _("Untrusted signature"),
                    summary=_("This ISO image is verified by an untrusted signature."),
                    details=details)
                return

        except Exception as e:
            self.show_result("dialog-error", _("An error occurred"), details=[str(e)])

    def check_integrity(self):
        expected_line = f"{self.sha256sum} *{self.filename}"
        with open(PATH_SUMS) as sums_file:
            for line in sums_file:
                line = line.strip()
                if line.endswith(f" *{self.filename}") or line.endswith(f" {self.filename}"):
                    if line == f"{self.sha256sum} *{self.filename}" or \
                       line == f"{self.sha256sum} {self.filename}":
                        return (True, None)
                    else:
                        return (False, _("The SHA256 sum of the ISO image is incorrect."))
        return (False, _("The SHA256 sums file does not contain sums for this ISO image."))

    def show_result(self, icon_name, text, summary=None, details=None):
        self.builder.get_object("image_result").set_from_icon_name(icon_name, 64)
        self.builder.get_object("label_result").set_text(text)
        if summary != None:
            self.builder.get_object("label_result_summary").set_text(summary)
        if details != None:
            self.builder.get_object("label_result_details").set_text("\n".join(details))
        self.builder.get_object("result_stack").set_visible_child_name("page_result")
        # Unselect the summary label
        self.builder.get_object("label_result_summary").select_region(0, 0)
        self.builder.get_object("back_button").grab_focus()

    def dialog(self, text):
        dialog = Gtk.MessageDialog(parent=self.window,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text=text)
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.run()
        dialog.destroy()

    def go_back(self, button):
        self.builder.get_object("result_stack").set_visible_child_name("page_verification")

    def quit(self, widget=None):
        Gtk.main_quit()

if len(sys.argv) != 2:
    print("Usage:\n  mint-iso-verify iso_file\n\nExiting.")
    sys.exit(1)

filename = sys.argv[1]
if not os.path.exists(filename):
    print(f"File not found '{filename}'.\nExiting.")
    sys.exit(1)

App(sys.argv[1])
Gtk.main()