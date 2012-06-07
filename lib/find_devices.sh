#!/bin/sh

for device in $(hal-find-by-capability --capability storage); do
    VENDOR=$(hal-get-property --udi $device --key storage.vendor)
    NAME=$(hal-get-property --udi $device --key storage.model)
    PLUGGABLE=$(hal-get-property --udi $device --key storage.hotpluggable)
    TYPE=$(hal-get-property --udi $device --key storage.drive_type)
    DEVPATH=$(hal-get-property --udi $device --key block.device)
    AVAIL=$(hal-get-property --udi $device --key storage.removable.media_available)

    if [ "${AVAIL}" = true ] && [ "${PLUGGABLE}" = true ] && \
        ( [ "${TYPE}" = "disk" ] || [ "${TYPE}" = "sd_mmc" ] ); then
        VENDOR=${VENDOR:-"Unknown"}
        NAME=${NAME:-"Unknown"}
        echo "$VENDOR $NAME, $DEVPATH"
    fi
done

