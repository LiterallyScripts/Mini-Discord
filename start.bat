@echo off
title Mini Discord
echo Mini Discord, V 0.0.1
if not exist "cache" mkdir "cache"
python discord_chat.py
pause