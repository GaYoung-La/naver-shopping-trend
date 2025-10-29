#!/bin/bash

echo ""
echo "========================================"
echo "  네이버 쇼핑 트렌드 분석"
echo "========================================"
echo ""
echo "잠시만 기다려주세요..."
echo "브라우저가 자동으로 열립니다."
echo ""
echo "(Control+C를 누르면 앱이 종료됩니다)"
echo "========================================"
echo ""

# 스크립트 위치로 이동
cd "$(dirname "$0")"

# 가상환경 확인 및 활성화
if [ -d "ckdpharm" ]; then
    source ckdpharm/bin/activate
else
    echo "[경고] 가상환경을 찾을 수 없습니다."
    echo "./install.sh를 먼저 실행해주세요."
    echo ""
    read -p "계속하려면 Enter를 누르세요..."
    exit 1
fi

# Streamlit 실행
echo "앱을 시작합니다..."
sleep 2
open http://localhost:8501
streamlit run streamlit_app.py

# 종료 시 메시지
echo ""
echo "========================================"
echo "앱이 종료되었습니다."
echo "========================================"

