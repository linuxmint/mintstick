#!/usr/bin/python

import commands 

# OLD CODE (USED HAL)
#for device in $(hal-find-by-capability --capability storage); do
#    VENDOR=$(hal-get-property --udi $device --key storage.vendor)
#    NAME=$(hal-get-property --udi $device --key storage.model)
#    PLUGGABLE=$(hal-get-property --udi $device --key storage.hotpluggable)
#    TYPE=$(hal-get-property --udi $device --key storage.drive_type)
#    DEVPATH=$(hal-get-property --udi $device --key block.device)
#    AVAIL=$(hal-get-property --udi $device --key storage.removable.media_available)
#
#    if [ "${AVAIL}" = true ] && [ "${PLUGGABLE}" = true ] && \
#        ( [ "${TYPE}" = "disk" ] || [ "${TYPE}" = "sd_mmc" ] ); then
#        VENDOR=${VENDOR:-"Unknown"}
#        NAME=${NAME:-"Unknown"}
#        echo "$VENDOR $NAME, $DEVPATH"
#    fi
#done

def getLabel (drive):
    result = ""
    matches = commands.getoutput("blkid").split("\n")
    for line in matches:
        if line.find(drive) is not -1:
            if line.find("LABEL=") is not -1:
                quote = line.index("\"")
                line = line[quote+1:]
                quote = line.index("\"")
                line = line [:quote]
                if len(result) > 0:
                    result += ", "
                result += "(" + line
    if len(result) > 0:
        result += ")"
    return result

# NEW CODE, relies on /sys/block
for line in commands.getoutput("ls -db /sys/block/[hsv]d*").split():
    device=line.replace("/sys/block/", "")
    drive="/dev/" + device    
    removable=commands.getoutput("cat /sys/block/%s/removable" % device)
    if removable == "1":
        vendor=commands.getoutput("cat /sys/block/%s/device/vendor" % device)
        name=commands.getoutput("cat /sys/block/%s/device/model" % device)
        if vendor == "":
            vendor = "Unknown"
        if name == "":
            name = "Unknown"
        name += getLabel(drive.strip())
        print "%s %s; %s" % (vendor.strip(), name.strip(), drive.strip())