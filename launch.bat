@echo off
chcp 65001
cd %~dp0
start http://127.0.0.1:8000
uvicorn server.app:app --reload --no-use-colors