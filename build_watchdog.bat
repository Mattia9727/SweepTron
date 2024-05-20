@echo off
cd "C:\Users\matti\PycharmProjects\search24\microservices\watchdog"
pyinstaller -y --clean service_exe.spec
move "dist\watchdog.exe" "C:\Users\matti\PycharmProjects\search24\exes"