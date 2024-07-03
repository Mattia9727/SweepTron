@echo off
cd "C:\Users\matti\PycharmProjects\search24\microservices\sensing"
move "dist\sensing" "C:\Users\matti\PycharmProjects\search24\onedirs\"
cd "C:\Users\matti\PycharmProjects\search24\microservices\processing"
move "dist\processing" "C:\Users\matti\PycharmProjects\search24\onedirs\"
cd "C:\Users\matti\PycharmProjects\search24\microservices\transfer"
move "dist\transfer" "C:\Users\matti\PycharmProjects\search24\onedirs\"
cd "C:\Users\matti\PycharmProjects\search24\microservices\watchdog"
move "dist\watchdog" "C:\Users\matti\PycharmProjects\search24\onedirs\"