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
    max_keywords_per_category: int = 30
) -> Dict:
    """
    계층적 카테고리별 트렌딩 키워드 자동 발견
    
    Args:
        client_id: API Client ID
        client_secret: API Client Secret
        categories: 계층적 카테고리 구조
        max_keywords_per_category: 카테고리당 최대 키워드 수
    
    Returns:
        계층적 구조의 키워드
    """
    from category_manager import CategoryManager
    
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


# 카테고리별 시드 검색어 (계층적 구조)
SEED_QUERIES = {
    "패션의류": {
        "대분류": ["패션의류", "의류"],
        "중분류": {
            "여성의류": ["여성의류", "여성옷", "레이디스"],
            "남성의류": ["남성의류", "남성옷", "맨즈"],
            "언더웨어": ["속옷", "이너웨어", "언더웨어"]
        }
    },
    "패션잡화": {
        "대분류": ["패션잡화", "액세서리"],
        "중분류": {
            "여성가방": ["여성가방", "숄더백", "크로스백"],
            "남성가방": ["남성가방", "백팩", "비즈니스백"],
            "지갑": ["지갑", "반지갑", "장지갑"]
        }
    },
    "화장품/미용": {
        "대분류": ["화장품", "코스메틱"],
        "중분류": {
            "스킨케어": ["스킨케어", "로션", "크림", "에센스"],
            "메이크업": ["메이크업", "립스틱", "파운데이션"],
            "향수": ["향수", "퍼퓸", "프래그런스"]
        }
    },
    "디지털/가전": {
        "대분류": ["디지털", "전자기기"],
        "중분류": {}
    },
    "식품": {
        "대분류": ["식품", "건강식품"],
        "중분류": {
            "농수축산물": ["농산물", "수산물", "축산물"],
            "가공식품": ["가공식품", "즉석식품"],
            "건강식품": ["건강식품", "영양제", "비타민"]
        }
    },
    "생활/건강": {
        "대분류": ["생활건강", "건강용품"],
        "중분류": {
            "생활용품": ["생활용품", "주방용품"],
            "건강용품": ["건강용품", "의료용품"],
            "의료용품": ["의료용품", "구급용품"]
        }
    },
    "출산/육아": {
        "대분류": ["출산육아", "육아용품"],
        "중분류": {
            "기저귀": ["기저귀", "유아용기저귀"],
            "분유": ["분유", "유아식", "이유식"],
            "이유식": ["이유식", "유아식"]
        }
    },
    "스포츠/레저": {
        "대분류": ["스포츠", "레저용품"],
        "중분류": {}
    },
    "여가/생활편의": {
        "대분류": ["생활편의", "여가용품"],
        "중분류": {}
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

