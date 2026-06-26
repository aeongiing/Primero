"""[여원] 실제 등록 시험 도구 (안전 모드).

저장된 로그인 세션으로 등록 페이지를 열고, 카테고리 선택 + 입력칸 채우기를
자동 수행한다. 그다음 **멈춰서** 사용자가 브라우저를 확인하고 직접 등록 여부를
결정한다(자동 등록 안 함).

사용법: python scripts/test_publish.py bunjang

안전장치:
  - 제목에 [테스트] 표시, 가격을 매우 높게(실수 구매 방지).
  - 사용자가 터미널에 'y' 를 입력해야만 실제 '등록하기' 클릭.
  - 등록했다면 즉시 해당 플랫폼에서 삭제할 것.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.platform.bunjang import BunjangAdapter
from app.services.platform.junggonara import JunggonaraAdapter
from app.services.platform.forms import FieldKind

_SPECS = {
    "bunjang": BunjangAdapter.spec,
    "junggonara": JunggonaraAdapter.spec,
}

# 시험용 샘플 데이터(실수 구매 방지를 위해 가격 매우 높게).
_SAMPLE = {
    "bunjang": {
        "category": "여성의류 > 상의 > 니트/스웨터",
        "title": "[테스트] 삭제예정 상품 무시해주세요",
        "price": "99000000",
        "description": "자동화 테스트 등록입니다. 판매하지 않으며 곧 삭제합니다.",
        "condition": "사용감 없음",
    },
    "junggonara": {
        "category": "패션의류 > 여성의류",
        "title": "[테스트] 삭제예정 상품 무시해주세요",
        "price": "99000000",
        "description": "자동화 테스트 등록입니다. 판매하지 않으며 곧 삭제합니다.",
        "condition": "중고",
        "components": "없음",
        "trade_method": "택배거래",
    },
}


def run(name: str) -> None:
    from playwright.sync_api import sync_playwright

    spec = _SPECS[name]
    data = _SAMPLE[name]
    auth = Path(__file__).resolve().parent.parent / "auth" / f"{name}.json"
    if not auth.exists():
        print(f"[오류] 세션 파일 없음: {auth} (먼저 save_login.py 실행)")
        return

    captured = Path(__file__).resolve().parent.parent / "captured"
    captured.mkdir(exist_ok=True)

    # 업로드 테스트용 더미 이미지 생성(실제 사진 대신).
    test_image = captured / "_test_image.jpg"
    try:
        from PIL import Image
        Image.new("RGB", (800, 800), (210, 210, 210)).save(test_image)
    except Exception as exc:
        print(f"[경고] 테스트 이미지 생성 실패(사진 수동 업로드 필요): {exc}")
        test_image = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=str(auth))
        page = context.new_page()
        page.goto(spec.new_listing_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # 1) 카테고리 (컨테이너 스코프 + 정확한 텍스트로 단계 클릭)
        if spec.category_container and data.get("category"):
            try:
                if spec.category_opener:
                    page.click(spec.category_opener, timeout=5000)
                for seg in data["category"].split(">"):
                    seg = seg.strip()
                    page.click(f'{spec.category_container} li:has-text("{seg}")', timeout=7000)
                print(f"  카테고리 클릭: {data['category']}")
            except Exception as exc:
                print(f"  [경고] 카테고리 단계 실패(수동 선택 필요): {exc}")

        # 2) 입력 필드
        for f in spec.fields:
            value = data.get(f.key)
            if not value:
                continue
            try:
                if f.kind is FieldKind.select:
                    page.select_option(f.selector, value, timeout=5000)
                elif f.kind is FieldKind.radio:
                    target = f.options.get(value)
                    if target:
                        page.click(target, timeout=5000)
                elif f.kind is FieldKind.files:
                    if test_image is not None:
                        page.set_input_files(f.selector, [str(test_image)], timeout=5000)
                        print(f"  사진 업로드: {test_image.name}")
                    continue
                else:
                    page.fill(f.selector, value, timeout=5000)
                print(f"  입력: {f.key} = {value}")
            except Exception as exc:
                print(f"  [경고] {f.key} 입력 실패: {exc}")

        # 사진 업로드(spec.image_field)
        if spec.image_field and spec.image_field.selector and test_image is not None:
            try:
                page.set_input_files(spec.image_field.selector, [str(test_image)], timeout=5000)
                print(f"  사진 업로드: {test_image.name}")
            except Exception as exc:
                print(f"  [경고] 사진 업로드 실패(수동 업로드 필요): {exc}")

        print("\n" + "=" * 60)
        print("브라우저에서 폼이 잘 채워졌는지 확인하세요.")
        print("⚠️ 카테고리는 자동 선택이 비활성입니다 → 직접 골라주세요.")
        print("⚠️ 번개 '상품 상태'는 팝업이라 자동이 안 됩니다 → 직접 골라주세요.")
        print("   (중고나라 상품상태는 자동 선택됩니다.)")
        print("실제로 '등록하기' 까지 진행하려면 y 입력, 아니면 그냥 Enter.")
        print("=" * 60)
        answer = input("등록 진행? (y / Enter=취소) > ").strip().lower()

        if answer == "y":
            try:
                page.click(spec.submit_selector, timeout=5000)
                page.wait_for_timeout(5000)
                print(f"\n등록 후 URL: {page.url}")
                out = captured / f"{name}_after_submit.html"
                out.write_text(page.content(), encoding="utf-8")
                print(f"등록 후 화면 저장: {out}")
                print("⚠️ 실제 등록되었을 수 있습니다. 플랫폼에서 즉시 삭제하세요.")
            except Exception as exc:
                print(f"[오류] 등록 클릭 실패: {exc}")
        else:
            print("등록 취소(미발행).")

        input("\n브라우저를 닫으려면 Enter > ")
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in _SPECS:
        print("사용법: python scripts/test_publish.py <bunjang|junggonara>")
        raise SystemExit(1)
    run(sys.argv[1])
