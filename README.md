# Tokification

## Script to track Token Values for Egg, Inc Speedruns

This is a Real-Time Token Value Tracker for Egg, Inc. Contract Speedruns. If the Sink is running it, all players TVals are tracked, but individual players can also run it to track their own.

The script is written in Python, and designed to run inside the Termux app. Termux must be installed from GitHub or from F-Droid as the Play Store version is no longer updated. Termux API is also required for GUIs and Notification access.

There is no support for iOS, but if you know of a way for an App to get a list of all notifications (not just ones posted by that App), please contact me!

### Setup

1. Install Termux from [GitHub Releases](https://github.com/termux/termux-app/releases/latest) or [F-Droid](https://f-droid.org/en/packages/com.termux/) (Recommended).
2. Install Termux API from [GitHub Releases](https://github.com/termux/termux-api/releases/latest) or [F-Droid](https://f-droid.org/en/packages/com.termux.api/).  Must be from the same source as step 1.
3. Open Termux and install the required packages: `pkg update; pkg install git python3 termux-api`
4. Run each of `termux-notification-list`, `termux-notification`, `termux-dialog`, and `termux-clipboard-set "Test"` once to setup the required permissions.
   - `notification-list` is used to read Egg, Inc's notifications to track received tokens.
   - `notification` is used to post a notification with buttons for triggering the program.
   - `dialog` is used to make the on-screen dialogs.
   - `toast` is used to show quick messages and confirmations.
5. Download tokification: `git clone https://github.com/ItsJustSomeDude/Tokification`
6. Run it! `cd Tokification; python main.py`
7. This will open the Main Menu. Choose "Player" and enter your In-game name.
   - You should now also have a notification in the drawer that can be clicked to open the Main Menu again. There are also quick buttons for sending tokens or generating a report.
   - Make sure Egg, Inc's notifications are enabled. They can be set to Silent, but they must be visible in the drawer for this to work.

### GUI Usage

This script is designed to be run by the Token Broker/Sink to track the Token Values (TVal) of all the players in the Co-op. It _can_ also be used to track your own TVal if you're not the sink as well.

As the sink, when you're ready to start tracking tokens, open the Main Menu and enter the Co-op Code you want to track. When you send a player their tokens, choose "Send 6" or "Send Other" from the Notification, or "Send Tokens" from the Main Menu. Choose the player who received the Tokens, and the number of tokens sent (unless you chose "Send 6"). If the player is not in the list, choose "Other" and enter their In-Game Name. A toast will appear confirming the player and count that was recorded.

If you're not the sink, set the co-op code same as above, and change the Mode to "standard" from the main menu. Your TVal info will then be shown in the notification, and the Report on the main menu will just show your values.

Once you have an End Time estimation, enter it on the Main Menu. If the Start Time is incorrect, enter this as well. Next, choose "Generate Report" from the Main Menu or "Copy Report" from the notification. The report will be copied to your device's clipboard. This is pre-formatted for posting on Discord, so can be directly pasted into a message and sent.

#### Important Note

Android seems to prevent any individual app from posting more than ~45 notifications at a time. If this limit is hit, the oldest ones from that app will be silently dropped. So, if you're in a medium-large co-op (>5 players) make sure to generate a report _before_ Egg, Inc. hits that limit, otherwise the earliest tokens will not be recorded or tracked.

I recommend generating a report about every 15 minutes, or more often if in a VERY large co-op (30+ players). 

### CLI usage (Advanced)

You can call the script with Command Line Args to trigger certain menus.

```bash
python main.py <arg>
```

Where `<arg>` is one of `{ ui, send, send-1, send-6, report, copy-report, d-report, edit, start-time, end-time, change-coop, change-sink, notification }`. These map to many of the same actions on the main menu.

There is also a text-based UI that can be used over SSH if you play with a phone and computer at the same time. If called with the argument 'cli', this UI will be used instead of on-device dialogs.

```bash
python main.py cli
# or
python main.py cli <arg>
```

Follow the directions on the [Termux Wiki](https://wiki.termux.com/wiki/Remote_Access#Using_the_SSH_server) for instructions on how to setup SSH. If called in a shell running over SSH, the CLI will be used by default.

### Help

I am ItsJustSomeDude on the main Egg, Inc. Discord server, and can be pinged or DMed from there. Feel free to open a GitHub issue as well.

Special Thanks to The Majeggstics for getting me into Speedrunning!
