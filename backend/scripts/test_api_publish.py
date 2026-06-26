"""[여원] API를 통한 실제 발행 테스트.

백엔드 서버(uvicorn)가 돌고 있는 상태에서 실행.
POST /products 로 상품을 등록하면 자동 발행이 트리거된다.

사용법:
  1) 다른 터미널에서 서버 띄우기:
     $env:DATABASE_URL="sqlite+aiosqlite:///./test.db"
     .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000

  2) 이 스크립트 실행:
     .\.venv\Scripts\python.exe scripts/test_api_publish.py

주의: 성공하면 번개장터에 진짜 매물이 올라갑니다. 올렸으면 바로 삭제하세요.
"""

import httpx
import sys

BASE = "http://localhost:8000/api/v1"

# 테스트용 상품 데이터 (가격 극단적으로 높여 실수 구매 방지)
PRODUCT = {
    "title": "[테스트] 삭제예정 빈티지 니트",
    "brand": "무인양품",
    "description": "자동화 테스트입니다. 구매하지 마세요. 곧 삭제합니다.",
    "category": "여성의류 > 상의 > 니트/스웨터",
    "condition": 8,
    "price": 99000000,
    "size": "M",
    "colors": ["베이지"],
    "materials": ["울"],
    "platforms": ["bunjang"],
}


def main():
    with httpx.Client(base_url=BASE, timeout=120) as client:
        # 인증 없이 테스트 (서버가 인증 없이 동작하도록 설정된 경우)
        # 인증이 필요하면 여기서 토큰을 설정하세요:
        # headers = {"Authorization": "Bearer <토큰>"}
        headers = {}

        print("1) 상품 등록 + 발행 시도...")
        resp = client.post("/products", json=PRODUCT, headers=headers)
        print(f"   응답 코드: {resp.status_code}")

        if resp.status_code == 401:
            print("   인증 필요! 아래 방법 중 하나:")
            print("   - Google 로그인으로 토큰 받기")
            print("   - 또는 test_publish.py 로 직접 브라우저 시험 (인증 불필요)")
            return

        if resp.status_code != 201:
            print(f"   에러: {resp.text[:300]}")
            return

        data = resp.json()
        product_id = data["id"]
        print(f"   상품 생성됨: {product_id}")
        print(f"   상태: {data['status']}")

        # 리스팅 확인
        print("\n2) 리스팅(발행 결과) 확인...")
        listings = client.get(f"/listings/{product_id}", headers=headers)
        if listings.status_code == 200:
            for li in listings.json():
                print(f"   [{li['platform']}] status={li['status']}, id={li.get('platform_product_id','')}")
        else:
            print(f"   리스팅 조회 실패: {listings.status_code}")

        print(f"\n3) 번개장터에서 매물 확인 후 삭제하세요!")
        print(f"   상품 삭제 API: DELETE {BASE}/products/{product_id}")


if __name__ == "__main__":
    main()
