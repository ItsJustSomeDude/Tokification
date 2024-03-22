import time
from date import ts

def tval(start, end, token, count):
    i = (1 - 0.9 * ((token - start) / (end - start))) ** 4
    return max(i, 0.03) * float(count)

def report(events, people, sink="sink", startTime="", endTime=""):
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

        tv = tval(start, end, t, c)
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

def detailedReport(events, people, sink="sink", startTime="", endTime=""):
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

def simpleReport(events, startTime="", endTime=""):
    now = int(time.time())

    est = ""
    if startTime == "":
        sinceHourStart = now % 3600
        start = now - sinceHourStart
        est += "(Unknown Start)"
    else:
        start = ts(startTime)

    if endTime == "":
        end = start + 12 * 60 * 60
        est += "(Assuming 12 hour Duration)"
    else:
        end = ts(endTime)

    tokensSent = 0
    tvalSent = 0.0
    tokensRec = 0
    tvalRec = 0.0

    for ev in events:
        t = ts(ev['time'])
        d = ev['direction']
        c = int(ev['count'])

        tv = tval(start, end, t, c)
        if d == 'sent':
            tokensRec += c
            tvalRec += tv
        else:
            tokensSent += c
            tvalSent += tv

    tvNow = round(tval(start, end, now, 1), 4)
    if now > end:
        tvNow = "Co-op Ended."

    out = "\n".join([
        f"Your ΔTVal: {round(tvalSent - tvalRec, 4)} {est}",
        f"TVal Now: {tvNow} {est}",
        f"Sent TVal: {round(tvalSent, 4)} ({tokensSent} tokens)",
        f"Received TVal: -{round(tvalRec, 4)} ({tokensRec} tokens)"
    ])

    return out
