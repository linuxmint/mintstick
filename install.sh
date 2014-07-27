#!/bin/sh
#
#    Copyright 2007-2009 Canonical Ltd.
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA

DATAFILES="mintstick.py mintstick.glade raw_write.py raw_format.py mountutils.py"


if [ "$1" = "uninstall" ]; then
    rm -rf /usr/share/linuxmint/mintstick
    rm -r /usr/share/applications/mintstick.desktop
    rm -r /usr/share/applications/mintstick-kde.desktop
    rm -r /usr/share/applications/mintstick-format.desktop
    rm -r /usr/share/applications/mintstick-kde-format.desktop
    rm -f /usr/bin/mintstick
    rm -rf /usr/share/polkit-1/actions/org.linuxmint.im.policy
    rm -rf /usr/share/kde4/apps/solid/actions/mintstick-format.desktop
else
    cp share/applications/mintstick.desktop /usr/share/applications/
    cp share/applications/mintstick-format.desktop /usr/share/applications/
    cp share/applications/mintstick-kde.desktop /usr/share/applications/
    cp share/applications/mintstick-format-kde.desktop /usr/share/applications/
    cp share/polkit/org.linuxmint.im.policy /usr/share/polkit-1/actions
    cp share/kde4/mintstick-format_action.desktop /usr/share/kde4/apps/solid/actions
    cp mintstick /usr/bin/
    mkdir -p /usr/share/linuxmint/mintstick

    for item in $DATAFILES; do
        cp usr/share/linuxmint/mintstick/$item /usr/share/linuxmint/mintstick/
    done
fi
