@echo off

REM Change directory to project folder
cd C:\Users\Public\Documents\GitHub\filemanagement-post

REM Activate virtual env
call C:\Users\Public\Documents\PythonEnvironments\eeg_backup_env\Scripts\activate

REM Run app
python eeg_backup.py

REM Deactivate virtual environment after complete
deactivate

REM Pause to keep window open
pause

