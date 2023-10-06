#!/usr/bin/python3

from subprocess import call
import sys
import argparse
sys.path.append('/usr/lib/mintstick')
from mountutils import do_umount
import syslog

def execute(command):
    syslog.syslog(str(command))
    call(command)
    call(["sync"])

def raw_format(device_path, fstype, volume_label, uid, gid):

    do_umount(device_path)

    partition_path = "%s1" % device_path
    if fstype == "fat32":
        partition_type = "fat32"
    elif fstype == "exfat":
        partition_type = "ntfs"
    elif fstype == "ntfs":
        partition_type = "ntfs"
    elif fstype == "ext4":
        partition_type = "ext4"

    # First erase MBR and partition table , if any
    execute(["dd", "if=/dev/zero", "of=%s" % device_path, "bs=512", "count=1"])

    # Make the partition table
    execute(["parted", device_path, "mktable", "msdos"])

    # Make a partition (primary, with FS ID ext3, starting at 1MB & using 100% of space).
    # If it starts at 0% or 0MB, it's not aligned to MB's and complains
    execute(["parted", device_path, "mkpart", "primary", partition_type, "1", "100%"])

    # Call wipefs on the new partitions to avoid problems with old filesystem signatures
    execute(["wipefs", "-a", partition_path, "--force"])

    # Format the FS on the partition
    if fstype == "fat32":
        execute(["mkdosfs", "-F", "32", "-n", volume_label, partition_path])
    elif fstype == "exfat":
        execute(["mkfs.exfat", "-n", volume_label, partition_path])
    elif fstype == "ntfs":
        execute(["mkntfs", "-f", "-L", volume_label, partition_path])
    elif fstype == "ext4":
        execute(["mkfs.ext4", "-E", "root_owner=%s:%s" % (uid, gid), "-L", volume_label, partition_path])

    # Exit
    sys.exit(0)

def main():
    # parse command line options
    try:
        parser = argparse.ArgumentParser(description="Format USB",
                                         prog="mint-stick-format",
                                         epilog="Example : mint-stick-format -d /dev/sdj -f fat32 -l \"USB Stick\" -u 1000 -g 1000")
        parser.add_argument("-d", "--device", help="Device path", type=str, required=True)
        parser.add_argument("-f", "--filesystem", help="File system type", action="store",
                            type=str, choices=("fat32", "exfat", "ntfs", "ext4"), required=True)
        parser.add_argument("-u", "--uid", help="UID of the user", type=str, required=True)
        parser.add_argument("-g", "--gid", help="GID of the user", type=str, required=True)
        parser.add_argument("label", help="Volume label", type=str, nargs="*")
        args = parser.parse_args()
        print("Args", args)
        args.label = " ".join(args.label)
    except Exception as e:
        print(e)
        sys.exit(2)

    raw_format(args.device, args.filesystem, args.label, args.uid, args.gid)

if __name__ == "__main__":
    main()
