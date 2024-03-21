#!/usr/bin/env python

import json
import os
import subprocess
import datetime
import re
import time
import math
import sys

from ui import TermuxUI
from ui import TextUI

from date import ts
from date import unts
from date import extDate

# Contract Values
people = []
events = []
ids = []
startTime = ''
endTime = ''

# Config Values
selectedCoop = ""
sink = ""

# File Names
cwd = os.path.dirname(os.path.realpath(__file__))
configFile = os.path.join(cwd, "config.json")
coopFile = ""

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

def tval(start, end, token, count):
    # print(token, start, end, count)
    i = (1 - 0.9 * ((token - start) / (end - start))) ** 4
    return max(i, 0.03) * float(count)

def report():
    now = int(time.time())

    startLine = ""
    endLine= ""

    if startTime == "":
        sinceHourStart = now % 3600
        start = now - sinceHourStart
        startLine = ":warning: No start time set, assuming start of current hour."
    else:
        start = ts(startTime)
        startLine = f"<:contract:589317482901405697> Start Time: <t:{start}> (<t:{start}:R>)"

    if endTime == "":
        end = start + 12 * 60 * 60
        endLine = ":warning: No end time set, assuming 12 hours from start time."
    else:
        end = ts(endTime)
        endLine = f":alarm_clock: End Time: <t:{end}> (<t:{end}:R>)"

    rVals = []
    if now < end:
        rVals.append("__Running Token Value__")
        rVals.append(f"<:icon_token:653018008670961665> Now: `{ round(tval(start, end, now, 1), 4) }`")

        next = round(tval(start, end, now + 30 * 60, 1), 4)
        next2 = round(tval(start, end, now + 60 * 60, 1), 4)

        if next > 0.03:
            rVals.append(f"In 30 minutes: `{ next }`",)

        if next2 > 0.03:
            rVals.append(f"In 60 minutes: `{ next2 }`",)
    else:
        rVals.append(":tada: Contract Complete!")

    rowFormat = "{:<12.12s}|{:9.3f}|{:4d}|{:8.3f}|{:4d}|{:9.3f}"

    table = []
    tableDict = {}

    tokensSent = {}
    tokensRec = {}
    tvalSent = {}
    tvalRec = {}
    for person in people + [sink]:
        tokensSent[person] = 0
        tokensRec[person] = 0
        tvalSent[person] = 0.0
        tvalRec[person] = 0.0

    for ev in events:
        t = ts(ev['time'])
        d = ev['direction']
        c = int(ev['count'])
        p = ev['player']

        #print(t, d, c, startTime, endTime)
        tv = tval(start, end, t, c)
        #print(tv)
        if ev['direction'] == 'sent':
            tokensSent[p] += c
            tvalSent[p] += tv
            tokensRec[sink] += c
            tvalRec[sink] += tv
        else:
            tokensRec[p] += c
            tvalRec[p] += tv
            tokensSent[sink] += c
            tvalSent[sink] += tv

    for person in people + [sink]:
        delta = tvalSent[person] - tvalRec[person]
        #print(person, sT, sTval, rT, rTval, delta)
        output = rowFormat.format(person, delta, tokensSent[person], tvalSent[person], tokensRec[person], tvalRec[person] * -1)
        #print(output)
        table.append(output)
        tableDict[person] = output

    url = "https://discord.com/channels/455380663013736479/455512567004004353/1217529083286651082"

    out = ["# __Tokification.py__ (Beta)",
        f"",
        f"Report Generated at <t:{now}> (<t:{now}:R>)",
        f"_This message will be manually updated every 15 to 45 minutes, depending on how busy I am._",
        f"",
        f"__Contract Info__",
        startLine,
        endLine,
        f"_Note that all token values are only accurate once the end time is accurate._",
	f"",
        "\n".join(rVals),
        f"",
        f"__Player's Current TVals__ (as seen by the :people_hugging: sink)",
        f"```",
        f"Player      |   Δ TVal| +TS|  +TSVal| -TR|   -TRVal",
        f"------------+---------+----+--------+----+---------",
        "\n".join(table),
        f"```",
        f"_This is not a wonky command, but a script written by ItsJustSomeDude. See [the FAQ]({url}) for more info._",
        #f":question:: ||If you're looking to run this script for yourself, be aware that it only works if the Sink is the one running it, and only works on Android.  If interested, ping me.||"
    ]

    return "\n".join(out)

def detailedReport():
    header = "Elapse|# |D|Befor|Chang"
    rowFormat = "`{:6d}|{:2d}|{:1s}|{:5.2f}|{:s}{:4.2f}|`{:s}" #    {:<12.12s}|{:9.3f}|{:4d}|{:8.3f}|{:4d}|{:9.3f}"

    if startTime == "" or endTime == "":
        return "Start and End times are required to generate detailed report!"

    start = ts(startTime)
    end = ts(endTime)

    rows = {}
    cums = {}

    for person in people:
        rows[person] = []
        cums[person] = 0.0

    for ev in events:
        t = ts(ev['time'])
        d = ev['direction']
        c = int(ev['count'])
        p = ev['player']

        ela = t - start
        tv = tval(start, end, t, c)

        sign = ""
        direction = "←"
        if ev['direction'] == 'sent':
            direction = "→"
            sign = "+"
        else:
            tv = tv * -1

        # row = f"<t:{t}:f>`\t|{ela}|{c}|{direction}|{round(cums[p], 2)}|{sign}{round(tv, 2)}`"
        row = rowFormat.format(ela, c, direction, cums[p], sign, tv, f"<t:{t}:f>")
        rows[p].append(row)

        cums[p] += tv

    table = ["# __Tokification Detailed Report__",
        "Key:",
        "`Time (timeElapsed): count ↔ direction: runningDelta ±change`\n",
    ]
    for person in people:
        table.append(f"__{person}__")
        table.append(f"`{header}`")
        table.append("\n".join(rows[person]))
        table.append(f"Final TVal: `{round(cums[person], 2)}`")
        table.append("")

    print(table)
    return "\n".join(table)

def copyReport():
    processAllNotes()
    rep = report()
    ui.copy(rep)

def sendToken(count = 0):
    sendTo = ""
    sendAmount = 0
    sendTime = int(time.time())

    person = selectPlayer()
    if not person:
        return

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
            newPerson = "SpeedySoul"
        person = newPerson
    return person

def mainMenu():
    script = f"python {os.path.abspath(__file__)}"
    noteCmd = [
        "termux-notification",
        "-t", "Tokification.py",
        "-i", "tok_egg_py",
        "-c", "Click to open the Tokification menu.",
        "--action", f"{script} ui",
        "--button1", "Send 6",
        "--button1-action", f"{script} send-6",
        "--button2", "Send Other",
        "--button2-action", f"{script} send",
        "--button3", "Copy Report",
        "--button3-action", f"{script} copy-report"
    ]

    if not cli:
        try:
            subprocess.run(noteCmd)
        except subprocess.CalledProcessError as e:
            print("Timed Out creating notification:", e)

    reply = ui.radio("Tokification.py", [
        "Send Tokens",
        "Generate Report",
        "Generate Detailed Report",
        "Edit Events",
        f"Start Time: {extDate(startTime)}",
        f"End time: {extDate(endTime)}",
        f"Coop: {selectedCoop}",
        f"Player Name: {sink}"
    ])
    if not reply:
        return

    index = reply['index']
    if index == 0:
        processArg("send")
    elif index == 1:
        processArg("copy-report")
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

def changeSink():
    global sink
    newStr = ui.string("Player Name:")
    if not newStr:
        return

    sink = newStr
    saveConfig()

def processArg(arg):
    if arg == "ui":
        mainMenu()
    elif arg == "send":
        processAllNotes()
        sendToken()
    elif arg == "send-6":
        processAllNotes()
        sendToken(6)
    elif arg == "report":
        processAllNotes()
        print(report())
    elif arg == "copy-report":
        copyReport()
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
    else:
        print('Must pass a valid command!')

def loadConfig():
    global sink
    global selectedCoop
    global coopFile

    if os.path.exists(configFile):
        with open(configFile, 'r') as file:
            data = json.load(file)
            selectedCoop = data['coop']
            sink = data['sinkName']

            coopFile = os.path.join(cwd, f"./coops/{ selectedCoop }.json")
    else:
        saveConfig()
        loadConfig()

def saveConfig():
    with open(configFile, 'w') as file:
        json.dump({
            'sinkName': sink,
            'coop': selectedCoop
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
