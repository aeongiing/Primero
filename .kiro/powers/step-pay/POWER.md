---
name: step-pay
displayName: StepPay 결제 연동
description: 파라파라 판매 상품의 결제/정산을 위한 StepPay 결제 연동 power (추후 연결용 스캐폴드)
keywords:
  - payment
  - 결제
  - checkout
  - 정산
  - settlement
  - step pay
  - steppay
status: scaffold
---

# StepPay 결제 연동 (Power 스캐폴드)

> ⚠️ 현재는 **스캐폴드(placeholder)** 입니다. 실제 StepPay 계정·자격증명·엔드포인트가 확정되면 이 power를 활성화해 연결합니다. 지금은 코드 동작을 수행하지 않습니다.

## 목적
파라파라에서 판매가 발생했을 때 결제·정산 흐름을 StepPay로 위임하기 위한 연동 지점을 미리 마련해 둔다. 판매 동기화(`판매_동기화_모듈`)가 "판매 완료"를 확정하는 시점과 자연스럽게 맞물리도록 설계한다.

## 연동 시 채울 항목 (체크리스트)
- [ ] StepPay 가맹점 ID / API 키 (시크릿으로만 보관 — `STEPPAY_API_KEY`)
- [ ] 결제 생성 / 조회 / 환불 엔드포인트
- [ ] 웹훅 수신 엔드포인트(결제 완료 → 표준_상품 `sold` 전이 트리거)
- [ ] 정산 주기·수수료 정책
- [ ] `mcp.json`의 StepPay MCP 서버 활성화(`disabled: false`)

## 파라파라 연동 지점 (설계 정합)
- **트리거**: 외부 플랫폼 또는 파라파라 자체 판매 완료 → StepPay 결제/정산 기록.
- **SSOT**: 결제 상태는 표준_상품 상태와 정합을 유지한다. 결제 확정이 판매 완료(`sold`)의 근거가 될 수 있다.
- **보안**: StepPay 자격증명은 `시크릿_관리_모듈`로만 로드. 소스·로그에 평문 금지(steering `tech.md` 규칙 적용).
- **멱등성**: 웹훅 재전송에 대비해 결제 처리/정산은 멱등하게 구현한다.

## 활성화 방법 (추후)
1. `.kiro/powers/step-pay/mcp.json`에 StepPay MCP 서버 정보를 채우고 `disabled: false`로 변경.
2. 시크릿(`STEPPAY_API_KEY` 등)을 환경변수/시크릿 저장소에 설정.
3. Powers 패널에서 `step-pay` power를 설치/활성화.
