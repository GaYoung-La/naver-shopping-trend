"""
네이버 쇼핑 검색 API를 활용한 TOP100 분석 모듈
목적: 카테고리별 인기 제품 순위를 수집하여 급상승 브랜드를 자동 감지
"""

import time
import re
import pandas as pd
import requests
import json
import urllib3
from datetime import datetime
from typing import Optional, List, Dict
from urllib.parse import quote

# SSL 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 주요 카테고리 매핑
CATEGORIES = {
    "가글": "가글",
    "치약": "치약",
    "칫솔": "칫솔",
    "비타민": "비타민",
    "유산균": "유산균",
    "마스크팩": "마스크팩",
    "선크림": "선크림",
    "샴푸": "샴푸",
}


def naver_shopping_search(
    client_id: str,
    client_secret: str,
    keyword: str,
    display: int = 100,
    start: int = 1,
    sort: str = "sim"  # sim(유사도), date(날짜), asc(가격낮은순), dsc(가격높은순)
) -> dict:
    """
    네이버 쇼핑 검색 API 호출
    
    Args:
        client_id: 네이버 API Client ID
        client_secret: 네이버 API Client Secret
        keyword: 검색 키워드
        display: 한 번에 가져올 개수 (최대 100)
        start: 시작 위치 (1~1000)
        sort: 정렬 방법
    
    Returns:
        API 응답 JSON
    """
    url = "https://openapi.naver.com/v1/search/shop.json"
    
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    
    params = {
        "query": keyword,
        "display": display,
        "start": start,
        "sort": sort
    }
    
    try:
        # SSL 검증 비활성화 (회사 보안 프록시 환경 대응)
        response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise Exception("API 인증 실패: Client ID 또는 Secret을 확인하세요")
        elif response.status_code == 429:
            raise Exception("API 호출 한도 초과: 잠시 후 다시 시도하세요")
        else:
            raise Exception(f"API 오류 ({response.status_code}): {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"네트워크 오류: {str(e)}")


def crawl_shopping_top100(
    client_id: str,
    client_secret: str,
    keyword: str,
    max_items: int = 100
) -> pd.DataFrame:
    """
    네이버 쇼핑 검색 API로 특정 키워드의 TOP100 상품을 수집
    
    Args:
        client_id: 네이버 API Client ID
        client_secret: 네이버 API Client Secret
        keyword: 검색 키워드 (예: "가글", "비타민")
        max_items: 최대 수집 개수 (최대 100)
    
    Returns:
        DataFrame with columns: [순위, 제품명, 브랜드, 가격, 리뷰수, 평점, 순위변동, URL]
    """
    results = []
    
    try:
        print(f"🔍 '{keyword}' 검색 중... (API 사용)")
        
        # 네이버 쇼핑 검색 API 호출
        data = naver_shopping_search(
            client_id=client_id,
            client_secret=client_secret,
            keyword=keyword,
            display=min(max_items, 100),  # API는 최대 100개까지
            start=1,
            sort="sim"  # 유사도순 (인기순과 유사)
        )
        
        items = data.get("items", [])
        
        if not items:
            print(f"⚠️ '{keyword}' 검색 결과가 없습니다.")
            return pd.DataFrame()
        
        print(f"✅ {len(items)}개 제품 발견")
        
        # 상품 정보 파싱
        for idx, item in enumerate(items, start=1):
            try:
                # 제품명 (HTML 태그 제거)
                product_name = re.sub(r'<[^>]+>', '', item.get("title", ""))
                
                # 브랜드 추출
                brand = extract_brand(product_name)
                if not brand:
                    brand = item.get("brand", "알수없음")
                
                # 가격
                price_str = item.get("lprice", "0")
                price = int(price_str) if price_str.isdigit() else 0
                
                # URL
                url = item.get("link", "")
                
                # 카테고리
                category1 = item.get("category1", "")
                category2 = item.get("category2", "")
                
                # 쇼핑몰
                mall_name = item.get("mallName", "")
                
                results.append({
                    "순위": idx,
                    "제품명": product_name,
                    "브랜드": brand,
                    "가격": price,
                    "리뷰수": 0,  # API에서는 리뷰수 제공 안함
                    "평점": 0,  # API에서는 평점 제공 안함
                    "순위변동": "",
                    "URL": url,
                    "카테고리1": category1,
                    "카테고리2": category2,
                    "쇼핑몰": mall_name,
                    "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                if idx % 10 == 0:
                    print(f"  → {idx}개 제품 수집 완료...")
                
            except Exception as e:
                print(f"  ⚠️ 상품 {idx} 파싱 오류: {str(e)}")
                continue
        
        print(f"✅ 총 {len(results)}개 제품 수집 완료")
        
    except Exception as e:
        print(f"❌ API 호출 오류: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return pd.DataFrame(results)


def extract_brand(product_name: str) -> str:
    """제품명에서 브랜드명 추출"""
    # 일반적으로 첫 단어가 브랜드
    if not product_name:
        return ""
    
    # 대괄호 안의 브랜드명
    match = re.search(r'\[([^\]]+)\]', product_name)
    if match:
        return match.group(1)
    
    # 첫 단어 (공백 또는 특수문자 기준)
    words = re.split(r'[\s\[\]()]+', product_name)
    return words[0] if words else ""


def compare_with_history(
    current_df: pd.DataFrame,
    history_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    현재 순위와 이전 순위를 비교하여 변동사항 계산
    
    Args:
        current_df: 현재 수집한 데이터
        history_df: 이전에 수집한 데이터 (없으면 None)
    
    Returns:
        순위변동 정보가 추가된 DataFrame
    """
    if history_df is None or history_df.empty:
        current_df["순위변동"] = "NEW"
        current_df["변동폭"] = 0
        return current_df
    
    # 브랜드 기준으로 매칭
    for idx, row in current_df.iterrows():
        brand = row["브랜드"]
        current_rank = row["순위"]
        
        # 이전 데이터에서 같은 브랜드 찾기
        prev_data = history_df[history_df["브랜드"] == brand]
        
        if prev_data.empty:
            current_df.at[idx, "순위변동"] = "🆕 NEW"
            current_df.at[idx, "변동폭"] = 0
        else:
            prev_rank = prev_data.iloc[0]["순위"]
            diff = prev_rank - current_rank  # 양수면 상승, 음수면 하락
            
            if diff > 0:
                current_df.at[idx, "순위변동"] = f"⬆️ +{diff}"
                current_df.at[idx, "변동폭"] = diff
            elif diff < 0:
                current_df.at[idx, "순위변동"] = f"⬇️ {diff}"
                current_df.at[idx, "변동폭"] = diff
            else:
                current_df.at[idx, "순위변동"] = "─"
                current_df.at[idx, "변동폭"] = 0
    
    return current_df


def find_rising_brands(
    current_df: pd.DataFrame,
    history_df: Optional[pd.DataFrame] = None,
    min_rise: int = 10
) -> pd.DataFrame:
    """
    급상승 브랜드 자동 감지
    
    Args:
        current_df: 현재 데이터
        history_df: 이전 데이터
        min_rise: 최소 상승폭 (기본 10위)
    
    Returns:
        급상승 브랜드만 필터링된 DataFrame
    """
    df_with_change = compare_with_history(current_df, history_df)
    
    # 변동폭 컬럼이 있으면 필터링
    if "변동폭" in df_with_change.columns:
        rising = df_with_change[
            (df_with_change["변동폭"] >= min_rise) | 
            (df_with_change["순위변동"].str.contains("NEW", na=False))
        ]
    else:
        rising = df_with_change.head(10)  # 히스토리 없으면 상위 10개
    
    return rising.sort_values("변동폭", ascending=False)


def save_history(df: pd.DataFrame, keyword: str, history_dir: str = "history"):
    """수집 데이터를 히스토리 파일로 저장"""
    import os
    
    os.makedirs(history_dir, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{history_dir}/{keyword}_{date_str}.csv"
    
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"💾 히스토리 저장: {filename}")
    
    return filename


def load_latest_history(keyword: str, history_dir: str = "history") -> Optional[pd.DataFrame]:
    """가장 최근 히스토리 파일 로드"""
    import os
    import glob
    
    if not os.path.exists(history_dir):
        return None
    
    pattern = f"{history_dir}/{keyword}_*.csv"
    files = sorted(glob.glob(pattern), reverse=True)
    
    if not files:
        return None
    
    try:
        df = pd.read_csv(files[0], encoding="utf-8-sig")
        print(f"📂 이전 데이터 로드: {files[0]}")
        return df
    except Exception as e:
        print(f"⚠️ 히스토리 로드 실패: {str(e)}")
        return None


def analyze_top100(keyword: str, client_id: str, client_secret: str) -> Dict:
    """
    TOP100 API 수집 + 히스토리 비교 + 급상승 감지를 한번에!
    
    Returns:
        {
            "current": 현재 TOP100 DataFrame,
            "rising": 급상승 브랜드 DataFrame,
            "summary": 요약 통계
        }
    """
    print("=" * 60)
    print(f"🔍 '{keyword}' TOP100 분석 시작")
    print("=" * 60)
    
    # 1. 현재 TOP100 API 수집
    current_df = crawl_shopping_top100(
        client_id=client_id,
        client_secret=client_secret,
        keyword=keyword,
        max_items=100
    )
    
    if current_df.empty:
        return {
            "current": current_df,
            "rising": pd.DataFrame(),
            "summary": {"error": "데이터 수집 실패"}
        }
    
    # 2. 이전 히스토리 로드
    history_df = load_latest_history(keyword)
    
    # 3. 순위 변동 계산
    current_df = compare_with_history(current_df, history_df)
    
    # 4. 급상승 브랜드 감지
    rising_df = find_rising_brands(current_df, history_df, min_rise=10)
    
    # 5. 현재 데이터를 히스토리로 저장
    save_history(current_df, keyword)
    
    # 6. 요약 통계
    summary = {
        "수집_제품수": len(current_df),
        "신규_진입": len(current_df[current_df["순위변동"].str.contains("NEW", na=False)]),
        "급상승_10위이상": len(rising_df),
        "평균_가격": int(current_df["가격"].mean()),
        "평균_리뷰수": int(current_df["리뷰수"].mean()),
        "평균_평점": round(current_df["평점"].mean(), 2),
        "수집_시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    print("\n" + "=" * 60)
    print("📊 분석 완료!")
    print("=" * 60)
    print(f"수집 제품: {summary['수집_제품수']}개")
    print(f"신규 진입: {summary['신규_진입']}개")
    print(f"급상승 (10위↑): {summary['급상승_10위이상']}개")
    print("=" * 60)
    
    return {
        "current": current_df,
        "rising": rising_df,
        "summary": summary
    }


if __name__ == "__main__":
    # 테스트 실행
    import os
    
    CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "9LKTOG5R9F8Yx74PnZe0")
    CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "gytCGuuEeX")
    
    result = analyze_top100("가글", client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    
    if not result["rising"].empty:
        print("\n🔥 급상승 브랜드:")
        print(result["rising"][["순위", "브랜드", "제품명", "순위변동", "변동폭"]].to_string(index=False))

