#!/bin/bash

echo ""
echo "========================================"
echo "  네이버 쇼핑 트렌드 분석 설치"
echo "========================================"
echo ""
echo "필요한 패키지를 설치합니다..."
echo "처음 설치 시 5-10분 정도 소요됩니다."
echo ""

# 스크립트 위치로 이동
cd "$(dirname "$0")"

# Python 확인
if ! command -v python3 &> /dev/null; then
    echo "[오류] Python이 설치되지 않았습니다."
    echo ""
    echo "Python 다운로드: https://www.python.org/downloads/"
    echo "또는 Homebrew 사용: brew install python3"
    echo ""
    read -p "계속하려면 Enter를 누르세요..."
    exit 1
fi

echo "[1/3] Python 확인 완료"
python3 --version
echo ""

# 가상환경 생성
if [ -d "ckdpharm" ]; then
    echo "[2/3] 기존 가상환경 발견"
else
    echo "[2/3] 가상환경 생성 중..."
    python3 -m venv ckdpharm
fi
echo ""

# 가상환경 활성화
source ckdpharm/bin/activate

# 패키지 설치
echo "[3/3] 필요한 패키지 설치 중..."
echo "(시간이 걸릴 수 있습니다...)"
echo ""
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "========================================"
echo "  설치 완료!"
echo "========================================"
echo ""
echo "이제 ./run_app.sh를 실행하세요."
echo ""
echo "실행 권한 부여:"
echo "  chmod +x run_app.sh"
echo ""
echo "실행:"
echo "  ./run_app.sh"
echo ""

