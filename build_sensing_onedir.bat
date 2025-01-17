@echo off
cd "C:\Users\matti\PycharmProjects\search24\microservices\sensing"
pyinstaller -y --clean service_onedir.spec
move "dist\sensing" "C:\Users\matti\PycharmProjects\search24\onedirs\"
cd "C:\Users\matti\PycharmProjects\search24\onedirs"
tar.exe acvf sensing.zip sensing