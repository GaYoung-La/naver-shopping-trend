@echo off
chcp 65001 > nul
title 네이버 쇼핑 트렌드 분석

echo.
echo ========================================
echo   네이버 쇼핑 트렌드 분석
echo ========================================
echo.
echo 잠시만 기다려주세요...
echo 브라우저가 자동으로 열립니다.
echo.
echo (창을 닫으면 앱이 종료됩니다)
echo ========================================
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"

REM 가상환경이 있으면 활성화
if exist "ckdpharm\Scripts\activate.bat" (
    call ckdpharm\Scripts\activate.bat
) else (
    echo [경고] 가상환경을 찾을 수 없습니다.
    echo install.bat을 먼저 실행해주세요.
    echo.
    pause
    exit
)

REM Streamlit 실행
echo 앱을 시작합니다...
timeout /t 2 /nobreak > nul
start http://localhost:8501
streamlit run streamlit_app.py

REM 종료 시 메시지
echo.
echo ========================================
echo 앱이 종료되었습니다.
echo ========================================
pause

