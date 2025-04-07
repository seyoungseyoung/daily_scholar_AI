# DailyAI Scholar

DailyAI Scholar는 매일 업로드되는 AI 관련 논문을 자동으로 수집, 분석하고 요약하여 이메일로 전송하는 시스템입니다.

## 주요 기능

- arXiv에서 최신 AI 논문 자동 수집
- 논문 품질 분석 및 순위 매기기
- 논문 내용 요약 및 한국어 번역
- HTML 형식의 보고서 생성
- 이메일을 통한 자동 배포

## 설치 방법

1. 저장소 클론:
```bash
git clone https://github.com/seyoungseyoung/daily_scholar_AI.git
cd daily_scholar_AI
```

2. 가상 환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정:
- `.env.example` 파일을 복사하여 `.env` 파일 생성
- 필요한 API 키와 이메일 설정 입력

5. 이메일 수신자 설정:
- `config/email_list.txt` 파일에 수신자 이메일 주소 추가

## 사용 방법

1. 일일 실행:
```bash
python src/daily_top10.py
```

2. 스케줄링 (선택사항):
- Windows: 작업 스케줄러 설정
- Linux/Mac: crontab 설정

## 보안 주의사항

- `.env` 파일은 절대 공개 저장소에 푸시하지 마세요
- API 키와 이메일 비밀번호는 안전하게 보관하세요
- `email_list.txt` 파일은 권한이 있는 사용자만 접근할 수 있도록 설정하세요

## 라이선스

MIT License

## 기여 방법

1. 이슈 생성
2. 포크 후 브랜치 생성
3. 변경사항 커밋
4. 풀 리퀘스트 생성

## 문의

문제가 있거나 제안사항이 있다면 이슈를 생성해주세요. 