#!/usr/bin/env python

import json
import os
import subprocess
import datetime
import re
import time
import math
import sys

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

# Date/Time Format Strings
intFormat = "%Y-%m-%d %H:%M:%S"
extFormat = "%b %d %I:%M %p"

def ts(dateStr):
    try:
        dt = datetime.datetime.strptime(dateStr, intFormat)
        return int(dt.timestamp())
    except ValueError:
        print("Invalid date string format:", dateStr)
        return None

def unts(timestamp):
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime(intFormat)
    except ValueError:
        print("Invalid timestamp:", timestamp)
        return None

def extDate(input):
    try:
        if isinstance(input, int):
            input = unts(time)

        dt = datetime.datetime.strptime(input, intFormat)
        return dt.strftime(extFormat)
    except ValueError:
        print("Invalid timestamp:", input)
        return None

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
    if len(sys.argv) > 2:
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

    for ev in sorted(events, key=lambda x: x["time"]):
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

    for ev in sorted(events, key=lambda x: x["time"]):
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
    copy(rep)

def copy(str):
    print(str)
    subprocess.run(["termux-clipboard-set", str])

def askDateTime():
    try:
        output = subprocess.check_output(["timeout", "120", "termux-dialog", "date", "-d", "yyyy-MM-dd"], text=True)
        reply = json.loads(output)
        #print(reply)

        if reply['code'] != -1:
            return

        output2 = subprocess.check_output(["timeout", "120", "termux-dialog", "time", ], text=True)
        reply2 = json.loads(output2)
        #print(reply)

        if reply2['code'] != -1:
            return

        return f"{reply['text']} {reply2['text']}:00"
    except subprocess.CalledProcessError as e:
        return None

def askString(title):
    try:
        output = subprocess.check_output(["timeout", "120", "termux-dialog", "text", "-t", title], text=True)
        reply = json.loads(output)

        if reply['code'] != -1:
            return None

        return reply['text']
    except subprocess.CalledProcessError as e:
        return None

def toast(message):
    try:
        subprocess.run(["termux-toast", message])
    except subprocess.CalledProcessError as e:
        print("Toast Failed:", message)

def sendToken(count = 0):
    sendTo = ""
    sendAmount = 0
    sendTime = int(time.time())

    try:
        # try catch this
        output = subprocess.check_output(["timeout", "120", "termux-dialog", "spinner", "-t", "Sending Tokens to...", "-v", ",".join(people) + ",Other"], text=True)
        reply = json.loads(output)
        #print(reply)

        if reply['code'] != -1:
            return

        if count == 0:
            output2 = subprocess.check_output(["timeout", "120", "termux-dialog", "spinner", "-t", "Tokens Count:", "-v", "1,2,3,4,5,6,7,8,9,10"], text=True)
            reply2 = json.loads(output2)
            #print(reply)

            if reply2['code'] != -1:
                return
            count = int(reply2['text'])

        person = reply['text']

        if person == 'Other':
            newPerson = askString('Enter Name:')
            if not newPerson:
                newPerson = "SpeedySoul"
            person = newPerson

        addEvent(sendTime, count, 'received', person, 0)
        saveCoop()

        toast(f"Recorded {count} tokens to {person}")
    except subprocess.CalledProcessError as e:
        print("Send Timeout.")

def ui():
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
    uiCmd = [
        "timeout", "120",
        "termux-dialog", "radio",
        "-t", "Tokification.py",
        "-v", ",".join([
            "Send Tokens",
            "Generate Report",
            "Generate Detailed Report",
            "Edit Events",
            f"Start Time: {extDate(startTime)}",
            f"End time: {extDate(endTime)}",
            f"Coop: {selectedCoop}",
            f"Player Name: {sink}"
        ])
    ]
    #print(noteCmd)

    try:
        subprocess.run(noteCmd)
        out = subprocess.check_output(uiCmd)
        reply = json.loads(out)
    except subprocess.CalledProcessError as e:
        print("Timed Out.", e)
        return

    if reply['code'] != -1 or 'index' not in reply:
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
    elif index == 4:
        processArg("start-time")
        ui()
    elif index == 5:
        processArg("end-time")
        ui()
    elif index == 6:
        processArg("change-coop")
        ui()
    elif index == 7:
        processArg("change-sink")
        ui()

def askEndTime():
    global endTime
    newTime = askDateTime()
    if not newTime:
        return

    print("Updating time to " + newTime)
    endTime = newTime
    saveCoop()

def askStartTime():
    global startTime
    newTime = askDateTime()
    if not newTime:
        return

    print("Updating time to " + newTime)
    startTime = newTime
    saveCoop()

def changeCoop():
    global selectedCoop
    newStr = askString("Coop code:")
    if not newStr:
        return

    selectedCoop = newStr
    saveConfig()

def changeSink():
    global sink
    newStr = askString("Player Name:")
    if not newStr:
        return

    sink = newStr
    saveConfig()

def processArg(arg):
    if arg == "ui":
        ui()
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
        copy(detailedReport())
    elif arg == "change-coop":
        changeCoop()
    elif arg == "change-sink":
        changeSink()
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
            events = data['events']
            people = data['people']
            startTime = data['startTime']
            endTime = data['endTime']

            for ev in events:
                ids.append(ev['id'])
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
            'people': people,
            'startTime': startTime,
            'endTime': endTime,
        }, f, indent=4)

loadConfig()
loadCoop()

if len(sys.argv) < 2:
    processArg("ui")
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
