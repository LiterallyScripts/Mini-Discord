"""
Discord Chat Script
Version: 1.13
"""

__version__ = "1.13"
__author__ = "LiterallyScripts"
__last_updated__ = "2025-09-26"

import os
import requests
import json
import threading
import time
import queue
import sys

CACHE_DIR = "cache"
TOKEN_FILE = os.path.join(CACHE_DIR, "token.txt")
TOKENS_FILE = os.path.join(CACHE_DIR, "tokens.txt")

def show_loading_animation():
    """Display a simple rotating box loading animation"""
    frames = ["/", "|", "\\", "-"]
    clear_screen()
    print("\n" * 5)
    print(" " * 20 + "Discord Chat Script")
    print(" " * 25 + "Loading...")
    print()
    for i in range(20):
        frame = frames[i % len(frames)]
        print(" " * 30 + frame, end="\r")
        time.sleep(0.1)
    print("\n" * 2)
    print(" " * 22 + "Initializing Discord...")
    time.sleep(0.5)
    clear_screen()

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

def print_account_status(username, status):
    GREEN = "\033[32m"
    BLUE = "\033[34m"
    RED = "\033[31m"
    RESET = "\033[0m"
    print(f"{GREEN}Account: {username}{RESET} | {BLUE}Status: {status}{RESET}")
    print(f"{RED}Version: {__version__}{RESET}")

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
        WHITE = "\033[97m"
        GREY = "\033[90m"
        RESET = "\033[0m"
        print(f"{WHITE}0: Direct Messages{RESET}")
        for idx, guild in enumerate(guilds, 1):
            color = WHITE if idx % 2 == 1 else GREY
            print(f"{color}{idx}: {guild['name']}{RESET}")
        if len(guilds) < 10:
            color = WHITE if (len(guilds)+1) % 2 == 1 else GREY
            print(f"{color}{len(guilds)+1}: Add new account{RESET}")
        sel = input("Select a server by number (or type 'refresh', 'back', 'status'): ").strip()
        if sel.lower() == "refresh":
            continue
        if sel.lower() == "back":
            return "back_account"
        if sel.lower() == "status":
            new_status = input("Enter new status (online, dnd, idle, invisible): ")
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
            if sel == 0:
                dm_channel = get_dm_channel(token, username, status)
                if dm_channel == "back_dm":
                    continue
                return dm_channel
            elif 1 <= sel <= len(guilds):
                return guilds[sel-1]
        except:
            pass
        print("Invalid selection.")

def get_dm_channel(token, username, status):
    page = 0
    while True:
        clear_screen()
        print_account_status(username, status)
        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0"
        }
        resp = requests.get("https://discord.com/api/v9/users/@me/channels", headers=headers)
        if resp.status_code != 200:
            print("Failed to fetch DMs:", resp.text)
            time.sleep(2)
            return "back_dm"
        dms = [ch for ch in resp.json() if ch["type"] == 1 or ch["type"] == 3] 
        dms_sorted = sorted(dms, key=lambda c: c.get("last_message_id", "0"), reverse=True)
        per_page = 10
        total_pages = (len(dms_sorted) + per_page - 1) // per_page
        start = page * per_page
        end = start + per_page
        print("\n=== Direct Messages (Page {}/{}) ===".format(page+1, max(total_pages,1)))
        WHITE = "\033[97m"
        GREY = "\033[90m"
        RESET = "\033[0m"
        for idx, ch in enumerate(dms_sorted[start:end], 1):
            color = WHITE if idx % 2 == 1 else GREY
            if ch["type"] == 1:
                name = ch["recipients"][0]["username"]
            elif ch["type"] == 3:
                name = ch.get("name") or ", ".join([u["username"] for u in ch["recipients"]])
            else:
                name = "Unknown"
            print(f"{color}{idx}: {name}{RESET}")
        print(f"{WHITE}b: Back to server list{RESET}")
        if total_pages > 1:
            if page > 0:
                print(f"{WHITE}p: Previous page{RESET}")
            if page < total_pages - 1:
                print(f"{WHITE}n: Next page{RESET}")
        sel = input("Select a DM by number (or 'b' to go back): ").strip().lower()
        if sel == "b":
            return "back_dm"
        if sel == "p" and page > 0:
            page -= 1
            continue
        if sel == "n" and page < total_pages - 1:
            page += 1
            continue
        try:
            sel = int(sel)
            if 1 <= sel <= min(per_page, len(dms_sorted) - start):
                return dms_sorted[start + sel - 1]
        except:
            pass
        print("Invalid selection.")
        time.sleep(1)

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
        WHITE = "\033[97m"
        GREY = "\033[90m"
        RESET = "\033[0m"
        for idx, (ch, can_send) in enumerate(text_channels, 1):
            color = WHITE if idx % 2 == 1 else GREY
            extra = ""
            if not can_send:
                extra += " (cannot send here)"
            print(f"{color}{idx}: {ch['name']}{extra}{RESET}")
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
    if "type" in guild and (guild["type"] == 1 or guild["type"] == 3):
        return guild["id"], True
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
    RED = "\033[31m"
    RESET = "\033[0m"
    print(f"{GREEN}Account: {username}{RESET} | {BLUE}Status: {status}{RESET}")
    print(f"{RED}Version: {__version__}{RESET}")

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
                print("\nType 'page N', 'send' to send messages, 'back' to change channel.")
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
    show_loading_animation()
    main()
