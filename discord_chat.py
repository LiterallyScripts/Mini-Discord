"""
Discord Chat Script
Version: 1.0.1
"""

__version__ = "1.0.1"
__author__ = "LiterallyScripts"
__last_updated__ = "2025-09-26"

import os
import requests
import json
import threading
import time
import queue

CACHE_DIR = "cache"
TOKEN_FILE = os.path.join(CACHE_DIR, "token.txt")
TOKENS_FILE = os.path.join(CACHE_DIR, "tokens.txt")
LOG_FILE = os.path.join(CACHE_DIR, "Mainmessage.txt")

def fetch_username(token):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
    if resp.status_code == 200:
        user = resp.json()
        return user.get("username", "Unknown"), user.get("id", "")
    return None, None

def fetch_status(token):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get("https://discord.com/api/v9/users/@me/settings", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        status = data.get("status", "unknown")
        return status
    return "unknown"

def select_token():
    if not os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "w") as f:
            pass
    with open(TOKENS_FILE, "r") as f:
        tokens = [line.strip() for line in f if line.strip()]
    users = []
    for token in tokens:
        username, user_id = fetch_username(token)
        if username:
            users.append((username, user_id, token))
        else:
            users.append(("Invalid token", "", token))
    while True:
        clear_screen()
        print("\n==== Discord Accounts ====")
        for idx, (username, user_id, _) in enumerate(users, 1):
            print(f"{idx}: {username}")
        if len(users) < 10:
            print(f"{len(users)+1}: Add new account")
        sel = input("Select an account by number: ").strip()
        try:
            sel = int(sel)
            if 1 <= sel <= len(users):
                if users[sel-1][0] == "Invalid token":
                    print("This token is invalid. Please remove or replace it.")
                    continue
                return users[sel-1][2]
            elif sel == len(users)+1 and len(users) < 10:
                new_token = input("Enter your Discord token: ").strip()
                username, user_id = fetch_username(new_token)
                if username:
                    if new_token not in tokens:
                        with open(TOKENS_FILE, "a") as f:
                            f.write(new_token + "\n")
                    print(f"Added account: {username}")
                    return new_token
                else:
                    print("Invalid token.")
            else:
                print("Invalid selection.")
        except:
            print("Invalid selection.")

def get_token():
    return select_token()

def get_guild(token, username, status):
    while True:
        clear_screen()
        print_account_status(username, status)
        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0"
        }
        resp = requests.get("https://discord.com/api/v9/users/@me/guilds", headers=headers)
        if resp.status_code != 200:
            print("Failed to fetch guilds:", resp.text)
            exit(1)
        guilds = resp.json()
        print("\n=== Your Servers ===")
        for idx, guild in enumerate(guilds, 1):
            print(f"{idx}: {guild['name']}")
        sel = input("Select a server by number (or type 'refresh', 'back', 'status'): ").strip()
        if sel.lower() == "refresh":
            continue
        if sel.lower() == "back":
            return "back_account"
        if sel.lower() == "status":
            new_status = input("Enter new status (online, dnd, idle, invisible): ").strip().lower()
            if new_status in ("online", "dnd", "idle", "invisible", "offline"):
                if new_status == "offline":
                    new_status = "invisible"
                if set_status(token, new_status):
                    status = new_status
            else:
                print("Invalid status.")
            time.sleep(1)
            continue
        try:
            sel = int(sel)
            if 1 <= sel <= len(guilds):
                return guilds[sel-1]
        except:
            pass
        print("Invalid selection.")

def get_channel(token, guild_id, username, status):
    while True:
        clear_screen()
        print_account_status(username, status)
        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0"
        }
        resp = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}/channels", headers=headers)
        if resp.status_code != 200:
            print("Failed to fetch channels:", resp.text)
            exit(1)
        channels = resp.json()
        text_channels = []
        for ch in channels:
            if ch["type"] in [0, 5, 10, 11, 12, 15]:
                perms = ch.get("permissions", None)
                can_send = True
                if perms is not None:
                    perms_int = int(perms)
                    can_send = (perms_int & 0x800) != 0
                text_channels.append((ch, can_send))
        if not text_channels:
            print("No text channels found.")
            exit(1)
        print("\n=== Channels ===")
        for idx, (ch, can_send) in enumerate(text_channels, 1):
            extra = ""
            if not can_send:
                extra += " (cannot send here)"
            print(f"{idx}: {ch['name']}{extra}")
        sel = input("Select a channel by number (or type 'refresh', 'back'): ").strip()
        if sel.lower() == "refresh":
            continue
        if sel.lower() == "back":
            return "back_guild", None
        try:
            sel = int(sel)
            if 1 <= sel <= len(text_channels):
                ch, can_send = text_channels[sel-1]
                return ch, can_send
        except:
            pass
        print("Invalid selection.")

def get_channel_id(token, username, status):
    guild = get_guild(token, username, status)
    if guild == "back_account":
        return "back_account", None
    channel, can_send = get_channel(token, guild["id"], username, status)
    if channel == "back_guild":
        return "back_guild", None
    if not can_send:
        print("You cannot send messages in this channel.")
    return channel["id"], can_send

def fetch_messages(token, channel_id, page=1, limit=20):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0"
    }
    params = {
        "limit": limit,
        "before": None
    }
    messages = []
    last_message_id = None
    for _ in range(page):
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        if last_message_id:
            params["before"] = last_message_id
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            print("Failed to fetch messages:", resp.text)
            return []
        batch = resp.json()
        if not batch:
            break
        messages = batch
        last_message_id = batch[-1]["id"]
    return messages

def log_messages(messages):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        for msg in messages:
            author = msg["author"]["username"]
            content = msg["content"]
            f.write(f"{author}: {content}\n")

def send_message(token, channel_id, content):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    data = {"content": content}
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    resp = requests.post(url, headers=headers, data=json.dumps(data))
    if resp.status_code == 200 or resp.status_code == 201:
        print("Message sent!")
    else:
        print("Failed to send message:", resp.text)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_account_status(username, status):
    GREEN = "\033[32m"
    BLUE = "\033[34m"
    RESET = "\033[0m"
    print(f"{GREEN}Account: {username}{RESET} | {BLUE}Status: {status}{RESET}")

def display_page(token, channel_id, page, self_id, username, status):
    clear_screen()
    print_account_status(username, status)
    print(f"\n--- Messages Page {page} ---")
    messages = fetch_messages(token, channel_id, page=page)
    if not messages:
        print("No messages or failed to fetch.")
    else:
        messages = list(reversed(messages))
        for idx, msg in enumerate(messages):
            author = msg["author"]["username"]
            content = msg["content"]
            is_self = self_id and msg["author"]["id"] == self_id
            RESET = "\033[0m"
            GOLD = "\033[33;1m"
            WHITE = "\033[97m"
            GREY = "\033[90m"
            if is_self:
                color = GOLD
            else:
                color = WHITE if idx % 2 == 0 else GREY
            print(f"{color}{author}: {content}{RESET}")
        log_messages(messages)
    return messages

def get_self_id(token):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
    if resp.status_code == 200:
        return resp.json()["id"]
    return None

def send_mode(token, channel_id, page, self_id, username, status):
    while True:
        content = input("Enter message (type 'exit' to stop sending and load messages, 'back' to change channel): ")
        if content.lower() in ("exit", "back"):
            return content.lower()
        send_message(token, channel_id, content)
        display_page(token, channel_id, page, self_id, username, status)

def set_status(token, new_status):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    data = {"status": new_status}
    resp = requests.patch("https://discord.com/api/v9/users/@me/settings", headers=headers, data=json.dumps(data))
    if resp.status_code == 200:
        print(f"Status changed to {new_status}!")
        return True
    else:
        print("Failed to change status:", resp.text)
        return False

def main():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    while True:
        token = get_token()
        username, _ = fetch_username(token)
        status = fetch_status(token)
        self_id = get_self_id(token)
        while True:
            channel_id, can_send = get_channel_id(token, username, status)
            if channel_id == "back_account":
                break
            if channel_id == "back_guild":
                continue
            page = 1
            last_refresh = 0
            
            display_page(token, channel_id, page, self_id, username, status)
            last_refresh = time.time()
            
            while True:
                print("\nType 'page N', 'send' to send messages, 'back' to change channel, or 'exit' to quit.")
                start = time.time()
                cmd = None
                
                while True:
                    if time.time() - start >= 10:
                        break
                    if os.name == 'nt':
                        import msvcrt
                        if msvcrt.kbhit():
                            cmd = input("> ").strip()
                            break
                    else:
                        import select, sys
                        print("> ", end='', flush=True)
                        remaining_time = 10 - (time.time() - start)
                        if remaining_time <= 0:
                            break
                        rlist, _, _ = select.select([sys.stdin], [], [], remaining_time)
                        if rlist:
                            cmd = sys.stdin.readline().strip()
                            break
                
                if cmd is None:
                    display_page(token, channel_id, page, self_id, username, status)
                    last_refresh = time.time()
                    continue

                if cmd.lower() == "exit":
                    return
                elif cmd.lower() == "back":
                    break
                elif cmd.lower().startswith("page "):
                    try:
                        page = int(cmd.split()[1])
                        display_page(token, channel_id, page, self_id, username, status)
                        last_refresh = time.time()
                    except:
                        print("Invalid page number.")
                elif cmd.lower() == "send":
                    result = send_mode(token, channel_id, page, self_id, username, status)
                    last_refresh = time.time()
                    if result == "back":
                        break 
                else:
                    print("Unknown command.")

if __name__ == "__main__":

    main()

