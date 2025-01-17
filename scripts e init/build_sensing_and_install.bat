@echo off
cd "C:\Users\matti\PycharmProjects\search24\exes"
sensing\sensing.exe remove
rmdir /S /Q sensing
cd "C:\Users\matti\PycharmProjects\search24\microservices\sensing"
pyinstaller -y --clean service_onedir.spec
move "dist\sensing" "C:\Users\matti\PycharmProjects\search24\onedirs\"
cd "C:\Users\matti\PycharmProjects\search24\onedirs"
sensing\sensing.exe install
sensing\sensing.exe start
cd ..