#!/usr/bin/python

import commands
from subprocess import Popen,PIPE,call,STDOUT
import os, sys
import getopt

def raw_write(source, target):
    bs = 1024
    size=0
    input = open(source, 'rb')
    total_size = float(os.path.getsize(source))
    print total_size
    output = open(target, 'wb')
    while True:
	buffer = input.read(bs)
	if len(buffer) == 0:
	  break
	output.write(buffer)
	size = size + bs
	print size/total_size

    output.flush()    
    #os.fsync(output.fileno())
    input.close()
    output.close()

def main():
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:t:", ["help", "source=","target="])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)

    for o, a in opts:
        if o in ("-h", "--help"):
            print "Usage: "
            sys.exit(0)
        elif o in ("-s"):
	    source = a
	elif o in ("-t"):
	    target = a
    
    argc = len(sys.argv)
    if argc < 5:
      print "Too few arguments"
      print "for help use --help"
      exit(2)
    
    raw_write(source, target)
    
if __name__ == "__main__":
    main()