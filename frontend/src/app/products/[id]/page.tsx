interface Props {
  params: Promise<{ id: string }>;
}

export default async function ProductDetailPage({ params }: Props) {
  const { id } = await params;

  return (
    <main className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="text-2xl font-bold mb-6">상품 상세</h1>
      <p className="text-sm text-muted-foreground">ID: {id}</p>
      {/* TODO: 플랫폼별 등록 URL, 판매 상태 */}
      {/* TODO: 수동 판매완료 처리 버튼 */}
    </main>
  );
}
