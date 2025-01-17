@echo off
cd "C:\Users\matti\PycharmProjects\search24\microservices\transfer"
pyinstaller -y --clean service_onedir.spec
move "dist\transfer" "C:\Users\matti\PycharmProjects\search24\onedirs\"
cd "C:\Users\matti\PycharmProjects\search24\onedirs"
tar.exe acvf transfer.zip *