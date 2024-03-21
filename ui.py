import subprocess
import json
import datetime

class TermuxUI:
    def __init__(self):
        print("Setting up Termux for UI.")

    def _dialog(self, type, title = "", args = []):
        try:
            output = subprocess.check_output([
                "timeout", "120",
                "termux-dialog", type,
                "-t", title
            ] + args, text=True)
            reply = json.loads(output)

            if reply['code'] != -1 and reply['code'] != 0:
                return None

            return reply
        except subprocess.CalledProcessError as e:
            return None

    def date(self, title):
        reply = self._dialog("date", title, [
            "-d", "yyyy-MM-dd"
        ])
        if not reply: return None
        return reply['text']

    def time(self, title):
        reply = self._dialog("time", title)
        if not reply: return None
        return reply['text']

    def dateTime(self, title):
        date = self.date(title)
        if not date: return None

        time = self.time(title)
        if not time: return None

        return f"{date} {time}:00"

    def string(self, title, hint = ''):
        reply = self._dialog("text", title, [
            "-i", hint
        ])
        if not reply: return None
        return reply['text']

    def number(self, title, min = -1000, max = 1000, start = 0):
        reply = self._dialog("counter", title, [
            "-r", f"{min},{max},{start}"
        ])
        if not reply: return None
        return int(reply['text'])

    def radio(self, title, options):
        reply = self._dialog("radio", title, [
            "-v",
            ",".join(options)
        ])
        if not reply or not 'index' in reply:
            return None
        return { 'index': reply['index'], 'text': reply['text'] }

    def list(self, title, options):
        reply = self._dialog("spinner", title, [
            "-v",
            ",".join(options)
        ])
        if not reply or not 'index' in reply:
            return None
        return { 'index': reply['index'], 'text': reply['text'] }

    def yesno(self, title, text = ""):
        reply = self._dialog("confirm", title, [
            "-i", text
        ])
        if not reply:
            return None
        elif reply['text'] == "yes":
            return True
        elif reply['text'] == "no":
            return False
        else:
            return None

    def info(self, title, text = ""):
        self.yesno(title, text)
        return None

    def toast(self, text):
        try:
            subprocess.run(["termux-toast", text])
        except subprocess.CalledProcessError as e:
            print("Info:", text)

    def copy(self, str):
        print(str)
        subprocess.run(["termux-clipboard-set", str])

class TextUI:
    def __init__(self):
        print("Setting up CLI.")

    def _prompt(self, title, hint):
        print(title)
        reply = input(f"({hint}): ")
        if reply.strip() == "":
            return None
        return reply

    def date(self, title):
        year = datetime.datetime.now().strftime("%Y")
        while True:
            reply = self._prompt(title, "Date - MM/DD or MM/DD/YY")
            if not reply:
                reply = datetime.datetime.now().strftime("%m-%d-%Y")
            reply = reply.replace("/", "-")

            try:
                d = datetime.datetime.strptime(reply, "%m-%d-%Y")
            except ValueError:
                try:
                    d = datetime.datetime.strptime(reply, "%m-%d-%y")
                except ValueError:
                    try:
                        d = datetime.datetime.strptime(f"{reply}-{year}", "%m-%d-%Y")
                    except ValueError:
                        continue

            return d.strftime("%Y-%m-%d")

    def time(self, title):
        formats = [
            "%H:%M "
        ]
        while True:
            reply = self._prompt(title, "Time - 5:33pm or 17:33")
            if not reply:
                reply = datetime.datetime.now().strftime("%H:%M")
            reply = reply.replace(" ", "")

            try:
                d = datetime.datetime.strptime(reply, "%H:%M")
            except ValueError:
                try:
                    d = datetime.datetime.strptime(reply, "%I:%M%p")
                except ValueError:
                    try:
                        d = datetime.datetime.strptime(f"{reply}m", "%I:%M%p")
                    except ValueError:
                        continue

            return d.strftime("%H:%M")

    def dateTime(self, title):
        date = self.date(title)
        if not date: return None

        time = self.time(title)
        if not time: return None

        return f"{date} {time}:00"

    def string(self, title, hint = ''):
        return self._prompt(title, hint)

    def number(self, title, min = -1000, max = 1000, start = 0):
        while True:
            reply = self._prompt(title, f"{min}..{max}, default={start}")
            if not reply:
                return start

            try:
                num = int(reply)
            except ValueError:
                continue

            if num < min or num > max:
                continue

            return num

    def radio(self, title, options):
        opts = [title,  "===================="]
        i = 1
        for o in options:
            opts.append(f"{i}. {o}")
            i += 1

        count = len(options)

        while True:
            reply = self._prompt(
                "\n".join(opts),
                f"Enter 1..{count}, 0 to cancel"
            )
            if not reply:
                continue

            try:
                num = int(reply)
            except ValueError:
                continue

            if num == 0:
                return None

            if num < 1 or num > count:
                continue

            return { 'index': num - 1, 'text': options[num - 1] }

    def list(self, title, options):
        return self.radio(title, options)

    def yesno(self, title, text = ""):
        while True:
            reply = self._prompt(f"{title}\n{text}", "y/n")
            if reply in ['y', 'Y', 'Yes', 'yes']:
                return True
            elif reply in ['n', 'N', 'No', 'no']:
                return False

    def info(self, title, text = ""):
        print(title, '\n', text)

    def toast(self, text):
        print(text)

    def copy(self, str):
        print(str)


if __name__  == '__main__':
    tui = TextUI()
    gui = TermuxUI()

    toTest = tui.radio("Choose a test.", [
        "GUI Date",
        "GUI Time",
        "GUI Date/Time",
        "GUI String",
        "GUI Number",
        "GUI Radio",
        "GUI List",
        "GUI Yes/No",
        "GUI Info",
        "GUI Toast",

        "TUI Date",
        "TUI Time",
        "TUI Date/Time",
        "TUI String",
        "TUI Number",
        "TUI Radio",
        "TUI List",
        "TUI Yes/No",
        "TUI Info",
        "TUI Toast",
    ])
    print(toTest)
    i = toTest['index']

    if i == 0:
        print(gui.date("GUI Date Test"))
    elif i == 1:
        print(gui.time("GUI Time Test"))
    elif i == 2:
        print(gui.dateTime("GUI Date+Time Test"))
    elif i == 3:
        print(gui.string("GUI String Test", "Prefilled"))
        print(gui.string("GUI String Test 2"))
    elif i == 4:
        print(gui.number("GUI Number Test"))
        print(gui.number("GUI Number Test 2", -20))
        print(gui.number("GUI Number Test 3", -20, 20))
        print(gui.number("GUI Number Test 4", -20, 20, 10))
    elif i == 5:
        print(gui.radio("GUI Radio Test", []))
        print(gui.radio("GUI Radio Test", ["Opt1"]))
        print(gui.radio("GUI Radio Test", ["Opt1","2","3"]))
    elif i == 6:
        print(gui.list("GUI List Test", []))
        print(gui.list("GUI List Test", ["Opt1"]))
        print(gui.list("GUI List Test", ["Opt1","2","3"]))
    elif i == 7:
        print(gui.yesno("GUI Yes/No Test"))
        print(gui.yesno("GUI Yes/No Test", 'Opt. String'))
        print(gui.yesno("GUI Yes/No Test", 'Opt. String w/ new\nLine'))
    elif i == 8:
        print(gui.info("GUI Info Test"))
        print(gui.info("GUI Info Test", 'Opt. String'))
        print(gui.info("GUI Info Test", 'Opt. String w/ new\nLine'))
    elif i == 9:
        print(gui.toast("GUI Toast Test"))

    elif i == 10:
        print(tui.date("GUI Date Test"))
    elif i == 11:
        print(tui.time("GUI Time Test"))
    elif i == 12:
        print(tui.dateTime("GUI Date+Time Test"))
    elif i == 13:
        print(tui.string("GUI String Test", "Prefilled"))
        print(tui.string("GUI String Test 2"))
    elif i == 14:
        print(tui.number("GUI Number Test"))
        print(tui.number("GUI Number Test 2", -20))
        print(tui.number("GUI Number Test 3", -20, 20))
        print(tui.number("GUI Number Test 4", -20, 20, 10))
    elif i == 15:
        print(tui.radio("GUI Radio Test", []))
        print(tui.radio("GUI Radio Test", ["Opt1"]))
        print(tui.radio("GUI Radio Test", ["Opt1","2","3"]))
    elif i == 16:
        print(tui.list("GUI List Test", []))
        print(tui.list("GUI List Test", ["Opt1"]))
        print(tui.list("GUI List Test", ["Opt1","2","3"]))
    elif i == 17:
        print(tui.yesno("GUI Yes/No Test"))
        print(tui.yesno("GUI Yes/No Test", 'Opt. String'))
        print(tui.yesno("GUI Yes/No Test", 'Opt. String w/ new\nLine'))
    elif i == 18:
        print(tui.info("GUI Info Test"))
        print(tui.info("GUI Info Test", 'Opt. String'))
        print(tui.info("GUI Info Test", 'Opt. String w/ new\nLine'))
    elif i == 19:
        print(tui.toast("GUI Toast Test"))
