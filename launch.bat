@echo off
cd %~dp0
cd server
start http://127.0.0.1:8000
uvicorn app:app --reload
