# 🛍️ 네이버 쇼핑 트렌드 분석

네이버 DataLab API를 활용한 **실시간 급상승 키워드 분석 도구**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)

---

## 🎯 주요 기능

### 📊 자동 카테고리 분석
- 네이버 쇼핑의 **실제 카테고리**를 자동으로 수집
- 각 카테고리의 **인기 키워드** 자동 추출 (592개)
- **실시간 트렌드** 분석으로 급상승 키워드 발견

### 🔥 급상승 키워드 탐지
- 검색량 변화율 기반 급상승 점수 계산
- 카드 형태의 직관적인 순위 표시
- 클릭으로 상세 트렌드 분석

### 📈 시각화
- 시계열 그래프로 검색량 추이 확인
- 히트맵으로 트렌드 패턴 파악
- 여러 키워드 동시 비교

### 🔄 자동 키워드 업데이트
- 네이버 쇼핑 실시간 인기 제품에서 키워드 자동 수집
- 교체 모드 / 병합 모드 선택 가능

---

## 🚀 빠른 시작

### Streamlit Cloud 배포 (추천)

```bash
# 1. GitHub에 업로드
git clone https://github.com/YOUR_USERNAME/naver-shopping-trend.git
cd naver-shopping-trend
git add .
git commit -m "Initial commit"
git push origin main

# 2. https://share.streamlit.io 접속
# 3. New app → Repository 선택 → Deploy!

# 4. 완료! 🎉
```

**사용자는**: 링크 접속 → API 키 입력 → 바로 사용!

---

### 로컬 실행

#### Windows
```bash
# 1. 설치
install.bat

# 2. 실행
run_app.bat
```

#### Mac/Linux
```bash
# 1. 설치
chmod +x install.sh run_app.sh
./install.sh

# 2. 실행
./run_app.sh
```

---

## 🔑 API 키 발급

### 네이버 개발자 센터

1. **https://developers.naver.com** 접속
2. **로그인 / 회원가입** (무료)
3. **Application 등록**
   - 애플리케이션 이름: 네이버트렌드분석
   - 사용 API: 검색 → 데이터랩(검색어 트렌드)
4. **Client ID, Client Secret** 복사

### 앱에서 입력

- Streamlit 앱 실행
- 좌측 사이드바에서 API 키 입력
- 저장 → 바로 사용!

**✅ 보안**: API 키는 브라우저 세션에만 저장, 서버 전송 없음

자세한 내용: [`API_KEY_가이드.md`](API_KEY_가이드.md)

---

## 📂 프로젝트 구조

```
네이버_Agent/
├── streamlit_app.py              # 메인 앱
├── datalab_api.py                # DataLab API 연동
├── naver_shopping_categories.py  # 카테고리 자동 수집
├── auto_keyword_discovery.py     # 키워드 자동 발견
├── shopping_top100_crawler.py    # 쇼핑 TOP100 분석
├── selenium_crawler.py           # 셀레니움 크롤링 (백업)
├── datalab_shopping_insight.py   # 쇼핑 인사이트 API
├── requirements.txt              # 의존성 패키지
├── naver_categories_demo.json    # 데모 카테고리 데이터
├── .gitignore                    # Git 제외 파일
├── README.md                     # 이 문서
├── API_KEY_가이드.md             # API 키 사용 가이드
├── 빠른시작.md                   # 빠른 시작 가이드
├── run_app.bat / run_app.sh      # 실행 스크립트
└── install.bat / install.sh      # 설치 스크립트
```

---

## 💡 사용 방법

### 1. API 키 입력
```
좌측 사이드바 > 🔑 API 인증
→ Client ID 입력
→ Client Secret 입력
→ 💾 API 키 저장
```

### 2. 카테고리 생성 (최초 1회)
```
좌측 사이드바 > 📂 카테고리 관리
→ 📥 기본 카테고리 생성
```

### 3. 트렌드 분석
```
메인 화면 > 📂 카테고리 선택
→ 화장품/미용, 패션의류 등 선택
→ 🚀 트렌드 분석 시작
→ 급상승 키워드 확인!
```

### 4. 상세 분석
```
각 키워드 카드 아래
→ 🔍 '키워드명' 상세 분석 클릭
→ 검색량 그래프 & 통계 확인
```

---

## 📊 지원 카테고리 (9개)

- 패션의류
- 패션잡화
- 화장품/미용
- 디지털/가전
- 출산/육아
- 식품
- 스포츠/레저
- 생활/건강
- 여가/생활편의

**총 592개 키워드** (실시간 업데이트 가능)

---

## 🎨 주요 화면

### 급상승 키워드 순위
```
┌────────────────────────────────┐
│ 1  키워드A  🆕 NEW   점수: 98     │
│ 📈 검색량 +364.2% | ⭐ 42.4      │
│ ▼ 🔍 '키워드A' 상세 분석           │
└────────────────────────────────┘
```

### 트렌드 비교 차트
- **시계열 비교**: 여러 키워드 동시 비교
- **히트맵**: 날짜별 인기도 색상 표시
- **정규화 비교**: 공정한 비교를 위한 0-100 스케일

---

## 🔐 보안

### API 키 관리
```
✅ 코드에 하드코딩 없음
✅ 사용자가 UI에서 직접 입력
✅ 브라우저 세션에만 저장
✅ 서버 전송 없음
✅ GitHub 안전 공개
```

### .gitignore 포함
- API 키 파일
- 사용자 데이터
- 캐시 파일
- 백업 파일

---

## 🛠️ 기술 스택

### 프레임워크
- **Streamlit**: 웹 UI
- **Pandas**: 데이터 처리
- **Plotly**: 시각화

### API
- **Naver DataLab API**: 검색어 트렌드
- **Naver Shopping Search API**: 제품 검색
- **Selenium**: 웹 크롤링 (백업)

---

## 📦 의존성

```txt
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.17.0
requests>=2.31.0
selenium>=4.15.0
webdriver-manager>=4.0.1
python-dateutil>=2.8.2
```

설치:
```bash
pip install -r requirements.txt
```

---

## 🌐 배포

### Streamlit Cloud (무료)

**장점**:
- ✅ 완전 무료
- ✅ 자동 배포
- ✅ HTTPS 지원
- ✅ 모바일 지원

**방법**:
1. GitHub에 업로드
2. https://share.streamlit.io
3. New app → Deploy!

### 로컬 서버

**요구사항**:
- Python 3.9+
- 8501 포트

**실행**:
```bash
streamlit run streamlit_app.py --server.port=8501
```

---

## 📱 모바일 지원

### PWA (Progressive Web App)

**iPhone/iPad**:
```
Safari > 공유 버튼 > 홈 화면에 추가
→ 앱 아이콘 생성!
```

**Android**:
```
Chrome > 메뉴 > 홈 화면에 추가
→ 앱 아이콘 생성!
```

---

## 🎓 학습 자료

- [`빠른시작.md`](빠른시작.md) - 3단계 시작 가이드
- [`API_KEY_가이드.md`](API_KEY_가이드.md) - API 키 발급 & 사용법
- [네이버 DataLab API 문서](https://developers.naver.com/docs/serviceapi/datalab/search/search.md)

---

## 🤝 기여

이슈와 PR을 환영합니다!

### 개발 환경 설정
```bash
git clone https://github.com/YOUR_USERNAME/naver-shopping-trend.git
cd naver-shopping-trend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

## 🙋 FAQ

### Q: API 키가 없어도 사용할 수 있나요?
A: 아니요. 네이버 개발자 센터에서 무료로 발급받을 수 있습니다 (5분 소요).

### Q: API 호출 한도는?
A: 무료 플랜 기준 일일 25,000회, 초당 10회입니다.

### Q: 여러 명이 사용할 수 있나요?
A: 네! 각자의 API 키로 독립적으로 사용 가능합니다.

### Q: 데이터는 어디에 저장되나요?
A: API 키는 브라우저 세션에만 저장되며, 서버에 전송되지 않습니다.

### Q: 모바일에서도 사용할 수 있나요?
A: 네! 반응형 디자인으로 모바일 최적화되어 있습니다.

---

Made with ❤️ using Streamlit
