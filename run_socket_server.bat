cd /d %~dp0

cmd.exe /K "conda activate iot_env & python.exe socket_server.py 127.0.0.1 8889"

