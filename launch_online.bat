@echo off
chcp 65001
cd %~dp0
uvicorn server.app:app --host 0.0.0.0 --port 8000