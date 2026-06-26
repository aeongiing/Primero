export default function TermsPage() {
  return (
    <main className="mx-auto max-w-[800px] px-6 py-12">
      <h1 className="text-2xl font-bold">이용약관</h1>
      <p className="mt-2 text-sm text-muted-foreground">최종 수정일: 2025년 1월 1일</p>

      <section className="mt-8 flex flex-col gap-6 text-sm leading-relaxed text-foreground">
        <div>
          <h2 className="font-semibold">제1조 (목적)</h2>
          <p className="mt-2 text-muted-foreground">
            본 약관은 ParaPara(이하 "서비스")가 제공하는 중고 의류 멀티 플랫폼 자동 등록 서비스의 이용 조건 및 절차,
            회원과 서비스 간의 권리·의무 및 책임 사항을 규정함을 목적으로 합니다.
          </p>
        </div>

        <div>
          <h2 className="font-semibold">제2조 (서비스 내용)</h2>
          <p className="mt-2 text-muted-foreground">
            ParaPara는 회원이 등록한 상품 정보를 번개장터, 중고나라, eBay 등 복수의 플랫폼에 자동으로 등록·관리할 수 있는
            도구를 제공합니다. 서비스는 각 플랫폼의 이용약관 범위 내에서 운영됩니다.
          </p>
        </div>

        <div>
          <h2 className="font-semibold">제3조 (회원 가입 및 계정)</h2>
          <p className="mt-2 text-muted-foreground">
            서비스는 Google 계정을 통한 소셜 로그인으로 가입할 수 있습니다. 회원은 자신의 계정 정보를 안전하게 관리할
            책임이 있으며, 타인에게 계정을 양도하거나 공유할 수 없습니다.
          </p>
        </div>

        <div>
          <h2 className="font-semibold">제4조 (금지 행위)</h2>
          <p className="mt-2 text-muted-foreground">
            회원은 허위 상품 정보 등록, 타인의 계정 도용, 서비스의 정상 운영을 방해하는 행위를 해서는 안 됩니다.
            위반 시 서비스 이용이 제한될 수 있습니다.
          </p>
        </div>

        <div>
          <h2 className="font-semibold">제5조 (서비스 변경 및 중단)</h2>
          <p className="mt-2 text-muted-foreground">
            서비스는 운영상 필요에 따라 서비스 내용을 변경하거나 중단할 수 있습니다. 중단 시 사전에 공지하며,
            불가피한 경우 사후 공지할 수 있습니다.
          </p>
        </div>

        <div>
          <h2 className="font-semibold">제6조 (면책)</h2>
          <p className="mt-2 text-muted-foreground">
            ParaPara는 회원이 서비스를 통해 등록한 상품의 거래에 직접 개입하지 않으며, 거래 당사자 간 분쟁에 대한
            책임을 지지 않습니다.
          </p>
        </div>
      </section>
    </main>
  );
}
