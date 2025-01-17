@echo off
cd "C:\Users\matti\PycharmProjects\search24\microservices\transfer"
pyinstaller -y --clean service_exe.spec
move "dist\transfer.exe" "C:\Users\matti\PycharmProjects\search24\exes"