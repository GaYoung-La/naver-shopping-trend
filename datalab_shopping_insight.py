"""
네이버 DataLab 쇼핑인사이트 API
카테고리별 인기 키워드 자동 수집
"""

import requests
import urllib3
from typing import List, Dict
import json
from pathlib import Path

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_shopping_category_keywords(
    client_id: str,
    client_secret: str,
    start_date: str,
    end_date: str,
    category_name: str = None,
    category_params: List[str] = None,
    device: str = "",
    gender: str = "",
    ages: List[str] = None
) -> Dict:
    """
    네이버 DataLab 쇼핑인사이트 API로 카테고리별 키워드 조회
    
    Args:
        client_id: 네이버 API Client ID
        client_secret: 네이버 API Client Secret
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        category_name: 카테고리명 (예: "화장품/미용")
        category_params: 카테고리 파라미터 (예: ["50000002"])
        device: 디바이스 (pc, mo)
        gender: 성별 (m, f)
        ages: 연령대 리스트
    
    Returns:
        API 응답 JSON
    """
    url = "https://openapi.naver.com/v1/datalab/shopping/categories"
    
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json"
    }
    
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "date"
    }
    
    # 선택적 파라미터
    if category_name and category_params:
        body["category"] = [{
            "name": category_name,
            "param": category_params
        }]
    if device:
        body["device"] = device if device != "pc,mobile" else ""
    if gender:
        body["gender"] = gender
    if ages:
        body["ages"] = ages
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            data=json.dumps(body), 
            timeout=30, 
            verify=False
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise Exception("API 인증 실패: Client ID 또는 Secret을 확인하세요")
        elif response.status_code == 429:
            raise Exception("API 호출 한도 초과: 잠시 후 다시 시도하세요")
        else:
            raise Exception(f"API 오류 ({response.status_code}): {response.text}")
    except Exception as e:
        raise Exception(f"네트워크 오류: {str(e)}")


def extract_keywords_from_shopping_insight(
    client_id: str,
    client_secret: str,
    start_date: str,
    end_date: str,
    category_name: str,
    max_keywords: int = 50
) -> List[str]:
    """
    쇼핑인사이트에서 카테고리별 인기 키워드 추출
    
    Args:
        category_name: 카테고리명 (예: "화장품", "건강식품" 등)
        max_keywords: 최대 키워드 수
    
    Returns:
        키워드 리스트
    """
    keywords = set()
    
    try:
        # 쇼핑인사이트 API 호출
        data = get_shopping_category_keywords(
            client_id=client_id,
            client_secret=client_secret,
            start_date=start_date,
            end_date=end_date,
            category=category_name
        )
        
        # 키워드 추출 (API 응답 구조에 따라 조정 필요)
        if "results" in data:
            for result in data["results"]:
                if "keywords" in result:
                    for kw in result["keywords"]:
                        if isinstance(kw, dict) and "keyword" in kw:
                            keywords.add(kw["keyword"])
                        elif isinstance(kw, str):
                            keywords.add(kw)
        
        print(f"✓ {category_name}: {len(keywords)}개 키워드 수집")
        
    except Exception as e:
        print(f"✗ {category_name} 수집 실패: {str(e)}")
    
    return list(keywords)[:max_keywords]


def auto_collect_keywords(
    client_id: str,
    client_secret: str,
    start_date: str,
    end_date: str,
    categories: List[str],
    save_path: str = "./naver_categories.json"
) -> Dict:
    """
    여러 카테고리의 키워드 자동 수집
    
    Args:
        categories: 카테고리 리스트 (예: ["화장품", "건강식품", ...])
        save_path: 저장 경로
    
    Returns:
        {카테고리: [키워드 리스트]}
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
    
    all_keywords = existing_data.copy()
    success_count = 0
    fail_count = 0
    
    print("="*60)
    print("🛍️ 쇼핑인사이트 API로 키워드 자동 수집")
    print("="*60)
    
    for category in categories:
        keywords = extract_keywords_from_shopping_insight(
            client_id=client_id,
            client_secret=client_secret,
            start_date=start_date,
            end_date=end_date,
            category_name=category,
            max_keywords=50
        )
        
        if keywords:
            all_keywords[category] = keywords
            success_count += 1
        else:
            fail_count += 1
            if category in existing_data:
                print(f"  ⚠️ {category}: 기존 데이터 유지")
    
    # 저장
    if success_count > 0:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(all_keywords, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 저장 완료: {save_path}")
        print(f"총 {len(all_keywords)}개 카테고리, {sum(len(v) for v in all_keywords.values())}개 키워드")
        print(f"✓ 성공: {success_count}개 | ⚠️ 실패: {fail_count}개")
    else:
        print(f"\n❌ 모든 카테고리 수집 실패 - 기존 데이터 유지")
    
    return all_keywords


# 네이버 쇼핑 카테고리 코드 매핑
CATEGORY_CODES = {
    "패션의류": ["50000000"],
    "패션잡화": ["50000001"],
    "화장품/미용": ["50000002"],
    "디지털/가전": ["50000003"],
    "가구/인테리어": ["50000004"],
    "출산/육아": ["50000005"],
    "식품": ["50000006"],
    "스포츠/레저": ["50000007"],
    "생활/건강": ["50000010"],
    "여가/생활편의": ["50000011"],
}

# 기본 카테고리 목록
DEFAULT_CATEGORIES = list(CATEGORY_CODES.keys())


if __name__ == "__main__":
    import os
    from datetime import datetime, timedelta
    
    CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "9LKTOG5R9F8Yx74PnZe0")
    CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "gytCGuuEeX")
    
    # 기간 설정 (최근 30일)
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=30)
    
    print("🔍 쇼핑인사이트 API 테스트")
    print(f"기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print()
    
    # 테스트: 화장품/미용 카테고리
    try:
        category_params = CATEGORY_CODES["화장품/미용"]
        
        data = get_shopping_category_keywords(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            category_name="화장품/미용",
            category_params=category_params
        )
        
        print(f"\n✅ API 응답 성공!")
        print(f"\n응답 구조:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
        print("\n...")
        
        # 카테고리 트렌드 확인
        if "results" in data:
            print(f"\n카테고리 데이터: {len(data['results'])}개")
            for result in data["results"]:
                print(f"  - {result.get('title', 'N/A')}")
                if "data" in result:
                    print(f"    데이터 포인트: {len(result['data'])}개")
        
    except Exception as e:
        print(f"\n❌ 실패: {e}")
        print("\n💡 쇼핑인사이트 API는 카테고리 클릭 트렌드를 제공합니다.")
        print("   키워드 목록은 검색어 트렌드 API나 JSON 파일로 관리하는 것을 권장합니다.")

