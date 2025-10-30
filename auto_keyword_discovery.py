"""
네이버 쇼핑 자동 키워드 발견 시스템
실시간 인기 제품에서 키워드 추출
"""

import requests
import urllib3
from typing import List, Dict, Set
import json
from pathlib import Path
import re
from collections import Counter

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def naver_shopping_search(
    query: str,
    client_id: str,
    client_secret: str,
    display: int = 100,
    sort: str = "sim"
) -> Dict:
    """
    네이버 쇼핑 검색 API
    
    Args:
        query: 검색어
        client_id: API Client ID
        client_secret: API Client Secret
        display: 결과 개수 (최대 100)
        sort: 정렬 (sim:유사도, date:날짜, asc:가격오름차순, dsc:가격내림차순)
    
    Returns:
        API 응답
    """
    url = "https://openapi.naver.com/v1/search/shop.json"
    
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    
    params = {
        "query": query,
        "display": display,
        "sort": sort
    }
    
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30,
            verify=False
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ 검색 실패 ({query}): {str(e)}")
        return {"items": []}


def extract_keywords_from_products(products: List[Dict], min_freq: int = 2) -> List[str]:
    """
    제품 데이터에서 키워드 추출
    
    Args:
        products: 제품 목록
        min_freq: 최소 빈도 (이 횟수 이상 등장한 단어만)
    
    Returns:
        키워드 리스트
    """
    keywords = []
    brands = set()
    
    for product in products:
        title = product.get("title", "")
        brand = product.get("brand", "")
        
        # HTML 태그 제거
        title = re.sub(r'<[^>]+>', '', title)
        brand = re.sub(r'<[^>]+>', '', brand)
        
        # 브랜드명 수집
        if brand and len(brand) >= 2:
            brands.add(brand.strip())
        
        # 제목에서 의미있는 단어 추출
        # 한글 2자 이상, 영문 3자 이상
        words = re.findall(r'[가-힣]{2,}|[A-Za-z]{3,}', title)
        keywords.extend(words)
    
    # 빈도 분석
    word_freq = Counter(keywords)
    
    # 자주 등장하는 단어 + 모든 브랜드
    frequent_words = [word for word, freq in word_freq.items() if freq >= min_freq]
    
    # 중복 제거 및 정렬
    all_keywords = list(set(frequent_words) | brands)
    
    return sorted(all_keywords)


def discover_trending_keywords_hierarchical(
    client_id: str,
    client_secret: str,
    categories: Dict,
    max_keywords_per_category: int = 30,
    manager = None
) -> Dict:
    """
    계층적 카테고리별 트렌딩 키워드 자동 발견
    
    Args:
        client_id: API Client ID
        client_secret: API Client Secret
        categories: 계층적 카테고리 구조
        max_keywords_per_category: 카테고리당 최대 키워드 수
        manager: CategoryManager 인스턴스 (선택사항, 없으면 새로 생성)
    
    Returns:
        계층적 구조의 키워드
    """
    from category_manager import CategoryManager
    
    if manager is None:
        manager = CategoryManager()
    
    print("="*70)
    print("🔍 실시간 트렌드 키워드 자동 발견 (계층적)")
    print("="*70)
    
    for major_category, cat_data in categories.items():
        print(f"\n📦 {major_category}")
        
        # 대분류 키워드 수집
        if "대분류" in cat_data:
            print(f"  🏢 대분류 키워드 수집...")
            all_products = []
            
            for query in cat_data["대분류"]:
                print(f"    검색: {query}...", end=" ")
                data = naver_shopping_search(
                    query=query,
                    client_id=client_id,
                    client_secret=client_secret,
                    display=100,
                    sort="sim"
                )
                items = data.get("items", [])
                all_products.extend(items)
                print(f"✓ {len(items)}개")
            
            keywords = extract_keywords_from_products(all_products, min_freq=3)
            keywords = keywords[:max_keywords_per_category]
            
            # 대분류에 저장
            manager.update_auto_keywords(major_category, keywords, sub=None)
            
            print(f"    ✅ 대분류: {len(keywords)}개 키워드")
            print(f"       예: {', '.join(keywords[:5])}")
        
        # 중분류 키워드 수집
        if "중분류" in cat_data and cat_data["중분류"]:
            print(f"  📁 중분류 키워드 수집...")
            
            for sub_category, search_queries in cat_data["중분류"].items():
                print(f"    └─ {sub_category}:", end=" ")
                
                all_products = []
                for query in search_queries:
                    data = naver_shopping_search(
                        query=query,
                        client_id=client_id,
                        client_secret=client_secret,
                        display=50,
                        sort="sim"
                    )
                    items = data.get("items", [])
                    all_products.extend(items)
                
                keywords = extract_keywords_from_products(all_products, min_freq=2)
                keywords = keywords[:max_keywords_per_category]
                
                # 중분류에 저장
                manager.update_auto_keywords(major_category, keywords, sub=sub_category)
                
                print(f" ✓ {len(keywords)}개 ({', '.join(keywords[:3])}...)")
    
    print(f"\n{'='*70}")
    print(f"✅ 수집 완료!")
    print(f"{'='*70}")
    
    return manager.data


def discover_trending_keywords(
    client_id: str,
    client_secret: str,
    categories: Dict[str, List[str]],
    max_keywords_per_category: int = 30
) -> Dict[str, List[str]]:
    """
    카테고리별 트렌딩 키워드 자동 발견 (하위 호환성)
    
    Args:
        client_id: API Client ID
        client_secret: API Client Secret
        categories: {카테고리명: [검색어 리스트]}
        max_keywords_per_category: 카테고리당 최대 키워드 수
    
    Returns:
        {카테고리명: [자동 발견된 키워드]}
    """
    discovered = {}
    
    print("="*70)
    print("🔍 실시간 트렌드 키워드 자동 발견")
    print("="*70)
    
    for category, search_queries in categories.items():
        print(f"\n📦 {category}")
        
        all_products = []
        
        # 각 검색어로 제품 수집
        for query in search_queries:
            print(f"  검색: {query}...", end=" ")
            
            data = naver_shopping_search(
                query=query,
                client_id=client_id,
                client_secret=client_secret,
                display=100,
                sort="sim"  # 인기순
            )
            
            items = data.get("items", [])
            all_products.extend(items)
            print(f"✓ {len(items)}개")
        
        # 키워드 추출
        keywords = extract_keywords_from_products(all_products, min_freq=3)
        
        # 상위 N개만
        keywords = keywords[:max_keywords_per_category]
        
        discovered[category] = keywords
        
        print(f"  ✅ 발견: {len(keywords)}개 키워드")
        print(f"     예: {', '.join(keywords[:5])}")
    
    return discovered


def merge_with_existing_keywords(
    discovered: Dict[str, List[str]],
    existing_file: str = "./naver_categories.json",
    mode: str = "replace"
) -> Dict[str, List[str]]:
    """
    기존 키워드와 병합
    
    Args:
        discovered: 새로 발견된 키워드
        existing_file: 기존 키워드 파일
        mode: "merge" (누적) 또는 "replace" (교체, 기본값)
    
    Returns:
        병합된 키워드
    """
    # 기존 데이터 로드
    existing = {}
    existing_path = Path(existing_file)
    
    if existing_path.exists():
        try:
            with open(existing_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            print(f"\n📦 기존 데이터: {len(existing)}개 카테고리, {sum(len(v) for v in existing.values())}개 키워드")
        except:
            pass
    
    merged = {}
    
    if mode == "merge":
        # 병합 모드: 기존 + 신규 (누적)
        print("🔄 모드: 병합 (기존 키워드 유지 + 신규 추가)")
        
        for category in set(list(existing.keys()) + list(discovered.keys())):
            old_keywords = set(existing.get(category, []))
            new_keywords = set(discovered.get(category, []))
            
            # 합치기
            merged[category] = sorted(list(old_keywords | new_keywords))
    
    else:  # mode == "replace"
        # 교체 모드: 신규로만 교체 (최신 인기 키워드만 유지)
        print("🔄 모드: 교체 (최신 인기 키워드만 유지)")
        merged = discovered
    
    print(f"✅ 결과: {len(merged)}개 카테고리, {sum(len(v) for v in merged.values())}개 키워드")
    
    return merged


def save_keywords(
    keywords: Dict[str, List[str]],
    save_path: str = "./naver_categories.json",
    backup: bool = True
) -> None:
    """
    키워드 저장
    
    Args:
        keywords: 키워드 딕셔너리
        save_path: 저장 경로
        backup: 백업 생성 여부
    """
    save_path = Path(save_path)
    
    # 백업 생성
    if backup and save_path.exists():
        import shutil
        from datetime import datetime
        backup_name = f"{save_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = save_path.parent / backup_name
        shutil.copy(save_path, backup_path)
        print(f"📦 백업: {backup_path}")
    
    # 저장
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(keywords, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 저장: {save_path}")
    print(f"   총 {len(keywords)}개 카테고리, {sum(len(v) for v in keywords.values())}개 키워드")


# 카테고리별 시드 검색어 (실제 네이버 쇼핑 카테고리 구조 기반)
SEED_QUERIES = {
    "패션의류": {
        "대분류": ["패션의류", "의류"],
        "중분류": {
            "여성의류": ["여성의류", "여성옷", "레이디스"],
            "남성의류": ["남성의류", "남성옷", "맨즈"],
            "언더웨어": ["속옷", "이너웨어", "언더웨어"],
            "스포츠의류": ["스포츠의류", "운동복", "트레이닝복"],
            "아동의류": ["아동의류", "키즈의류", "유아동복"],
            "유니섹스": ["유니섹스", "남녀공용"],
            "잠옷": ["잠옷", "파자마", "홈웨어"],
            "정장": ["정장", "수트", "드레스"],
            "캐주얼": ["캐주얼", "데일리룩"]
        }
    },
    "패션잡화": {
        "대분류": ["패션잡화", "액세서리"],
        "중분류": {
            "여성가방": ["여성가방", "숄더백", "크로스백"],
            "남성가방": ["남성가방", "백팩", "비즈니스백"],
            "지갑": ["지갑", "반지갑", "장지갑"],
            "모자": ["모자", "캡", "버킷햇"],
            "벨트": ["벨트", "허리띠"],
            "양말": ["양말", "스타킹"],
            "스카프": ["스카프", "머플러", "목도리"],
            "넥타이": ["넥타이", "타이"],
            "시계": ["시계", "손목시계", "워치"],
            "선글라스": ["선글라스", "안경"],
            "쥬얼리": ["쥬얼리", "악세사리", "목걸이"]
        }
    },
    "화장품/미용": {
        "대분류": ["화장품", "코스메틱", "뷰티"],
        "중분류": {
            "스킨케어": ["스킨케어", "로션", "크림", "에센스"],
            "메이크업": ["메이크업", "립스틱", "파운데이션"],
            "클렌징": ["클렌징", "클렌저", "폼클렌징"],
            "마스크팩": ["마스크", "팩", "시트마스크"],
            "선케어": ["선크림", "자외선차단제"],
            "바디케어": ["바디로션", "바디케어", "바디워시"],
            "헤어케어": ["샴푸", "트리트먼트", "헤어케어"],
            "향수": ["향수", "퍼퓸", "프래그런스"],
            "네일": ["네일", "매니큐어", "네일케어"],
            "남성화장품": ["남성화장품", "남성스킨케어"],
            "미용소품": ["미용소품", "화장솜", "퍼프"]
        }
    },
    "디지털/가전": {
        "대분류": ["디지털", "가전", "전자기기"],
        "중분류": {
            "노트북": ["노트북", "랩탑"],
            "태블릿": ["태블릿", "아이패드"],
            "스마트폰": ["스마트폰", "핸드폰"],
            "PC주변기기": ["키보드", "마우스", "모니터"],
            "이어폰": ["이어폰", "헤드폰", "이어버드"],
            "생활가전": ["생활가전", "청소기", "에어컨"],
            "주방가전": ["주방가전", "전자레인지", "에어프라이어"],
            "영상가전": ["TV", "텔레비전"],
            "카메라": ["카메라", "DSLR"],
            "게임기": ["게임기", "콘솔"],
            "음향기기": ["스피커", "사운드바"]
        }
    },
    "가구/인테리어": {
        "대분류": ["가구", "인테리어"],
        "중분류": {
            "침대": ["침대", "매트리스"],
            "소파": ["소파", "쇼파"],
            "책상": ["책상", "데스크"],
            "의자": ["의자", "체어", "게이밍의자"],
            "수납가구": ["수납장", "서랍장", "옷장"],
            "조명": ["조명", "스탠드", "LED"],
            "커튼": ["커튼", "블라인드"],
            "러그": ["러그", "카펫"],
            "침구": ["이불", "베개", "침구세트"],
            "주방용품": ["식기", "냄비", "프라이팬"]
        }
    },
    "식품": {
        "대분류": ["식품", "먹거리"],
        "중분류": {
            "농수축산물": ["농산물", "수산물", "과일", "채소"],
            "가공식품": ["가공식품", "즉석식품"],
            "건강식품": ["건강식품", "영양제", "비타민"],
            "음료": ["음료", "음료수", "주스"],
            "커피": ["커피", "원두", "인스턴트커피"],
            "차": ["차", "티", "녹차"],
            "과자": ["과자", "스낵", "간식"],
            "베이커리": ["빵", "케이크"],
            "냉동식품": ["냉동식품", "냉동만두"],
            "밀키트": ["밀키트", "간편식", "HMR"],
            "김치": ["김치", "반찬"],
            "양념": ["양념", "소스", "조미료"]
        }
    },
    "스포츠/레저": {
        "대분류": ["스포츠", "레저", "아웃도어"],
        "중분류": {
            "운동화": ["운동화", "스니커즈", "러닝화"],
            "운동복": ["운동복", "트레이닝복", "요가복"],
            "등산": ["등산", "등산화", "배낭"],
            "캠핑": ["캠핑", "텐트", "침낭"],
            "낚시": ["낚시", "낚싯대"],
            "자전거": ["자전거", "로드바이크"],
            "수영": ["수영복", "수경"],
            "골프": ["골프", "골프채", "골프웨어"],
            "요가": ["요가매트", "요가복"],
            "헬스": ["헬스", "덤벨", "아령"],
            "구기": ["축구", "야구", "배구"]
        }
    },
    "생활/건강": {
        "대분류": ["생활건강", "건강용품"],
        "중분류": {
            "생활용품": ["생활용품", "주방용품", "욕실용품"],
            "건강용품": ["건강용품", "의료용품"],
            "의료용품": ["의료용품", "구급용품", "밴드"],
            "마사지": ["안마기", "마사지기"],
            "다이어트": ["다이어트", "체중계"],
            "건강측정": ["혈압계", "체온계"],
            "세제": ["세제", "세탁세제", "섬유유연제"],
            "화장지": ["화장지", "티슈", "물티슈"],
            "청소용품": ["청소용품", "걸레"],
            "수건": ["수건", "타올", "목욕타올"]
        }
    },
    "출산/육아": {
        "대분류": ["출산육아", "육아용품", "베이비"],
        "중분류": {
            "기저귀": ["기저귀", "유아용기저귀"],
            "분유": ["분유", "조제분유"],
            "이유식": ["이유식", "유아식"],
            "유아동의류": ["유아동의류", "아동복", "베이비복"],
            "유모차": ["유모차", "아기띠"],
            "카시트": ["카시트", "주니어시트"],
            "아기욕실": ["아기욕조", "목욕용품"],
            "완구": ["장난감", "완구"],
            "수유용품": ["젖병", "젖꼭지"],
            "임부복": ["임부복", "수유복"]
        }
    },
    "도서/음반": {
        "대분류": ["도서", "책"],
        "중분류": {
            "소설": ["소설", "문학", "베스트셀러"],
            "자기계발": ["자기계발", "성공"],
            "경제경영": ["경제", "경영", "재테크"],
            "만화": ["만화", "웹툰"],
            "아동도서": ["아동도서", "어린이책"],
            "외국어": ["외국어", "영어", "토익"],
            "수험서": ["수험서", "자격증"],
            "잡지": ["잡지", "매거진"],
            "음반": ["음반", "CD"]
        }
    },
    "완구/취미": {
        "대분류": ["완구", "취미"],
        "중분류": {
            "장난감": ["장난감", "완구"],
            "레고": ["레고", "블록"],
            "피규어": ["피규어", "프라모델"],
            "보드게임": ["보드게임", "카드게임"],
            "인형": ["인형", "봉제인형"],
            "RC": ["RC카", "드론"],
            "악기": ["악기", "기타"],
            "미술": ["미술용품", "화구"],
            "DIY": ["DIY", "공예"]
        }
    },
    "반려동물": {
        "대분류": ["반려동물", "애완동물", "펫"],
        "중분류": {
            "강아지사료": ["강아지사료", "개사료"],
            "고양이사료": ["고양이사료", "캣푸드"],
            "간식": ["반려동물간식", "펫간식"],
            "위생용품": ["배변패드", "모래"],
            "미용용품": ["반려동물샴푸", "빗"],
            "의류": ["반려동물의류", "펫패션"],
            "외출용품": ["이동가방", "목줄"],
            "장난감": ["반려동물장난감", "펫토이"],
            "하우스": ["하우스", "방석"]
        }
    },
    "자동차용품": {
        "대분류": ["자동차", "차량용품"],
        "중분류": {
            "내장용품": ["시트커버", "핸들커버"],
            "외장용품": ["썬팅", "와이퍼"],
            "전자기기": ["블랙박스", "네비게이션"],
            "세차용품": ["세차", "왁스"],
            "방향제": ["차량방향제", "방향제"],
            "수납": ["수납용품", "트렁크정리"],
            "타이어": ["타이어", "휠"],
            "오일": ["엔진오일", "오일"]
        }
    }
}


if __name__ == "__main__":
    import os
    
    CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "9LKTOG5R9F8Yx74PnZe0")
    CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "gytCGuuEeX")
    
    print("🚀 자동 키워드 발견 시작\n")
    
    # 1. 트렌딩 키워드 발견
    discovered = discover_trending_keywords(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        categories=SEED_QUERIES,
        max_keywords_per_category=50
    )
    
    print(f"\n{'='*70}")
    print("📊 발견 결과")
    print(f"{'='*70}")
    
    for category, keywords in discovered.items():
        print(f"\n{category}: {len(keywords)}개")
        print(f"  {', '.join(keywords[:10])}")
        if len(keywords) > 10:
            print(f"  ... 외 {len(keywords)-10}개")
    
    # 2. 기존 키워드와 병합
    print(f"\n{'='*70}")
    print("🔄 기존 데이터와 병합")
    print(f"{'='*70}")
    
    # 기본값: replace (최신 인기 키워드만 유지)
    # "merge"로 변경하면 기존 키워드도 유지
    merged = merge_with_existing_keywords(discovered, mode="replace")
    
    # 3. 저장
    print(f"\n{'='*70}")
    print("💾 저장")
    print(f"{'='*70}\n")
    
    save_keywords(merged, backup=True)
    
    print(f"\n{'='*70}")
    print("✨ 완료!")
    print(f"{'='*70}")
    print("\n💡 이제 Streamlit 앱을 다시 시작하면 새로운 키워드로 분석됩니다!")
    print("   streamlit run streamlit_app.py")
