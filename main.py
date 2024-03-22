#!/usr/bin/env python

import json
import os
import subprocess
import datetime
import re
import time
import sys

from ui import TermuxUI
from ui import TextUI

from date import ts
from date import unts
from date import extDate

from reports import report as _report
from reports import detailedReport as _detailedReport
from reports import simpleReport as _simpleReport

# Contract Values
people = []
events = []
ids = []
startTime = ''
endTime = ''

# Config Values
selectedCoop = ""
sink = ""
mode = ""

# File Names
cwd = os.path.dirname(os.path.realpath(__file__))
configFile = os.path.join(cwd, "config.json")
coopFile = ""

# Report Wrappers
def report():
    return _report(events, people, sink=sink, startTime=startTime, endTime=endTime)
def detailedReport():
    return _detailedReport(events, people, sink=sink, startTime=startTime, endTime=endTime)
def simpleReport():
    return _simpleReport(events, startTime=startTime, endTime=endTime)

def addEvent(time, number, direction, person, id):
    global startTime
    #print(f"Adding event at {time}, count {number}, {direction} by {person}")

    if isinstance(time, int):
        time = unts(time)

    if person not in people:
        #print("Woah, new speedy soul " + person)
        people.append(person)

    if startTime == "" or ts(time) < ts(startTime):
        #print("Earlier start!")
        startTime = time

    events.append({
        'time': time,
        'count': number,
        'direction': direction,
        'player': person,
        'id': id
    })
    events.sort(key=lambda x: x["time"])

def processNote(note):
    global startTime

    if note['id'] in ids:
        #print("Existing: ", note['id'])
        return
    else:
        ids.append(note['id'])

    if "Gift Received" not in note['title']:
        return

    matches = re.search(r'^(.+) \((.+)\) has (?:sent you|hatched)', note['content'])

    if not matches:
        print("RegEx fail!", note['content'])
        return

    person = matches.group(1)
    coop = matches.group(2)

    #print(f"{person} in {coop}")

    if coop != selectedCoop:
        #print("Wrong Coop!", coop)
        return

    timeStamp = note['when']

    if '🐣' in note['title']:
        #print("CR...")
        if startTime == "" or ts(timeStamp) < ts(startTime):
            #print("Earlier.")
            startTime = timeStamp
        return

    amount = 0

    if 'has sent you a Boost Token' in note['content']:
        amount = 1
    else:
        match = re.search(r'(?<=has sent you a gift of )[0-9]+', note['content'])
        if not match:
            #print("Amount Parse Error! " + note['content'])
            return
        amount = match.group()

    addEvent(note['when'], amount, 'sent', person, note['id'])

def processAllNotes():
    rawNotes = ""
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        print('Using Debug Notifications!')
        with open(sys.argv[2], 'r') as file:
            rawNotes = file.read()
    else:
        rawNotes = subprocess.check_output(["termux-notification-list"], text=True)

    notifications = json.loads(rawNotes)

    for note in notifications:
        if note.get('packageName') != 'com.auxbrain.egginc':
            continue
        if 'new message' in note.get('content'):
            continue

        processNote(note)
    saveCoop()

def sendToken(count = 0):
    sendTo = ""
    sendAmount = 0
    sendTime = int(time.time())

    if mode == "sink":
        person = selectPlayer()
        if not person:
            return
    else:
        person = "Sink"

    if count == 0:
        reply = ui.list("Token Count", ["1","2","3","4","5","6","7","8","9","10"])
        if not reply:
            return
        count = int(reply['text'])

    addEvent(sendTime, count, 'received', person, 0)
    saveCoop()

    ui.toast(f"Recorded {count} tokens to {person}")

def editEvents():
    print("Editing events.")
    eventNames = []
    for ev in events:
        eventNames.append(f"{extDate(ev['time'])} {ev['player']} {ev['direction']} {ev['count']}")

    reply = ui.list("Choose an Event", eventNames)
    if not reply:
        return
    eventIndex = reply['index']
    event = events[eventIndex]

    reply2 = ui.radio("Choose what to edit", [
        f"Time: {extDate(event['time'])}",
        f"Player: {event['player']}",
        f"Direction: {event['direction']}",
        f"Count: {event['count']}",
        f"Delete Event"
    ])
    if not reply2:
        return
    action = reply2['index']

    if action == 0:
        newTime = ui.dateTime("New time")
        if not newTime:
            return
        event['time'] = newTime
    elif action == 1:
        newPlayer = selectPlayer()
        if not newPlayer:
            return
        event['player'] = newPlayer
    elif action == 2:
        newDir = ui.radio("Choose Direction", [
            f"{event['player']} Sent the Tokens",
            f"{event['player']} Received the Tokens"
        ])
        if not newDir:
            return
        if newDir['index'] == 0:
            event['direction'] = "sent"
        else:
            event['direction'] = "received"
    elif action == 3:
        newCount = ui.string("Enter Count")
        if not newCount:
            return
        try:
            event['count'] = int(newCount)
        except ValueError:
            return
    elif action == 4:
        confirm = ui.radio(f"Delete {eventNames[eventIndex]}?", ["Yes", "No"])
        if not confirm or confirm['index'] != 0:
            return
        event = None

    if event:
        events[eventIndex] = event
    else:
        del events[eventIndex]
    saveCoop()
    ui.toast("Event Saved.")

def selectPlayer():
    reply = ui.list("Choose Player", people + ['Other'])
    if not reply:
        return
    person = reply['text']

    if person == 'Other':
        newPerson = ui.string('Enter Name:')
        if not newPerson:
            newPerson = "Speedy Soul"
        person = newPerson
    return person

def notification():
    if cli:
        return

    script = f"python {os.path.abspath(__file__)}"
    if mode == "sink":
        noteCmd = [
            "termux-notification",
            "-t", "Tokification.py",
            "-i", "tok_egg_py",
            "-c", f"Click for Menu.",
            "--action", f"{script} ui",
            "--button1", "Send 6",
            "--button1-action", f"{script} send-6",
            "--button2", "Send Other",
            "--button2-action", f"{script} send",
            "--button3", "Copy Report",
            "--button3-action", f"{script} copy-report"
        ]
    else:
        noteCmd = [
            "termux-notification",
            "-t", "Tokification.py",
            "-i", "tok_egg_py",
            "-c", simpleReport(),
            "--action", f"{script} ui",
            "--button1", "Send 1",
            "--button1-action", f"{script} send-1",
            "--button2", "Send Other",
            "--button2-action", f"{script} send",
            "--button3", "Refresh",
            "--button3-action", f"{script} notification"
        ]

    try:
        subprocess.run(noteCmd)
    except subprocess.CalledProcessError as e:
        print("Timed Out creating notification:", e)

def mainMenu():
    global mode

    if cli:
        print(simpleReport())
    else:
        notification()

    reply = ui.radio("Tokification.py", [
        "Send Tokens",
        "Generate Report",
        "Generate Detailed Report",
        "Edit Events",
        f"Start Time: {extDate(startTime)}",
        f"End time: {extDate(endTime)}",
        f"Coop: {selectedCoop}",
        f"Player Name: {sink}",
        f"Toggle Mode: {mode}"
    ])
    if not reply:
        return

    index = reply['index']
    if index == 0:
        processArg("send")
    elif index == 1:
        if mode == 'sink':
            processArg("copy-report")
        else:
            ui.info('Report', simpleReport())
            mainMenu()
    elif index == 2:
        processArg("d-report")
    elif index == 3:
        processArg("edit")
        mainMenu()
    elif index == 4:
        processArg("start-time")
        mainMenu()
    elif index == 5:
        processArg("end-time")
        mainMenu()
    elif index == 6:
        processArg("change-coop")
        mainMenu()
    elif index == 7:
        processArg("change-sink")
        mainMenu()
    elif index == 8:
        if mode == "sink":
            mode = "standard"
        else:
            mode = "sink"
        saveConfig()
        mainMenu()

def askEndTime():
    global endTime
    newTime = ui.dateTime("Co-op End Time")
    if not newTime:
        return

    print("Updating time to " + newTime)
    endTime = newTime
    saveCoop()

def askStartTime():
    global startTime
    newTime = ui.dateTime("Co-op Start Time")
    if not newTime:
        return

    print("Updating time to " + newTime)
    startTime = newTime
    saveCoop()

def changeCoop():
    global selectedCoop
    newStr = ui.string("Coop code:")
    if not newStr:
        return

    selectedCoop = newStr
    saveConfig()
    loadConfig()
    loadCoop()

def changeSink():
    global sink
    newStr = ui.string("Player Name:")
    if not newStr:
        return

    sink = newStr
    saveConfig()

def processArg(arg):
    if arg == "ui" or arg == "menu":
        mainMenu()
    elif arg == "send":
        processAllNotes()
        sendToken()
    elif arg == "send-6":
        processAllNotes()
        sendToken(6)
    elif arg == "send-1":
        processAllNotes()
        sendToken(1)
    elif arg == "report":
        processAllNotes()
        print(report())
    elif arg == "copy-report":
        processAllNotes()
        ui.copy(report())
    elif arg == "start-time":
        askStartTime()
    elif arg == "end-time":
        askEndTime()
    elif arg == "d-report":
        ui.copy(detailedReport())
    elif arg == "change-coop":
        changeCoop()
    elif arg == "change-sink":
        changeSink()
    elif arg == "edit":
        editEvents()
    elif arg == "s-report":
        simpleReport()
    elif arg == "notification":
        notification()

    else:
        print('Must pass a valid command!')

def loadConfig():
    global sink
    global selectedCoop
    global coopFile
    global mode

    if os.path.exists(configFile):
        with open(configFile, 'r') as file:
            data = json.load(file)
            selectedCoop = data['coop']
            sink = data['sinkName']
            mode = data['mode']

            coopFile = os.path.join(cwd, f"./coops/{ selectedCoop }.json")
    else:
        saveConfig()
        loadConfig()

def saveConfig():
    with open(configFile, 'w') as file:
        json.dump({
            'sinkName': sink,
            'coop': selectedCoop,
            'mode': mode
        }, file, indent=4)

def loadCoop():
    global people
    global events
    global ids
    global startTime
    global endTime
    ids = []

    if os.path.exists(coopFile):
        with open(coopFile, 'r') as file:
            data = json.load(file)
            events = sorted(data['events'], key=lambda x: x["time"])
            startTime = data['startTime']
            endTime = data['endTime']

            for ev in events:
                ids.append(ev['id'])
                if ev['player'] not in people:
                    people.append(ev['player'])
    else:
        saveCoop()

def saveCoop():
    if selectedCoop == "":
        print("Cannot Save, no coop set!")
        return

    if not os.path.exists(os.path.dirname(coopFile)):
        os.makedirs(os.path.dirname(coopFile))
        print("Coops Dir Created!")

    with open(coopFile, 'w') as f:
        json.dump({
            'events': events,
            'startTime': startTime,
            'endTime': endTime,
        }, f, indent=4)

loadConfig()
loadCoop()

cli=False
if 'SSH_CLIENT' in os.environ or (len(sys.argv) > 1 and sys.argv[1] == "cli"):
    ui = TextUI()
    cli=True
else:
    ui = TermuxUI()

if len(sys.argv) < 2:
    # no args
    processArg("ui")
elif len(sys.argv) > 1 and sys.argv[1] == "cli":
    # arg1 == 'cli'
    if len(sys.argv) < 3:
        # cli is only arg
        processArg("ui")
    else:
        processArg(sys.argv[2])
else:
    processArg(sys.argv[1])

#	reply=""
#	while true; do
#		reply="$( su -c /system/bin/getevent -c 1 -l /dev/input/event0 )"
#		echo "($reply)"
#		[[ -z "$reply" || "$reply" = *"^C"* ]] && exit 0
#		[[ $reply = *"KEY_VOLUMEDOWN"* ]] && send
#		echo "Send End."
#		sleep 1
#	done
