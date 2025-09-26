"""
Discord Chat Script
Version: 1.14
"""

__version__ = "1.14"
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

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
BLUE = "\033[34m"
RED = "\033[31m"
WHITE = "\033[97m"
GREY = "\033[90m"
YELLOW = "\033[33m"
CYAN = "\033[36m"

def show_loading_animation():
    frames = ["/", "|", "\\", "-"]
    clear_screen()
    print("\n" * 5)
    print(" " * 20 + f"{BOLD}{CYAN}Discord Chat Script{RESET}")
    print(" " * 25 + f"{YELLOW}Loading...{RESET}")
    print()
    for i in range(20):
        frame = frames[i % len(frames)]
        print(" " * 30 + f"{CYAN}{frame}{RESET}", end="\r")
        time.sleep(0.08)
    print("\n" * 2)
    print(" " * 22 + f"{GREEN}Initializing Discord...{RESET}")
    time.sleep(0.5)
    clear_screen()

def fetch_username(token):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0"
    }
    try:
        resp = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
        if resp.status_code == 200:
            user = resp.json()
            return user.get("username", "Unknown"), user.get("id", "")
    except Exception:
        pass
    return None, None

def fetch_status(token):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0"
    }
    try:
        resp = requests.get("https://discord.com/api/v9/users/@me/settings", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("status", "unknown")
    except Exception:
        pass
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
        print(f"{BOLD}{CYAN}==== Discord Accounts ===={RESET}\n")
        for idx, (username, user_id, _) in enumerate(users, 1):
            color = GREEN if username != "Invalid token" else RED
            print(f"{color}{idx}: {username}{RESET}")
        if len(users) < 10:
            print(f"{YELLOW}{len(users)+1}: Add new account{RESET}")
        print(f"{RED}q: Quit{RESET}")
        sel = input(f"\n{BOLD}Select an account by number:{RESET} ").strip()
        if sel.lower() == "q":
            sys.exit(0)
        try:
            sel = int(sel)
            if 1 <= sel <= len(users):
                if users[sel-1][0] == "Invalid token":
                    print(f"{RED}This token is invalid. Please remove or replace it.{RESET}")
                    input("Press Enter to continue...")
                    continue
                return users[sel-1][2]
            elif sel == len(users)+1 and len(users) < 10:
                new_token = input("Enter your Discord token: ").strip()
                username, user_id = fetch_username(new_token)
                if username:
                    if new_token not in tokens:
                        with open(TOKENS_FILE, "a") as f:
                            f.write(new_token + "\n")
                    print(f"{GREEN}Added account: {username}{RESET}")
                    input("Press Enter to continue...")
                    return new_token
                else:
                    print(f"{RED}Invalid token.{RESET}")
                    input("Press Enter to continue...")
            else:
                print(f"{RED}Invalid selection.{RESET}")
                input("Press Enter to continue...")
        except Exception:
            print(f"{RED}Invalid selection.{RESET}")
            input("Press Enter to continue...")

def get_token():
    return select_token()

def print_account_status(username, status):
    print(f"{BOLD}{GREEN}Account:{RESET} {username} | {BOLD}{BLUE}Status:{RESET} {status}")
    print(f"{BOLD}{CYAN}Version:{RESET} {__version__}\n")

def get_guild(token, username, status):
    while True:
        clear_screen()
        print_account_status(username, status)
        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0"
        }
        try:
            resp = requests.get("https://discord.com/api/v9/users/@me/guilds", headers=headers)
            if resp.status_code != 200:
                print(f"{RED}Failed to fetch guilds:{RESET}", resp.text)
                input("Press Enter to exit...")
                exit(1)
            guilds = resp.json()
        except Exception as e:
            print(f"{RED}Error fetching guilds:{RESET} {e}")
            input("Press Enter to exit...")
            exit(1)
        print(f"{BOLD}{CYAN}=== Your Servers ==={RESET}")
        print(f"{WHITE}0: Direct Messages{RESET}")
        for idx, guild in enumerate(guilds, 1):
            color = WHITE if idx % 2 == 1 else GREY
            print(f"{color}{idx}: {guild['name']}{RESET}")
        print(f"{YELLOW}b: Back to account selection{RESET}")
        print(f"{RED}q: Quit{RESET}")
        sel = input(f"\n{BOLD}Select a server by number:{RESET} ").strip().lower()
        if sel == "b":
            return "back_account"
        if sel == "q":
            sys.exit(0)
        try:
            sel = int(sel)
            if sel == 0:
                dm_channel = get_dm_channel(token, username, status)
                if dm_channel == "back_dm":
                    continue
                return dm_channel
            elif 1 <= sel <= len(guilds):
                return guilds[sel-1]
        except Exception:
            pass
        print(f"{RED}Invalid selection.{RESET}")
        input("Press Enter to continue...")

def get_dm_channel(token, username, status):
    page = 0
    while True:
        clear_screen()
        print_account_status(username, status)
        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0"
        }
        try:
            resp = requests.get("https://discord.com/api/v9/users/@me/channels", headers=headers)
            if resp.status_code != 200:
                print(f"{RED}Failed to fetch DMs:{RESET}", resp.text)
                time.sleep(2)
                return "back_dm"
            dms = [ch for ch in resp.json() if ch["type"] == 1 or ch["type"] == 3]
        except Exception as e:
            print(f"{RED}Error fetching DMs:{RESET} {e}")
            time.sleep(2)
            return "back_dm"
        dms_sorted = sorted(dms, key=lambda c: c.get("last_message_id", "0"), reverse=True)
        per_page = 10
        total_pages = (len(dms_sorted) + per_page - 1) // per_page
        start = page * per_page
        end = start + per_page
        print(f"{BOLD}{CYAN}=== Direct Messages (Page {page+1}/{max(total_pages,1)}) ==={RESET}")
        for idx, ch in enumerate(dms_sorted[start:end], 1):
            color = WHITE if idx % 2 == 1 else GREY
            if ch["type"] == 1:
                name = ch["recipients"][0]["username"]
            elif ch["type"] == 3:
                name = ch.get("name") or ", ".join([u["username"] for u in ch["recipients"]])
            else:
                name = "Unknown"
            print(f"{color}{idx}: {name}{RESET}")
        print(f"{YELLOW}b: Back to server list{RESET}")
        if total_pages > 1:
            if page > 0:
                print(f"{CYAN}p: Previous page{RESET}")
            if page < total_pages - 1:
                print(f"{CYAN}n: Next page{RESET}")
        print(f"{RED}q: Quit{RESET}")
        sel = input(f"\n{BOLD}Select a DM by number:{RESET} ").strip().lower()
        if sel == "b":
            return "back_dm"
        if sel == "q":
            sys.exit(0)
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
        except Exception:
            pass
        print(f"{RED}Invalid selection.{RESET}")
        input("Press Enter to continue...")

def get_channel(token, guild_id, username, status):
    while True:
        clear_screen()
        print_account_status(username, status)
        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0"
        }
        try:
            resp = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}/channels", headers=headers)
            if resp.status_code != 200:
                print(f"{RED}Failed to fetch channels:{RESET}", resp.text)
                input("Press Enter to exit...")
                exit(1)
            channels = resp.json()
        except Exception as e:
            print(f"{RED}Error fetching channels:{RESET} {e}")
            input("Press Enter to exit...")
            exit(1)
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
            print(f"{RED}No text channels found.{RESET}")
            input("Press Enter to exit...")
            exit(1)
        print(f"{BOLD}{CYAN}=== Channels ==={RESET}")
        for idx, (ch, can_send) in enumerate(text_channels, 1):
            color = WHITE if idx % 2 == 1 else GREY
            extra = ""
            if not can_send:
                extra += f" {RED}(read-only){RESET}"
            print(f"{color}{idx}: {ch['name']}{extra}{RESET}")
        print(f"{YELLOW}b: Back to server list{RESET}")
        print(f"{RED}q: Quit{RESET}")
        sel = input(f"\n{BOLD}Select a channel by number:{RESET} ").strip().lower()
        if sel == "b":
            return "back_guild", None
        if sel == "q":
            sys.exit(0)
        try:
            sel = int(sel)
            if 1 <= sel <= len(text_channels):
                ch, can_send = text_channels[sel-1]
                return ch, can_send
        except Exception:
            pass
        print(f"{RED}Invalid selection.{RESET}")
        input("Press Enter to continue...")

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
        print(f"{YELLOW}You cannot send messages in this channel.{RESET}")
        input("Press Enter to continue...")
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
        try:
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                print(f"{RED}Failed to fetch messages:{RESET}", resp.text)
                return []
            batch = resp.json()
            if not batch:
                break
            messages = batch
            last_message_id = batch[-1]["id"]
        except Exception:
            break
    return messages

def send_message(token, channel_id, content):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    data = {"content": content}
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        if resp.status_code == 200 or resp.status_code == 201:
            print(f"{GREEN}Message sent!{RESET}")
        else:
            print(f"{RED}Failed to send message:{RESET}", resp.text)
    except Exception as e:
        print(f"{RED}Error sending message:{RESET} {e}")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_page(token, channel_id, page, self_id, username, status):
    clear_screen()
    print_account_status(username, status)
    print(f"{BOLD}{CYAN}--- Messages Page {page} ---{RESET}")
    messages = fetch_messages(token, channel_id, page=page)
    if not messages:
        print(f"{YELLOW}No messages or failed to fetch.{RESET}")
    else:
        messages = list(reversed(messages))
        for idx, msg in enumerate(messages):
            author = msg["author"]["username"]
            content = msg["content"]
            is_self = self_id and msg["author"]["id"] == self_id
            color = YELLOW if is_self else (WHITE if idx % 2 == 0 else GREY)
            print(f"{color}{author}:{RESET} {content}")
    return messages

def get_self_id(token):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0"
    }
    try:
        resp = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
        if resp.status_code == 200:
            return resp.json()["id"]
    except Exception:
        pass
    return None

def send_mode(token, channel_id, page, self_id, username, status):
    while True:
        content = input(f"{BOLD}Enter message (type 'exit' to stop, 'back' to change channel):{RESET} ")
        if content.lower() in ("exit", "back"):
            return content.lower()
        if not content.strip():
            print(f"{YELLOW}Cannot send empty message.{RESET}")
            continue
        send_message(token, channel_id, content)
        display_page(token, channel_id, page, self_id, username, status)

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
            display_page(token, channel_id, page, self_id, username, status)
            while True:
                print(f"\n{BOLD}Commands:{RESET} {CYAN}page N{RESET}, {CYAN}send{RESET}, {CYAN}back{RESET}, {CYAN}help{RESET}, {CYAN}quit{RESET}")
                cmd = input(f"{BOLD}> {RESET}").strip()
                if cmd.lower() == "quit":
                    print(f"{RED}Goodbye!{RESET}")
                    sys.exit(0)
                elif cmd.lower() == "back":
                    break
                elif cmd.lower().startswith("page "):
                    try:
                        page = int(cmd.split()[1])
                        display_page(token, channel_id, page, self_id, username, status)
                    except Exception:
                        print(f"{RED}Invalid page number.{RESET}")
                elif cmd.lower() == "send":
                    if not can_send:
                        print(f"{YELLOW}You cannot send messages in this channel.{RESET}")
                        continue
                    result = send_mode(token, channel_id, page, self_id, username, status)
                    if result == "back":
                        break
                elif cmd.lower() == "help":
                    print(f"{CYAN}Type:{RESET} {BOLD}page N{RESET} to view page N, {BOLD}send{RESET} to send a message, {BOLD}back{RESET} to change channel, {BOLD}quit{RESET} to exit.")
                else:
                    print(f"{YELLOW}Unknown command. Type 'help' for options.{RESET}")

if __name__ == "__main__":
    show_loading_animation()
    main()
