"""
네이버 쇼핑 카테고리 자동 수집 및 관리
실제 네이버 쇼핑의 카테고리 구조를 사용
"""

import requests
import urllib3
from typing import Dict, List, Set
import json
from pathlib import Path

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 네이버 쇼핑의 주요 카테고리 (실제 카테고리 ID)
NAVER_SHOPPING_CATEGORIES = {
    "패션의류": {
        "id": "50000000",
        "sub": {
            "여성의류": "50000001",
            "남성의류": "50000002",
            "언더웨어": "50000003",
            "캐주얼의류": "50000006"
        }
    },
    "패션잡화": {
        "id": "50000001",
        "sub": {
            "여성가방": "50000007",
            "남성가방": "50000008",
            "지갑": "50000009",
            "패션소품": "50000010"
        }
    },
    "화장품/미용": {
        "id": "50000002",
        "sub": {
            "스킨케어": "50000011",
            "메이크업": "50000012",
            "향수": "50000013",
            "남성화장품": "50000015",
            "네일": "50000016",
            "뷰티소품": "50000017"
        }
    },
    "식품": {
        "id": "50000006",
        "sub": {
            "농수축산물": "50000029",
            "가공식품": "50000030",
            "건강식품": "50000031"
        }
    },
    "생활/건강": {
        "id": "50000010",
        "sub": {
            "생활용품": "50000049",
            "건강용품": "50000050",
            "의료용품": "50000051",
            "건강식품": "50000052"
        }
    },
    "출산/육아": {
        "id": "50000011",
        "sub": {
            "기저귀": "50000056",
            "분유": "50000057",
            "이유식": "50000058",
            "유아동의류": "50000059"
        }
    }
}


def get_category_keywords(
    client_id: str,
    client_secret: str,
    category_name: str,
    max_products: int = 100
) -> List[str]:
    """
    네이버 쇼핑 API로 특정 카테고리의 인기 키워드 자동 수집
    
    Args:
        client_id: 네이버 API Client ID
        client_secret: 네이버 API Client Secret
        category_name: 카테고리명 (예: "화장품/미용")
        max_products: 수집할 제품 수
    
    Returns:
        카테고리의 인기 키워드 리스트
    """
    keywords = set()
    
    try:
        # 카테고리명으로 검색
        url = "https://openapi.naver.com/v1/search/shop.json"
        
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }
        
        params = {
            "query": category_name,
            "display": min(max_products, 100),
            "sort": "sim"  # 유사도순
        }
        
        response = requests.get(url, headers=headers, params=params, 
                               timeout=30, verify=False)
        response.raise_for_status()
        
        data = response.json()
        
        # 제품명과 브랜드에서 키워드 추출
        for item in data.get("items", []):
            # 제목에서 태그 제거
            title = item.get("title", "")
            title = title.replace("<b>", "").replace("</b>", "")
            
            # 브랜드
            brand = item.get("brand", "")
            
            # 카테고리
            category1 = item.get("category1", "")
            category2 = item.get("category2", "")
            category3 = item.get("category3", "")
            category4 = item.get("category4", "")
            
            # 키워드 추출 (단어 단위)
            words = title.split()
            for word in words:
                # 필터링: 한글/영문 2자 이상
                word = word.strip()
                if len(word) >= 2 and (word.isalpha() or any('\uac00' <= c <= '\ud7a3' for c in word)):
                    keywords.add(word)
            
            # 브랜드 추가
            if brand and len(brand) >= 2:
                keywords.add(brand)
        
        print(f"✓ {category_name}: {len(keywords)}개 키워드 수집")
        
    except Exception as e:
        print(f"✗ {category_name} 수집 실패: {str(e)}")
    
    return list(keywords)[:50]  # 상위 50개만


def collect_all_categories(
    client_id: str,
    client_secret: str,
    save_path: str = "./naver_categories.json"
) -> Dict:
    """
    모든 네이버 쇼핑 카테고리의 키워드 자동 수집
    
    Returns:
        {카테고리명: [키워드 리스트], ...}
    """
    # 기존 데이터 로드 (백업)
    save_path = Path(save_path)
    existing_data = {}
    if save_path.exists():
        try:
            with open(save_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            print(f"📦 기존 데이터: {len(existing_data)}개 카테고리")
        except:
            pass
    
    all_keywords = existing_data.copy()  # 기존 데이터로 시작
    success_count = 0
    fail_count = 0
    
    print("="*60)
    print("🛍️ 네이버 쇼핑 카테고리 키워드 자동 수집")
    print("="*60)
    
    for major_cat, info in NAVER_SHOPPING_CATEGORIES.items():
        print(f"\n📂 {major_cat}")
        
        # 대분류 키워드 수집
        major_keywords = get_category_keywords(
            client_id, client_secret, major_cat, max_products=50
        )
        
        if major_keywords:
            all_keywords[major_cat] = major_keywords
            success_count += 1
        else:
            fail_count += 1
            print(f"  ⚠️ {major_cat}: 기존 데이터 유지")
        
        # 중분류 키워드 수집
        for sub_cat in info.get("sub", {}).keys():
            full_cat = f"{major_cat} {sub_cat}"
            sub_keywords = get_category_keywords(
                client_id, client_secret, sub_cat, max_products=50
            )
            
            if sub_keywords:
                all_keywords[full_cat] = sub_keywords
                success_count += 1
            else:
                fail_count += 1
                print(f"  ⚠️ {full_cat}: 기존 데이터 유지")
    
    # 저장 (성공한 항목이 있을 때만)
    if success_count > 0:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(all_keywords, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 저장 완료: {save_path}")
        print(f"총 {len(all_keywords)}개 카테고리, {sum(len(v) for v in all_keywords.values())}개 키워드")
        print(f"✓ 성공: {success_count}개 | ⚠️ 실패: {fail_count}개")
    else:
        print(f"\n❌ 모든 카테고리 수집 실패 - 기존 데이터 유지")
        print(f"⚠️ API 키를 확인하세요:")
        print(f"   - 네이버 개발자센터에서 '검색 > 쇼핑' API 활성화 필요")
    
    return all_keywords


def load_categories(path: str = "./naver_categories.json") -> Dict:
    """저장된 카테고리 키워드 로드"""
    path = Path(path)
    
    if not path.exists():
        return {}
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_category(
    client_id: str,
    client_secret: str,
    category_name: str,
    path: str = "./naver_categories.json"
):
    """특정 카테고리만 업데이트"""
    categories = load_categories(path)
    
    keywords = get_category_keywords(client_id, client_secret, category_name)
    categories[category_name] = keywords
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {category_name} 업데이트 완료")


if __name__ == "__main__":
    import os
    
    CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
    CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ API 키가 필요합니다!")
        print("   export NAVER_CLIENT_ID=your_id")
        print("   export NAVER_CLIENT_SECRET=your_secret")
    else:
        # 모든 카테고리 수집
        collect_all_categories(CLIENT_ID, CLIENT_SECRET)

