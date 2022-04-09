@echo off

:init
@echo Started: %date% %time%
echo init starts

@REM 프로젝트 경로
cd C:\Users\ljj94\PycharmProjects\SystemTrading

@REM 가상환경 구동
call activate system_trading_py38_32
@taskkill /f /im "python.exe"
set loop=0
@REM 약 30분(900)주기로 재실행, 20분은 약 600정도
set max_loop=900

:loop
set /a loop+=10
echo %loop%
timeout 2 > NUL
if %loop%==%max_loop% goto init
if %loop%==1 goto starter
if not %loop%==1 goto loop

:starter
start python main.py
timeout 10 > NUL
goto loop
