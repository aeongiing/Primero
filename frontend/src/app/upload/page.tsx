"use client";

import { useEffect, useRef, useState } from "react";
import {
  IMAGE_ORDER_LABELS,
  CONDITION_GRADES,
  COLORS,
  GENDERS,
  UPLOAD_PLATFORMS,
  PLATFORMS,
} from "@/lib/constants";
import type { Platform } from "@/types";
import {
  analyzeImages,
  createProduct,
  uploadProductImages,
  publishProduct,
  fitRecommendation,
  ApiError,
} from "@/lib/api";

function gradeFor(score: number) {
  return CONDITION_GRADES.find((g) => score >= g.min) ?? CONDITION_GRADES.at(-1)!;
}

/** 라벨 + 도움말이 있는 필드 블록 */
function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <label className="text-sm font-bold">{label}</label>
        {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
      </div>
      {children}
    </div>
  );
}

/** 칩 토글 (단일/다중 선택 공용) */
function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-full border px-3.5 py-1.5 text-sm transition-colors ${
        active
          ? "border-primary bg-primary text-primary-foreground"
          : "border-border bg-background text-foreground hover:bg-muted"
      }`}
    >
      {children}
    </button>
  );
}

/** 라디오 행 */
function Radio({
  checked,
  onChange,
  children,
}: {
  checked: boolean;
  onChange: () => void;
  children: React.ReactNode;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-2 text-sm">
      <input
        type="radio"
        checked={checked}
        onChange={onChange}
        className="size-4 accent-[#a47864]"
      />
      {children}
    </label>
  );
}

const inputCls =
  "h-11 w-full rounded-md border border-input px-3 text-sm outline-none focus:ring-2 focus:ring-ring";

// joonggonara(프론트 표기) → junggonara(백엔드 표기)
const toBackendPlatform = (p: string) => (p === "joonggonara" ? "junggonara" : p);

type PhotoItem = { id: string; file: File; url: string };

const newId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

export default function UploadPage() {
  const [photos, setPhotos] = useState<PhotoItem[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [gender, setGender] = useState<string>("");
  const [major, setMajor] = useState<string>("");
  const [size, setSize] = useState<string>("");
  const [sizeLabel, setSizeLabel] = useState("");
  const [condition, setCondition] = useState(8);
  const [conditionNote, setConditionNote] = useState("");
  const [brand, setBrand] = useState("");
  const [chest, setChest] = useState("");
  const [length, setLength] = useState("");
  const [shoulder, setShoulder] = useState("");
  const [sleeve, setSleeve] = useState("");
  const [fitText, setFitText] = useState("");
  const [fitLoading, setFitLoading] = useState(false);
  const [fitError, setFitError] = useState<string | null>(null);
  const [fitAdded, setFitAdded] = useState(false);
  const [colors, setColors] = useState<string[]>([]);
  const [shippingFee, setShippingFee] = useState("");
  const [price, setPrice] = useState("");
  const [acceptOffer, setAcceptOffer] = useState(true);
  const [platforms, setPlatforms] = useState<Platform[]>([...UPLOAD_PLATFORMS]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitMsg, setSubmitMsg] = useState<string | null>(null);

  const toggle = <T,>(list: T[], v: T, max?: number): T[] => {
    if (list.includes(v)) return list.filter((x) => x !== v);
    if (max && list.length >= max) return list;
    return [...list, v];
  };

  // 여러 장 한 번에 추가 (파일 선택 / OS 드래그앤드롭 공용)
  const addFiles = (files: FileList | File[]) => {
    const imgs = Array.from(files).filter((f) => f.type.startsWith("image/"));
    if (!imgs.length) return;
    setPhotos((prev) => [
      ...prev,
      ...imgs.map((file) => ({ id: newId(), file, url: URL.createObjectURL(file) })),
    ]);
  };

  const removePhoto = (id: string) =>
    setPhotos((prev) => {
      const target = prev.find((p) => p.id === id);
      if (target) URL.revokeObjectURL(target.url);
      return prev.filter((p) => p.id !== id);
    });

  // from 위치의 사진을 to 위치로 이동 (순서 = 앞면·확대·뒷면…)
  const reorderPhoto = (from: number, to: number) =>
    setPhotos((prev) => {
      if (from === to || from < 0 || to < 0 || from >= prev.length || to >= prev.length)
        return prev;
      const next = [...prev];
      const [moved] = next.splice(from, 1);
      next.splice(to, 0, moved);
      return next;
    });

  // 드래그 중인 사진 인덱스
  const dragFrom = useRef<number | null>(null);
  const [dragOver, setDragOver] = useState<number | null>(null);
  const [fileHover, setFileHover] = useState(false);

  // AI 분석: 사진을 백엔드로 보내 Claude 분석 결과를 폼에 채움 (모두 수정 가능)
  // 백엔드: POST /api/v1/products/analyze (multipart images) → AIAnalysisResult
  const runAiAnalysis = async () => {
    if (!photos.length || analyzing) return;
    setAnalyzing(true);
    setAnalyzeError(null);
    try {
      const d = await analyzeImages(photos.map((p) => p.file));
      // AIAnalysisResult → 폼 필드 매핑 (인식 안 된 값은 채우지 않고 비워둠)
      if (d.title) setTitle(String(d.title).slice(0, 40));
      if (d.brand && d.brand !== "미상") setBrand(d.brand);
      if (d.description) setDescription(d.description);
      if (d.category) setMajor(String(d.category).split(">")[0].trim()); // "아우터 > 재킷" → 아우터
      if (d.gender === "남성") setGender("남성의류");
      else if (d.gender === "여성") setGender("여성의류");
      if (Array.isArray(d.colors)) {
        const allowed = new Set<string>(COLORS as readonly string[]);
        setColors(d.colors.filter((c: string) => allowed.has(c)));
      }
      if (d.size) setSize(String(d.size));
    } catch (e) {
      setAnalyzeError(
        e instanceof ApiError
          ? `AI 분석 실패: ${e.message}`
          : "AI 분석에 실패했어요. 백엔드 서버를 확인해주세요."
      );
    } finally {
      setAnalyzing(false);
    }
  };

  // AI 핏 추천: 표기 사이즈 + 실측 → 정핏/오버핏 텍스트
  const runFitRecommendation = async () => {
    if (fitLoading) return;
    setFitLoading(true);
    setFitError(null);
    setFitAdded(false);
    try {
      const { text } = await fitRecommendation({
        category: major || undefined,
        size: size || sizeLabel || undefined,
        gender: gender || undefined,
        chest: chest ? Number(chest) : null,
        total_length: length ? Number(length) : null,
        shoulder: shoulder ? Number(shoulder) : null,
        sleeve: sleeve ? Number(sleeve) : null,
      });
      setFitText(text);
    } catch (e) {
      setFitError(
        e instanceof ApiError
          ? `핏 추천 실패: ${e.message}`
          : "핏 추천에 실패했어요. 백엔드 서버를 확인해주세요."
      );
    } finally {
      setFitLoading(false);
    }
  };

  // 업로드/임시저장: 표준_상품 생성(+사진 S3 업로드)
  const submit = async () => {
    if (submitting) return;
    if (!title.trim()) {
      setSubmitMsg("상품명을 입력해주세요.");
      return;
    }
    const priceNum = Number(price);
    if (!priceNum || priceNum <= 0) {
      setSubmitMsg("판매가를 입력해주세요.");
      return;
    }
    setSubmitting(true);
    setSubmitMsg(null);
    try {
      const product = await createProduct({
        title: title.trim(),
        brand: brand.trim(),
        description: description.trim(),
        category: major || gender || "",
        condition: Math.min(10, Math.max(1, Math.round(condition))),
        price: priceNum,
        colors,
        materials: [],
        size: size || sizeLabel || null,
        chest: chest ? Number(chest) : null,
        total_length: length ? Number(length) : null,
        platforms: platforms.map(toBackendPlatform),
      });
      if (photos.length) {
        try {
          await uploadProductImages(
            product.id,
            photos.map((p) => p.file)
          );
        } catch {
          setSubmitMsg("상품은 저장됐지만 사진 업로드는 실패했어요(S3 권한 확인).");
          return;
        }
      }
      // 플랫폼 발행 (백그라운드 실행 — 즉시 응답)
      if (platforms.length) {
        publishProduct(product.id, platforms.map(toBackendPlatform)).catch(() => {});
        setSubmitMsg(`등록됐어요! ${platforms.map(toBackendPlatform).join(", ")} 발행 중...`);
      } else {
        setSubmitMsg("등록되었어요!");
      }
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setSubmitMsg("로그인이 필요해요. (백엔드 인증 연동 후 가능)");
      } else if (e instanceof ApiError) {
        setSubmitMsg(`등록 실패: ${e.message}`);
      } else {
        setSubmitMsg("등록 중 오류가 발생했어요. 백엔드 서버를 확인해주세요.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  // 언마운트 시 미리보기 URL 정리 (메모리 누수 방지)
  const photosRef = useRef<PhotoItem[]>([]);
  useEffect(() => {
    photosRef.current = photos;
  }, [photos]);
  useEffect(() => {
    return () => {
      photosRef.current.forEach((p) => URL.revokeObjectURL(p.url));
    };
  }, []);

  const roleLabel = (i: number) =>
    i < IMAGE_ORDER_LABELS.length ? IMAGE_ORDER_LABELS[i] : `추가 ${i - IMAGE_ORDER_LABELS.length + 1}`;

  const grade = gradeFor(condition);
  const settlement = Number(price) || 0;

  return (
    <main className="mx-auto max-w-[1280px] px-6 pb-28 pt-8">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-xl font-bold">
          상품 등록
        </h1>
        <div className="flex items-center gap-3">
          <button type="button" className="text-sm text-muted-foreground hover:text-foreground">
            취소
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={submitting}
            className="rounded-lg border border-border px-5 py-2 text-sm font-semibold text-foreground transition-colors hover:bg-muted disabled:opacity-50"
          >
            임시저장
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={submitting}
            className="rounded-lg bg-primary px-5 py-2 text-sm font-bold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
          >
            {submitting ? "등록 중…" : "업로드"}
          </button>
        </div>
      </div>

      <div className="mt-6 grid gap-8 lg:grid-cols-2">
        {/* ── 좌측: 사진 ── */}
        <div className="lg:sticky lg:top-6 lg:self-start">
          <div className="flex items-baseline justify-between">
            <h2 className="text-sm font-bold">사진</h2>
            <span className="text-xs text-muted-foreground">{photos.length}장</span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            여러 장을 한 번에 올린 뒤 드래그해서 순서를 바꿔주세요. 맨 앞이 앞면(대표)이에요.
          </p>

          {/* 사진 박스: 6칸(3×2) 그리드 — 썸네일 채우고 빈 칸은 추가 슬롯, 드래그로 순서 변경 */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              if (dragFrom.current === null) setFileHover(true);
            }}
            onDragLeave={() => setFileHover(false)}
            onDrop={(e) => {
              if (dragFrom.current !== null) return;
              e.preventDefault();
              setFileHover(false);
              if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files);
            }}
            className={`mt-3 rounded-lg border-2 border-dashed p-3 transition-colors ${
              fileHover ? "border-primary bg-accent" : "border-border bg-muted/40"
            }`}
          >
            <ul className="grid grid-cols-3 gap-3">
              {photos.map((item, i) => {
                const isFront = i === 0;
                return (
                  <li
                    key={item.id}
                    draggable
                    onDragStart={(e) => {
                      dragFrom.current = i;
                      e.dataTransfer.effectAllowed = "move";
                    }}
                    onDragEnter={() => {
                      if (dragFrom.current !== null) setDragOver(i);
                    }}
                    onDragOver={(e) => {
                      if (dragFrom.current !== null) e.preventDefault();
                    }}
                    onDrop={(e) => {
                      if (dragFrom.current === null) return;
                      e.preventDefault();
                      e.stopPropagation();
                      reorderPhoto(dragFrom.current, i);
                      dragFrom.current = null;
                      setDragOver(null);
                    }}
                    onDragEnd={() => {
                      dragFrom.current = null;
                      setDragOver(null);
                    }}
                    className={`group relative aspect-square cursor-grab overflow-hidden rounded-lg border bg-muted active:cursor-grabbing ${
                      dragOver === i ? "border-primary ring-2 ring-primary" : "border-border"
                    } ${isFront ? "ring-2 ring-primary" : ""}`}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={item.url}
                      alt={`${roleLabel(i)} 사진`}
                      className="pointer-events-none absolute inset-0 h-full w-full object-cover"
                    />
                    <span
                      className={`absolute left-1.5 top-1.5 rounded font-semibold ${
                        isFront
                          ? "bg-primary px-2 py-1 text-[11px] text-primary-foreground shadow-sm"
                          : "bg-black/55 px-1.5 py-0.5 text-[10px] font-medium text-white"
                      }`}
                    >
                      {isFront ? `★ 대표 · ${roleLabel(i)}` : `${i + 1}. ${roleLabel(i)}`}
                    </span>
                    <button
                      type="button"
                      onClick={() => removePhoto(item.id)}
                      aria-label={`${roleLabel(i)} 사진 삭제`}
                      className="absolute right-1.5 top-1.5 flex size-5 items-center justify-center rounded-full bg-black/55 text-xs text-white opacity-0 transition-opacity hover:bg-black/75 group-hover:opacity-100"
                    >
                      ×
                    </button>
                  </li>
                );
              })}
              {/* 빈 슬롯: 최소 6칸(3×2) 유지 + 역할 안내 */}
              {Array.from({ length: Math.max(0, 6 - photos.length) }).map((_, k) => {
                const idx = photos.length + k;
                return (
                  <li key={`slot-${idx}`}>
                    <label className="flex aspect-square cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border border-dashed border-border bg-background text-center transition-colors hover:border-primary">
                      <input
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        multiple
                        className="sr-only"
                        onChange={(e) => {
                          if (e.target.files?.length) addFiles(e.target.files);
                          e.target.value = "";
                        }}
                      />
                      <span className="text-2xl text-muted-foreground">＋</span>
                      <span className="text-xs text-muted-foreground">{roleLabel(idx)}</span>
                    </label>
                  </li>
                );
              })}
              {/* 6장 이상이면 맨 뒤에 추가 칸 */}
              {photos.length >= 6 && (
                <li>
                  <label className="flex aspect-square cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border border-dashed border-border bg-background text-center transition-colors hover:border-primary">
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      multiple
                      className="sr-only"
                      onChange={(e) => {
                        if (e.target.files?.length) addFiles(e.target.files);
                        e.target.value = "";
                      }}
                    />
                    <span className="text-2xl text-muted-foreground">＋</span>
                    <span className="text-xs text-muted-foreground">추가</span>
                  </label>
                </li>
              )}
            </ul>
          </div>

          <button
            type="button"
            onClick={runAiAnalysis}
            disabled={!photos.length || analyzing}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-bold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {analyzing ? "AI가 분석 중…" : "AI로 판매글 작성하기"}
          </button>

          <p className="mt-2 text-xs text-muted-foreground">
            {photos.length
              ? "AI가 사진을 분석해 카테고리·색상을 정하고 설명을 자동으로 작성해요. 결과는 직접 수정할 수 있어요."
              : "사진을 먼저 올리면 AI 분석을 할 수 있어요."}
          </p>
          {analyzeError && (
            <p className="mt-1 text-xs text-destructive">{analyzeError}</p>
          )}
          <p className="mt-2 text-xs text-muted-foreground">
            Tip: 앞면 → 뒷면 → 태그 → 디테일 → 오염 → 기타 순을 권장해요.
          </p>
        </div>

        {/* ── 우측: 입력 폼 ── */}
        <div className="flex flex-col gap-6">
          <Field label="브랜드">
            <input
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              placeholder="브랜드를 입력하세요"
              className={inputCls}
            />
          </Field>

          <Field label="상품명" hint={`${title.length}/40`}>
            <input
              value={title}
              maxLength={40}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="상품명 입력"
              className={inputCls}
            />
          </Field>

          <Field
            label="상품 설명"
            hint={`${description.length}/2500`}
          >
            <textarea
              value={description}
              maxLength={2500}
              onChange={(e) => setDescription(e.target.value)}
              rows={6}
              placeholder="상품 설명을 자세히 적을수록 빠르게 판매할 수 있어요. 구매 시기, 사용 기간, 하자 여부, 소재, 실측 사이즈 등"
              className="w-full rounded-md border border-input p-3 text-sm outline-none focus:ring-2 focus:ring-ring"
            />
          </Field>

          <Field label="성별">
            <div className="flex gap-8">
              {GENDERS.map((g) => (
                <Radio
                  key={g}
                  checked={gender === g}
                  onChange={() => setGender(g)}
                >
                  {g.replace("의류", "")}
                </Radio>
              ))}
            </div>
          </Field>

          <Field label="카테고리">
            <div className="flex flex-wrap gap-2">
              {["아우터", "상의", "하의"].map((c) => (
                <Chip key={c} active={major === c} onClick={() => setMajor(c)}>
                  {c}
                </Chip>
              ))}
            </div>
          </Field>

          <Field label="사이즈">
            <div className="flex flex-wrap gap-2">
              {["XS", "S", "M", "L", "XL", "XXL", "Free"].map((s) => (
                <Chip key={s} active={size === s} onClick={() => setSize(s)}>{s}</Chip>
              ))}
            </div>
            <input
              value={sizeLabel}
              onChange={(e) => setSizeLabel(e.target.value)}
              placeholder="표기 사이즈 (예: 95 · 100 · IT 48 · 30 · 55)"
              className={`${inputCls} mt-2`}
            />
            <div className="mt-2 grid grid-cols-2 gap-3">
              <input type="number" value={chest} onChange={(e) => setChest(e.target.value)} placeholder="가슴단면(cm)" className={inputCls} />
              <input type="number" value={length} onChange={(e) => setLength(e.target.value)} placeholder="총장(cm)" className={inputCls} />
              <input type="number" value={shoulder} onChange={(e) => setShoulder(e.target.value)} placeholder="어깨너비(cm, 선택)" className={inputCls} />
              <input type="number" value={sleeve} onChange={(e) => setSleeve(e.target.value)} placeholder="소매길이(cm, 선택)" className={inputCls} />
            </div>
          </Field>

          {/* AI 핏 추천 */}
          <Field label="핏 추천" hint="표기 사이즈·실측 기반">
            <button
              type="button"
              onClick={runFitRecommendation}
              disabled={fitLoading}
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-primary bg-accent px-4 py-3 text-sm font-bold text-primary transition-colors hover:bg-accent/70 disabled:opacity-50"
            >
              {fitLoading ? "분석 중…" : fitAdded ? "추가 완료!" : "AI 핏 추천 받기 (정핏·오버핏)"}
            </button>
            {fitError && <p className="mt-1 text-xs text-destructive">{fitError}</p>}
            {!fitAdded && fitText && (
              <div className="mt-2 rounded-md border border-border bg-muted/40 p-3">
                <p className="whitespace-pre-line text-sm leading-relaxed">{fitText}</p>
                <button
                  type="button"
                  onClick={() => {
                    setDescription((d) =>
                      d ? `${d}\n\n[핏 추천]\n${fitText}` : `[핏 추천]\n${fitText}`
                    );
                    setFitAdded(true);
                  }}
                  className="mt-2 rounded-md border border-border px-2.5 py-1 text-xs font-medium transition-colors hover:bg-muted"
                >
                  설명에 추가
                </button>
              </div>
            )}

          </Field>

          <Field label="상태" hint={`${condition.toFixed(1)}점 · ${grade.grade}`}>
            <input
              type="range"
              min={1}
              max={10}
              step={0.5}
              value={condition}
              onChange={(e) => setCondition(Number(e.target.value))}
              className="w-full accent-[#a47864]"
              aria-label="컨디션 점수"
            />
            <input
              value={conditionNote}
              onChange={(e) => setConditionNote(e.target.value)}
              placeholder="컨디션 메모 (예: 오른쪽 소매 끝 약한 오염)"
              className={`${inputCls} mt-2`}
            />
          </Field>

          <Field label="대표 색상">
            <div className="flex flex-wrap gap-2">
              {COLORS.map((c) => (
                <Chip key={c} active={colors.includes(c)} onClick={() => setColors(toggle(colors, c))}>{c}</Chip>
              ))}
            </div>
          </Field>

          <Field label="기본 배송비">
            <div className="relative">
              <input type="number" value={shippingFee} onChange={(e) => setShippingFee(e.target.value)} placeholder="0" className={`${inputCls} pr-8`} />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">원</span>
            </div>
          </Field>

          <Field label="판매가">
            <div className="relative">
              <input type="number" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="0" className={`${inputCls} pr-8`} />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">원</span>
            </div>
          </Field>

          <Field label="등록할 플랫폼" hint="선택한 곳에 동시 등록">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {UPLOAD_PLATFORMS.map((p) => {
                const active = platforms.includes(p);
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPlatforms(toggle(platforms, p))}
                    aria-pressed={active}
                    className={`flex items-center justify-center gap-2 rounded-lg border px-3 py-3 text-sm font-medium transition-colors ${
                      active ? "border-primary bg-accent" : "border-border hover:bg-muted"
                    }`}
                  >
                    <span className="size-2.5 rounded-full" style={{ background: PLATFORMS[p].color }} aria-hidden />
                    {PLATFORMS[p].label}
                  </button>
                );
              })}
              {(["fruits", "ebay"] as const).map((p) => (
                <div
                  key={p}
                  className="flex items-center justify-center gap-2 rounded-lg border border-border px-3 py-3 text-sm font-medium text-muted-foreground opacity-50 cursor-not-allowed"
                >
                  <span className="size-2.5 rounded-full" style={{ background: PLATFORMS[p].color }} aria-hidden />
                  {PLATFORMS[p].label}
                  <span className="text-[10px]">지원예정</span>
                </div>
              ))}
            </div>
          </Field>
        </div>
      </div>

      {/* 하단 고정바 */}
      <div className="fixed inset-x-0 bottom-0 border-t bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1280px] items-center justify-between px-6 py-4">
          <label className="flex cursor-pointer items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={acceptOffer}
              onChange={(e) => setAcceptOffer(e.target.checked)}
              className="size-4 accent-[#a47864]"
            />
            네고 제안받기
          </label>
          <div className="flex items-center gap-4">
            {submitMsg && (
              <span className="text-sm font-medium text-foreground">{submitMsg}</span>
            )}
            <span className="text-sm text-muted-foreground">
              정산 금액 <strong className="text-base font-bold text-foreground">{settlement.toLocaleString("ko-KR")}원</strong>
            </span>
          </div>
        </div>
      </div>
    </main>
  );
}
