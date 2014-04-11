#!/usr/bin/python
#-*- coding: utf-8 -*-

from crashplan_logparser.model import BackupLogParser
from ConfigParser import SafeConfigParser

def main():
    # read config
    config = SafeConfigParser()
    config.read("logparser.conf")

    try:
        logfile = config.get("General", "logfile")
    except ConfigParser.NoSectionError:
        print("Unable to read configuration file")
        exit(1)

    blp = BackupLogParser(logfile)
    blp.latest_completed_job_in_nagios_format()

    
     

if __name__=="__main__":
    main()

