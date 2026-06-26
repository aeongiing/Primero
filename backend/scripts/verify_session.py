"""[여원] 저장된 로그인 세션 + 셀렉터 검증 도구.

auth/<플랫폼>.json 세션으로 등록 페이지를 열어:
  1) 로그인 페이지로 튕기지 않는지(세션 유효),
  2) 어댑터에 적힌 셀렉터가 실제로 요소를 찾는지
확인한다. 등록(submit)은 절대 누르지 않는다(읽기 전용 점검).

사용법: python scripts/verify_session.py bunjang
"""

import sys
from pathlib import Path

# backend 루트를 import 경로에 추가(scripts/ 에서 직접 실행 시 app 패키지 인식).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.platform.bunjang import BunjangAdapter
from app.services.platform.junggonara import JunggonaraAdapter

_SPECS = {
    "bunjang": BunjangAdapter.spec,
    "junggonara": JunggonaraAdapter.spec,
}


def verify(name: str) -> None:
    from playwright.sync_api import sync_playwright

    spec = _SPECS[name]
    auth = Path(__file__).resolve().parent.parent / "auth" / f"{name}.json"
    if not auth.exists():
        print(f"[오류] 세션 파일 없음: {auth} (먼저 save_login.py 실행)")
        return

    checks = [(f.key, f.selector) for f in spec.fields if f.selector]
    if spec.image_field and spec.image_field.selector:
        checks.append(("images", spec.image_field.selector))
    if spec.submit_selector:
        checks.append(("submit", spec.submit_selector))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(auth))
        page = context.new_page()
        page.goto(spec.new_listing_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3500)

        print(f"\n[{name}] 등록 페이지 도착 URL: {page.url}")
        if "login" in page.url.lower() or "signin" in page.url.lower():
            print("  ⚠️ 로그인 페이지로 튕김 → 세션이 만료/무효일 수 있음")

        print("  셀렉터 점검:")
        for key, sel in checks:
            try:
                count = page.locator(sel).count()
            except Exception as exc:
                print(f"   [에러] {key}: {sel} ({exc})")
                continue
            mark = "OK " if count > 0 else "X  "
            print(f"   [{mark}] {key}: {sel}  (count={count})")
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in _SPECS:
        print("사용법: python scripts/verify_session.py <bunjang|junggonara>")
        raise SystemExit(1)
    verify(sys.argv[1])
