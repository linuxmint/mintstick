#!/usr/bin/python3

DOMAIN = "mintstick"
PATH = "/usr/share/linuxmint/locale"

import os, gettext
from mintcommon import additionalfiles

os.environ['LANGUAGE'] = "en_US.UTF-8"
gettext.install(DOMAIN, PATH)

prefix = """[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=mintstick
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
Icon=mintstick
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
Icon-Name=media-removable-symbolic
Selection=S
Extensions=iso;img;
"""
additionalfiles.generate(DOMAIN, PATH, "share/nemo/actions/mintstick.nemo_action", prefix, _("Make bootable USB stick"), _("Make a bootable USB stick"), "")

prefix="""[Nemo Action]
Active=true
Exec=mintstick -m format -u %D
Icon-Name=edit-clear-all-symbolic
Selection=S
Extensions=any;
Conditions=removable;
"""
additionalfiles.generate(DOMAIN, PATH, "share/nemo/actions/mintstick-format.nemo_action", prefix, _("Format"), _("Format a USB stick"), "")

prefix="""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>

  <vendor>Linux Mint</vendor>
  <vendor_url>https://linuxmint.com</vendor_url>

  <action id="com.linuxmint.mintstick">
    <description>USB Image Writer / USB Stick Formatter</description>
"""

suffix="""
    <icon_name>mintstick</icon_name>
    <defaults>
      <allow_any>no</allow_any>
      <allow_inactive>no</allow_inactive>
      <allow_active>auth_self_keep</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/bin/python3</annotate>
    <annotate key="org.freedesktop.policykit.exec.argv1">/usr/lib/linuxmint/mintstick/raw_write.py</annotate>
    <annotate key="org.freedesktop.policykit.exec.argv1">/usr/lib/linuxmint/mintstick/raw_format.py</annotate>
  </action>

</policyconfig>
"""

additionalfiles.generate_polkit_policy(DOMAIN, PATH, "share/polkit/com.linuxmint.mintstick.policy", prefix, _("This will destroy all data on the USB stick, are you sure you want to proceed?"), suffix)

