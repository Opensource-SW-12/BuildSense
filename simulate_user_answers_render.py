"""
BuildSense 시뮬레이션 — Render 배포 프록시 서버 버전.

simulate_user_answers.py와 동일하게 "모니터링 기간 종료 → 추가 정보 입력 →
분석 → 보고서" 흐름을 더미 데이터로 재현하지만, 가격 조회는 로컬
(localhost:8000)이 아닌 Render에 배포된 프록시 서버를 사용한다.

dist.env(PROXY_BASE_URL=https://buildsense-proxy.onrender.com 등)를
override=True로 먼저 로드해 환경변수를 선점한다 — simulate_user_answers.py가
내부적으로 호출하는 load_dotenv()는 기본값(override=False)이라 이미 설정된
PROXY_BASE_URL/PROXY_API_KEY를 .env(로컬 주소)로 덮어쓰지 않는다. price_fetcher.py가
이 두 값을 모듈 임포트 시점에 한 번만 읽으므로, import보다 먼저 설정돼야 한다.

사용법:
    python simulate_user_answers_render.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / "dist.env", override=True)

import simulate_user_answers

if __name__ == "__main__":
    simulate_user_answers.main()
