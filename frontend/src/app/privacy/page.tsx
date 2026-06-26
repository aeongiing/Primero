export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-[800px] px-6 py-12">
      <h1 className="text-2xl font-bold">개인정보 처리방침</h1>
      <p className="mt-2 text-sm text-muted-foreground">최종 수정일: 2025년 1월 1일</p>

      <section className="mt-8 flex flex-col gap-6 text-sm leading-relaxed text-foreground">
        <div>
          <h2 className="font-semibold">1. 수집하는 개인정보</h2>
          <p className="mt-2 text-muted-foreground">
            ParaPara는 Google 로그인을 통해 이메일 주소와 Google 계정 고유 식별자를 수집합니다.
            서비스 이용 과정에서 등록된 상품 정보(제목, 설명, 사진 등)가 저장됩니다.
          </p>
        </div>

        <div>
          <h2 className="font-semibold">2. 개인정보의 이용 목적</h2>
          <p className="mt-2 text-muted-foreground">
            수집된 개인정보는 회원 식별 및 서비스 제공, 문의 응대, 서비스 개선을 위해 사용됩니다.
            수집 목적 외의 용도로 사용하거나 제3자에게 제공하지 않습니다.
          </p>
        </div>

        <div>
          <h2 className="font-semibold">3. 개인정보의 보관 기간</h2>
          <p className="mt-2 text-muted-foreground">
            회원 탈퇴 시 개인정보는 즉시 파기됩니다. 단, 관계 법령에 따라 보존이 필요한 경우 해당 기간 동안 보관합니다.
          </p>
        </div>

        <div>
          <h2 className="font-semibold">4. 개인정보의 제3자 제공</h2>
          <p className="mt-2 text-muted-foreground">
            ParaPara는 회원의 동의 없이 개인정보를 제3자에게 제공하지 않습니다.
            단, 법령에 의한 요청이 있는 경우는 예외로 합니다.
          </p>
        </div>

        <div>
          <h2 className="font-semibold">5. 쿠키 및 토큰</h2>
          <p className="mt-2 text-muted-foreground">
            서비스는 로그인 상태 유지를 위해 브라우저 로컬 스토리지에 인증 토큰을 저장합니다.
            브라우저 설정을 통해 언제든지 삭제할 수 있습니다.
          </p>
        </div>

        <div>
          <h2 className="font-semibold">6. 문의</h2>
          <p className="mt-2 text-muted-foreground">
            개인정보 처리에 관한 문의는 서비스 내 문의 채널을 통해 접수해주세요.
          </p>
        </div>
      </section>
    </main>
  );
}
