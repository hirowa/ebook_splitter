@echo off
setlocal EnableDelayedExpansion

:: Prompt for input path
set /p RAW_PATH=Enter the full path to the EPUB file or folder: 

:: Remove leading and trailing quotes if present
set EPUB_PATH=!RAW_PATH:"=!

:: Run the Python script with cleaned path
python ebook_splitter.py "!EPUB_PATH!"

pause
