@echo off
chcp 65001
cd %~dp0
uvicorn server.app:app --reload --no-use-colors