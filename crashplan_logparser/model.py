#!/usr/bin/python
#-*- coding: utf-8 -*-
""" model.py: part of crashplan-log-parser """

import re
import datetime

RE_BACKUP_EVENT = re.compile(r"^[A-Z]\s([0-9\/\s:PAM]+)\s\[[a-zA-Z0-9 ]+\]\s+?(.*)")
RE_BACKUP_START_EVENT = re.compile(r"Starting backup to CrashPlan Central: [0-9,]+ files? \([KMGTB0-9\.]+\) to back up")
RE_BACKUP_STOP_EVENT = re.compile(r"Stopped backup to CrashPlan Central in [0-9\.]+ [a-z]+: [0-9,]+ files? \([KMGTB0-9\.]+\) backed up, [KMGTB0-9\.]+ encrypted and sent @ [KMGTbps0-9]+")
RE_BACKUP_COMPLETED_EVENT = re.compile(r"Completed backup to CrashPlan Central in [<\s0-9\.]+ [a-z]+: [0-9\,]+ files? \([KMGTB0-9\.]+\) backed up, [KMGTB0-9\.]+ encrypted and sent")
RE_BACKUP_SCANNING_STARTED_EVENT = re.compile(r"Scanning for files to back up")
RE_BACKUP_SCANNING_COMPLETED_EVENT = re.compile(r"Scanning for files completed in [<\s0-9]+ minutes?: [0-9,]+ files? \([0-9\.MGTB]+\) found")
RE_BACKUP_IGNORE_EVENT_1 = re.compile(r"Configured to backup the following")

def enum(**enums):
    return type('Enum', (), enums)

EventTypes = enum(
                    BackupStartEvent=1,
                    BackupStopEvent=2,
                    BackupCompletedEvent=3,
                    BackupScanningStartedEvent=4,
                    BackupScanningCompletedEvent=5,
                    UnknownEvent=6,
                    IgnoredEvent=7,
                    )

JobTypes = enum(
                    ScanJob=1,
                    BackupJob=2,
                )

BackupEventRegexes = {
                         RE_BACKUP_START_EVENT : EventTypes.BackupStartEvent,
                         RE_BACKUP_STOP_EVENT : EventTypes.BackupStopEvent,
                         RE_BACKUP_COMPLETED_EVENT : EventTypes.BackupCompletedEvent,
                         RE_BACKUP_SCANNING_STARTED_EVENT : EventTypes.BackupScanningStartedEvent,
                         RE_BACKUP_SCANNING_COMPLETED_EVENT : EventTypes.BackupScanningCompletedEvent,
                         RE_BACKUP_IGNORE_EVENT_1 : EventTypes.IgnoredEvent,
                     } 

class BackupEvent(object):
    def __init__(self, time_start, line_number, msg):
        self.time_start = time_start
        self.line_number = line_number
        self.msg = msg
        self.type = None
        self._parse_event()

    def _parse_event(self):
        for ber in BackupEventRegexes.iterkeys():
            match = ber.findall(self.msg)
            if len(match) > 0:
                self.type = BackupEventRegexes[ber]
                break
        if len(match)==0:
            self.type = EventTypes.UnknownEvent

class BackupJob(object):
        def __init__(self, type, eventStart, eventStop):
            self.type = type
            self.eventStart = eventStart
            self.eventStop = eventStop

        def __repr__(self):
            return "<BackupJob || Start: %s || Stop: %s || Msg: %s>" % (self.eventStart.time_start, self.eventStop.time_start, self.eventStop.msg)


class BackupLogParser(object):
    def __init__(self, logfile):
            self.jobs = []
            self.matches = []
            self.logfile = logfile
            self.first_job_at_line = 0
            self.logfile_size = 0

    def _parse(self):
        self._parse_logfile()
        self._parse_jobs()

    def _parse_logfile(self):
        with open(self.logfile) as f:
            f.seek(0,2) # seek to EOF
            tmp = f.tell()
            if self.logfile_size == tmp:
                return # already parsed (no change. skip)
            self.logfile_size = tmp
            f.seek(0,0)
            matches = []
            lines = f.readlines()
            for i, line in enumerate(lines):
                match = RE_BACKUP_EVENT.findall(line)
                if len(match) > 0:
                    timestamp = datetime.datetime.strptime(match[0][0], "%m/%d/%y %I:%M%p")
                    msg = match[0][1]
                    matches.append(BackupEvent(timestamp, i, msg))
            self.matches = matches

    def _parse_jobs(self):
        # clear ignored and unhandled events
        self.matches = [x for x in self.matches if x.type not in (EventTypes.IgnoredEvent, EventTypes.UnknownEvent) ]
        
        # start parsing events
        previousEventCount = -1
        currentEventCount = 0
        while (previousEventCount != currentEventCount):
            eventStart = None
            eventStop = None
            eventStartItem = None
            disqualifyingEvents = []
            for i in xrange(len(self.matches)):
                event = self.matches[i]
                #START EVENTS
                if eventStart == None and event.type in (EventTypes.BackupScanningStartedEvent, EventTypes.BackupStartEvent):
                    eventStart = event
                    self.matches[i] = None
                # STOP EVENTS 
                # TODO: Should probably add some disqualifying events in case
                # the log file has been corrupted (e.g. crashplan suddently
                # stopped) during a start event. In that case, there would be
                # more start events than there are stop events.
                if eventStart != None and eventStop == None:
                    if eventStart.type == EventTypes.BackupScanningStartedEvent and event.type == EventTypes.BackupScanningCompletedEvent:
                        eventStop = event
                        self.jobs.append(BackupJob(JobTypes.ScanJob, eventStart, eventStop))
                        self.matches[i] = None
                    elif eventStart.type == EventTypes.BackupStartEvent and event.type in (EventTypes.BackupStopEvent, EventTypes.BackupCompletedEvent):
                        eventStop = event
                        self.jobs.append(BackupJob(JobTypes.BackupJob, eventStart, eventStop))
                        self.matches[i] = None
                    if eventStart != None and eventStop != None:
                        break
            previousEventCount = currentEventCount
            self.matches = [ x for x in self.matches if x != None ]
            currentEventCount = len(self.matches)

    def get_last_job(self):
        self._parse()
        return self.jobs[-1]

    def get_statistics(self):
        self._parse()
        print "  Scan jobs: %4d" % len([ x for x in self.jobs if x.type==JobTypes.ScanJob])
        print "Backup jobs: %4d" % len([ x for x in self.jobs if x.type==JobTypes.BackupJob])
        print " Total jobs: %4d" % len(self.jobs)
        print ""
        print "Last job completed at %s" % self.jobs[-1].eventStop.time_start
        # self._parse()
        # print "size: %d bytes" % self.logfile_size
        pass


