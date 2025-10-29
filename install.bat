@echo off
chcp 65001 > nul
title 네이버 트렌드 분석 설치

echo.
echo ========================================
echo   네이버 쇼핑 트렌드 분석 설치
echo ========================================
echo.
echo 필요한 패키지를 설치합니다...
echo 처음 설치 시 5-10분 정도 소요됩니다.
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"

REM Python 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되지 않았습니다.
    echo.
    echo Python 다운로드: https://www.python.org/downloads/
    echo 설치 시 "Add Python to PATH" 옵션을 꼭 체크하세요!
    echo.
    pause
    exit
)

echo [1/3] Python 확인 완료
python --version
echo.

REM 가상환경 생성
if exist "ckdpharm" (
    echo [2/3] 기존 가상환경 발견
) else (
    echo [2/3] 가상환경 생성 중...
    python -m venv ckdpharm
)
echo.

REM 가상환경 활성화
call ckdpharm\Scripts\activate.bat

REM 패키지 설치
echo [3/3] 필요한 패키지 설치 중...
echo (시간이 걸릴 수 있습니다...)
echo.
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================
echo   설치 완료!
echo ========================================
echo.
echo 이제 "run_app.bat" 파일을 실행하세요.
echo 또는 바탕화면의 바로가기 아이콘을 더블클릭하세요.
echo.
pause

