@echo off
echo Starting batch script...

REM Change directory to project folder
echo Changing working directory...
cd C:\Users\eplab\Documents\GitHub\filemanagement-post

REM Activate virtual env
echo Activating virtual environment...
call C:\Users\eplab\Documents\virtualenvs\eeg_backup_env\Scripts\activate

REM Run app
echo Running python script...
python eeg_backup.py

echo Batch script completed.

REM Pause to keep window open
pause