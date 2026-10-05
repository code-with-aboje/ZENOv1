from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv, PairStatusEv
from time import sleep
import threading
import os
import random
import json
import shutil
from neonize.utils import build_jid
from neonize.utils.enum import ParticipantChange
import re

LINK_EXTS = ["com", "net", "info", "co", "io", "me", "tv", "xyz", "online",
             "site", "store", "shop", "app", "dev", "link", "live", "club", "top",
             "ng", "us", "uk", "gh", "za", "ke", "vercel.app", "netlify.app", "github.io"]

link_pattern = re.compile(
    r"(https?://|www\.)\S+|\b[\w-]+\.(" + "|".join(LINK_EXTS) + r")\b",
    re.IGNORECASE,
)

DATA_DIR = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", ".")
DB_FILE = os.path.join(DATA_DIR, "db.json")
SESSION_FILE = os.path.join(DATA_DIR, "bot.sqlite3")

# first run on the volume: create the leaderboard file
if not os.path.exists(DB_FILE):
    if os.path.exists("db.json"):
        shutil.copy("db.json", DB_FILE)
    else:
        with open(DB_FILE, "w") as f:
            json.dump({"leaderboard": []}, f)

first_time = not os.path.exists(SESSION_FILE)   # check BEFORE making client
client = NewClient(SESSION_FILE)
PHONE = "2347075635330"

@client.event(ConnectedEv)
def on_connected(client, event):
    print("Connected ✅")

@client.event(PairStatusEv)
def on_pair(client, event):
    print("Paired ✅")

ADMINS = ["24378754511092","177069002625201"]
#EMOJIS
# HAPPPY
happy = ["😀", "😄", "😊", "😎"]
laughing = ["😂", "😅"]
crying = ["😭"]    
sad =["😔", "🥺", "😢"]
silly = ["😝", "😜", "🤭"]
shocked = ["😱", "😮", "😳"]

#=== GAME ===
words = [
    "algorithm", "bandwidth", "cybersecurity", "database", "firewall",
    "hardware", "malware", "software", "api", "information",
    "python", "compiler", "variable", "function", "network",
    "protocol", "encryption", "password", "server", "browser",
    "router", "kernel", "terminal", "script", "payload",
    "exploit", "phishing", "botnet", "backdoor", "sandbox",
    "debugger", "framework", "library", "binary", "boolean",
    "integer", "string", "array", "syntax", "cache",
    "cookie", "domain", "gateway", "hashing", "keylogger",
    "packet", "proxy", "ransomware", "rootkit", "session",
    "socket", "token", "trojan", "virus", "website",
    "wireless", "firmware", "hacker", "linux", "android"
]
#===== GAME STORAGE ======
games ={}

#=== RANKS ====
noob = "NOOB"
rookie = "ROOKIE"
script = "SCRIPT KIDDIE"
red = "RED TEAMER"
pro = "PRO"
veteran = "VETERAN"
elite = "ELITE"
mythic = "MYTHIC"

def get_rank(points):
    if points >= 20000:
        return mythic
    elif points >= 15000:
        return elite
    elif points >= 10000:
        return veteran
    elif points >= 5000:
        return pro
    elif points >= 3000:
        return red
    elif points >= 1500:
        return script
    elif points >= 500:
        return rookie
    else:
        return noob

#====== SCRAMBLE ======
def scramble_start(client, event):
    # get chat id#waits 30 seconds before initializing game 
    chat = event.Info.MessageSource.Chat.User
     
    if chat in games:
        client.reply_message("⚠️ A game is already running here!", event)
        return
    games[chat] = {
        "players": [],
        "state": "lobby",
         "turn": 0,
        "answer": "",
        "used": [],
        "final": False,
        "round": 1,
        "mode": "scramble"
    }
    client.reply_message("*🎮 Scramble lobby open! Type !join in 30 seconds.*", event)
    threading.Timer(15, warn, args=(client, event, chat)).start()
    threading.Timer(30, scramble_begin, args=(client, event, chat)).start()  

def scramble_join(client, event):
    #get sender and chat ID
    user = event.Info.MessageSource.Sender.User
    chat = event.Info.MessageSource.Chat.User
    chat_jid = event.Info.MessageSource.Chat

    if chat not in games or games[chat]["state"] != "lobby":
        client.reply_message("*⚠️ No lobby is oPened!*", event)
        return
    
    if user in games[chat]["players"]:
        client.reply_message("*⚠️ You already joined!*", event)
        return
    games[chat]["players"].append(user)
    tags = "\n".join(f"@{u}" for u in games[chat]["players"])
    client.send_message(chat_jid, f"*PLAYERS 🎮:*\n{tags}", mentions_are_lids=True)

#=== SCRAMBLE WORDS ===
def make_scramble(used):
    if len(used) >= len(words):
        used.clear()
    word = random.choice(words)
    while word in used:
        word = random.choice(words)
    letters = list(word)
    random.shuffle(letters)
    while "".join(letters) == word:
        random.shuffle(letters)
    return word, "".join(letters)

    
def scramble_begin(client, event, chat):
   
    #gets users jid
    chat_jid = event.Info.MessageSource.Chat

    #checks for game user amount
    if len(games[chat]["players"]) < 2:
        del games[chat]
        client.reply_message("*❌ Not enough players. Game cancelled.*", event)
        return
    games[chat]["state"] = "playing"
    client.reply_message("*🔥 Game starting!*", event)
    send_next(client, event, chat)


def warn(client, event, chat):
    if chat not in games:
        return
    client.reply_message("*⏳ 15 seconds left to join!*", event)

def time_up(client, event, chat, player):
    if chat not in games:
        return
    game = games[chat]
    if player not in game["players"] or game["players"][game["turn"]] != player:
        return

    chat_jid = event.Info.MessageSource.Chat

    # final word failed -> tie
    if game["final"]:
        client.send_message(chat_jid, "🤝 *It's a tie!* Nobody wins this round.")
        del games[chat]
        return

    out = game["players"].pop(game["turn"])
    client.send_message(chat_jid, f"⏳ Time's up! @{out} is out ❌", mentions_are_lids=True)

    # one player left -> final word
    if len(game["players"]) == 1:
        game["final"] = True
        game["turn"] = 0
        last = game["players"][0]
        client.send_message(chat_jid, f"🔥 *FINAL WORD!* @{last}, answer correctly to win", mentions_are_lids=True)
        send_next(client, event, chat)
        return
    
    if game["turn"] >= len(game["players"]):
        game["turn"] = 0
        game["round"] += 1
        client.send_message(chat_jid, f"🔥 *ROUND {game['round']}!* Timer is now {round_seconds(game['round'])}s ⏳")
    send_next(client, event, chat)

def round_seconds(round_num):
    return max(10, 45 - round_num * 5) 

def next_turn(client, event, chat):
    chat_jid = event.Info.MessageSource.Chat
    game = games[chat]
    player = game["players"][game["turn"]]
    seconds = round_seconds(game["round"])
    next_player = game["players"][(game["turn"] + 1) % len(game["players"])]
    word, scrambled = make_scramble(game["used"])
    spaced = " ".join(scrambled.upper())
    game["used"].append(word)
    game["answer"] = word
    game["timer"] = threading.Timer(seconds, time_up, args=(client, event, chat, player))
    next_line = "" if game["final"] else f"\n⏭️ Next Player: @{next_player}"
    client.send_message(chat_jid, f"🎯 @{player}, unscramble: *{spaced}* ({seconds}s){next_line}", mentions_are_lids=True)
    game["timer"].start()

def check_answer(client, event, chat, text):
    sender = event.Info.MessageSource.Sender.User
    game = games[chat]
    player = game["players"][game["turn"]]
    if player != sender:
        return
    answers = game["answer"] if isinstance(game["answer"], list) else [game["answer"]]
    if text.lower().strip() in answers:
        client.reply_message("*✅ Correct!*", event)
        game["timer"].cancel()

        if game["final"]:
            chat_jid = event.Info.MessageSource.Chat
            winner = player
            client.send_message(chat_jid, f"🏆 @{winner} wins! +10 points", mentions_are_lids=True)

            with open(DB_FILE, "r") as f:
                data = json.load(f)
            for p in data["leaderboard"]:
                if p["id"] == winner:
                    p["points"] += 10
                    old_rank = p["rank"]
                    p["rank"] = get_rank(p["points"])
                    if p["rank"] != old_rank:
                        client.send_message(chat_jid, f"🎉 *RANK UP!* @{winner} is now *{p['rank']}* 🔥", mentions_are_lids=True)
                    break
            with open(DB_FILE, "w") as f:
                json.dump(data, f, indent=2)

            del games[chat]
            return

        game["turn"] += 1
        if game["turn"] >= len(game["players"]):
            game["turn"] = 0
            game["round"] +=1
            client.send_message(event.Info.MessageSource.Chat, f"🔥 *ROUND {game['round']}!* Timer is now {round_seconds(game['round'])}s ⏳")
        send_next(client, event, chat)


#====== BATTLE ROYAL ======
riddles = [
    {"q": "What has keys but can't open locks?", 
     "a": ["piano", "keyboard"]},
    {"q": "What has hands but can't clap?",
     "a": ["clock", "watch"]},
    {"q": "What gets wetter the more it dries?",
     "a": ["towel"]},
    {"q": "What has a head and a tail but no body?",
     "a": ["coin"]},
    {"q": "What can you catch but not throw?",
     "a": ["cold"]},
    {"q": "What has teeth but can't bite?",
     "a": ["comb"]},
    {"q": "What goes up but never comes down?",
     "a": ["age"]},
    {"q": "What has a neck but no head?",
     "a": ["bottle"]},
    {"q": "What runs but never walks?",
     "a": ["water", "river"]},
    {"q": "What has an eye but can't see?",
     "a": ["needle"]},
    {"q": "The more you take, the more you leave behind. What am I?",
     "a": ["footsteps", "steps"]},
    {"q": "What can travel around the world while staying in a corner?",
     "a": ["stamp"]},
    {"q": "What has words but never speaks?",
     "a": ["book"]},
    {"q": "What belongs to you but other people use it more than you?",
     "a": ["name"]},
    {"q": "What building has the most stories?",
     "a": ["library"]},
    {"q": "What breaks the moment you say its name?",
     "a": ["silence"]},
    {"q": "What can fill a room but takes up no space?",
     "a": ["light"]},
    {"q": "I have cities but no houses, mountains but no trees, water but no fish. What am I?",
     "a": ["map"]},
    {"q": "What has a ring but no finger?",
     "a": ["phone", "telephone"]},
    {"q": "What is always in front of you but can't be seen?",
     "a": ["future"]},
    {"q": "What has legs but doesn't walk?",
     "a": ["table", "chair"]},
    {"q": "What has 13 hearts but no other organs?",
     "a": ["cards", "deck of cards", "deck"]},
    {"q": "What has a thumb and four fingers but isn't alive?",
     "a": ["glove"]},
    {"q": "What comes down but never goes up?",
     "a": ["rain"]},
    {"q": "What has a bottom at the top?",
     "a": ["legs", "leg"]},
    {"q": "What goes through cities and fields but never moves?",
     "a": ["road"]},
    {"q": "What is full of holes but still holds water?",
     "a": ["sponge"]},
    {"q": "What has four wheels and flies?",
     "a": ["garbage truck", "trash truck"]},
    {"q": "What begins with T, ends with T, and has T in it?",
     "a": ["teapot"]},
    {"q": "What is easy to lift but hard to throw?",
     "a": ["feather"]},
    {"q": "What invention lets you look right through a wall?",
     "a": ["window"]},
    {"q": "What is always coming but never arrives?",
     "a": ["tomorrow"]},
    {"q": "What month of the year has 28 days?",
     "a": ["all", "all of them", "every month"]},
    {"q": "What is black when clean and white when dirty?",
     "a": ["chalkboard", "blackboard"]},
    {"q": "What gets bigger the more you take away from it?",
     "a": ["hole"]},
    {"q": "What is lighter than a feather, yet the strongest man can't hold it for long?",
     "a": ["breath"]},
    {"q": "What flies without wings?",
     "a": ["time"]},
    {"q": "What can be cracked, made, told, and played?",
     "a": ["joke"]},
    {"q": "What goes up and down without moving?",
     "a": ["stairs", "staircase"]},
    {"q": "What has a mouth but never eats?",
     "a": ["river"]},
    {"q": "What word is spelled wrong in every dictionary?",
     "a": ["wrong"]},
    {"q": "What starts with E, ends with E, but only has one letter in it?",
     "a": ["envelope"]},
    {"q": "What kind of room has no doors or windows?",
     "a": ["mushroom"]},
    {"q": "What can you keep after giving it to someone?",
     "a": ["word", "promise"]},
    {"q": "What has a tongue but can't talk?",
     "a": ["shoe"]},
    {"q": "What has a bark but no bite?",
     "a": ["tree"]},
    {"q": "What kind of band never plays music?",
     "a": ["rubber band", "rubber"]},
    {"q": "What is at the end of a rainbow?",
     "a": ["w"]},
    {"q": "What goes in hard and comes out soft?",
     "a": ["gum", "chewing gum"]},
    {"q": "What two things can you never eat for breakfast?",
     "a": ["lunch and dinner", "lunch", "dinner"]},
    {"q": "What can you see in the middle of March and April that you can't see at the beginning or end of either month?",
     "a": ["r"]},
    {"q": "What has a mouse but never eats cheese?",
     "a": ["computer", "laptop"]},
    {"q": "What do you create to get in, but must keep secret from everyone?",
     "a": ["password"]},
    {"q": "The more of me you have, the less you see. What am I?",
     "a": ["darkness", "dark"]},
    {"q": "What gets sharper the more you use it?",
     "a": ["brain", "mind"]},
    {"q": "What is round, rolls, and has no legs?",
     "a": ["ball", "wheel"]},
    {"q": "What do you throw out when you want to use it, and take back in when you're done?",
     "a": ["anchor"]},
    {"q": "What has branches but no leaves or fruit?",
     "a": ["bank"]},
    {"q": "What has to be broken before you can use it?",
     "a": ["egg"]},
    {"q": "What needs air to live, eats wood, and dies if you give it water?",
     "a": ["fire"]},
]

#1) RIDDLES
def start_riddle(client, event):
    #get chat id
    chat = event.Info.MessageSource.Chat.User
    #check if game already exists
    if chat in games:
        client.reply_message("⚠️ A game is already running here!", event)
        return
    games[chat] = {
        "players": [],
        "state": "lobby",
        "turn": 0,
        "answer": "",
        "used": [],
        "final": False,
        "round": 1,
        "mode": "riddle"
    }
    client.reply_message("*🎮 RIDDLE lobby open! Type !join in 30 seconds.*", event)
    threading.Timer(15, warn, args=(client, event, chat)).start()
    threading.Timer(30, riddle_begin, args=(client, event, chat)).start()


# === RIDDLE BEGIN ===
def riddle_begin(client, event, chat):
    #gets users jid
    chat_jid = event.Info.MessageSource.Chat

    #checks for game user amount
    if len(games[chat]["players"]) < 2:
        del games[chat]
        client.reply_message("*❌ Not enough players. Game cancelled.*", event)
        return
    games[chat]["state"] = "playing"
    client.reply_message("*🔥 Game starting!*", event)
    riddle_next_turn(client, event, chat)

def make_riddle(used):
    if len(used) >= len(riddles):
        used.clear()
    riddle = random.choice(riddles)
    while riddle in used:
        riddle = random.choice(riddles)
    return riddle["q"], riddle["a"], riddle

def riddle_next_turn(client, event, chat):
    chat_jid = event.Info.MessageSource.Chat
    game = games[chat]
    player = game["players"][game["turn"]]
    seconds = round_seconds(game["round"])
    next_player = game["players"][(game["turn"] + 1) % len(game["players"])]
    question, answer, riddle = make_riddle(game["used"])
    game["used"].append(riddle)
    game["answer"] = answer
    game["question"] = question
    game["timer"] = threading.Timer(seconds, time_up, args=(client, event, chat, player))
    next_line = "" if game["final"] else f"\n⏭️ Next Player: @{next_player}"
    client.send_message(chat_jid, f"🎯 @{player}, Riddle: *{question}* ({seconds}s){next_line}", mentions_are_lids=True)
    game["timer"].start()

def send_next(client, event, chat):
    if games[chat]["mode"] == "riddle":
        riddle_next_turn(client, event, chat)
    else:
        next_turn(client, event, chat)
#greeting message
def greet(event):
    try:
        name = event.Info.Pushname
        return f"hey *{name}*"
    except Exception as e:
        return str(e)
#COMMAND LIST
def cmd(client,event):
    message = '''
╔═══════════════╗
║  🤖 *BLUEYVERSE BOT*  ║
║
➤ *prifix: !*
╚═══════════════╝

┏━━ 📌 *INFO* ━━┓
┃ 
┃ ➤ !groups
┃ ➤ !schedule
┃ ➤ !rules
┗━━━━━━━━━━━━━
┏━━  *GAMES* 
┃ ➤ !scramble
┃ ➤ !riddle
┗━━━━━━━━━━━━━
┏━━  *GROUP* 
┃ ➤ !kick
┃ ➤ !lock
┃ ➤ !open
┃ ➤ !del
┃ ➤ !vv
┗━━━━━━━━━━━━━┛
    '''
    client.reply_message(message, event) 

#SCHEDULE
def schedule(client, event):
    message = '''
🎓 *BLUEYVERSE ACADEMY*
Here at BlueyVerse Academy, we're building the next generation of creators and hackers. Here's when to show up 👇

━━━━━━━━━━━━━━━━━━

📅 *CLASS SCHEDULE*

🕵️ *Hacking*
⏰ 9:00 PM - 2:00 AM
🔁 Daily

┏━━📌 *ON STAND BY* ━━┓
┃ ❱🎮 *Game Dev*
┃ ❱🌐 *Web Dev*
┃ ❱📱 *App Dev*
┃ 🚀 *Opening October 10th*
┗━━━━━━━━━━━━━┛

━━━━━━━━━━━━━━━━━━

📍 Classes hold in the group chat
🌍 Time: Nigerian time (WAT)

_Don't miss a class!_ 🔥
'''
    try:
        emotion = random.choice(happy)
        client.reply_message(f"Sure thing! {emotion}",event)
        sleep(0.5)
        client.reply_message(message, event)
    except Exception as e:
        return  "Error" , str(e) 


#=== ACADEMY CURRICULUM === 
def curriculum(client, event):
    emotion = random.choice(happy)
    message = '''
🛡️ ══ HACKING ACADEMY CURRICULUM ══ 🛡️
┃ ➤ NOOB

✦ Basic Python
✦ Bash and Linux basics

📦 Project: Recon Notes Script

• Bash script that creates a folder per target
• Python script that checks if a list of domains is up and saves results to a file

───────────────────────────

┃ ➤ BEGINNER

✦ Networking (TCP/IP, DNS, HTTP, ports)
✦ HTML, JavaScript, and basic SQL
✦ Nmap and Wireshark basics

📦 Project: Port Scanner

• Python socket scanner for your own machine or scanme.nmap.org
• Grabs service banners and prints a clean report

───────────────────────────

┃ ➤ INTERMEDIATE

✦ Web hacking: OWASP Top 10, Burp Suite, PortSwigger labs
✦ Python scripting for recon and automation

📦 Project: Build Your Own Web Scanner

• Python tool that brute-forces hidden paths from a wordlist
• Checks for missing security headers (CSP, X-Frame-Options, etc.) and prints a report

───────────────────────────

┃ ➤ ADVANCED

✦ Mobile hacking: Android APKs, jadx, RATs
✦ CTFs and bug bounty with write-ups

📦 Project: Crack the UnCrackable Apps

• Crack an App
• Build a custom RAT
• Write a walkthrough of how you solved each one

⚔️ ══════════════════════ ⚔️
⚠️ Golden Rule: only test what you own or have permission to test. ~ bluey
'''

    client.reply_message(f"Sure thing boss, give me a sec.. {emotion}", event)
    sleep(1)
    client.reply_message(message,event)

rank_order = [mythic, elite, veteran, pro, red, script, rookie, noob]

def leaderboard(client, event):
    chat_jid = event.Info.MessageSource.Chat
    with open(DB_FILE) as f:
        data = json.load(f)

    message = "*🛡️ ══ LEADERBOARD ══ 🛡️*\n\n"

    for rank in rank_order:
        members = [p for p in data["leaderboard"] if p["rank"] == rank]
        if not members:
            continue
        members.sort(key=lambda p: p["points"], reverse=True)

        message += f"┏━━ *{rank}* ━━┓\n"
        for p in members:
            message += f"┃ ➤ @{p['id']} ➤ *{p['points']}* pts\n"
        message += "┗━━━━━━━━━━━━━┛\n\n"

    client.send_message(chat_jid, message, mentions_are_lids=True)
    
def add_leaderboard(client, event):
    sender = event.Info.MessageSource.Sender.User
    if not sender in ADMINS:
                client.reply_message("*❌ Admins only*", event)
                return
    mentioned = event.Message.extendedTextMessage.contextInfo.mentionedJID
    #checks if someone isnt mentioned
    if not mentioned:
        client.reply_message("*Tag someone: !add @person leaderboard*", event)
        return
    user_id = mentioned[0].split("@")[0]
    #opening DATABASE
    with open(DB_FILE, "r") as f:
        data = json.load(f)

    #loop through database 
    for p in data["leaderboard"]:
        if p["id"] == user_id:
            client.reply_message("*Already on leaderboard!*", event)
            return
    data["leaderboard"].append({"id": user_id, "points": 0 , "rank":  noob})

    with open(DB_FILE, "w") as f:
        #update DB
        json.dump(data, f, indent=2)
    client.reply_message("*Added to Leaderboard✅*", event)
    #leaderboard(client, event)

    
def add_point(client, event, text):
    chat_jid = event.Info.MessageSource.Chat
    mentioned = event.Message.extendedTextMessage.contextInfo.mentionedJID
    sender = event.Info.MessageSource.Sender.User
    if not sender in ADMINS:
             client.reply_message("*❌ Admins only*", event)
             return
    if not mentioned:
        client.reply_message("*Usage: !points @person 5*", event)
        return
    user_id = mentioned[0].split("@")[0]
    
    parts = text.split()
    try:
        points = int(parts[-1])
    except ValueError:
        client.reply_message("*Usage: !points @person 5*", event)
        return

    #open db 
    with open(DB_FILE,"r") as f:
        data = json.load(f)
        for p in data["leaderboard"]:
            if p["id"] == user_id:
                #add points
                p["points"] += points
                break
        else:
            client.reply_message("*❌ Not on the leaderboard. Use !add first.*", event)
            return
    #write to file
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)
    client.reply_message(f"*{points} Points Added!✅*", event)
    #upgrade tier
    with open(DB_FILE,"r") as f:
        data = json.load(f)
        for p in data["leaderboard"]:
            if p["id"] == user_id:
                old_rank = p["rank"]                 # rank before

                if p["points"] >= 20000:
                    new_rank = mythic
                elif p["points"] >= 15000:
                    new_rank = elite
                elif p["points"] >= 10000:
                    new_rank = veteran
                elif p["points"] >= 5000:
                    new_rank = pro
                elif p["points"] >= 3000:
                    new_rank = red
                elif p["points"] >= 1500:
                    new_rank = script
                elif p["points"] >= 500:
                    new_rank = rookie
                else:
                    new_rank = noob

                p["rank"] = new_rank

                if new_rank != old_rank:             # only if it changed
                    client.send_message(chat_jid, f"🎉 *RANK UP!* @{user_id} is now *{new_rank}* 🔥", mentions_are_lids=True)
                break

    with open(DB_FILE, "w") as f:
        json.dump(data, f ,indent=2)
    #leaderboard(client, event)

#kick members
def kick(client, event):
     chat_jid = event.Info.MessageSource.Chat
     sender = event.Info.MessageSource.Sender.User
     if not sender in ADMINS:
         client.reply_message("*❌ Admins only*", event)
         return
     mentioned = event.Message.extendedTextMessage.contextInfo.mentionedJID
     if not mentioned:
            client.reply_message("*Usage: !kick @person*", event)
            return
     user_id = mentioned[0].split("@")[0]
     user_jid = build_jid(user_id, "lid")
     client.update_group_participants(chat_jid, [user_jid], ParticipantChange.REMOVE)
     client.send_message(chat_jid, f"*Successfully kicked @{user_id}*", mentions_are_lids=True)

#group settings
def close_group(client, event):
    sender = event.Info.MessageSource.Sender.User
    chat_jid = event.Info.MessageSource.Chat
    #check if sender is admin
    if sender not in  ADMINS:
        client.reply_message("*⚠️ Admin command only!*", event)
        return
    client.set_group_announce(chat_jid, True)
    client.send_message(chat_jid, "*🔒 Group closed successfully!*")

def open_group(client, event):
    sender = event.Info.MessageSource.Sender.User
    chat_jid = event.Info.MessageSource.Chat
    #checks if sender is admin
    if sender not in  ADMINS:
        client.reply_message("*⚠️ Admin command only!*", event)
        return
    client.set_group_announce(chat_jid, False)
    client.send_message(chat_jid, "*🔓 Group opened successfully!*")

def delete_msg(client, event):
    chat = event.Info.MessageSource.Chat
    context = event.Message.extendedTextMessage.contextInfo
    message_id = context.stanzaID
    sender = context.participant
    sender_jid = build_jid(sender.split("@")[0], "lid")
    client.revoke_message(chat, sender_jid, message_id)

def del_link(client, event):
    try:
        chat_jid = event.Info.MessageSource.Chat
        sender_jid = event.Info.MessageSource.Sender
        message_id = event.Info.ID

        client.revoke_message(chat_jid, sender_jid, message_id)
        client.send_message(chat_jid, "*No links allowed, no make me swear for you! 😒*")
    except Exception as e:
        print("del_link error:", e)
        
@client.event(MessageEv)
def on_message(client, event):
    text = (event.Message.conversation
            or event.Message.extendedTextMessage.text or "")
    print(repr(text))
    chat = event.Info.MessageSource.Chat.User
    if chat in games and games[chat]["state"] == "playing":
        check_answer(client, event, chat, text)
    match text:
        case "!help":
            cmd(client,event)
        case "!scramble":
            scramble_start(client, event)
        case "!riddle":
            start_riddle(client, event)
        case "!join":
            scramble_join(client, event)
        case "!leaderboard":
            leaderboard(client, event)
        case "!board":
            leaderboard(client, event)
        case "!menu":
            cmd(client, event)
        case "!lock":
            close_group(client, event)
        case "!open":
            open_group(client, event)
        case "!del":
            delete_msg(client, event)
        case _:

            if text == "!ping":
                client.reply_message("pong 🏓", event)

            if text.startswith("hi"):
                client.reply_message(greet(event), event)

            if "schedule" in text.lower():
                schedule(client, event)
            if any(word in text.lower() for word in ["curriculum", "Syllabus", "Roadmap", "Course outline", "training program"]):
                curriculum(client, event)
            if text.startswith("!add"):
                add_leaderboard(client, event)
            if text.startswith("!points"):
                add_point(client, event, text)
            if text.startswith("!kick"):
                kick(client, event)
            if link_pattern.search(text) and not event.Info.MessageSource.IsFromMe:
                del_link(client, event)



if __name__ == "__main__":
    threading.Thread(target=client.connect, daemon=True).start()

    if first_time:
        for _ in range(10):
            sleep(3)
            try:
                print("Pairing code:", client.PairPhone(PHONE, show_push_notification=True))
                break
            except Exception as e:
                print("Retrying...", e)

    while True:
        sleep(1)
