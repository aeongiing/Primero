"""[여원] 트리거 팝업(상품상태/사이즈 등) 옵션 캡처 도구.

판매 폼의 특정 섹션(예: #scroll-condition, #scroll-option) 트리거 버튼을 자동
클릭해 팝업을 연 뒤, 그 안의 짧은 텍스트 클릭 요소들을 경로와 함께 떠온다.
등록은 하지 않는다.

사용법: python scripts/capture_trigger.py bunjang scroll-condition
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.platform.bunjang import BunjangAdapter
from app.services.platform.junggonara import JunggonaraAdapter

_SPECS = {"bunjang": BunjangAdapter.spec, "junggonara": JunggonaraAdapter.spec}

_COLLECT_JS = r"""
() => {
  function cssPath(el) {
    const parts = [];
    while (el && el.nodeType === 1 && parts.length < 7) {
      let sel = el.tagName.toLowerCase();
      if (el.id) { parts.unshift(sel + '#' + el.id); break; }
      const cls = (typeof el.className === 'string' && el.className.trim())
        ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '';
      let nth = 1, sib = el;
      while ((sib = sib.previousElementSibling)) { if (sib.tagName === el.tagName) nth++; }
      parts.unshift(sel + cls + ':nth-of-type(' + nth + ')');
      el = el.parentElement;
    }
    return parts.join(' > ');
  }
  const els = Array.from(document.querySelectorAll('button,li,a,[role="option"],[role="button"],label,span'));
  const seen = new Set();
  const out = [];
  for (const el of els) {
    const t = (el.innerText || '').trim();
    if (!t || t.length > 14) continue;
    const key = el.tagName + '|' + t + '|' + cssPath(el);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ tag: el.tagName.toLowerCase(), text: t.slice(0, 24),
               cls: (typeof el.className === 'string' ? el.className : '').slice(0, 60),
               path: cssPath(el) });
  }
  return out.slice(0, 250);
}
"""


def run(name: str, section: str) -> None:
    from playwright.sync_api import sync_playwright

    spec = _SPECS[name]
    auth = Path(__file__).resolve().parent.parent / "auth" / f"{name}.json"
    out_dir = Path(__file__).resolve().parent.parent / "captured"
    out_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(auth))
        page = context.new_page()
        page.goto(spec.new_listing_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # 섹션 내 트리거 버튼 클릭(팝업 열기)
        trigger = f"#{section} button"
        try:
            page.locator(trigger).first.click(timeout=6000)
            page.wait_for_timeout(1500)
            print(f"트리거 클릭: {trigger}")
        except Exception as exc:
            print(f"[경고] 트리거 클릭 실패: {exc}")

        items = page.evaluate(_COLLECT_JS)
        out = out_dir / f"{name}_{section}.json"
        out.write_text(json.dumps({"url": page.url, "items": items}, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        print(f"저장: {out} ({len(items)}개)")
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python scripts/capture_trigger.py <platform> <section_id>")
        raise SystemExit(1)
    run(sys.argv[1], sys.argv[2])
