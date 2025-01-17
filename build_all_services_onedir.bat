@echo off
cd "C:\Users\master\Desktop\progetto chiaraviglio\Progetto Iot\SweepTron-main_08_11_24\SweepTron-main\microservices\sensing"
pyinstaller -y --clean service_onedir.spec
move "dist\sensing" "C:\Users\master\Desktop\progetto chiaraviglio\Progetto Iot\SweepTron-main_08_11_24\SweepTron-main\onedirs\"
cd "C:\Users\master\Desktop\progetto chiaraviglio\Progetto Iot\SweepTron-main_08_11_24\SweepTron-main\microservices\processing"
pyinstaller -y --clean service_onedir.spec
move "dist\processing" "C:\Users\master\Desktop\progetto chiaraviglio\Progetto Iot\SweepTron-main_08_11_24\SweepTron-main\onedirs\"
cd "C:\Users\master\Desktop\progetto chiaraviglio\Progetto Iot\SweepTron-main_08_11_24\SweepTron-main\microservices\transfer"
pyinstaller -y --clean service_onedir.spec
move "dist\transfer" "C:\Users\master\Desktop\progetto chiaraviglio\Progetto Iot\SweepTron-main_08_11_24\SweepTron-main\onedirs\"
cd "C:\Users\master\Desktop\progetto chiaraviglio\Progetto Iot\SweepTron-main_08_11_24\SweepTron-main\microservices\watchdog"
pyinstaller -y --clean service_onedir.spec
move "dist\watchdog" "C:\Users\master\Desktop\progetto chiaraviglio\Progetto Iot\SweepTron-main_08_11_24\SweepTron-main\onedirs\"
cd "C:\Users\master\Desktop\progetto chiaraviglio\Progetto Iot\SweepTron-main_08_11_24\SweepTron-main\onedirs\"
tar.exe acvf services.zip *