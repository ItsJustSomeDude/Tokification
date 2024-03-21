from datetime import datetime

# Date/Time Format Strings
intFormat = "%Y-%m-%d %H:%M:%S"
extFormat = "%b %d %I:%M %p"

def ts(dateStr):
    try:
        dt = datetime.strptime(dateStr, intFormat)
        return int(dt.timestamp())
    except ValueError:
        print("Invalid date string format:", dateStr)
        return None

def unts(timestamp):
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime(intFormat)
    except ValueError:
        print("Invalid timestamp:", timestamp)
        return None

def extDate(input):
    try:
        if isinstance(input, int):
            input = unts(time)

        dt = datetime.strptime(input, intFormat)
        return dt.strftime(extFormat)
    except ValueError:
        print("Invalid timestamp:", input)
        return None
