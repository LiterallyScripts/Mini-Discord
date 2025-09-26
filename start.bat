@echo off
setlocal enabledelayedexpansion

:: ----- CONFIGURATION -----
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe"
set "PYTHON_INSTALLER=python-installer.exe"
set "PYTHON_PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe"
set "GITHUB_RAW_URL=https://raw.githubusercontent.com/LiterallyScripts/Mini-Discord/refs/heads/main/discord_chat.py"
set "LOCAL_FILE=discord_chat.py"
set "BACKUP_FILE=discord_chat_backup.py"
set "TEMP_FILE=temp_download.py"

:: ----- CHECK FOR CURL -----
curl --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: curl not available
    pause
    exit /b 1
)

:: ----- CHECK FOR PYTHON -----
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Downloading and installing Python...
    curl -L -o "%PYTHON_INSTALLER%" "%PYTHON_URL%"
    if not exist "%PYTHON_INSTALLER%" (
        echo Failed to download Python installer.
        pause
        exit /b 1
    )
    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1
    if exist "%PYTHON_INSTALLER%" del "%PYTHON_INSTALLER%"
    set "PATH=%PATH%;%USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts;%USERPROFILE%\AppData\Local\Programs\Python\Python311\"
    "%PYTHON_PATH%" --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Python installation failed.
        pause
        exit /b 1
    )
)

:: *Ensure pip is available (Python 3.4+ comes with pip, but just in case)*
python -m ensurepip --upgrade >nul 2>&1

:: ----- INSTALL DEPENDENCIES IF requirements.txt EXISTS -----
if exist requirements.txt (
    echo Installing dependencies from requirements.txt ...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
)

echo Checking for updates...

set "local_version="
if exist "%LOCAL_FILE%" (
    for /f "tokens=3 delims= " %%a in ('findstr /C:"__version__ = " "%LOCAL_FILE%" 2^>nul') do (
        set "local_version=%%a"
        set "local_version=!local_version:"=!"
        goto :local_version_found
    )
    :local_version_found
    if "!local_version!"=="" set "local_version=0.0.0"
) else (
    set "local_version=0.0.0"
)

curl -s -L -o "%TEMP_FILE%" "%GITHUB_RAW_URL%"
if %errorlevel% neq 0 goto :run_local

if not exist "%TEMP_FILE%" goto :run_local

for %%A in ("%TEMP_FILE%") do set "filesize=%%~zA"
if %filesize% LSS 10 (
    del "%TEMP_FILE%" >nul 2>&1
    goto :run_local
)

set "remote_version="
for /f "tokens=3 delims= " %%a in ('findstr /C:"__version__ = " "%TEMP_FILE%" 2^>nul') do (
    set "remote_version=%%a"
    set "remote_version=!remote_version:"=!"
    goto :remote_version_found
)
:remote_version_found

if "!remote_version!"=="" goto :file_comparison

call :compare_versions "!local_version!" "!remote_version!"
if !version_result! equ 0 (
    del "%TEMP_FILE%" >nul 2>&1
    echo Already up to date
    goto :run_script
) else if !version_result! equ -1 (
    echo Update: !local_version! -> !remote_version!
    goto :do_update
) else (
    del "%TEMP_FILE%" >nul 2>&1
    echo Local version newer
    goto :run_script
)

:file_comparison
if not exist "%LOCAL_FILE%" goto :do_update
fc /b "%LOCAL_FILE%" "%TEMP_FILE%" >nul 2>&1
if %errorlevel% neq 0 (
    echo File changed
    goto :do_update
) else (
    del "%TEMP_FILE%" >nul 2>&1
    echo No changes
    goto :run_script
)

:do_update
if exist "%LOCAL_FILE%" copy "%LOCAL_FILE%" "%BACKUP_FILE%" >nul
move "%TEMP_FILE%" "%LOCAL_FILE%" >nul
if %errorlevel% neq 0 (
    if exist "%BACKUP_FILE%" copy "%BACKUP_FILE%" "%LOCAL_FILE%" >nul
    pause
    exit /b 1
)
echo Updated!
if exist "%BACKUP_FILE%" del "%BACKUP_FILE%" >nul 2>&1
goto :run_script

:run_local
if exist "%TEMP_FILE%" del "%TEMP_FILE%" >nul 2>&1
goto :run_script

:run_script
echo Running Python script...
python "%LOCAL_FILE%"
if %errorlevel% neq 0 (
    echo Script failed with error code %errorlevel%
    echo Backup deleted - cannot restore
) else (
    echo Script completed successfully
)
pause
goto :eof

:compare_versions
set "ver1=%~1"
set "ver2=%~2"
if "!ver1:~0,1!"=="v" set "ver1=!ver1:~1!"
if "!ver2:~0,1!"=="v" set "ver2=!ver2:~1!"
for /f "tokens=1,2,3 delims=." %%a in ("!ver1!") do (
    set "v1_major=%%a"
    set "v1_minor=%%b"
    set "v1_patch=%%c"
)
for /f "tokens=1,2,3 delims=." %%a in ("!ver2!") do (
    set "v2_major=%%a"
    set "v2_minor=%%b"
    set "v2_patch=%%c"
)
if "!v1_minor!"=="" set "v1_minor=0"
if "!v1_patch!"=="" set "v1_patch=0"
if "!v2_minor!"=="" set "v2_minor=0"
if "!v2_patch!"=="" set "v2_patch=0"
if !v1_major! LSS !v2_major! (
    set "version_result=-1"
    goto :eof
)
if !v1_major! GTR !v2_major! (
    set "version_result=1"
    goto :eof
)
if !v1_minor! LSS !v2_minor! (
    set "version_result=-1"
    goto :eof
)
if !v1_minor! GTR !v2_minor! (
    set "version_result=1"
    goto :eof
)
if !v1_patch! LSS !v2_patch! (
    set "version_result=-1"
    goto :eof
)
if !v1_patch! GTR !v2_patch! (
    set "version_result=1"
    goto :eof
)
set "version_result=0"
goto :eof
