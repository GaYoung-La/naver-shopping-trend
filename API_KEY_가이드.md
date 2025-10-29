# 🔑 API 키 사용자 입력 방식

## ✅ 변경 사항

### Before (보안 취약)
```python
# 코드에 API 키 하드코딩
client_id = "9LKTOG5R9F8Yx74PnZe0"
client_secret = "gytCGuuEeX"

→ ❌ GitHub에 업로드 시 키 노출
→ ❌ 모든 사용자가 동일한 키 사용
→ ❌ 키 유출 위험
```

### After (안전)
```python
# 사용자가 UI에서 직접 입력
client_id = st.session_state.get("client_id", "")
client_secret = st.session_state.get("client_secret", "")

→ ✅ GitHub에 코드만 업로드 (키 없음)
→ ✅ 각 사용자가 자신의 키 사용
→ ✅ 브라우저 세션에만 저장 (안전)
```

---

## 🎯 장점

### 1. 보안성
```
✅ API 키가 코드에 노출되지 않음
✅ GitHub, Streamlit Cloud 등 어디든 안전하게 배포
✅ 키 유출 걱정 없음
```

### 2. 독립성
```
✅ 각 사용자가 자신의 API 키 사용
✅ API 호출 한도 독립적
✅ 비용 청구 개별적
```

### 3. 유연성
```
✅ 공개 배포 가능
✅ 누구나 자유롭게 사용
✅ API 키만 있으면 즉시 시작
```

---

## 📝 사용자 가이드

### 1단계: API 키 발급받기

#### 네이버 개발자 센터 접속
```
https://developers.naver.com
```

#### 회원가입 / 로그인
```
- 네이버 계정으로 로그인
- 무료 가입
```

#### Application 등록
```
1. [Application] 메뉴 클릭
2. [애플리케이션 등록] 버튼
3. 정보 입력:
   - 애플리케이션 이름: 네이버트렌드분석
   - 사용 API: 검색
   - 환경: PC 웹
   - 서비스 URL: http://localhost:8501 (또는 배포 URL)
4. [등록하기] 클릭
```

#### API 추가
```
1. 등록한 Application 클릭
2. [API 설정] 탭
3. "검색" 섹션에서:
   - ✅ 데이터랩(검색어 트렌드) 체크
4. [확인] 클릭
```

#### Client ID & Secret 복사
```
1. [개요] 탭
2. Client ID 복사 (예: 9LKTOG5R9F8Yx74PnZe0)
3. Client Secret 복사 (예: gytCGuuEeX)
```

---

### 2단계: 앱에서 API 키 입력

#### Streamlit 앱 실행
```bash
# 로컬
streamlit run streamlit_app.py

# 또는 배포된 URL 접속
https://your-app.streamlit.app
```

#### 좌측 사이드바에서 입력
```
🔑 API 인증

┌─────────────────────────┐
│ Client ID               │
│ [입력란]                │
└─────────────────────────┘

┌─────────────────────────┐
│ Client Secret           │
│ [••••••••] (비밀번호)   │
└─────────────────────────┘

[💾 API 키 저장]
```

#### 저장 확인
```
✅ API 키가 저장되었습니다!
🔑 API 인증 완료
Client ID: 9LKTOG5R9F...
```

---

### 3단계: 앱 사용

#### 카테고리 선택
```
📂 카테고리 선택
└─ 화장품/미용
└─ 패션의류
└─ ... (선택)
```

#### 트렌드 분석 시작
```
🚀 트렌드 분석 시작 (클릭)
→ 결과 표시
```

---

## 🔐 보안 정보

### 저장 위치
```
✅ 브라우저 세션 메모리에만 저장
✅ 서버에 전송되지 않음
✅ 데이터베이스에 저장되지 않음
✅ 로그에 기록되지 않음
```

### 유효 기간
```
- 브라우저 창을 닫으면: 삭제됨
- 페이지 새로고침: 유지됨
- 다른 브라우저: 별도로 입력 필요
```

### 주의사항
```
⚠️ API 키를 다른 사람과 공유하지 마세요
⚠️ 공개 장소에서 입력 시 주의하세요
⚠️ 의심스러운 접속 발견 시 키를 재발급 받으세요
```

---

## 🎨 사용자 경험

### 첫 접속 시
```
┌─────────────────────────────┐
│ ⚠️ API 키를 입력해주세요    │
│                             │
│ ### 🔑 시작하기             │
│                             │
│ 1. 좌측 사이드바에서        │
│    네이버 API 키 입력       │
│                             │
│ 2. API 키가 없다면:         │
│    - 네이버 개발자 센터     │
│    - 무료 회원가입          │
│    - Application 등록       │
│    - API 키 발급            │
└─────────────────────────────┘
```

### API 키 입력 후
```
┌─────────────────────────────┐
│ ✅ API 인증 완료            │
│ Client ID: 9LKTOG5R9F...    │
│                             │
│ [🔄 API 키 변경]            │
│                             │
│ ─────────────────────────   │
│                             │
│ 📂 카테고리 관리            │
│ ... (정상 사용 가능)        │
└─────────────────────────────┘
```

---

## 🚀 배포 시나리오

### Streamlit Cloud 공개 배포
```
✅ 코드에 API 키 없음
✅ GitHub에 안전하게 업로드
✅ 전 세계 누구나 사용 가능
✅ 각자의 API 키로 사용

배포 URL 예시:
https://naver-shopping-trend.streamlit.app

→ 링크만 공유하면 끝!
→ 사용자는 자신의 API 키만 입력
```

### 사내 배포
```
✅ 직원들이 각자 API 키 발급
✅ 개인별 API 호출 한도 관리
✅ 보안 정책 준수

내부 URL 예시:
http://company-server:8501

→ 사내 직원에게 URL 공유
→ 각자 API 키 입력 후 사용
```

---

## 💡 API 호출 한도

### 네이버 DataLab API
```
무료 한도:
- 일일 25,000회
- 초당 10회

→ 개인 사용에 충분
→ 여러 사용자가 각자의 키 사용 시 한도 독립적
```

### 한도 초과 시
```
오류 메시지:
"API 오류 (429): 호출 한도 초과"

해결 방법:
1. 10-30분 대기
2. 또는 다음날 사용
3. 또는 추가 API 키 발급
```

---

## 🔄 API 키 변경

### 변경이 필요한 경우
```
- 키가 유출된 것으로 의심될 때
- 다른 계정의 키를 사용하고 싶을 때
- 호출 한도를 분산하고 싶을 때
```

### 변경 방법
```
1. 사이드바에서 [🔄 API 키 변경] 클릭
2. 새로운 Client ID 입력
3. 새로운 Client Secret 입력
4. [💾 API 키 저장] 클릭
5. 완료!
```

---

## ❓ FAQ

### Q1. API 키를 잊어버렸어요
```
A. 네이버 개발자 센터에서 확인
1. https://developers.naver.com 접속
2. [Application] 메뉴
3. 등록한 Application 클릭
4. Client ID, Secret 확인
```

### Q2. API 키가 작동하지 않아요
```
A1. API 설정 확인
- 데이터랩(검색어 트렌드) API가 활성화되어 있는지 확인

A2. 복사/붙여넣기 확인
- 앞뒤 공백 없이 정확히 복사했는지 확인

A3. 네이버 개발자 센터에서 재발급
- 문제 지속 시 새 Application 등록
```

### Q3. 여러 명이 같은 키를 공유해도 되나요?
```
A. 권장하지 않습니다
- API 호출 한도가 공유됨
- 한 명이 많이 사용하면 다른 사람도 영향
- 보안상 개인 키 사용 권장
```

### Q4. 브라우저를 닫으면 다시 입력해야 하나요?
```
A. 아니요!
- 페이지 새로고침: 유지됨
- 다른 탭 열기: 유지됨
- 브라우저 완전 종료: 삭제됨 (재입력 필요)
```

### Q5. 모바일에서도 사용할 수 있나요?
```
A. 네, 가능합니다!
- 모바일 브라우저에서 접속
- 사이드바에서 API 키 입력
- 정상 사용
```

---

## 📊 개발자 정보

### 구현 코드

#### API 키 입력 폼
```python
with st.form("api_key_form"):
    client_id_input = st.text_input(
        "Client ID",
        type="default"
    )
    
    client_secret_input = st.text_input(
        "Client Secret",
        type="password"
    )
    
    submit_btn = st.form_submit_button("💾 API 키 저장")
    
    if submit_btn:
        if client_id_input and client_secret_input:
            st.session_state["client_id"] = client_id_input
            st.session_state["client_secret"] = client_secret_input
            st.session_state["api_keys_saved"] = True
            st.success("✅ API 키가 저장되었습니다!")
```

#### API 키 사용
```python
# session_state에서 가져오기
client_id = st.session_state.get("client_id", "")
client_secret = st.session_state.get("client_secret", "")

# API 호출
result = datalab_api.find_rising_keywords(
    client_id=client_id,
    client_secret=client_secret,
    keywords=keywords,
    start_date=start_date,
    end_date=end_date
)
```

---

## 🎉 요약

### 사용자 입장
```
1. 앱 접속
2. 사이드바에서 API 키 입력
3. 저장 클릭
4. 바로 사용!

→ 간단하고 안전!
```

### 배포자 입장
```
1. GitHub에 코드 업로드 (API 키 없음)
2. Streamlit Cloud에 배포
3. URL 공유
4. 끝!

→ 보안 걱정 없음!
```

### 보안
```
✅ 코드에 키 노출 없음
✅ 서버에 저장 안 함
✅ 브라우저 세션에만 존재
✅ 각 사용자가 자신의 키 사용

→ 완벽한 보안!
```

---

**이제 안심하고 공개 배포하세요!** 🚀🔒

