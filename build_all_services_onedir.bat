@echo off
cd "C:\Users\matti\PycharmProjects\search24\microservices\sensing"
pyinstaller -y --clean service_onedir.spec
move "dist\sensing" "C:\Users\matti\PycharmProjects\search24\onedirs\"
cd "C:\Users\matti\PycharmProjects\search24\microservices\processing"
pyinstaller -y --clean service_onedir.spec
move "dist\processing" "C:\Users\matti\PycharmProjects\search24\onedirs\"
cd "C:\Users\matti\PycharmProjects\search24\microservices\transfer"
pyinstaller -y --clean service_onedir.spec
move "dist\transfer" "C:\Users\matti\PycharmProjects\search24\onedirs\"
cd "C:\Users\matti\PycharmProjects\search24\microservices\watchdog"
pyinstaller -y --clean service_onedir.spec
move "dist\watchdog" "C:\Users\matti\PycharmProjects\search24\onedirs\"
cd "C:\Users\matti\PycharmProjects\search24\onedirs"
tar.exe acvf services.zip *