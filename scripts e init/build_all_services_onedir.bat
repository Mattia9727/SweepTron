.@echo off
cd "C:\Users\Mattia971\PycharmProjects\search24\microservices\sensing"
pyinstaller -y --clean service_onedir.spec
move "dist\sensing" "C:\Users\Mattia971\PycharmProjects\search24\onedirs\"
cd "C:\Users\Mattia971\PycharmProjects\search24\microservices\processing"
pyinstaller -y --clean service_onedir.spec
move "dist\processing" "C:\Users\Mattia971\PycharmProjects\search24\onedirs\"
cd "C:\Users\Mattia971\PycharmProjects\search24\microservices\transfer"
pyinstaller -y --clean service_onedir.spec
move "dist\transfer" "C:\Users\Mattia971\PycharmProjects\search24\onedirs\"
cd "C:\Users\Mattia971\PycharmProjects\search24\microservices\watchdog"
pyinstaller -y --clean service_onedir.spec
move "dist\watchdog" "C:\Users\Mattia971\PycharmProjects\search24\onedirs\"
cd "C:\Users\Mattia971\PycharmProjects\search24\onedirs"
tar.exe acvf services.zip *