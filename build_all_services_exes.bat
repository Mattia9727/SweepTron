@echo off
cd "C:\Users\matti\PycharmProjects\search24\microservices\sensing"
pyinstaller -y --clean service_exe.spec
move "dist\sensing.exe" "C:\Users\matti\PycharmProjects\search24\exes"
cd "C:\Users\matti\PycharmProjects\search24\microservices\processing"
pyinstaller -y --clean service_exe.spec
move "dist\processing.exe" "C:\Users\matti\PycharmProjects\search24\exes"
cd "C:\Users\matti\PycharmProjects\search24\microservices\transfer"
pyinstaller -y --clean service_exe.spec
move "dist\transfer.exe" "C:\Users\matti\PycharmProjects\search24\exes"
cd "C:\Users\matti\PycharmProjects\search24\microservices\watchdog"
pyinstaller -y --clean service_exe.spec
move "dist\watchdog.exe" "C:\Users\matti\PycharmProjects\search24\exes"
cd "C:\Users\matti\PycharmProjects\search24\exes\
tar.exe acvf services.zip *