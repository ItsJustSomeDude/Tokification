# Tokification FAQ

Tokification is a program designed for Speedrun co-ops to help track player's Token Values (TVals). TVal is important for leaderboard players in maxing the Contribution part of the Contract Scoring formula.  Tokification leverages information the Token Sink has to track everyone's TVal in real time.

## What is TVal?

In a co-op, there is a hidden number called the Current Token Value. This value is `1.0` at the very beginning of the co-op, and goes down over time until it reaches `0.03`. Each player also has their own value called their Delta Token Value (ΔTVal). Each player's Delta starts at `0`, and increases or decreases when that player sends or receives tokens.

In order to maximize score, a player's ΔTVal must be above `3.0` at the end of the contract (yellow scroll). Do note that in some contracts with long completion times and/or very short token timers, the Target ΔTVal may be higher than `3.0`.

## How is TVal Calculated?

When a player sends a token, the Current TVal is added to their Delta. When a player receives a token, the Current TVal is subtracted from their Delta. If multiple are transacted at once, the Current TVal is multiplied by the number of tokens sent or received. So for example, if Jimothy receives 3 tokens when the Current TVal is `0.5`, and his ΔTVal was at `0`, his new ΔTVal will be `-1.5`.

The Current TVal is based on two numbers: The Elapsed Time (in seconds) into the contract the token was sent at, and the length of the contract. This makes a challenge for real-time tracking because the End Time, and thus Length, cannot be known for certain. As such, an estimate will be used once a reliable one is available. However, this means that if the End Time Estimate changes, all the calculated Token Values will change accordingly.

## How do I track my TVal?

Good news! If you were linked this message by the Token Sink of your coop, it's _probably_ already being tracked for you! Check for your name in the table and you should see your Delta in the table, along with a breakdown of the values from sending and receiving tokens. The "Running TVal" shows the Current TVal, as well as what it will be 30 and 60 minutes from now.

If you don't have that luxury, there is [a tool created by Chris 💜](https://t-farmer.gigalixirapp.com/) to help you. To use it, enter the Start Time of your Co-op, and click the corresponding Send/Receive button foe each token you send or receive. Once you have an estimated End Time this can be entered as well. 

## Can I use this for my co-ops?

Tokification works by tracking information only available to the Token Broker/Sink. As of now, it only runs on Android. So if you often play as the sink, and use Android, give me (@) a ping.

There is work being done to make it be able to track your own tokens if you're not the sink. Check back here later for updates.

It _may_ be possible to make a version that runs on Apple devices if an app has a way to read Egg, Inc's System notifications. If you're an iOS App Dev, and you are able to write code that does this, please get in touch!

Feel free to ping me (@) with any questions or comments.
