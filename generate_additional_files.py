#!/usr/bin/python2

DOMAIN = "mintstick"
PATH = "/usr/share/linuxmint/locale"

import os, gettext, sys
sys.path.append('/usr/lib/linuxmint/common')
import additionalfiles

os.environ['LANG'] = "en_US.UTF-8"
gettext.install(DOMAIN, PATH)

prefix = """[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=usb-creator
Exec=mintstick -m iso
Categories=GNOME;GTK;Utility;
NotShowIn=KDE;
"""

additionalfiles.generate(DOMAIN, PATH, "share/applications/mintstick.desktop", prefix, _("USB Image Writer"), _("Make a bootable USB stick"), "")

prefix = """[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=system-run
Exec=mintstick -m iso
Categories=System;
OnlyShowIn=KDE;
"""

additionalfiles.generate(DOMAIN, PATH, "share/applications/mintstick-kde.desktop", prefix, _("USB Image Writer"), _("Make a bootable USB stick"), "", genericName=_("Make a bootable USB stick"))

prefix = """[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=usb-creator
Exec=mintstick -m format
Categories=GNOME;GTK;Utility;
NotShowIn=KDE;
"""

additionalfiles.generate(DOMAIN, PATH, "share/applications/mintstick-format.desktop", prefix, _("USB Stick Formatter"), _("Format a USB stick"), "")

prefix = """[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=system-run
Exec=mintstick -m format
Categories=System;
OnlyShowIn=KDE;
"""

additionalfiles.generate(DOMAIN, PATH, "share/applications/mintstick-format-kde.desktop", prefix, _("USB Stick Formatter"), _("Format a USB stick"), "", genericName=_("Format a USB stick"))

prefix="""[Nemo Action]
Active=true
Exec=mintstick -m iso -i "%F"
Icon-Name=usb-creator
Selection=S
Extensions=iso;img;
"""
additionalfiles.generate(DOMAIN, PATH, "share/nemo/actions/mintstick.nemo_action", prefix, _("Make bootable USB stick"), _("Make a bootable USB stick"), "")

prefix="""[Nemo Action]
Active=true
Exec=mintstick -m format -u %D
Icon-Name=usb-creator
Selection=S
Extensions=any;
Conditions=removable;
"""
additionalfiles.generate(DOMAIN, PATH, "share/nemo/actions/mintstick-format.nemo_action", prefix, _("Format"), _("Format a USB stick"), "")
