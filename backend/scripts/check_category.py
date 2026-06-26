"""[여원] 카테고리 자동 선택 눈으로 확인 도구.

지정한 카테고리 경로를 실제 판매 폼에서 단계별 클릭하고, 브라우저를 띄워둔 채
멈춘다(등록은 하지 않음). 사용자가 직접 잘 선택됐는지 눈으로 확인한다.

사용법:
    python scripts/check_category.py bunjang "여성의류 > 상의 > 니트/스웨터"
    python scripts/check_category.py bunjang            (기본 샘플 사용)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.platform.bunjang import BunjangAdapter
from app.services.platform.junggonara import JunggonaraAdapter

_SPECS = {"bunjang": BunjangAdapter.spec, "junggonara": JunggonaraAdapter.spec}
_SAMPLE = {
    "bunjang": "여성의류 > 상의 > 니트/스웨터",
    "junggonara": "패션의류 > 여성의류",
}


def run(name: str, category: str) -> None:
    from playwright.sync_api import sync_playwright

    spec = _SPECS[name]
    auth = Path(__file__).resolve().parent.parent / "auth" / f"{name}.json"
    if not auth.exists():
        print(f"[오류] 세션 파일 없음: {auth}")
        return
    if not spec.category_container:
        print(f"[안내] {name} 은 아직 카테고리 자동 선택 미지원(container 없음).")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 눈으로 보도록 창 표시
        context = browser.new_context(storage_state=str(auth))
        page = context.new_page()
        page.goto(spec.new_listing_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        print(f"\n[{name}] 카테고리 선택 시도: {category}")
        for seg in category.split(">"):
            seg = seg.strip()
            target = f'{spec.category_container} li:has-text("{seg}")'
            try:
                page.click(target, timeout=7000)
                print(f"  [OK ] {seg}")
            except Exception as exc:
                print(f"  [실패] {seg}: {type(exc).__name__} → 직접 확인 필요")
                break
        print(f"  현재 URL: {page.url}")
        print("\n브라우저에서 카테고리가 올바르게 선택됐는지 확인하세요.")
        input("확인 후 Enter 누르면 창을 닫습니다 > ")
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in _SPECS:
        print('사용법: python scripts/check_category.py <bunjang|junggonara> ["A > B > C"]')
        raise SystemExit(1)
    name = sys.argv[1]
    category = sys.argv[2] if len(sys.argv) > 2 else _SAMPLE[name]
    run(name, category)
