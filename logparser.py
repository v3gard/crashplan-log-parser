#!/usr/bin/python
#-*- coding: utf-8 -*-
""" logparser.py: CLI interface to the crashplan-log-parser library"""

__author__  = "Vegard Haugland"
__license__   = "LGPLv3"
__version__ = 1.0
__email__ = "vegard@haugland.at"

from crashplan_logparser.model import BackupLogParser
import ConfigParser
from ConfigParser import SafeConfigParser
from optparse import OptionParser
from datetime import datetime

def main():
    # read options
    usage = "usage: %prog [options] COMMAND"
    op = OptionParser(usage, version="%prog "+"%s" % __version__)
    op.add_option("-d", "--debug", dest="debug", action="store_true",
            default=False, help="print additional debug information")
    op.add_option("-l", "--list", dest="listCmds", action="store_true",
            default=False, help="prints a list of available commands")
    op.add_option("-c", "--config", dest="config", default=None,
            help="override the default configuration file with CONFIG")

    (options, args) = op.parse_args()

    # read config
    config = SafeConfigParser()
    config.read("logparser.conf")

    try:
        if not options.config:
            logfile = config.get("General", "logfile")
        else:
            logfile = options.config
        with open(logfile, "r") as f:
            pass
    except ConfigParser.NoSectionError, e:
        print("Unable to read section of configuration file. %s" % str(e))
        exit(1)
    except IOError, e:
        print("Unable to read configuration file. %s" % str(e))
        exit(1)

    valid_commands = ["stats", "last", "hours"]
    # parse options
    if options.listCmds == True:
        for v in valid_commands:
            print v
        exit(1)

    # read arguments and parse commands
    if len(args) > 1:
        print("Too many command line arguments given.")
        print op.get_usage()
        exit(1)
    if len(args) == 0:
        print("No command given.")
        print op.get_usage()
        exit(1)
    if args[0] not in valid_commands:
        print("Command not recognized.")
        print op.get_usage()
        exit(1)

    # ok, enough input validation
    blp = BackupLogParser(logfile)

    if args[0] == "stats":
        blp.get_statistics()
    if args[0] == "last":
        job = blp.get_last_job()
        print "Last job started %s and completed %s. Logged message was \"%s\"" % (job.eventStop.time_start, job.eventStop.time_start, job.eventStop.msg)
    if args[0] == "hours":
        job = blp.get_last_job()
        print (datetime.now()-job.eventStop.time_start).seconds/(60*60)



if __name__=="__main__":
    main()
