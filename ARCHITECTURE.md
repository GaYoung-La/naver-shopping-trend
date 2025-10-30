# 네이버 쇼핑 트렌드 분석 시스템 아키텍처

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [아키텍처 구조](#아키텍처-구조)
3. [주요 컴포넌트](#주요-컴포넌트)
4. [데이터 구조](#데이터-구조)
5. [사용 흐름](#사용-흐름)
6. [파일 구조](#파일-구조)
7. [API 통합](#api-통합)

---

## 시스템 개요

### 목적
네이버 쇼핑의 카테고리별 트렌드를 분석하여 급상승 키워드를 발견하는 시스템

### 핵심 기능
- **계층적 카테고리 관리**: 대분류 > 중분류 구조
- **자동 키워드 수집**: 네이버 쇼핑 인기 제품에서 자동 추출
- **사용자 키워드 관리**: 특정 브랜드/제품 키워드 추가
- **트렌드 분석**: 네이버 DataLab API로 검색량 트렌드 분석
- **급상승 키워드 발견**: 검색량 변화율 기반 급상승 키워드 탐지

### 기술 스택
- **Frontend**: Streamlit
- **Backend**: Python 3.x
- **API**: 네이버 쇼핑 API, 네이버 DataLab API
- **데이터**: JSON (로컬 저장)
- **시각화**: Plotly

---

## 아키텍처 구조

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   사이드바    │  │  카테고리    │  │  트렌드 분석  │  │
│  │  - API 키    │  │  - 선택      │  │  - 급상승    │  │
│  │  - 통계      │  │  - 키워드    │  │  - 시각화    │  │
│  │  - 업데이트  │  │  - 편집      │  │  - 다운로드  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 Core Components                          │
│  ┌──────────────────┐  ┌──────────────────────────┐    │
│  │ CategoryManager  │  │ Auto Keyword Discovery   │    │
│  │ - 계층 구조 관리  │  │ - 쇼핑 검색              │    │
│  │ - 키워드 CRUD    │  │ - 키워드 추출            │    │
│  │ - 병합 로직      │  │ - 계층적 수집            │    │
│  └──────────────────┘  └──────────────────────────┘    │
│  ┌──────────────────┐  ┌──────────────────────────┐    │
│  │ DataLab API      │  │ Naver Shopping API       │    │
│  │ - 트렌드 조회    │  │ - 제품 검색              │    │
│  │ - 급상승 분석    │  │ - 키워드 발견            │    │
│  └──────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Data Layer                            │
│  categories_hierarchical.json                           │
│  - 대분류/중분류 구조                                    │
│  - 자동/사용자 키워드                                    │
│  - 활성화 상태                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 주요 컴포넌트

### 1. `streamlit_app.py` (메인 앱)

**역할**: UI 및 사용자 인터랙션 처리

**주요 기능**:
- 사이드바: API 키 관리, 카테고리 통계, 자동 업데이트
- 메인 영역: 카테고리 선택, 키워드 관리, 트렌드 분석

**핵심 코드 흐름**:
```python
def main():
    # 1. CategoryManager 초기화
    if "category_manager" not in st.session_state:
        st.session_state["category_manager"] = CategoryManager()
    
    # 2. 사이드바 렌더링
    with st.sidebar:
        render_api_keys()
        render_category_stats()
        render_auto_update_button()
    
    # 3. 메인 영역 렌더링
    render_category_selection()
    render_keyword_management()
    render_analysis_section()
```

---

### 2. `category_manager.py` (카테고리 관리자)

**역할**: 계층적 카테고리 및 키워드 관리

**주요 클래스**: `CategoryManager`

**핵심 메서드**:

```python
class CategoryManager:
    def __init__(self):
        """계층적 카테고리 구조 초기화"""
        
    def get_enabled_keywords(major, sub=None):
        """
        활성화된 키워드 반환
        - 중분류 선택 시: 해당 중분류만
        - 대분류 전체 시: 대분류 + 모든 중분류 병합
        """
        
    def get_all_keywords(major, sub=None):
        """
        전체 키워드 반환
        Returns: {
            "auto": [...],      # 자동 수집
            "user": [...],      # 사용자 지정
            "enabled": [...]    # 활성화
        }
        """
        
    def add_user_keyword(major, keyword, sub=None):
        """사용자 키워드 추가"""
        
    def update_auto_keywords(major, keywords, sub=None):
        """자동 수집 키워드 업데이트 (교체 모드)"""
```

**병합 로직**:
```python
# 대분류 전체 선택 시
def get_enabled_keywords(major, sub=None):
    if sub:
        # 중분류 선택: 해당 중분류만
        return subcategories[sub]["enabled_keywords"]
    else:
        # 대분류 전체: 병합
        all_keywords = set(major_data["enabled_keywords"])
        for sub_data in subcategories.values():
            all_keywords.update(sub_data["enabled_keywords"])
        return sorted(list(all_keywords))
```

---

### 3. `auto_keyword_discovery.py` (자동 키워드 수집)

**역할**: 네이버 쇼핑에서 키워드 자동 추출

**주요 함수**:

```python
def naver_shopping_search(query, client_id, client_secret):
    """네이버 쇼핑 API 검색"""
    # 검색어로 제품 조회
    # 최대 100개 제품 반환
    
def extract_keywords_from_products(products):
    """제품 데이터에서 키워드 추출"""
    # 제목, 브랜드에서 단어 추출
    # 빈도 분석으로 의미있는 키워드 선별
    # 한글 2자 이상, 영문 3자 이상
    
def discover_trending_keywords_hierarchical(
    client_id, client_secret, categories, manager
):
    """계층적 키워드 수집"""
    # 1. 대분류별로 키워드 수집
    # 2. 중분류별로 키워드 수집
    # 3. CategoryManager에 직접 저장
```

**수집 프로세스**:
```
1. 대분류 키워드 수집
   └─ "화장품" 검색 → 100개 제품
   └─ 키워드 추출 → 50개 선별
   
2. 중분류 키워드 수집
   ├─ "스킨케어" 검색 → 50개 제품 → 50개 키워드
   ├─ "메이크업" 검색 → 50개 제품 → 50개 키워드
   └─ "향수" 검색 → 50개 제품 → 50개 키워드
```

---

### 4. `datalab_api.py` (트렌드 분석)

**역할**: 네이버 DataLab API를 통한 검색량 트렌드 분석

**주요 함수**:

```python
def datalab_keyword_trend(
    client_id, client_secret, keywords, 
    start_date, end_date
):
    """네이버 DataLab API 호출"""
    # 최대 5개 키워드 동시 조회
    # 시계열 검색량 데이터 반환
    
def find_rising_keywords(
    client_id, client_secret, keywords,
    start_date, end_date, topk=20
):
    """급상승 키워드 분석"""
    # 키워드를 5개씩 배치로 조회
    # 시작/종료 시점 검색량 비교
    # 변화율 계산
    # 상위 topk개 반환
```

**급상승 계산 로직**:
```python
first = timeline[0]["ratio"]  # 시작 시점
last = timeline[-1]["ratio"]   # 종료 시점

abs_change = last - first      # 절대 변화량
pct_change = (change / first) * 100  # 변화율

# 급상승 스코어 = 절대변화량 × 0.3 + 변화율 × 0.5
```

---

## 데이터 구조

### `categories_hierarchical.json`

```json
{
  "화장품/미용": {
    "auto_keywords": ["로션", "크림", "에센스", ...],
    "user_keywords": ["락토핏", "키포벨"],
    "enabled_keywords": ["로션", "크림", "락토핏", ...],
    "subcategories": {
      "스킨케어": {
        "auto_keywords": ["세럼", "토너", ...],
        "user_keywords": [],
        "enabled_keywords": ["세럼", "토너", ...]
      },
      "메이크업": {
        "auto_keywords": ["립스틱", "파운데이션", ...],
        "user_keywords": [],
        "enabled_keywords": ["립스틱", "파운데이션", ...]
      }
    }
  }
}
```

### 키워드 타입

| 타입 | 설명 | 예시 |
|------|------|------|
| `auto_keywords` | 자동 수집된 키워드 | 로션, 크림, 에센스 |
| `user_keywords` | 사용자가 추가한 키워드 | 락토핏, 키포벨 |
| `enabled_keywords` | 실제 분석에 사용되는 키워드 | auto + user 중 활성화된 것 |

### Session State 구조

```python
st.session_state = {
    "api_keys_saved": bool,           # API 키 저장 여부
    "client_id": str,                 # 네이버 Client ID
    "client_secret": str,             # 네이버 Client Secret
    "category_manager": CategoryManager,  # 카테고리 관리자
    "df_rising": DataFrame,           # 급상승 키워드 결과
    "category": str,                  # 현재 선택된 카테고리
    "analysis_params": dict,          # 분석 파라미터
    "generate_compare_chart": bool    # 차트 생성 플래그
}
```

---

## 사용 흐름

### 1. 초기 설정

```
┌─────────────────┐
│ 앱 시작          │
└────────┬────────┘
         ▼
┌─────────────────┐
│ API 키 입력      │
│ - Client ID     │
│ - Client Secret │
└────────┬────────┘
         ▼
┌─────────────────┐
│ 키워드 수집      │
│ (자동 업데이트)  │
└────────┬────────┘
         ▼
┌─────────────────┐
│ 준비 완료        │
└─────────────────┘
```

### 2. 키워드 수집

```
🔄 자동 업데이트 버튼 클릭
         ▼
┌─────────────────────────────┐
│ 대분류별 키워드 수집          │
│ - 화장품/미용 → 50개         │
│ - 패션의류 → 50개            │
│ - 식품 → 50개                │
└────────┬────────────────────┘
         ▼
┌─────────────────────────────┐
│ 중분류별 키워드 수집          │
│ - 스킨케어 → 50개            │
│ - 메이크업 → 50개            │
│ - 향수 → 50개                │
└────────┬────────────────────┘
         ▼
┌─────────────────────────────┐
│ CategoryManager에 저장       │
│ categories_hierarchical.json │
└─────────────────────────────┘
```

### 3. 카테고리 선택 및 분석

```
┌─────────────────┐
│ 카테고리 선택    │
│ - 대분류 선택    │
│ - 중분류 선택    │
└────────┬────────┘
         ▼
┌─────────────────┐       ┌──────────────────┐
│ 키워드 관리      │       │ 대분류 전체 선택  │
│ ✅ 활성화        │  OR   │ → 모든 중분류    │
│ ⬜ 비활성화      │       │    키워드 병합   │
│ ➕ 사용자 추가   │       └────────┬─────────┘
└────────┬────────┘                │
         ▼                          ▼
         └──────────┬───────────────┘
                    ▼
         ┌──────────────────┐
         │ 트렌드 분석 시작  │
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐
         │ DataLab API 호출 │
         │ - 5개씩 배치 처리 │
         │ - 검색량 조회    │
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐
         │ 급상승 키워드     │
         │ - 변화율 계산    │
         │ - 상위 N개 정렬  │
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐
         │ 결과 시각화       │
         │ - 급상승 순위    │
         │ - 시계열 차트    │
         │ - 비교 차트      │
         └──────────────────┘
```

---

## 파일 구조

```
네이버_Agent/
│
├── streamlit_app.py              # 메인 Streamlit 앱
├── category_manager.py           # 카테고리 관리 클래스
├── auto_keyword_discovery.py    # 자동 키워드 수집
├── datalab_api.py                # DataLab API 연동
├── naver_shopping_categories.py # 쇼핑 카테고리 정의
├── selenium_crawler.py           # 크롤러 (미사용)
├── shopping_top100_crawler.py   # 크롤러 (미사용)
│
├── categories_hierarchical.json  # 계층적 카테고리 데이터 (메인)
├── naver_categories.json         # 구 형식 (호환성)
├── naver_categories_demo.json   # 데모 데이터
│
├── requirements.txt              # Python 패키지
├── README.md                     # 프로젝트 설명
├── API_KEY_가이드.md             # API 키 발급 가이드
├── ARCHITECTURE.md               # 이 문서
│
├── install.bat                   # Windows 설치 스크립트
├── install.sh                    # Mac/Linux 설치 스크립트
├── run_app.bat                   # Windows 실행 스크립트
└── run_app.sh                    # Mac/Linux 실행 스크립트
```

---

## API 통합

### 1. 네이버 쇼핑 API

**용도**: 키워드 자동 수집

**엔드포인트**: `https://openapi.naver.com/v1/search/shop.json`

**요청 예시**:
```python
headers = {
    "X-Naver-Client-Id": client_id,
    "X-Naver-Client-Secret": client_secret
}
params = {
    "query": "화장품",
    "display": 100,
    "sort": "sim"  # 유사도순
}
```

**응답 처리**:
```python
for item in response["items"]:
    title = item["title"]
    brand = item["brand"]
    # 키워드 추출
```

**제한 사항**:
- 최대 100개 제품/요청
- 일일 호출 한도 존재

---

### 2. 네이버 DataLab API

**용도**: 검색량 트렌드 분석

**엔드포인트**: `https://openapi.naver.com/v1/datalab/search`

**요청 예시**:
```python
body = {
    "startDate": "2024-01-01",
    "endDate": "2024-01-31",
    "timeUnit": "date",
    "keywordGroups": [
        {"groupName": "로션", "keywords": ["로션"]},
        {"groupName": "크림", "keywords": ["크림"]}
    ]
}
```

**응답 구조**:
```json
{
  "results": [
    {
      "title": "로션",
      "data": [
        {"period": "2024-01-01", "ratio": 45.2},
        {"period": "2024-01-02", "ratio": 48.7}
      ]
    }
  ]
}
```

**제한 사항**:
- 최대 5개 키워드/요청
- 일일 호출 한도 존재
- 5개씩 배치로 처리 필요

**배치 처리 로직**:
```python
for i in range(0, len(keywords), 5):
    batch = keywords[i:i+5]
    data = datalab_keyword_trend(
        client_id, client_secret, batch,
        start_date, end_date
    )
    # 결과 처리
```

---

## 핵심 알고리즘

### 1. 급상승 스코어 계산

```python
def calculate_rising_score(
    is_new: bool,
    rank_delta: int,
    trend_delta: float,
    trend_pct: float
) -> float:
    score = 0.0
    
    if is_new:
        score += 100  # 신규 진입 보너스
    
    if rank_delta and rank_delta < 0:
        score += abs(rank_delta) * 2  # 순위 상승
    
    score += max(0, trend_pct) * 0.5    # 변화율
    score += max(0, trend_delta) * 0.3  # 절대 변화량
    
    return score
```

### 2. 키워드 병합 (대분류 전체 선택 시)

```python
def get_enabled_keywords(major: str, sub: Optional[str]):
    if sub:
        # 중분류 선택: 해당 중분류만
        return subcategories[sub]["enabled_keywords"]
    
    # 대분류 전체: 병합
    all_enabled = set()
    
    # 대분류 키워드
    all_enabled.update(major_data["enabled_keywords"])
    
    # 모든 중분류 키워드 병합
    for sub_data in subcategories.values():
        all_enabled.update(sub_data["enabled_keywords"])
    
    return sorted(list(all_enabled))  # 중복 제거 및 정렬
```

### 3. 키워드 추출

```python
def extract_keywords_from_products(products, min_freq=2):
    keywords = []
    brands = set()
    
    for product in products:
        title = product["title"]
        brand = product["brand"]
        
        # HTML 태그 제거
        title = re.sub(r'<[^>]+>', '', title)
        
        # 브랜드 수집
        if brand and len(brand) >= 2:
            brands.add(brand)
        
        # 단어 추출 (한글 2자 이상, 영문 3자 이상)
        words = re.findall(r'[가-힣]{2,}|[A-Za-z]{3,}', title)
        keywords.extend(words)
    
    # 빈도 분석
    word_freq = Counter(keywords)
    frequent_words = [
        word for word, freq in word_freq.items() 
        if freq >= min_freq
    ]
    
    # 브랜드 + 빈도 높은 단어
    return sorted(list(set(frequent_words) | brands))
```

---

## 확장 가능성

### 1. 추가 가능 기능

- **소분류 추가**: 3단계 계층 구조
- **키워드 그룹핑**: 유사 키워드 자동 그룹화
- **경쟁사 분석**: 브랜드 간 트렌드 비교
- **알림 기능**: 특정 키워드 급상승 시 알림
- **스케줄링**: 주기적 자동 업데이트
- **히스토리**: 과거 트렌드 데이터 저장

### 2. 최적화 방안

- **캐싱**: API 응답 캐싱으로 호출 횟수 감소
- **병렬 처리**: 배치 요청 병렬화
- **DB 연동**: JSON → PostgreSQL/MongoDB
- **CDN**: 정적 자원 캐싱

### 3. 배포 옵션

- **Streamlit Cloud**: 현재 사용 중 ✅
- **Docker**: 컨테이너화 배포
- **AWS/GCP**: 클라우드 배포
- **사내 서버**: 온프레미스 배포

---

## 문제 해결 가이드

### 1. API 오류

**문제**: `API 인증 실패 (401)`
```
해결:
1. Client ID/Secret 확인
2. 네이버 개발자 센터에서 API 활성화 확인
3. 쇼핑 + DataLab API 모두 활성화 필요
```

**문제**: `API 호출 한도 초과 (429)`
```
해결:
1. 일일 한도 확인
2. 다음 날 재시도
3. API 호출 횟수 최적화
```

### 2. 키워드 수집 실패

**문제**: 수집된 키워드 0개
```
해결:
1. 인터넷 연결 확인
2. API 키 유효성 확인
3. 터미널 로그 확인
4. min_freq 값 조정 (더 낮게)
```

### 3. 분석 결과 없음

**문제**: 트렌드 분석 결과 빈 DataFrame
```
해결:
1. 활성화된 키워드가 있는지 확인
2. 날짜 범위 확인 (과거 데이터만 가능)
3. 키워드가 너무 마이너한지 확인
```

---

## 버전 히스토리

### v0.1.0 (초기 버전)
- 평면 카테고리 구조
- 기본 트렌드 분석

### v0.2.0 (계층 구조)
- 대분류/중분류 계층 구조 도입
- 병합 로직 구현

### v0.3.0 (키워드 관리)
- 사용자 지정 키워드 추가
- 활성화/비활성화 기능
- 키워드 검색 필터

### v1.0.0 (현재)
- 계층적 자동 수집
- 교체 모드 전용
- 초기 상태 키워드 없음
- 안정화 및 최적화

---

## 라이선스 및 크레딧

**개발**: 종근당 데이터팀  
**API**: 네이버 개발자 센터  
**프레임워크**: Streamlit, Plotly  
**언어**: Python 3.x  

---

**작성일**: 2025-10-30  
**버전**: 1.0.0  
**문서 관리자**: AI Assistant

