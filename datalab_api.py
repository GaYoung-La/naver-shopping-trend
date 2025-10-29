"""
네이버 DataLab 검색어 트렌드 API를 활용한 급상승 키워드 분석 모듈
"""

import os
import json
import requests
import urllib3
import pandas as pd
from datetime import datetime
from typing import List, Optional

# SSL 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def datalab_keyword_trend(
    client_id: str,
    client_secret: str,
    keywords: List[str],
    start_date: str,  # "YYYY-MM-DD"
    end_date: str,    # "YYYY-MM-DD"
    time_unit: str = "date",  # "date" | "week" | "month"
    device: str = "pc,mobile",  # "pc" | "mobile" | "pc,mobile"
    gender: str = "",           # "" | "m" | "f"
    ages: Optional[List[str]] = None  # e.g. ["10","20","30","40","50","60"]
) -> dict:
    """
    네이버 DataLab 검색어 트렌드 API 호출.
    참고: https://developers.naver.com/docs/serviceapi/datalab/search/search.md
    
    Args:
        client_id: 네이버 API 클라이언트 ID
        client_secret: 네이버 API 클라이언트 Secret
        keywords: 검색할 키워드 리스트 (최대 5개)
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        time_unit: 시간 단위 (date, week, month)
        device: 디바이스 (pc, mobile, pc,mobile)
        gender: 성별 ("", "m", "f")
        ages: 연령대 리스트
    
    Returns:
        API 응답 JSON
    """
    if ages is None:
        ages = []
    
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json"
    }
    
    # 각 키워드를 개별 그룹으로 생성
    if isinstance(keywords, str):
        keywords = [keywords]
    
    # 네이버 API는 최대 5개 그룹까지 허용
    if len(keywords) > 5:
        raise ValueError("네이버 DataLab API는 한 번에 최대 5개 키워드만 조회 가능합니다.")
    
    groups = [{"groupName": kw, "keywords": [kw]} for kw in keywords]
    
    body = {
        "startDate": start_date,  # YYYY-MM-DD 형식 유지
        "endDate": end_date,      # YYYY-MM-DD 형식 유지
        "timeUnit": time_unit,
        "keywordGroups": groups,
    }
    
    # device: "" (전체), "pc" (PC), "mo" (모바일) 중 하나
    if device:
        # "pc,mobile"을 ""으로, "mobile"을 "mo"로 변환
        if device == "pc,mobile" or device == "":
            pass  # device 파라미터를 추가하지 않음 (기본값이 전체)
        elif device == "mobile":
            body["device"] = "mo"
        elif device == "pc":
            body["device"] = "pc"
    
    # 성별이나 연령대가 지정된 경우에만 추가
    if gender:
        body["gender"] = gender
    if ages:
        body["ages"] = ages
    
    try:
        # SSL 검증 비활성화 (회사 보안 프록시 환경 대응)
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30, verify=False)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 401:
            raise Exception("API 인증 실패: Client ID 또는 Secret을 확인하세요")
        elif resp.status_code == 429:
            raise Exception("API 호출 한도 초과: 잠시 후 다시 시도하세요")
        elif resp.status_code == 400:
            raise Exception(f"잘못된 요청: {resp.text}")
        else:
            raise Exception(f"API 오류 ({resp.status_code}): {resp.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"네트워크 오류: {str(e)}")


def find_rising_keywords(
    client_id: str,
    client_secret: str,
    keywords: List[str],
    start_date: str,
    end_date: str,
    time_unit: str = "date",
    device: str = "pc,mobile",
    gender: str = "",
    ages: Optional[List[str]] = None,
    topk: int = 20
) -> pd.DataFrame:
    """
    조회 기간의 첫 시점 대비 마지막 시점의 상대 검색량 변화를 계산해
    증가폭(마지막 - 처음)이 큰 순으로 정렬 → '급상승' 리스트 반환
    
    Args:
        client_id: 네이버 API 클라이언트 ID
        client_secret: 네이버 API 클라이언트 Secret
        keywords: 검색할 키워드 리스트
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        time_unit: 시간 단위
        device: 디바이스
        gender: 성별
        ages: 연령대
        topk: 상위 N개 키워드
    
    Returns:
        급상승 키워드 DataFrame
    """
    all_rows = []
    total_batches = (len(keywords) + 4) // 5  # 올림 계산
    success_count = 0
    error_count = 0
    
    print(f"\n🔍 분석 시작: {len(keywords)}개 키워드 ({total_batches}개 배치)")
    
    # 키워드를 5개씩 나누어 API 호출
    for i in range(0, len(keywords), 5):
        batch = keywords[i:i+5]
        batch_num = i//5 + 1
        
        print(f"\n📦 배치 {batch_num}/{total_batches}: {', '.join(batch[:2])}{'...' if len(batch) > 2 else ''}")
        
        try:
            data = datalab_keyword_trend(
                client_id=client_id,
                client_secret=client_secret,
                keywords=batch,
                start_date=start_date,
                end_date=end_date,
                time_unit=time_unit,
                device=device,
                gender=gender,
                ages=ages
            )
            
            for series in data["results"]:
                kw = series["title"]
                timeline = series["data"]
                
                if not timeline:
                    print(f"   ⚠️  '{kw}': 데이터 없음")
                    continue
                
                first = timeline[0]["ratio"]
                last = timeline[-1]["ratio"]
                change = last - first
                
                # 변화율 계산
                if first > 0:
                    change_pct = (change / first * 100)
                elif last > 0:
                    change_pct = float('inf')
                else:
                    change_pct = 0
                
                # 평균 검색량
                avg_ratio = sum(t["ratio"] for t in timeline) / len(timeline)
                
                all_rows.append({
                    "keyword": kw,
                    "first_ratio": first,
                    "last_ratio": last,
                    "abs_change": change,
                    "pct_change": round(change_pct, 2),
                    "avg_ratio": round(avg_ratio, 2)
                })
                
                print(f"   ✅ '{kw}': 변화 {change:+.1f} ({change_pct:+.1f}%)")
            
            success_count += 1
            
        except Exception as e:
            error_count += 1
            error_msg = str(e)
            print(f"\n❌ 배치 {batch_num}/{total_batches} 처리 중 오류!")
            print(f"   키워드: {', '.join(batch)}")
            print(f"   오류: {error_msg}")
            
            # 구체적인 에러 메시지
            if "API 인증 실패" in error_msg or "401" in error_msg:
                print("   💡 해결: API 인증 정보를 확인하세요 (Client ID/Secret)")
                print("   → https://developers.naver.com에서 확인")
            elif "429" in error_msg or "한도 초과" in error_msg:
                print("   💡 해결: API 호출 한도를 초과했습니다")
                print("   → 잠시 후 다시 시도하세요")
            elif "400" in error_msg:
                print("   💡 해결: 잘못된 요청입니다")
                print("   → 날짜 형식과 키워드를 확인하세요")
            
            continue
    
    print(f"\n📊 분석 완료: 성공 {success_count}/{total_batches}, 실패 {error_count}/{total_batches}")
    print(f"   수집된 키워드: {len(all_rows)}개\n")
    
    if not all_rows:
        print("⚠️  경고: 분석 결과가 비어있습니다!")
        print("   가능한 원인:")
        print("   1. API 인증 실패 (Client ID/Secret 확인)")
        print("   2. API 호출 한도 초과 (잠시 후 재시도)")
        print("   3. 모든 키워드에 대한 데이터 없음")
        print("   4. 네트워크 오류\n")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_rows).sort_values(["abs_change", "pct_change"], ascending=False)
    df = df.reset_index(drop=True)
    
    # 상위 topk개를 급상승으로 라벨링
    df["label"] = ["급상승"] * min(len(df), topk) + ["정상"] * max(0, len(df) - topk)
    
    return df


def get_keyword_timeline(
    client_id: str,
    client_secret: str,
    keywords: List[str],
    start_date: str,
    end_date: str,
    time_unit: str = "date",
    device: str = "pc,mobile",
    gender: str = "",
    ages: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    키워드별 시계열 데이터를 반환
    
    Returns:
        날짜별 키워드 검색량 DataFrame (wide format)
    """
    all_timelines = {}
    
    # 키워드를 5개씩 나누어 API 호출
    for i in range(0, len(keywords), 5):
        batch = keywords[i:i+5]
        try:
            data = datalab_keyword_trend(
                client_id=client_id,
                client_secret=client_secret,
                keywords=batch,
                start_date=start_date,
                end_date=end_date,
                time_unit=time_unit,
                device=device,
                gender=gender,
                ages=ages
            )
            
            for series in data["results"]:
                kw = series["title"]
                timeline = series["data"]
                all_timelines[kw] = {t["period"]: t["ratio"] for t in timeline}
        except Exception as e:
            print(f"배치 {i//5 + 1} 처리 중 오류: {str(e)}")
            continue
    
    if not all_timelines:
        return pd.DataFrame()
    
    # DataFrame으로 변환
    df = pd.DataFrame(all_timelines)
    df.index.name = "date"
    # date를 인덱스로 유지 (reset_index 제거)
    
    return df


# 기본 키워드 풀 (예시)
DEFAULT_KEYWORDS = {
    "화장품/미용": [
        "로션", "바이오더마", "피지오겔", "아벤느", "에스트라",
        "마녀공장", "닥터지", "시카크림", "선크림", "비타민C",
        "레티놀", "히알루론산", "나이아신아마이드", "세럼", "앰플",
        "토너", "에센스", "클렌징", "팩", "마스크팩"
    ],
    "건강/의약품": [
        "비타민", "유산균", "오메가3", "프로폴리스", "홍삼",
        "루테인", "콜라겐", "마그네슘", "철분", "아연",
        "타이레놀", "게보린", "이지엔6", "베아제", "닥터베아제"
    ],
    "식품": [
        "프로틴", "쉐이크", "견과류", "다크초콜릿", "올리브오일",
        "아몬드", "꿀", "현미", "귀리", "치아씨드"
    ],
    "생활/건강": [
        # 위생용품
        "마스크", "손소독제", "알콜솜", "물티슈", "세정제",
        # 의료용품
        "체온계", "혈압계", "혈당측정기", "파스", "밴드", "붕대",
        # 구강용품
        "칫솔", "치약", "가글", "가그린", "리스테린", "페리오가드", "헥사메딘",
        # 생활용품
        "비누", "샴푸", "린스",
        # 여성용품
        "생리대", "탐폰", "생리컵",
        # 건강관리
        "찜질팩", "냉찜질", "온열팩", "안마기", "족욕기"
    ],
    "종근당 제품": [
        # 영양제/건강기능식품
        "키포벨", "키포벨산", "락토핏",
        # 외용제/피부약
        "더마그램", 
        # 해열진통제
        "펜잘",
        # 소화제/위장약
        "속청",
        # 비타민/신경통약
        "벤포벨",
        # 비염/감기약
        "모드알레", "모드콜",
        # 무좀약
        "에피나벨",
        # 관절/뼈 건강
        "뮤코다",
        # 기타
        "텔미트랜", "두테스몰"
    ]
}

