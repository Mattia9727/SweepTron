@echo off
cd "C:\Users\matti\PycharmProjects\search24\microservices\sensing"
pyinstaller -y --clean service_exe.spec
move "dist\sensing.exe" "C:\Users\matti\PycharmProjects\search24\exes"