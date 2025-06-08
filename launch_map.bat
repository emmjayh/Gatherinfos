@echo off
echo Running XML Parser...
python parse_xml.py

echo.
echo Launching Interactive Map...
python interactive_map.py

echo.
echo Script execution finished.
pause
