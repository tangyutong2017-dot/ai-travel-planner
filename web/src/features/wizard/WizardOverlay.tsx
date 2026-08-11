import { useState } from "react";
import { getJobStatus } from "../../api/jobs";
import { createTrip, startTripGeneration } from "../../api/trips";
import type { AgentJob } from "../../types/job";
import type { CreateTripPayload, CreateTripResponse } from "../../types/trip";
import { Divider, SectionTitle, WAnnotation, WBox, WBtn } from "../../components/ui/Primitives";

type WizardStep = "create" | "preferences" | "generating";

type WizardForm = CreateTripPayload;

// 默认出发日取「今天 +7 天」，默认 5 天行程。
// 曾经写死成 2026-08-10，日子一过就成了过去的日期。
const isoDate = (offsetDays: number) => {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().slice(0, 10);
};

const DEFAULT_TRIP_DAYS = 5;

const initialForm: WizardForm = {
  // 目的地必须留空：填了默认值会让用户不知不觉创建一条别人的行程
  destination: "",
  startDate: isoDate(7),
  endDate: isoDate(7 + DEFAULT_TRIP_DAYS - 1),
  days: DEFAULT_TRIP_DAYS,
  travelers: {
    adults: 2,
    children: 0,
    infants: 0,
  },
  budget: {
    min: 0,
    max: 12000,
  },
  preferences: {
    interests: ["自然风光", "美食探索", "文化历史"],
    pace: 50,
    transport: ["公共交通", "步行为主"],
    accommodation: ["酒店"],
    customText: "",
  },
};

const calculateDays = (startDate: string, endDate: string) => {
  if (!startDate || !endDate) return 0;

  const start = new Date(startDate);
  const end = new Date(endDate);
  const diff = end.getTime() - start.getTime();

  if (Number.isNaN(diff) || diff < 0) return 0;

  return Math.floor(diff / 86400000) + 1;
};

const sleep = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export function WizardOverlay({ onClose, onDone }: { onClose: () => void; onDone: (tripId: string) => void }) {
  const [step, setStep] = useState<WizardStep>("create");
  const [form, setForm] = useState<WizardForm>(initialForm);
  const [submitState, setSubmitState] = useState<"idle" | "submitting" | "polling" | "succeeded" | "error">("idle");
  const [submitResult, setSubmitResult] = useState<CreateTripResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<AgentJob | null>(null);
  const [submitError, setSubmitError] = useState("");

  const patchForm = (patch: Partial<WizardForm>) => {
    setForm((current) => ({ ...current, ...patch }));
  };

  const patchTravelers = (patch: Partial<WizardForm["travelers"]>) => {
    setForm((current) => ({
      ...current,
      travelers: { ...current.travelers, ...patch },
    }));
  };

  const patchBudget = (patch: Partial<WizardForm["budget"]>) => {
    setForm((current) => ({
      ...current,
      budget: { ...current.budget, ...patch },
    }));
  };

  const patchPreferences = (patch: Partial<WizardForm["preferences"]>) => {
    setForm((current) => ({
      ...current,
      preferences: { ...current.preferences, ...patch },
    }));
  };

  const handleBasicNext = () => {
    patchForm({ days: calculateDays(form.startDate, form.endDate) });
    setStep("preferences");
  };

  const handleSubmit = async () => {
    const payload = {
      ...form,
      days: calculateDays(form.startDate, form.endDate),
    };

    setForm(payload);
    setStep("generating");
    setSubmitState("submitting");
    setSubmitResult(null);
    setJobStatus(null);
    setSubmitError("");

    try {
      const created = await createTrip(payload);
      const generation = await startTripGeneration(created.tripId);
      setSubmitResult(generation);
      setSubmitState("polling");

      for (;;) {
        const job = await getJobStatus(generation.jobId, generation.tripId);
        setJobStatus(job);

        if (job.status === "succeeded") {
          setSubmitState("succeeded");
          return;
        }

        if (job.status === "failed") {
          setSubmitState("error");
          setSubmitError(job.message);
          return;
        }

        await sleep(1500);
      }
    } catch (error) {
      setSubmitState("error");
      setSubmitError(error instanceof Error ? error.message : "创建行程失败");
    }
  };

  return (
    <div className="absolute inset-0 z-40 flex flex-col" style={{ fontFamily: "'Inter', sans-serif" }}>
      <div className="absolute inset-0 bg-white" />

      <div className="relative border-b border-slate-200 bg-white/95 backdrop-blur flex items-center justify-between px-6 h-14 shrink-0 z-10 shadow-sm shadow-slate-200/60">
        <div className="flex items-center gap-4">
          <span className="text-sm font-semibold text-slate-900">创建新行程</span>
          <StepPills current={step} />
        </div>
        {step !== "generating" && (
          <button
            onClick={onClose}
            className="rounded-md text-slate-400 hover:text-slate-800 text-xs font-mono border border-slate-200 px-3 py-1.5 cursor-pointer transition-colors hover:bg-slate-50"
          >
            × 取消
          </button>
        )}
      </div>

      <div className="relative flex-1 flex flex-col overflow-hidden">
        {step === "create" && (
          <PageCreate
            form={form}
            onPatchForm={patchForm}
            onPatchTravelers={patchTravelers}
            onPatchBudget={patchBudget}
            onNext={handleBasicNext}
          />
        )}
        {step === "preferences" && (
          <PagePreferences
            form={form}
            onPatchPreferences={patchPreferences}
            onBack={() => setStep("create")}
            onNext={handleSubmit}
          />
        )}
        {step === "generating" && (
          <PageGenerating
            form={form}
            state={submitState}
            result={submitResult}
            job={jobStatus}
            error={submitError}
            onRetry={handleSubmit}
            onDone={onDone}
          />
        )}
      </div>
    </div>
  );
}

function StepPills({ current }: { current: WizardStep }) {
  const order: WizardStep[] = ["create", "preferences", "generating"];
  const labels = ["基本信息", "偏好设置", "生成行程"];
  const currentIndex = order.indexOf(current);

  return (
    <div className="flex items-center gap-0">
      {order.map((step, i) => {
        const isCurrent = current === step;
        const isDone = i < currentIndex;

        return (
          <div key={step} className="flex items-center">
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 border text-[11px] font-mono ${
                isCurrent
                  ? "border-sky-600 bg-sky-600 text-white shadow-sm shadow-sky-200"
                  : isDone
                    ? "border-sky-200 bg-sky-50 text-sky-700"
                    : "border-slate-200 bg-white text-slate-400"
              }`}
            >
              <span className="font-bold">{i + 1}</span>
              <span>{labels[i]}</span>
              {isDone && <span className="text-sky-600">✓</span>}
            </div>
            {i < order.length - 1 && <div className="w-5 border-t border-dashed border-slate-200" />}
          </div>
        );
      })}
    </div>
  );
}

function StepIndicator({ activeIndex, onFirstClick }: { activeIndex: number; onFirstClick?: () => void }) {
  return (
    <div className="flex items-center gap-0 mb-5">
      {(["基本信息", "偏好设置", "生成行程"] as const).map((label, i) => (
        <div key={label} className="flex items-center">
          <div
            onClick={i === 0 ? onFirstClick : undefined}
            className={`flex items-center gap-2 px-3 py-1.5 border text-xs font-mono ${
              i <= activeIndex ? "border-sky-600 bg-sky-600 text-white" : "border-slate-200 bg-white text-slate-400"
            } ${i === 0 && onFirstClick ? "cursor-pointer hover:bg-sky-700" : ""}`}
          >
            <span className="font-bold">{i + 1}</span>
            <span>{label}</span>
            {i === 0 && onFirstClick && <span className="opacity-60 text-[10px]">←</span>}
          </div>
          {i < 2 && <div className="w-8 border-t border-dashed border-slate-300" />}
        </div>
      ))}
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs font-medium text-slate-600">{label}</span>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-md border border-slate-200 bg-slate-50 h-9 px-3 text-xs text-slate-700 font-mono outline-none focus:border-sky-400 focus:bg-white"
      />
    </label>
  );
}

function PageCreate({
  form,
  onPatchForm,
  onPatchTravelers,
  onPatchBudget,
  onNext,
}: {
  form: WizardForm;
  onPatchForm: (patch: Partial<WizardForm>) => void;
  onPatchTravelers: (patch: Partial<WizardForm["travelers"]>) => void;
  onPatchBudget: (patch: Partial<WizardForm["budget"]>) => void;
  onNext: () => void;
}) {
  const days = calculateDays(form.startDate, form.endDate);
  const canContinue = form.destination.trim().length > 0 && days > 0;

  const updateTraveler = (key: keyof WizardForm["travelers"], delta: number) => {
    onPatchTravelers({ [key]: Math.max(0, form.travelers[key] + delta) });
  };

  return (
    <div className="flex-1 overflow-auto bg-slate-50">
      <div className="min-h-full flex items-center justify-center py-6 px-6">
        <div className="w-full max-w-2xl">
          <div className="mb-5">
            <h1 className="text-2xl font-bold text-slate-950 mt-1 mb-1">开始规划你的旅行</h1>
            <p className="text-sm text-slate-500">填写基本信息，AI 将为你生成专属行程方案</p>
          </div>

          <StepIndicator activeIndex={0} />

          <WBox className="p-5">
            <SectionTitle text="目的地" />
            <div className="mb-4">
              <Field
                label="搜索目的地城市或国家"
                value={form.destination}
                placeholder="例如：云南大理 / 四川成都"
                onChange={(destination) => onPatchForm({ destination })}
              />
            </div>

            <SectionTitle text="行程时间" />
            <div className="grid grid-cols-3 gap-3 mb-4">
              <Field
                label="出发日期"
                type="date"
                value={form.startDate}
                onChange={(startDate) => onPatchForm({ startDate })}
              />
              <Field
                label="返回日期"
                type="date"
                value={form.endDate}
                onChange={(endDate) => onPatchForm({ endDate })}
              />
              <div className="flex flex-col gap-1">
                <span className="text-xs font-medium text-slate-600">行程天数</span>
                <div className="rounded-md border border-slate-200 bg-slate-50 h-9 px-3 flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-mono">自动计算</span>
                  <span className="text-xs font-bold text-slate-700 font-mono">{days || "-"} 天</span>
                </div>
              </div>
            </div>

            <SectionTitle text="旅行人数" />
            <div className="grid grid-cols-3 gap-3 mb-4">
              {[
                { key: "adults", label: "成人", sub: "18岁以上" },
                { key: "children", label: "儿童", sub: "2-17岁" },
                { key: "infants", label: "婴幼儿", sub: "0-2岁" },
              ].map((group) => {
                const key = group.key as keyof WizardForm["travelers"];
                return (
                  <div key={group.key} className="rounded-lg border border-slate-200 p-3 bg-slate-50">
                    <p className="text-xs font-medium text-slate-700">{group.label}</p>
                    <p className="text-[10px] text-slate-400 font-mono mb-2">{group.sub}</p>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => updateTraveler(key, -1)}
                        className="w-7 h-7 rounded-md border border-slate-200 bg-white flex items-center justify-center text-sm font-mono hover:bg-sky-50"
                      >
                        -
                      </button>
                      <span className="text-base font-bold w-6 text-center">{form.travelers[key]}</span>
                      <button
                        onClick={() => updateTraveler(key, 1)}
                        className="w-7 h-7 rounded-md border border-slate-200 bg-white flex items-center justify-center text-sm font-mono hover:bg-sky-50"
                      >
                        +
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            <SectionTitle text="预算范围（可选）" />
            <div className="grid grid-cols-2 gap-3 mb-4">
              <Field
                label="最低预算（元）"
                type="number"
                value={form.budget.min}
                onChange={(min) => onPatchBudget({ min: Number(min) })}
              />
              <Field
                label="最高预算（元）"
                type="number"
                value={form.budget.max}
                onChange={(max) => onPatchBudget({ max: Number(max) })}
              />
            </div>

            <Divider className="mb-4" />
            <div className="flex justify-between items-center">
              <WAnnotation text={canContinue ? "基本信息已可提交" : "请填写目的地和有效日期"} />
              <button
                onClick={onNext}
                disabled={!canContinue}
                className={`border font-medium font-mono text-sm px-5 py-2 ${
                  canContinue
                    ? "rounded-md bg-sky-600 text-white border-sky-600 cursor-pointer hover:bg-sky-700"
                    : "rounded-md bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed"
                }`}
              >
                下一步：偏好设置 →
              </button>
            </div>
          </WBox>
        </div>
      </div>
    </div>
  );
}

function TagGroup({
  title,
  preset,
  selected,
  onChange,
}: {
  title: string;
  preset: string[];
  selected: string[];
  onChange: (tags: string[]) => void;
}) {
  const [custom, setCustom] = useState<string[]>([]);
  const [inputVal, setInputVal] = useState("");
  const [editing, setEditing] = useState(false);

  const toggle = (tag: string) => {
    onChange(selected.includes(tag) ? selected.filter((item) => item !== tag) : [...selected, tag]);
  };

  const addCustom = () => {
    const value = inputVal.trim();
    if (value && !preset.includes(value) && !custom.includes(value)) {
      setCustom((current) => [...current, value]);
      onChange([...selected, value]);
    }
    setInputVal("");
    setEditing(false);
  };

  const removeCustom = (tag: string) => {
    setCustom((current) => current.filter((item) => item !== tag));
    onChange(selected.filter((item) => item !== tag));
  };

  const allTags = [...preset, ...custom];

  return (
    <WBox className="p-4">
      <SectionTitle text={title} />
      <div className="flex flex-wrap gap-2 mb-3">
        {allTags.map((tag) => (
          <div key={tag} className="flex items-center gap-0">
            <button
              onClick={() => toggle(tag)}
              className={`border text-xs px-3 py-1.5 font-mono cursor-pointer transition-colors ${
                selected.includes(tag)
                  ? "border-gray-900 bg-gray-900 text-white"
                  : "border-gray-400 bg-white text-gray-700 hover:border-gray-600"
              }`}
            >
              {tag}
            </button>
            {custom.includes(tag) && (
              <button
                onClick={() => removeCustom(tag)}
                className="border border-l-0 border-gray-400 bg-white text-gray-400 hover:text-gray-800 hover:bg-gray-100 px-1.5 py-1.5 text-xs font-mono cursor-pointer transition-colors"
                title="删除"
              >
                ×
              </button>
            )}
          </div>
        ))}

        {editing ? (
          <div className="flex items-center gap-0">
            <input
              autoFocus
              value={inputVal}
              onChange={(event) => setInputVal(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") addCustom();
                if (event.key === "Escape") {
                  setEditing(false);
                  setInputVal("");
                }
              }}
              placeholder="输入后回车确认"
              className="border border-gray-500 bg-white text-xs font-mono px-2 py-1.5 w-32 outline-none focus:border-gray-900"
            />
            <button
              onClick={addCustom}
              className="border border-l-0 border-gray-500 bg-gray-900 text-white text-xs font-mono px-2 py-1.5 cursor-pointer hover:bg-gray-700"
            >
              确认
            </button>
            <button
              onClick={() => {
                setEditing(false);
                setInputVal("");
              }}
              className="border border-l-0 border-gray-400 bg-white text-gray-500 text-xs font-mono px-2 py-1.5 cursor-pointer hover:bg-gray-50"
            >
              取消
            </button>
          </div>
        ) : (
          <button
            onClick={() => setEditing(true)}
            className="border border-dashed border-gray-400 text-xs px-3 py-1.5 font-mono text-gray-500 hover:border-gray-700 hover:text-gray-800 cursor-pointer transition-colors"
          >
            + 自定义
          </button>
        )}
      </div>
      <WAnnotation text={`已选 ${selected.length} 项${custom.length > 0 ? ` · ${custom.length} 项自定义` : ""}`} />
    </WBox>
  );
}

function PagePreferences({
  form,
  onPatchPreferences,
  onNext,
  onBack,
}: {
  form: WizardForm;
  onPatchPreferences: (patch: Partial<WizardForm["preferences"]>) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  return (
    <div className="flex-1 overflow-auto bg-gray-50">
      <div className="min-h-full flex items-center justify-center py-6 px-6">
        <div className="w-full max-w-2xl">
          <div className="mb-5">
            <h1 className="text-2xl font-bold text-slate-950 mt-1 mb-1">告诉我们你的旅行偏好</h1>
            <p className="text-sm text-slate-500">帮助 AI 生成更符合你风格的个性化行程</p>
          </div>

          <StepIndicator activeIndex={1} onFirstClick={onBack} />

          <div className="space-y-3">
            <TagGroup
              title="兴趣偏好（可多选）"
              preset={[
                "文化历史",
                "美食探索",
                "自然风光",
                "购物血拼",
                "户外冒险",
                "主题乐园",
                "艺术展览",
                "夜生活",
                "温泉休闲",
                "本地市场",
              ]}
              selected={form.preferences.interests}
              onChange={(interests) => onPatchPreferences({ interests })}
            />

            <WBox className="p-4">
              <SectionTitle text="行程节奏" />
              <div className="relative mb-3">
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={form.preferences.pace}
                  onChange={(event) => onPatchPreferences({ pace: Number(event.target.value) })}
                  className="w-full accent-gray-800"
                />
              </div>
              <div className="flex justify-between text-xs font-mono text-gray-500">
                <span>
                  轻松悠闲
                  <br />
                  <span className="text-[10px] text-gray-400">每天 1-2 个景点</span>
                </span>
                <span className="text-center">
                  适中
                  <br />
                  <span className="text-[10px] text-gray-400">每天 3-4 个景点</span>
                </span>
                <span className="text-right">
                  紧凑高效
                  <br />
                  <span className="text-[10px] text-gray-400">每天 5+ 个景点</span>
                </span>
              </div>
            </WBox>

            <TagGroup
              title="交通偏好"
              preset={["公共交通", "自驾", "出租车 / 网约车", "步行为主", "包车"]}
              selected={form.preferences.transport}
              onChange={(transport) => onPatchPreferences({ transport })}
            />

            <TagGroup
              title="住宿类型偏好"
              preset={["酒店", "民宿", "青旅", "度假村", "精品酒店"]}
              selected={form.preferences.accommodation}
              onChange={(accommodation) => onPatchPreferences({ accommodation })}
            />

            <WBox className="p-4">
              <SectionTitle text="其他自定义偏好（可选）" />
              <textarea
                value={form.preferences.customText}
                onChange={(event) => onPatchPreferences({ customText: event.target.value })}
                placeholder="例如：我有老人同行，希望行程不要太赶；对海鲜过敏；希望多安排购物时间……"
                className="border border-gray-300 bg-gray-50 h-20 p-3 w-full text-xs text-gray-700 font-mono outline-none focus:border-gray-900 focus:bg-white resize-none"
              />
            </WBox>
          </div>

          <div className="flex justify-between mt-6">
            <WBtn label="← 返回修改" onClick={onBack} />
            <WBtn label="开始生成行程 →" primary onClick={onNext} />
          </div>
        </div>
      </div>
    </div>
  );
}

function PageGenerating({
  form,
  state,
  result,
  job,
  error,
  onRetry,
  onDone,
}: {
  form: WizardForm;
  state: "idle" | "submitting" | "polling" | "succeeded" | "error";
  result: CreateTripResponse | null;
  job: AgentJob | null;
  error: string;
  onRetry: () => void;
  onDone: (tripId: string) => void;
}) {
  const progress = Math.max(
    4,
    Math.min(100, job?.progress ?? (state === "submitting" ? 12 : state === "error" ? 38 : 8)),
  );
  const summary = `${form.destination} · ${form.days}天 · 成人 ${form.travelers.adults} 人 · ${form.preferences.interests.slice(0, 2).join(" / ")}`;
  const title = state === "succeeded" ? "行程已生成" : state === "error" ? "生成遇到一点问题" : "正在生成你的行程";
  const currentMessage =
    state === "succeeded"
      ? "已整理好每日安排、景点信息和路线摘要"
      : state === "error"
        ? error || "本次生成没有完成，可以重新提交"
        : (job?.message ?? (state === "submitting" ? "正在保存旅行需求" : "正在理解偏好并生成候选安排"));
  const steps = [
    { label: "保存旅行需求", threshold: 10 },
    { label: "理解偏好与节奏", threshold: 28 },
    { label: "生成候选景点", threshold: 48 },
    { label: "查询景点、路线与天气", threshold: 76 },
    { label: "整理每日行程", threshold: 96 },
  ];
  const nextStepIndex = steps.findIndex((stepItem) => progress < stepItem.threshold);
  const activeIndex =
    state === "succeeded" ? steps.length : Math.max(0, nextStepIndex === -1 ? steps.length - 1 : nextStepIndex);

  return (
    <div className="flex-1 overflow-auto bg-[radial-gradient(circle_at_top,#e0f2fe_0,#f8fafc_34%,#f8fafc_100%)] flex items-center justify-center px-6 py-8">
      <div className="w-full max-w-2xl">
        <WBox className="p-8 sm:p-10">
          <div className="mb-8 flex items-start justify-between gap-6">
            <div>
              <div
                className={`mb-4 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] font-medium ${
                  state === "succeeded"
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                    : state === "error"
                      ? "border-rose-200 bg-rose-50 text-rose-700"
                      : "border-sky-200 bg-sky-50 text-sky-700"
                }`}
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    state === "succeeded"
                      ? "bg-emerald-500"
                      : state === "error"
                        ? "bg-rose-500"
                        : "bg-sky-500 animate-pulse"
                  }`}
                />
                {state === "succeeded" ? "规划完成" : state === "error" ? "需要重试" : "智能规划中"}
              </div>
              <h2 className="text-2xl font-bold text-slate-950 mb-2">{title}</h2>
              <p className="text-sm text-slate-500">{summary}</p>
            </div>
            <div className="hidden sm:flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl border border-sky-100 bg-white shadow-sm shadow-sky-100">
              <div className="relative h-10 w-10">
                <div className="absolute inset-0 rounded-full border-2 border-sky-100" />
                <div
                  className={`absolute inset-0 rounded-full border-2 border-sky-500 border-t-transparent ${state === "polling" || state === "submitting" ? "animate-spin" : ""}`}
                />
                <div className="absolute inset-3 rounded-full bg-sky-500/15" />
              </div>
            </div>
          </div>

          <div className="mb-7">
            <div className="mb-3 flex items-center justify-between gap-4 text-xs text-slate-500">
              <span>{currentMessage}</span>
              <span className="font-mono text-slate-400">{Math.round(state === "succeeded" ? 100 : progress)}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  state === "error" ? "bg-rose-500" : state === "succeeded" ? "bg-emerald-500" : "bg-sky-600"
                }`}
                style={{ width: `${state === "succeeded" ? 100 : progress}%` }}
              />
            </div>
          </div>

          <div className="grid gap-3 mb-7 sm:grid-cols-5">
            {steps.map((stepItem, index) => {
              const done = state === "succeeded" || progress >= stepItem.threshold;
              const active = !done && index === activeIndex && state !== "error";
              const failed = state === "error" && index === activeIndex;

              return (
                <div
                  key={stepItem.label}
                  className={`rounded-lg border p-3 transition-colors ${
                    done
                      ? "border-emerald-100 bg-emerald-50/70 text-emerald-700"
                      : failed
                        ? "border-rose-100 bg-rose-50 text-rose-700"
                        : active
                          ? "border-sky-200 bg-sky-50 text-sky-800"
                          : "border-slate-100 bg-slate-50 text-slate-400"
                  }`}
                >
                  <div
                    className={`mb-2 flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
                      done
                        ? "bg-emerald-500 text-white"
                        : failed
                          ? "bg-rose-500 text-white"
                          : active
                            ? "bg-sky-600 text-white"
                            : "bg-slate-200 text-slate-500"
                    }`}
                  >
                    {done ? "✓" : failed ? "!" : index + 1}
                  </div>
                  <p className="text-xs font-medium leading-snug">{stepItem.label}</p>
                </div>
              );
            })}
          </div>

          {error && (
            <div className="mb-5 rounded-lg border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          )}

          <div className="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3 text-xs text-slate-500">
            第 1 天生成完成后即可进入行程工作区；后续天数会在后台继续生成并自动同步。
          </div>

          <div className="mt-6">
            {state === "error" ? (
              <WBtn label="重新生成" primary onClick={onRetry} className="w-full" />
            ) : state === "succeeded" && result ? (
              <WBtn label="进入行程工作区" primary onClick={() => onDone(result.tripId)} className="w-full" />
            ) : (
              <button
                disabled
                className="w-full rounded-md border border-sky-200 bg-sky-50 px-4 py-2 text-[13px] font-medium text-sky-700"
              >
                正在生成，请稍候
              </button>
            )}
          </div>
        </WBox>
      </div>
    </div>
  );
}
