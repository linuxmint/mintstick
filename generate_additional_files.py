#!/usr/bin/python

import os, gettext

DOMAIN = "mintstick"
PATH = "/usr/share/linuxmint/locale"

def generate(filename, prefix, name, comment, suffix):
    gettext.install(DOMAIN, PATH)
    desktopFile = open(filename, "w")

    desktopFile.writelines(prefix)

    desktopFile.writelines("Name=%s\n" % name)
    for directory in os.listdir(PATH):
        if os.path.isdir(os.path.join(PATH, directory)):
            try:
                language = gettext.translation(DOMAIN, PATH, languages=[directory])
                language.install()          
                desktopFile.writelines("Name[%s]=%s\n" % (directory, _(name)))
            except:
                pass

    desktopFile.writelines("Comment=%s\n" % comment)
    for directory in os.listdir(PATH):
        if os.path.isdir(os.path.join(PATH, directory)):
            try:
                language = gettext.translation(DOMAIN, PATH, languages=[directory])
                language.install()                      
                desktopFile.writelines("Comment[%s]=%s\n" % (directory, _(comment)))
            except:
                pass

    desktopFile.writelines(suffix)


gettext.install(DOMAIN, PATH)

prefix = """[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=gtk-execute
Exec=mintstick -m iso
Categories=GNOME;GTK;Utility;
NotShowIn=KDE;
"""

generate("share/applications/mintstick.desktop", prefix, _("USB Image Writer"), _("Make a bootable USB stick"), "")

prefix = """[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=system-run
Exec=mintstick -m iso
Categories=System;
OnlyShowIn=KDE;
"""

generate("share/applications/mintstick-kde.desktop", prefix, _("USB Image Writer"), _("Make a bootable USB stick"), "")

prefix = """[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=gtk-execute
Exec=mintstick -m format
Categories=GNOME;GTK;Utility;
NotShowIn=KDE;
"""

generate("share/applications/mintstick-format.desktop", prefix, _("USB Stick Formatter"), _("Format a USB stick"), "")

prefix = """[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=system-run
Exec=mintstick -m format
Categories=System;
OnlyShowIn=KDE;
"""

generate("share/applications/mintstick-format-kde.desktop", prefix, _("USB Stick Formatter"), _("Format a USB stick"), "")

prefix="""[Nemo Action]
Active=true
Exec=mintstick -m iso -i "%F"
Icon-Name=gtk-execute
Selection=S
Extensions=iso;img;
"""
generate("share/nemo/actions/mintstick.nemo_action", prefix, _("Make bootable USB stick"), _("Make a bootable USB stick"), "")

prefix="""[Nemo Action]
Active=true
Exec=mintstick -m format -u %D
Icon-Name=gtk-execute
Selection=S
Extensions=any;
Conditions=removable;
"""
generate("share/nemo/actions/mintstick-format.nemo_action", prefix, _("Format"), _("Format a USB stick"), "")
