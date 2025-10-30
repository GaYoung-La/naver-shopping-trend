"""
네이버 쇼핑 트렌드 분석
- 네이버 쇼핑의 실제 카테고리 자동 수집
- 카테고리별 인기 키워드 자동 추출
- 실시간 트렌드 분석
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from pathlib import Path

# 로컬 모듈
from datalab_api import find_rising_keywords, get_keyword_timeline
from naver_shopping_categories import (
    NAVER_SHOPPING_CATEGORIES,
    get_category_keywords,
    collect_all_categories
)
from category_manager import CategoryManager


def test_api_connection(client_id: str, client_secret: str) -> bool:
    """
    API 키가 유효한지 간단히 테스트
    
    Args:
        client_id: 네이버 API 클라이언트 ID
        client_secret: 네이버 API 클라이언트 Secret
    
    Returns:
        bool: API 키가 유효하면 True, 아니면 False
    """
    from datetime import datetime, timedelta
    
    try:
        # 간단한 테스트: 최근 7일, 단일 키워드
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=7)
        
        from datalab_api import datalab_keyword_trend
        
        result = datalab_keyword_trend(
            client_id=client_id,
            client_secret=client_secret,
            keywords=["비타민"],  # 테스트용 간단한 키워드
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            time_unit="date"
        )
        
        # 정상 응답이면 True
        return "results" in result and len(result["results"]) > 0
    
    except Exception as e:
        print(f"API 테스트 실패: {str(e)}")
        return False


def calculate_rising_score(is_new: bool, rank_delta, trend_delta: float, trend_pct: float) -> float:
    """
    급상승 스코어 계산
    
    Args:
        is_new: 신규 진입 여부
        rank_delta: 순위 변화
        trend_delta: 검색량 절대 변화
        trend_pct: 검색량 변화율(%)
    
    Returns:
        float: 급상승 스코어
    """
    score = 0.0
    
    if is_new:
        score += 100
    
    if rank_delta is not None and rank_delta < 0:
        score += abs(rank_delta) * 2
    
    score += max(0, trend_pct) * 0.5
    score += max(0, trend_delta) * 0.3
    
    return score

# 페이지 설정
st.set_page_config(
    page_title="네이버 쇼핑 트렌드 분석 (자동)",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #03C75A 0%, #00B140 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .rising-card {
        background: white;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        padding: 10px 12px;
        margin: 6px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        transition: all 0.2s;
    }
    .rising-card:hover {
        box-shadow: 0 3px 8px rgba(0,0,0,0.12);
        transform: translateY(-1px);
    }
    
    .rising-rank {
        font-size: 1.5rem;
        font-weight: bold;
        color: #03C75A;
        display: inline-block;
        min-width: 35px;
    }
    
    .rising-keyword {
        font-size: 1.05rem;
        font-weight: 600;
        color: #333;
        margin-left: 8px;
    }
    
    .rising-badge-new {
        background: #ff4444;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-left: 8px;
    }
    
    .rising-badge-up {
        color: #ff4444;
        font-weight: bold;
        margin-left: 8px;
    }
    
    .rising-stat {
        color: #666;
        font-size: 0.85rem;
        margin-top: 3px;
    }
</style>
""", unsafe_allow_html=True)


def render_rising_keyword_card(rank: int, keyword: str, is_new: bool, 
                                 rank_delta: int, score: float, 
                                 trend_pct: float, avg_value: float):
    """실시간 급상승 스타일 카드 (Streamlit 네이티브 컴포넌트 사용)"""
    
    # 컨테이너로 카드 스타일 구현
    with st.container():
        # 순위와 키워드를 한 줄에
        col1, col2, col3 = st.columns([0.5, 3, 1])
        
        with col1:
            st.markdown(f"<h2 style='color: #03C75A; margin: 0;'>{rank}</h2>", 
                       unsafe_allow_html=True)
        
        with col2:
            badge_text = ""
            if is_new:
                badge_text = "🆕 NEW"
            elif rank_delta < 0:
                badge_text = f"🔺 {abs(rank_delta)}"
            
            st.markdown(f"<h4 style='margin: 0; padding-top: 5px;'>{keyword} {badge_text}</h4>", 
                       unsafe_allow_html=True)
        
        with col3:
            if score > 0:
                st.metric("점수", f"{score:.0f}", delta=None, delta_color="off")
        
        # 통계 정보
        stats_parts = []
        if trend_pct > 0:
            stats_parts.append(f"📈 검색량 {trend_pct:+.1f}%")
        if avg_value > 0:
            stats_parts.append(f"⭐ 평균 {avg_value:.1f}")
        
        if stats_parts:
            st.caption(" | ".join(stats_parts))
        
        st.divider()


def main():
    """메인 앱"""
    
    # CategoryManager 초기화 (앱 시작 시 한 번만)
    if "category_manager" not in st.session_state:
        st.session_state["category_manager"] = CategoryManager()
    
    st.markdown('<div class="main-header">🛍️ 네이버 쇼핑 트렌드 분석</div>', 
                unsafe_allow_html=True)
    
    # 설명
    st.info("""
    🎯 **자동 카테고리 분석**
    - 네이버 쇼핑의 **실제 카테고리**를 자동으로 가져옵니다
    - 각 카테고리의 **인기 키워드**를 자동으로 수집합니다
    - **실시간 트렌드**를 분석하여 급상승 키워드를 찾습니다
    """)
    
    # === 사이드바 ===
    with st.sidebar:
        st.header("🔑 API 인증")
        
        # session_state 초기화
        if "api_keys_saved" not in st.session_state:
            st.session_state["api_keys_saved"] = False
        
        # API 키 입력 폼
        with st.form("api_key_form"):
            client_id_input = st.text_input(
                "Client ID",
                type="default",
                help="네이버 개발자 센터에서 발급받은 Client ID"
            )
            
            client_secret_input = st.text_input(
                "Client Secret",
                type="password",
                help="네이버 개발자 센터에서 발급받은 Client Secret"
            )
            
            submit_btn = st.form_submit_button("💾 API 키 저장", use_container_width=True)
            
            if submit_btn:
                if client_id_input and client_secret_input:
                    st.session_state["client_id"] = client_id_input
                    st.session_state["client_secret"] = client_secret_input
                    st.session_state["api_keys_saved"] = True
                    st.success("✅ API 키가 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ Client ID와 Client Secret을 모두 입력하세요!")
        
        # 저장된 API 키 표시
        if st.session_state.get("api_keys_saved", False):
            st.success("🔑 API 인증 완료")
            st.caption(f"Client ID: {st.session_state['client_id'][:10]}...")
            
            # API 키 변경 버튼
            if st.button("🔄 API 키 변경", use_container_width=True):
                st.session_state["api_keys_saved"] = False
                st.rerun()
        else:
            st.warning("⚠️ API 키를 입력하세요")
        
        # API 키 가져오기
        client_id = st.session_state.get("client_id", "")
        client_secret = st.session_state.get("client_secret", "")
        
        st.divider()
        
        # 분석 설정
        st.header("⚙️ 분석 설정")
        
        # 기간
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=30)
        
        date_range = st.date_input(
            "분석 기간",
            value=(start_date, end_date),
            max_value=end_date
        )
        
        if len(date_range) == 2:
            start_date_str = date_range[0].strftime("%Y-%m-%d")
            end_date_str = date_range[1].strftime("%Y-%m-%d")
        else:
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
        
        # 급상승 개수
        topk = st.slider(
            "표시할 개수",
            min_value=5,
            max_value=50,
            value=20,
            step=5
        )
        
        st.divider()
        
        # 키워드 자동 업데이트
        st.header("🔄 키워드 업데이트")
        
        if st.button("🔄 실시간 인기 제품으로 키워드 자동 업데이트", 
                        type="primary", 
                        use_container_width=True,
                        help="대분류와 중분류별로 키워드를 자동으로 수집합니다"):
                
                with st.spinner("🔍 대분류/중분류별 키워드 수집 중... (시간이 걸릴 수 있습니다)"):
                    try:
                        # auto_keyword_discovery 모듈 import
                        from auto_keyword_discovery import (
                            discover_trending_keywords_hierarchical,
                            SEED_QUERIES
                        )
                        
                        # 계층적 키워드 자동 발견 (대분류 + 중분류)
                        # session_state의 manager를 전달
                        manager = st.session_state["category_manager"]
                        updated_data = discover_trending_keywords_hierarchical(
                            client_id=client_id,
                            client_secret=client_secret,
                            categories=SEED_QUERIES,
                            max_keywords_per_category=50,
                            manager=manager
                        )
                        
                        # CategoryManager 새로고침 (파일에서 다시 로드)
                        st.session_state["category_manager"] = CategoryManager()
                        manager = st.session_state["category_manager"]
                        stats = manager.get_stats()
                        
                        st.success(f"""
                        ✅ 계층적 키워드 자동 수집 완료!
                        
                        - 대분류: {stats['대분류']}개
                        - 중분류: {stats['중분류']}개
                        - 자동 키워드: {stats['자동 키워드']}개
                        - 활성화 키워드: {stats['활성화 키워드']}개
                        """)
                        
                        # 페이지 새로고침
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ 자동 업데이트 실패: {str(e)}")
                        
                        # 상세 오류
                        with st.expander("🔧 상세 오류"):
                            import traceback
                            st.code(traceback.format_exc())
        
        st.divider()
        
        # 카테고리 관리
        st.header("📂 카테고리 관리")
        
        # CategoryManager 통계 표시
        manager = st.session_state["category_manager"]
        stats = manager.get_stats()
        
        # 키워드가 있는지 확인
        has_keywords = stats['활성화 키워드'] > 0
        
        if has_keywords:
            st.success(f"✅ 키워드 수집 완료")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("대분류", f"{stats['대분류']}개")
                st.metric("중분류", f"{stats['중분류']}개")
            with col2:
                st.metric("자동 키워드", f"{stats['자동 키워드']}개")
                st.metric("활성화", f"{stats['활성화 키워드']}개")
        else:
            st.warning("⚠️ 키워드 없음")
            st.info("""
            💡 **먼저 키워드를 수집하세요**
            
            위의 "키워드 업데이트" 버튼을 클릭하여
            대분류와 중분류별로 키워드를 자동 수집합니다.
            """)
    
    # === 메인 영역 ===
    
    # API 키 확인
    if not client_id or not client_secret:
        st.warning("⚠️ **API 키를 입력해주세요**")
        st.info("""
        ### 🔑 시작하기
        
        1. **좌측 사이드바**에서 네이버 API 키를 입력하세요
        2. API 키가 없다면:
           - [네이버 개발자 센터](https://developers.naver.com) 접속
           - 무료 회원가입 및 Application 등록
           - 검색 > 데이터랩(검색어 트렌드) API 추가
           - Client ID와 Client Secret 발급
        
        ### 📝 사용 방법
        - API 키를 입력하면 바로 사용 가능합니다
        - 입력한 API 키는 **브라우저 세션에만 저장**됩니다
        - 서버나 다른 곳에 저장되지 않아 **안전**합니다
        """)
        
        return
    
    # 카테고리 관리자 가져오기 (이미 main()에서 초기화됨)
    manager = st.session_state["category_manager"]
    
    # 카테고리 선택
    st.markdown("### 📂 카테고리 선택")
    
    # 계층적 카테고리 선택
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 대분류 선택
        major_categories = manager.get_major_categories()
        selected_major = st.selectbox(
            "🏢 대분류",
            options=major_categories,
            help="분석할 대분류 카테고리를 선택하세요"
        )
    
    with col2:
        # 중분류 선택
        sub_categories = manager.get_subcategories(selected_major)
        if sub_categories:
            selected_sub = st.selectbox(
                "📁 중분류",
                options=["[대분류 전체]"] + sub_categories,
                help="중분류를 선택하거나 대분류 전체를 분석하세요"
            )
            if selected_sub == "[대분류 전체]":
                selected_sub = None
        else:
            selected_sub = None
            st.info("중분류 없음")
    
    with col3:
        # 키워드 통계
        keywords_info = manager.get_all_keywords(selected_major, selected_sub)
        total_keywords = len(keywords_info["enabled"])
        
        # 대분류 전체 선택 시 병합 정보 표시
        if not selected_sub:
            subcategories = manager.get_subcategories(selected_major)
            if subcategories:
                st.metric("활성 키워드", f"{total_keywords}개", delta="병합")
                st.caption(f"💡 대분류 + {len(subcategories)}개 중분류")
            else:
                st.metric("활성 키워드", f"{total_keywords}개")
        else:
            st.metric("활성 키워드", f"{total_keywords}개")
    
    # 키워드 관리 섹션
    st.markdown("---")
    st.markdown("### 🔧 키워드 관리")
    
    # 키워드가 없으면 안내 메시지
    if total_keywords == 0:
        st.warning("""
        ⚠️ **키워드가 없습니다!**
        
        키워드를 수집해야 트렌드 분석을 시작할 수 있습니다.
        """)
        
        st.info("""
        ### 🚀 시작하기
        
        1. **왼쪽 사이드바** 열기
        2. **API 키 입력** (네이버 개발자 센터)
        3. **"🔄 키워드 자동 업데이트"** 버튼 클릭
        4. 대분류와 중분류별로 자동 수집 (1-2분 소요)
        5. 키워드 수집 완료 후 **트렌드 분석** 시작!
        """)
        
        # 바로 가기 버튼
        if st.button("📖 API 키 발급 가이드 보기", use_container_width=True):
            st.markdown("""
            ### 네이버 API 키 발급 방법
            
            1. [네이버 개발자 센터](https://developers.naver.com) 접속
            2. 로그인 → "Application" → "애플리케이션 등록"
            3. 애플리케이션 이름 입력
            4. 사용 API 선택:
               - ✅ 검색 > 쇼핑
               - ✅ 검색 > 데이터랩(검색어 트렌드)
            5. Client ID와 Client Secret 복사
            6. 왼쪽 사이드바에 입력!
            """)
        
        return  # 키워드가 없으면 여기서 종료
    
    # 탭으로 구분
    tab1, tab2, tab3 = st.tabs(["📋 전체 키워드", "🤖 자동 수집", "✏️ 사용자 지정"])
    
    with tab1:
        # 전체 키워드 보기 및 활성화/비활성화
        st.markdown("#### 전체 키워드 목록")
        
        all_keywords = keywords_info["auto"] + keywords_info["user"]
        enabled_keywords = set(keywords_info["enabled"])
        
        if all_keywords:
            # 검색 필터
            search_term = st.text_input("🔍 키워드 검색", placeholder="검색어 입력...")
            
            if search_term:
                all_keywords = [kw for kw in all_keywords if search_term.lower() in kw.lower()]
            
            st.caption(f"총 {len(all_keywords)}개 키워드 (활성: {len(enabled_keywords)}개)")
            
            # 키워드 목록 (체크박스로 활성화/비활성화)
            cols = st.columns(4)
            for idx, keyword in enumerate(sorted(all_keywords)):
                with cols[idx % 4]:
                    is_enabled = keyword in enabled_keywords
                    is_user = keyword in keywords_info["user"]
                    
                    # 체크박스
                    new_state = st.checkbox(
                        f"{'👤' if is_user else '🤖'} {keyword}",
                        value=is_enabled,
                        key=f"kw_{idx}_{keyword}",
                        help="👤=사용자 지정, 🤖=자동 수집"
                    )
                    
                    # 상태 변경 시 업데이트
                    if new_state != is_enabled:
                        if new_state:
                            manager.enable_keyword(selected_major, keyword, selected_sub)
                        else:
                            manager.disable_keyword(selected_major, keyword, selected_sub)
                        st.rerun()
        else:
            st.info("키워드가 없습니다. 자동 수집을 실행하거나 사용자 지정 키워드를 추가하세요.")
    
    with tab2:
        # 자동 수집 키워드
        st.markdown("#### 🤖 자동 수집 키워드")
        
        auto_keywords = keywords_info["auto"]
        
        st.caption(f"총 {len(auto_keywords)}개")
        
        if auto_keywords:
            # 3열로 표시
            cols = st.columns(3)
            for idx, kw in enumerate(auto_keywords):
                is_enabled = kw in enabled_keywords
                status = "✅" if is_enabled else "⬜"
                cols[idx % 3].markdown(f"{status} {kw}")
        else:
            st.info("자동 수집된 키워드가 없습니다.")
        
        # 자동 수집 버튼 (사이드바에 있지만 여기서도 제공)
        if st.button("🔄 지금 자동 수집 실행", type="secondary", use_container_width=True):
            st.info("사이드바의 '🔄 실시간 인기 제품으로 키워드 자동 업데이트' 버튼을 사용하세요.")
    
    with tab3:
        # 사용자 지정 키워드
        st.markdown("#### ✏️ 사용자 지정 키워드")
        
        user_keywords = keywords_info["user"]
        
        st.caption(f"총 {len(user_keywords)}개")
        
        # 키워드 추가
        col_a, col_b = st.columns([3, 1])
        
        with col_a:
            new_keyword = st.text_input(
                "새 키워드 추가",
                placeholder="키워드 입력...",
                key="new_keyword_input"
            )
        
        with col_b:
            st.write("")  # 여백
            st.write("")  # 여백
            if st.button("➕ 추가", type="primary", use_container_width=True):
                if new_keyword:
                    success = manager.add_user_keyword(selected_major, new_keyword, selected_sub)
                    if success:
                        st.success(f"✅ '{new_keyword}' 추가 완료!")
                        st.rerun()
                    else:
                        st.error("❌ 키워드 추가 실패")
                else:
                    st.warning("⚠️ 키워드를 입력하세요")
        
        # 사용자 키워드 목록
        if user_keywords:
            st.markdown("**등록된 키워드:**")
            
            for keyword in user_keywords:
                col_kw, col_del = st.columns([4, 1])
                
                with col_kw:
                    is_enabled = keyword in enabled_keywords
                    status = "✅" if is_enabled else "⬜"
                    st.markdown(f"{status} {keyword}")
                
                with col_del:
                    if st.button("🗑️", key=f"del_{keyword}", help=f"'{keyword}' 삭제"):
                        manager.remove_user_keyword(selected_major, keyword, selected_sub)
                        st.success(f"'{keyword}' 삭제됨")
                        st.rerun()
        else:
            st.info("사용자 지정 키워드가 없습니다. 위에서 추가하세요.")
        
    st.divider()
    
    # 분석 실행
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        analyze_btn = st.button(
            "🚀 트렌드 분석 시작",
            type="primary",
            use_container_width=True
        )
    
    if analyze_btn:
        if not client_id or not client_secret:
            st.error("❌ API 키를 입력하세요!")
            return
        
        # 활성화된 키워드 가져오기
        keywords = manager.get_enabled_keywords(selected_major, selected_sub)
        
        if not keywords:
            category_name = f"{selected_major}" + (f" > {selected_sub}" if selected_sub else "")
            st.warning(f"⚠️ '{category_name}' 카테고리에 활성화된 키워드가 없습니다.")
            st.info("키워드를 추가하거나 활성화하세요.")
            return
        
        category_name = f"{selected_major}" + (f" > {selected_sub}" if selected_sub else "")
        
        with st.spinner(f"🔍 '{category_name}' 트렌드 분석 중..."):
            try:
                # 분석 정보
                st.info(f"""
                📊 **분석 정보**
                - 카테고리: {category_name}
                - 키워드: {len(keywords)}개
                - 기간: {start_date_str} ~ {end_date_str}
                """)
                
                # 급상승 분석
                # 상세 정보 표시
                st.write(f"🔍 분석 시작: {len(keywords)}개 키워드")
                
                # 로그 영역 생성
                log_placeholder = st.empty()
                log_placeholder.info("📋 터미널 로그를 확인하세요...")
                
                df_rising = find_rising_keywords(
                    client_id=client_id,
                    client_secret=client_secret,
                    keywords=keywords,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    topk=topk
                )
                
                log_placeholder.empty()  # 로그 메시지 제거
                
                if df_rising.empty:
                    st.error("❌ 분석 결과가 없습니다.")
                    
                    # 원인 진단
                    with st.expander("🔍 문제 진단", expanded=True):
                        st.markdown("""
                        ### 가능한 원인:
                        
                        1. **API 키 문제**
                           - Client ID 또는 Secret이 잘못되었을 수 있습니다
                           - [네이버 개발자 센터](https://developers.naver.com)에서 확인하세요
                        
                        2. **API 호출 한도 초과**
                           - 네이버 DataLab API는 일일 호출 한도가 있습니다
                           - 잠시 후 다시 시도하세요
                        
                        3. **키워드 문제**
                           - 키워드가 비어있거나 유효하지 않을 수 있습니다
                           - 다른 카테고리를 선택해보세요
                        
                        4. **네트워크 오류**
                           - 인터넷 연결을 확인하세요
                        
                        ### 해결 방법:
                        
                        1. **API 키 테스트**: 아래 버튼으로 API 키가 유효한지 확인하세요
                        2. **키워드 업데이트**: 사이드바에서 "🔄 키워드 자동 업데이트" 실행
                        3. **다른 카테고리 선택**: 다른 카테고리로 시도해보세요
                        """)
                        
                        # API 키 테스트 버튼
                        if st.button("🧪 API 키 테스트", type="secondary"):
                            test_result = test_api_connection(client_id, client_secret)
                            if test_result:
                                st.success("✅ API 키가 정상적으로 작동합니다!")
                            else:
                                st.error("❌ API 키가 유효하지 않습니다. Client ID와 Secret을 확인하세요.")
                    
                    return
                
                # 급상승 스코어 계산
                df_rising["rising_score"] = df_rising.apply(
                    lambda row: calculate_rising_score(
                        is_new=False,
                        rank_delta=None,
                        trend_delta=row["abs_change"],
                        trend_pct=row["pct_change"]
                    ),
                    axis=1
                )
                
                df_rising = df_rising.sort_values("rising_score", ascending=False).head(topk)
                
                # 세션에 저장
                st.session_state["df_rising"] = df_rising
                st.session_state["category"] = category_name
                st.session_state["analysis_params"] = {
                    "keywords": keywords,
                    "start_date": start_date_str,
                    "end_date": end_date_str
                }
                
                st.success(f"✅ {len(df_rising)}개 급상승 키워드 발견!")
                
            except Exception as e:
                st.error(f"❌ 분석 실패: {str(e)}")
                import traceback
                with st.expander("🔧 상세 오류"):
                    st.code(traceback.format_exc())
                return
        
    # === 결과 표시 ===
    if "df_rising" in st.session_state:
        df_rising = st.session_state["df_rising"]
        category = st.session_state["category"]
        params = st.session_state["analysis_params"]
        
        st.markdown("---")
        st.markdown(f"## 📊 {category} - 급상승 키워드")
        
        # 두 컬럼
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 🔥 실시간 급상승 순위")
            
            # 표시할 개수 선택
            display_count = min(10, len(df_rising))
        
            # 상위 N개 표시
            for idx, row in df_rising.head(display_count).iterrows():
                rank = idx + 1
                keyword = row["keyword"]
            
                # 카드 렌더링
                render_rising_keyword_card(
                    rank=rank,
                    keyword=keyword,
                    is_new=False,
                    rank_delta=0,
                    score=row["rising_score"],
                    trend_pct=row["pct_change"],
                    avg_value=row["last_ratio"]
                )
            
                # 상세 분석 Expander (카드 안에서 토글)
                with st.expander(f"🔍 '{keyword}' 상세 분석", expanded=False):
                    try:
                        # 키워드 타임라인 가져오기
                        timeline_df = get_keyword_timeline(
                            keywords=[keyword],
                            start_date=params["start_date"],
                            end_date=params["end_date"],
                            client_id=client_id,
                            client_secret=client_secret
                        )
                    
                        if not timeline_df.empty:
                            # 컴팩트한 시계열 그래프
                            fig = px.line(
                                timeline_df.reset_index(),
                                x="date",
                                y=keyword,
                                title=f"검색량 추이",
                                labels={"date": "날짜", keyword: "검색량"}
                            )
                            fig.update_traces(line_color="#03C75A", line_width=2)
                            fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                            st.plotly_chart(fig, use_container_width=True)
                        
                            # 통계 (컴팩트)
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("평균", f"{timeline_df[keyword].mean():.1f}", 
                                        delta=None, delta_color="off")
                            with col_b:
                                st.metric("최대", f"{timeline_df[keyword].max():.1f}",
                                        delta=None, delta_color="off")
                            with col_c:
                                st.metric("표준편차", f"{timeline_df[keyword].std():.1f}",
                                        delta=None, delta_color="off")
                        else:
                            st.warning("⚠️ 데이터를 불러올 수 없습니다.")
                
                    except Exception as e:
                        st.error(f"❌ 오류: {str(e)}")
        
            # 나머지 키워드 (11위 이하)
            if len(df_rising) > display_count:
                with st.expander(f"📋 {display_count+1}위 ~ {len(df_rising)}위 보기 ({len(df_rising)-display_count}개)"):
                    for idx, row in df_rising.iloc[display_count:].iterrows():
                        rank = idx + 1
                        keyword = row['keyword']
                    
                        # 컴팩트한 표시
                        col_rank, col_keyword, col_change = st.columns([1, 3, 2])
                    
                        with col_rank:
                            st.markdown(f"**{rank}위**")
                        with col_keyword:
                            st.markdown(f"**{keyword}**")
                        with col_change:
                            change_color = "🔴" if row['pct_change'] > 0 else "🔵"
                            st.markdown(f"{change_color} {row['pct_change']:+.1f}%")
                    
                        # 간단한 정보 표시
                        st.caption(f"검색량 평균: {row['last_ratio']:.1f} | 급상승 점수: {row['rising_score']:.1f}")
                        st.markdown("---")
    
        with col2:
            st.markdown("#### 📈 검색량 변화 상위")
        
            # 변화율 차트
            fig = px.bar(
                df_rising.head(10),
                x="pct_change",
                y="keyword",
                orientation="h",
                color="pct_change",
                color_continuous_scale="Reds",
                labels={"pct_change": "변화율 (%)", "keyword": "키워드"},
                title=f"{category} 검색량 변화율 Top 10"
            )
            fig.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
            # 요약 통계
            st.markdown("#### 📊 요약 통계")
        
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("평균 증가율", f"{df_rising['pct_change'].mean():.1f}%")
            with col_b:
                st.metric("최대 증가율", f"{df_rising['pct_change'].max():.1f}%")
            with col_c:
                st.metric("분석 키워드", f"{len(params['keywords'])}개")
    
        # 급상승 키워드 비교 차트
        st.markdown("---")
        st.markdown("## 📊 급상승 키워드 트렌드 비교")
    
        # 비교할 키워드 수 선택
        col_setting1, col_setting2 = st.columns([3, 1])
    
        with col_setting1:
            compare_count = st.slider(
                "비교할 키워드 수",
                min_value=3,
                max_value=min(10, len(df_rising)),
                value=min(5, len(df_rising)),
                help="상위 N개 급상승 키워드의 검색량 추이를 비교합니다"
            )
    
        with col_setting2:
            if st.button("🔄 차트 생성", type="primary", use_container_width=True):
                st.session_state["generate_compare_chart"] = True
    
        # 차트 생성
        if st.session_state.get("generate_compare_chart", False):
            with st.spinner(f"상위 {compare_count}개 키워드 데이터 로딩 중..."):
                try:
                    # 상위 키워드 선택
                    top_keywords = df_rising.head(compare_count)["keyword"].tolist()
                
                    # 타임라인 데이터 조회
                    timeline_df = get_keyword_timeline(
                        keywords=top_keywords,
                        start_date=params["start_date"],
                        end_date=params["end_date"],
                        client_id=client_id,
                        client_secret=client_secret
                    )
                
                    if not timeline_df.empty:
                        # 탭으로 여러 차트 제공
                        tab1, tab2, tab3 = st.tabs(["📈 시계열 비교", "📊 히트맵", "📉 정규화 비교"])
                    
                        with tab1:
                            st.markdown("### 📈 시계열 트렌드 비교")
                            st.caption("각 키워드의 검색량 추이를 직접 비교합니다")
                        
                            # 멀티 라인 차트
                            fig_line = go.Figure()
                        
                            colors = px.colors.qualitative.Set2
                            for idx, keyword in enumerate(top_keywords):
                                fig_line.add_trace(go.Scatter(
                                    x=timeline_df.index,
                                    y=timeline_df[keyword],
                                    name=keyword,
                                    mode='lines+markers',
                                    line=dict(width=2, color=colors[idx % len(colors)]),
                                    marker=dict(size=4)
                                ))
                        
                            fig_line.update_layout(
                                title=f"급상승 Top {compare_count} 키워드 검색량 비교",
                                xaxis_title="날짜",
                                yaxis_title="검색량 지수",
                                hovermode='x unified',
                                height=500,
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                )
                            )
                        
                            st.plotly_chart(fig_line, use_container_width=True)
                    
                        with tab2:
                            st.markdown("### 📊 검색량 히트맵")
                            st.caption("키워드별 검색량의 상대적 강도를 색상으로 표현합니다")
                        
                            # 히트맵 데이터 준비 (날짜를 짧게)
                            heatmap_data = timeline_df.copy()
                            # 인덱스를 datetime으로 변환 후 포맷
                            heatmap_data.index = pd.to_datetime(heatmap_data.index).strftime('%m/%d')
                        
                            fig_heatmap = px.imshow(
                                heatmap_data.T,
                                labels=dict(x="날짜", y="키워드", color="검색량"),
                                x=heatmap_data.index,
                                y=top_keywords,
                                color_continuous_scale="YlOrRd",
                                aspect="auto"
                            )
                        
                            fig_heatmap.update_layout(
                                title=f"급상승 키워드 검색량 히트맵",
                                height=400
                            )
                        
                            st.plotly_chart(fig_heatmap, use_container_width=True)
                    
                        with tab3:
                            st.markdown("### 📉 정규화 트렌드 비교")
                            st.caption("각 키워드의 검색량을 0-100 범위로 정규화하여 트렌드 패턴을 비교합니다")
                        
                            # 정규화 (각 키워드를 0-100 스케일로)
                            normalized_df = timeline_df.copy()
                            for col in normalized_df.columns:
                                min_val = normalized_df[col].min()
                                max_val = normalized_df[col].max()
                                if max_val > min_val:
                                    normalized_df[col] = ((normalized_df[col] - min_val) / (max_val - min_val)) * 100
                                else:
                                    normalized_df[col] = 50
                        
                            fig_normalized = go.Figure()
                        
                            for idx, keyword in enumerate(top_keywords):
                                fig_normalized.add_trace(go.Scatter(
                                    x=normalized_df.index,
                                    y=normalized_df[keyword],
                                    name=keyword,
                                    mode='lines',
                                    line=dict(width=2, color=colors[idx % len(colors)])
                                ))
                        
                            fig_normalized.update_layout(
                                title=f"정규화된 트렌드 패턴 비교",
                                xaxis_title="날짜",
                                yaxis_title="정규화 점수 (0-100)",
                                hovermode='x unified',
                                height=500,
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                )
                            )
                        
                            st.plotly_chart(fig_normalized, use_container_width=True)
                    
                        # 인사이트
                        st.markdown("### 💡 인사이트")
                    
                        col_insight1, col_insight2, col_insight3 = st.columns(3)
                    
                        with col_insight1:
                            st.markdown("#### 🏆 최고 검색량")
                            max_values = timeline_df.max()
                            max_keyword = max_values.idxmax()
                            max_value = max_values.max()
                            st.info(f"**{max_keyword}**\n\n{max_value:.1f}")
                    
                        with col_insight2:
                            st.markdown("#### 📈 가장 안정적")
                            std_values = timeline_df.std()
                            stable_keyword = std_values.idxmin()
                            stable_std = std_values.min()
                            st.info(f"**{stable_keyword}**\n\n표준편차 {stable_std:.1f}")
                    
                        with col_insight3:
                            st.markdown("#### 📊 평균 검색량")
                            avg_values = timeline_df.mean()
                            avg_keyword = avg_values.idxmax()
                            avg_value = avg_values.max()
                            st.info(f"**{avg_keyword}**\n\n{avg_value:.1f}")
                    
                        # 데이터 다운로드
                        with st.expander("📋 비교 데이터 다운로드"):
                            csv_compare = timeline_df.reset_index().to_csv(index=False, encoding="utf-8-sig")
                            st.download_button(
                                label="📥 비교 데이터 CSV 다운로드",
                                data=csv_compare,
                                file_name=f"compare_keywords_{category}_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                
                    else:
                        st.warning("⚠️ 비교 데이터를 불러올 수 없습니다.")
            
                except Exception as e:
                    st.error(f"❌ 비교 차트 생성 실패: {str(e)}")
                    with st.expander("🔧 상세 오류"):
                        import traceback
                        st.code(traceback.format_exc())
    
        # 데이터 다운로드
        st.markdown("---")
        st.markdown("### 💾 데이터 다운로드")
    
        csv = df_rising.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name=f"rising_keywords_{category}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()

