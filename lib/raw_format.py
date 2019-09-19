#!/usr/bin/python3

import subprocess
from subprocess import Popen,PIPE,call,STDOUT
import os, sys
import getopt
import parted
sys.path.append('/usr/lib/mintstick')
from mountutils import *
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
    elif fstype == "btrfs":
        partition_type = "btrfs"

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
    elif fstype == "btrfs":
        execute(["mkfs.btrfs", "-L", volume_label, partition_path])
        execute(["mkdir", "-p", "/tmp/compressPendrive"])
        execute(["mount", partition_path, "/tmp/compressPendrive"])
        execute(["btrfs", "property", "set", "/tmp/compressPendrive/", "compression", "zstd"])
        execute(["chmod", "777", "/tmp/compressPendrive"])
        execute(["umount", "/tmp/compressPendrive"])

    # Exit
    sys.exit(0)

def main():
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:f:l:u:g:", ["help", "device=","filesystem=","label=","uid=","gid="])
    except getopt.error as msg:
        print(msg)
        print("for help use --help")
        sys.exit(2)

    for o, a in opts:
        if o in ("-h", "--help"):
            print("Usage: %s -d device -f filesystem -l volume_label\n"  % sys.argv[0])
            print("-d|--device          : device path")
            print("-f|--filesystem      : filesystem\n")
            print("-l|--label           : volume label\n")
            print("-u|--uid             : uid of user\n")
            print("-g|--gid             : gid of user\n")
            print("Example : %s -d /dev/sdj -f fat32 -l \"USB Stick\" -u 1000 -g 1000" % sys.argv[0])
            sys.exit(0)
        elif o in ("-d"):
            device = a
        elif o in ("-f"):
            if a not in [ "fat32", "exfat", "ntfs", "ext4", "btrfs" ]:
                print "Specify fat32, exfat, ntfs, ext4 or btrfs"
                sys.exit(3)
            fstype = a
        elif o in ("-l"):
            label = a
        elif o in ("-u"):
            uid = a
        elif o in ("-g"):
            gid = a

    argc = len(sys.argv)
    if argc < 11:
      print("Too few arguments")
      print("for help use --help")
      exit(2)

    raw_format(device, fstype, label, uid, gid)

if __name__ == "__main__":
    main()
