@echo off
cd "C:\Users\master\Desktop\progetto_chiaraviglio\Progetto_Iot\SweepTron-main_new2\microservices\sensing"
pyinstaller -y --clean service_onedir.spec
move "dist\sensing" "C:\Users\master\Desktop\progetto_chiaraviglio\Progetto_Iot\SweepTron-main_new2\onedirs\"
cd "C:\Users\master\Desktop\progetto_chiaraviglio\Progetto_Iot\SweepTron-main_new2\microservices\processing"
pyinstaller -y --clean service_onedir.spec
move "dist\processing" "C:\Users\master\Desktop\progetto_chiaraviglio\Progetto_Iot\SweepTron-main_new2\onedirs\"
cd "C:\Users\master\Desktop\progetto_chiaraviglio\Progetto_Iot\SweepTron-main_new2\microservices\transfer"
pyinstaller -y --clean service_onedir.spec
move "dist\transfer" "C:\Users\master\Desktop\progetto_chiaraviglio\Progetto_Iot\SweepTron-main_new2\onedirs\"
cd "C:\Users\master\Desktop\progetto_chiaraviglio\Progetto_Iot\SweepTron-main_new2\microservices\watchdog"
pyinstaller -y --clean service_onedir.spec
move "dist\watchdog" "C:\Users\master\Desktop\progetto_chiaraviglio\Progetto_Iot\SweepTron-main_new2\onedirs\"
cd "C:\Users\master\Desktop\progetto_chiaraviglio\Progetto_Iot\SweepTron-main_new2\onedirs\"
tar.exe acvf arpaservices.zip *