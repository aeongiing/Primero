"""[여원] 등록 페이지 DOM 캡처 도구.

번개장터/중고나라처럼 로그인이 필요한 사이트의 "상품 등록" 화면 구조를 떠서
파일로 저장한다. 이 결과를 보고 각 어댑터의 셀렉터를 채운다.

사용법(가상환경에서):
    python scripts/capture_dom.py bunjang https://m.bunjang.co.kr
    python scripts/capture_dom.py junggonara https://web.joongna.com

동작:
    1) 창이 뜨면 직접 로그인하고, "상품 등록(판매하기)" 페이지까지 이동한다.
    2) 터미널로 돌아와 Enter 를 누르면 현재 화면을 분석해 저장한다.
    3) backend/captured/<이름>.html 과 <이름>.controls.json 이 생성된다.

주의: 캡처 결과에는 로그인된 개인 화면이 포함될 수 있어 git 에 올리지 않는다
(.gitignore 의 captured/).
"""

import json
import sys
import time
from pathlib import Path

# 폼 컨트롤(입력/선택/버튼) 정보를 모으는 브라우저 측 스크립트.
_COLLECT_JS = r"""
() => {
  const labelFor = (el) => {
    if (el.id) {
      const l = document.querySelector(`label[for="${el.id}"]`);
      if (l) return l.innerText.trim();
    }
    const parentLabel = el.closest('label');
    return parentLabel ? parentLabel.innerText.trim() : '';
  };
  const nodes = Array.from(
    document.querySelectorAll('input, textarea, select, button, [role="button"]')
  );
  return nodes.slice(0, 400).map((el) => ({
    tag: el.tagName.toLowerCase(),
    type: el.getAttribute('type') || '',
    id: el.id || '',
    name: el.getAttribute('name') || '',
    placeholder: el.getAttribute('placeholder') || '',
    ariaLabel: el.getAttribute('aria-label') || '',
    dataTestid: el.getAttribute('data-testid') || '',
    label: labelFor(el),
    text: (el.innerText || '').trim().slice(0, 40),
  }));
}
"""


def capture(out_name: str, start_url: str | None) -> None:
    from playwright.sync_api import sync_playwright

    out_dir = Path(__file__).resolve().parent.parent / "captured"
    out_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        if start_url:
            page.goto(start_url)

        print("\n" + "=" * 60)
        print("1) 뜬 창에서 직접 로그인하세요.")
        print("2) '판매하기 / 상품 등록' 페이지까지 이동하세요.")
        print("3) 그 상태로 이 터미널에 돌아와 Enter 를 누르세요.")
        print("   (브라우저 창을 닫지 마세요! Enter 누른 뒤 자동으로 닫힙니다.)")
        print(f"   저장 위치: {out_dir}")
        print("=" * 60)
        input("준비되면 Enter > ")

        # 페이지가 로딩/이동 중이면 content() 가 실패한다. 안정될 때까지 재시도.
        url, html = "", ""
        for attempt in range(1, 8):
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            try:
                url = page.url
                html = page.content()
                break
            except Exception as exc:
                print(f"  화면이 아직 바뀌는 중... 재시도 {attempt}/7 ({type(exc).__name__})")
                time.sleep(1.5)
        else:
            print("\n[오류] 화면이 계속 바뀌어 읽지 못했습니다.")
            print("페이지 로딩이 멈춘(움직임 없는) 상태에서 Enter 를 눌러주세요.")
            browser.close()
            return

        try:
            controls = page.evaluate(_COLLECT_JS)
        except Exception as exc:
            print(f"[경고] 폼 정보 수집 실패(HTML 은 저장됨): {exc}")
            controls = []

        html_path = out_dir / f"{out_name}.html"
        json_path = out_dir / f"{out_name}.controls.json"
        html_path.write_text(html, encoding="utf-8")
        json_path.write_text(
            json.dumps({"url": url, "controls": controls}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n저장 완료:\n  {html_path}\n  {json_path}")
        print(f"현재 URL: {url}")
        print(f"수집한 입력/버튼 수: {len(controls)}")
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python scripts/capture_dom.py <이름> [시작URL]")
        raise SystemExit(1)
    name = sys.argv[1]
    start = sys.argv[2] if len(sys.argv) > 2 else None
    capture(name, start)
