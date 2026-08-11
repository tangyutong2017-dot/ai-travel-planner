import { useState } from "react";
import { trips } from "../data/trips";

// ─── Wireframe Primitives ───────────────────────────────────────────────────

function WBox({ className = "", children }: { className?: string; children?: React.ReactNode }) {
  return (
    <div className={`border border-gray-300 bg-white ${className}`}>
      {children}
    </div>
  );
}

function WImgBox({ className = "", label = "图片占位" }: { className?: string; label?: string }) {
  return (
    <div className={`bg-gray-200 border border-gray-300 flex items-center justify-center ${className}`}>
      <span className="text-xs text-gray-500 font-mono">{label}</span>
    </div>
  );
}

function WInput({ placeholder, label }: { placeholder: string; label?: string }) {
  return (
    <div className="flex flex-col gap-1">
      {label && <span className="text-xs font-medium text-gray-600">{label}</span>}
      <div className="border border-gray-400 bg-gray-50 h-9 px-3 flex items-center">
        <span className="text-xs text-gray-400 font-mono">{placeholder}</span>
      </div>
    </div>
  );
}

function WBtn({
  label,
  primary = false,
  small = false,
  className = "",
  onClick,
}: {
  label: string;
  primary?: boolean;
  small?: boolean;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`border font-medium font-mono cursor-pointer transition-opacity hover:opacity-80 ${
        primary
          ? "bg-gray-900 text-white border-gray-900"
          : "bg-white text-gray-800 border-gray-400"
      } ${small ? "text-xs px-3 py-1" : "text-sm px-5 py-2"} ${className}`}
    >
      {label}
    </button>
  );
}

function WTag({ label, active = false }: { label: string; active?: boolean }) {
  return (
    <div
      className={`border text-xs px-3 py-1.5 font-mono cursor-pointer ${
        active ? "border-gray-900 bg-gray-900 text-white" : "border-gray-400 bg-white text-gray-700"
      }`}
    >
      {label}
    </div>
  );
}

function WAnnotation({ text }: { text: string }) {
  return (
    <span className="font-mono text-[10px] text-gray-400 leading-none">{text}</span>
  );
}

function WLabel({ text, className = "" }: { text: string; className?: string }) {
  return (
    <p className={`text-xs font-mono text-gray-500 ${className}`}>{text}</p>
  );
}

function Divider({ className = "" }: { className?: string }) {
  return <div className={`border-t border-gray-300 ${className}`} />;
}

function SectionTitle({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-sm font-semibold text-gray-800">{text}</span>
      <div className="flex-1 border-t border-dashed border-gray-300" />
    </div>
  );
}

// ─── TopNav ─────────────────────────────────────────────────────────────────

function TopNav() {
  return (
    <div className="border-b border-gray-300 bg-white flex items-stretch h-12 shrink-0">
      {/* Logo */}
      <div className="border-r border-gray-300 px-5 flex items-center gap-2 shrink-0 w-52">
        <WImgBox className="w-6 h-6" label="" />
        <span className="font-semibold text-sm tracking-tight">AI 行程规划</span>
      </div>
      {/* Center: breadcrumb / page title */}
      <div className="flex items-center px-5 flex-1">
        <span className="text-xs font-mono text-gray-400">工作区 / 东京 7 日文化之旅</span>
      </div>
      {/* Right: actions + user */}
      <div className="border-l border-gray-300 px-4 flex items-center gap-3 shrink-0">
        <button className="text-xs font-mono text-gray-500 border border-gray-300 px-3 py-1 hover:bg-gray-50 cursor-pointer">🔔</button>
        <button className="text-xs font-mono text-gray-500 border border-gray-300 px-3 py-1 hover:bg-gray-50 cursor-pointer">设置</button>
        <div className="flex items-center gap-2">
          <WImgBox className="w-7 h-7" label="" />
          <span className="text-xs font-mono text-gray-600">用户名</span>
        </div>
      </div>
    </div>
  );
}

// ─── LeftSidebar ────────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { id: "mytrips",   icon: "⊞", label: "我的行程" },
  { id: "workspace", icon: "▦", label: "行程工作区" },
  { id: "output",    icon: "⬡", label: "输出预览" },
];

function LeftSidebar({
  current,
  onNavigate,
  onCreateTrip,
}: {
  current: string;
  onNavigate: (id: string) => void;
  onCreateTrip: () => void;
}) {
  return (
    <div className="w-52 border-r border-gray-300 bg-white flex flex-col shrink-0 overflow-y-auto">
      {/* Create trip CTA */}
      <div className="p-3 border-b border-gray-200">
        <button
          onClick={onCreateTrip}
          className="w-full bg-gray-900 text-white text-xs font-mono font-semibold py-2.5 flex items-center justify-center gap-2 cursor-pointer hover:bg-gray-700 transition-colors"
        >
          <span className="text-base leading-none">+</span>
          创建新行程
        </button>
      </div>

      {/* Main nav */}
      <div className="flex-1 py-3">
        <p className="text-[10px] font-mono text-gray-400 uppercase tracking-widest px-4 mb-1">导航</p>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-2 text-xs font-mono cursor-pointer transition-colors text-left ${
              current === item.id
                ? "bg-gray-900 text-white"
                : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            }`}
          >
            <span className="text-sm leading-none w-4 text-center">{item.icon}</span>
            <span>{item.label}</span>
            {current === item.id && <span className="ml-auto w-1 h-4 bg-white opacity-60" />}
          </button>
        ))}
      </div>

      {/* Recent trips */}
      <div className="border-t border-gray-200 p-4">
        <p className="text-[10px] font-mono text-gray-400 uppercase tracking-widest mb-2">最近行程</p>
        {[
          { label: "东京 7 日", status: "计划中" },
          { label: "巴黎蜜月游", status: "草稿" },
          { label: "新加坡亲子", status: "已完成" },
        ].map((t) => (
          <button
            key={t.label}
            onClick={() => onNavigate("workspace")}
            className="w-full text-left flex items-center gap-2 py-1.5 text-xs font-mono text-gray-500 hover:text-gray-900 cursor-pointer transition-colors"
          >
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full shrink-0" />
            <span className="flex-1 truncate">{t.label}</span>
            <span className="text-[10px] text-gray-300">{t.status}</span>
          </button>
        ))}
      </div>

      {/* Bottom */}
      <div className="border-t border-gray-200 p-4 space-y-1">
        {["帮助中心", "意见反馈"].map((label) => (
          <button
            key={label}
            className="w-full text-left text-xs font-mono text-gray-400 hover:text-gray-700 py-1 cursor-pointer transition-colors"
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── 创建行程向导（全屏覆盖层）──────────────────────────────────────────────

function WizardOverlay({
  onClose,
  onDone,
}: {
  onClose: () => void;
  onDone: () => void;
}) {
  const [step, setStep] = useState<"create" | "preferences" | "generating">("create");

  const handleGeneratingDone = () => {
    onDone();
  };

  return (
    <div className="absolute inset-0 z-40 flex flex-col" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* Dimmed backdrop for "generating" feel, white for forms */}
      <div className="absolute inset-0 bg-white" />

      {/* Wizard header */}
      <div className="relative border-b border-gray-300 bg-white flex items-center justify-between px-6 h-12 shrink-0 z-10">
        <div className="flex items-center gap-4">
          <span className="text-sm font-semibold text-gray-800">创建新行程</span>
          {/* Step pills */}
          <div className="flex items-center gap-0">
            {(["create", "preferences", "generating"] as const).map((s, i) => {
              const labels = ["基本信息", "偏好设置", "生成行程"];
              const isCurrent = step === s;
              const isDone = (step === "preferences" && i === 0) || (step === "generating" && i <= 1);
              return (
                <div key={s} className="flex items-center">
                  <div className={`flex items-center gap-1.5 px-2.5 py-1 border text-[11px] font-mono ${
                    isCurrent ? "border-gray-900 bg-gray-900 text-white"
                    : isDone  ? "border-gray-500 bg-gray-100 text-gray-600"
                    :           "border-gray-300 bg-white text-gray-400"
                  }`}>
                    <span className="font-bold">{i + 1}</span>
                    <span>{labels[i]}</span>
                    {isDone && <span className="text-gray-500">✓</span>}
                  </div>
                  {i < 2 && <div className="w-5 border-t border-dashed border-gray-300" />}
                </div>
              );
            })}
          </div>
        </div>
        {/* Close — only allowed on form steps, not during generating */}
        {step !== "generating" && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-800 text-xs font-mono border border-gray-300 px-3 py-1 cursor-pointer transition-colors"
          >
            × 取消
          </button>
        )}
      </div>

      {/* Wizard body */}
      <div className="relative flex-1 flex flex-col overflow-hidden">
        {step === "create" && (
          <PageCreate onNext={() => setStep("preferences")} />
        )}
        {step === "preferences" && (
          <PagePreferences
            onNext={() => setStep("generating")}
            onBack={() => setStep("create")}
          />
        )}
        {step === "generating" && (
          <PageGenerating onDone={handleGeneratingDone} />
        )}
      </div>
    </div>
  );
}

// ─── Page 1: 创建行程 ──────────────────────────────────────────────────────

function PageCreate({ onNext }: { onNext: () => void }) {
  return (
    <div className="flex-1 overflow-auto bg-gray-50">
      <div className="max-w-3xl mx-auto py-12 px-6">
        {/* Header */}
        <div className="mb-10">
          <WAnnotation text="页面标题区" />
          <h1 className="text-2xl font-bold text-gray-900 mt-1 mb-1">开始规划你的旅行</h1>
          <p className="text-sm text-gray-500">填写基本信息，AI 将为你生成专属行程方案</p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center gap-0 mb-10">
          {["基本信息", "偏好设置", "生成行程"].map((s, i) => (
            <div key={s} className="flex items-center">
              <div className={`flex items-center gap-2 px-3 py-1.5 border text-xs font-mono ${
                i === 0 ? "border-gray-900 bg-gray-900 text-white" : "border-gray-300 bg-white text-gray-400"
              }`}>
                <span className="font-bold">{i + 1}</span>
                <span>{s}</span>
              </div>
              {i < 2 && <div className="w-8 border-t border-dashed border-gray-400" />}
            </div>
          ))}
          <WAnnotation text="  ← 步骤指示器" />
        </div>

        {/* Form */}
        <WBox className="p-6">
          <SectionTitle text="目的地" />
          <div className="mb-6">
            <WInput label="搜索目的地城市或国家" placeholder="例如：日本东京 / 法国巴黎" />
            <WAnnotation text="支持城市、国家、地区搜索" />
          </div>

          <SectionTitle text="行程时间" />
          <div className="grid grid-cols-3 gap-4 mb-6">
            <WInput label="出发日期" placeholder="选择日期" />
            <WInput label="返回日期" placeholder="选择日期" />
            <div className="flex flex-col gap-1">
              <span className="text-xs font-medium text-gray-600">行程天数</span>
              <div className="border border-gray-400 bg-gray-50 h-9 px-3 flex items-center justify-between">
                <span className="text-xs text-gray-400 font-mono">自动计算</span>
                <span className="text-xs font-bold text-gray-700 font-mono">7 天</span>
              </div>
            </div>
          </div>

          <SectionTitle text="旅行人数" />
          <div className="grid grid-cols-3 gap-4 mb-6">
            {[
              { label: "成人", sub: "18岁以上", val: "2" },
              { label: "儿童", sub: "2–17岁", val: "0" },
              { label: "婴幼儿", sub: "0–2岁", val: "0" },
            ].map((g) => (
              <div key={g.label} className="border border-gray-300 p-3 bg-gray-50">
                <p className="text-xs font-medium text-gray-700">{g.label}</p>
                <p className="text-[10px] text-gray-400 font-mono mb-2">{g.sub}</p>
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 border border-gray-400 flex items-center justify-center text-sm font-mono">−</div>
                  <span className="text-base font-bold w-6 text-center">{g.val}</span>
                  <div className="w-7 h-7 border border-gray-400 flex items-center justify-center text-sm font-mono">+</div>
                </div>
              </div>
            ))}
          </div>

          <SectionTitle text="预算范围（可选）" />
          <div className="grid grid-cols-2 gap-4 mb-6">
            <WInput label="最低预算（元）" placeholder="¥ 0" />
            <WInput label="最高预算（元）" placeholder="¥ 20,000" />
          </div>
          <div className="flex gap-2 mb-6">
            {["经济型", "舒适型", "豪华型"].map((t) => (
              <WTag key={t} label={t} active={t === "舒适型"} />
            ))}
            <WAnnotation text="  ← 预算档位快捷选择" />
          </div>

          <Divider className="mb-4" />
          <div className="flex justify-between items-center">
            <WAnnotation text="所有字段填写完整后可进入下一步" />
            <WBtn label="下一步：偏好设置 →" primary onClick={onNext} />
          </div>
        </WBox>
      </div>
    </div>
  );
}

// ─── Page 2: 偏好设置 ──────────────────────────────────────────────────────

// 可自定义标签组件：预设标签 + 添加自定义
function TagGroup({
  title,
  preset,
  defaultSelected,
}: {
  title: string;
  preset: string[];
  defaultSelected: string[];
}) {
  const [selected, setSelected] = useState<string[]>(defaultSelected);
  const [custom, setCustom] = useState<string[]>([]);
  const [inputVal, setInputVal] = useState("");
  const [editing, setEditing] = useState(false);

  const toggle = (tag: string) =>
    setSelected((s) => (s.includes(tag) ? s.filter((x) => x !== tag) : [...s, tag]));

  const addCustom = () => {
    const v = inputVal.trim();
    if (v && !preset.includes(v) && !custom.includes(v)) {
      setCustom((c) => [...c, v]);
      setSelected((s) => [...s, v]);
    }
    setInputVal("");
    setEditing(false);
  };

  const removeCustom = (tag: string) => {
    setCustom((c) => c.filter((x) => x !== tag));
    setSelected((s) => s.filter((x) => x !== tag));
  };

  const allTags = [...preset, ...custom];

  return (
    <WBox className="p-6">
      <SectionTitle text={title} />
      <div className="flex flex-wrap gap-2 mb-3">
        {allTags.map((t) => (
          <div key={t} className="flex items-center gap-0">
            <button
              onClick={() => toggle(t)}
              className={`border text-xs px-3 py-1.5 font-mono cursor-pointer transition-colors ${
                selected.includes(t)
                  ? "border-gray-900 bg-gray-900 text-white"
                  : "border-gray-400 bg-white text-gray-700 hover:border-gray-600"
              }`}
            >
              {t}
            </button>
            {/* 自定义标签可删除 */}
            {custom.includes(t) && (
              <button
                onClick={() => removeCustom(t)}
                className="border border-l-0 border-gray-400 bg-white text-gray-400 hover:text-gray-800 hover:bg-gray-100 px-1.5 py-1.5 text-xs font-mono cursor-pointer transition-colors"
                title="删除"
              >
                ×
              </button>
            )}
          </div>
        ))}

        {/* 添加按钮 / 输入框 */}
        {editing ? (
          <div className="flex items-center gap-0">
            <input
              autoFocus
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") addCustom();
                if (e.key === "Escape") { setEditing(false); setInputVal(""); }
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
              onClick={() => { setEditing(false); setInputVal(""); }}
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

function PagePreferences({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const [pace, setPace] = useState(50);

  return (
    <div className="flex-1 overflow-auto bg-gray-50">
      <div className="max-w-3xl mx-auto py-12 px-6">
        <div className="mb-8">
          <WAnnotation text="页面标题区" />
          <h1 className="text-2xl font-bold text-gray-900 mt-1 mb-1">告诉我们你的旅行偏好</h1>
          <p className="text-sm text-gray-500">帮助 AI 生成更符合你风格的个性化行程</p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center gap-0 mb-10">
          {["基本信息", "偏好设置", "生成行程"].map((s, i) => (
            <div key={s} className="flex items-center">
              <div
                onClick={i === 0 ? onBack : undefined}
                className={`flex items-center gap-2 px-3 py-1.5 border text-xs font-mono ${
                  i <= 1 ? "border-gray-900 bg-gray-900 text-white" : "border-gray-300 bg-white text-gray-400"
                } ${i === 0 ? "cursor-pointer hover:bg-gray-700" : ""}`}
              >
                <span className="font-bold">{i + 1}</span>
                <span>{s}</span>
                {i === 0 && <span className="opacity-60 text-[10px]">←</span>}
              </div>
              {i < 2 && <div className="w-8 border-t border-dashed border-gray-400" />}
            </div>
          ))}
        </div>

        <div className="space-y-5">
          {/* Interests — 可自定义 */}
          <TagGroup
            title="兴趣偏好（可多选）"
            preset={["文化历史", "美食探索", "自然风光", "购物血拼", "户外冒险", "主题乐园", "艺术展览", "夜生活", "温泉休闲", "本地市场"]}
            defaultSelected={["文化历史", "美食探索", "自然风光"]}
          />

          {/* Pace */}
          <WBox className="p-6">
            <SectionTitle text="行程节奏" />
            <div className="relative mb-3">
              <input
                type="range"
                min={0}
                max={100}
                value={pace}
                onChange={(e) => setPace(Number(e.target.value))}
                className="w-full accent-gray-800"
              />
            </div>
            <div className="flex justify-between text-xs font-mono text-gray-500">
              <span>轻松悠闲<br /><span className="text-[10px] text-gray-400">每天 1–2 个景点</span></span>
              <span className="text-center">适中<br /><span className="text-[10px] text-gray-400">每天 3–4 个景点</span></span>
              <span className="text-right">紧凑高效<br /><span className="text-[10px] text-gray-400">每天 5+ 个景点</span></span>
            </div>
          </WBox>

          {/* Transport — 可自定义 */}
          <TagGroup
            title="交通偏好"
            preset={["公共交通", "自驾", "出租车 / 网约车", "步行为主", "包车"]}
            defaultSelected={["公共交通", "步行为主"]}
          />

          {/* Accommodation — 可自定义 */}
          <TagGroup
            title="住宿类型偏好"
            preset={["酒店", "民宿", "青旅", "度假村", "精品酒店"]}
            defaultSelected={["酒店"]}
          />

          {/* Custom input */}
          <WBox className="p-6">
            <SectionTitle text="其他自定义偏好（可选）" />
            <div className="border border-gray-300 bg-gray-50 h-24 p-3">
              <span className="text-xs text-gray-400 font-mono">
                例如：我有老人同行，希望行程不要太赶；对海鲜过敏；希望多安排购物时间……
              </span>
            </div>
            <WAnnotation text="自由输入，AI 将结合以上偏好综合规划" />
          </WBox>
        </div>

        <div className="flex justify-between mt-6">
          <WBtn label="← 返回修改" onClick={onBack} />
          <WBtn label="开始生成行程 →" primary onClick={onNext} />
        </div>
      </div>
    </div>
  );
}

// ─── Page 3: 生成中 ─────────────────────────────────────────────────────────

function PageGenerating({ onDone }: { onDone: () => void }) {
  const steps = [
    { label: "分析旅行偏好", done: true },
    { label: "搜索热门景点", done: true },
    { label: "规划最优路线", done: true },
    { label: "匹配天气数据", active: true },
    { label: "估算行程预算", done: false },
    { label: "生成行程方案", done: false },
  ];
  return (
    <div className="flex-1 overflow-auto bg-gray-50 flex items-center justify-center">
      <div className="w-[480px]">
        <WBox className="p-10 text-center">
          {/* Animation placeholder */}
          <div className="w-20 h-20 bg-gray-200 border border-gray-300 mx-auto mb-6 flex items-center justify-center">
            <span className="text-[10px] font-mono text-gray-400">动画占位</span>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-1">AI 正在规划你的行程</h2>
          <p className="text-sm text-gray-500 mb-8">东京 · 7天 · 2人 · 文化历史 / 美食探索</p>

          {/* Progress bar */}
          <div className="mb-6">
            <div className="h-2 bg-gray-200 border border-gray-300 mb-1">
              <div className="h-full bg-gray-700" style={{ width: "65%" }} />
            </div>
            <div className="flex justify-between">
              <WAnnotation text="处理进度" />
              <WAnnotation text="65%" />
            </div>
          </div>

          {/* Steps */}
          <div className="text-left space-y-2 mb-8">
            {steps.map((s) => (
              <div key={s.label} className={`flex items-center gap-3 text-xs font-mono ${
                s.done ? "text-gray-500" : s.active ? "text-gray-900 font-medium" : "text-gray-300"
              }`}>
                <div className={`w-4 h-4 border flex items-center justify-center shrink-0 ${
                  s.done ? "border-gray-500 bg-gray-500 text-white" : s.active ? "border-gray-900 bg-white" : "border-gray-300"
                }`}>
                  {s.done && "✓"}
                  {s.active && <div className="w-2 h-2 bg-gray-900" />}
                </div>
                {s.label}
                {s.active && <span className="text-gray-400">…</span>}
              </div>
            ))}
          </div>

          <WAnnotation text="通常需要 10–30 秒，请稍候" />

          <div className="mt-6 pt-5 border-t border-gray-200">
            <WBtn label="跳过等待，直接查看草稿 →" primary onClick={onDone} className="w-full" />
          </div>
        </WBox>

        {/* Tip box */}
        <WBox className="mt-4 p-4 bg-gray-50">
          <WLabel text="💡 小贴士：东京 3 月份樱花季正值旺季，景点可能较拥挤，建议提前预订门票" />
        </WBox>
      </div>
    </div>
  );
}

// ─── Page 4: 可编辑行程工作区 ───────────────────────────────────────────────

function AttractionCard({ name, time, type, onClick }: {
  name: string; time: string; type: string; onClick: () => void;
}) {
  return (
    <div
      className="border border-gray-300 bg-white p-3 flex gap-3 cursor-pointer hover:border-gray-600 transition-colors"
      onClick={onClick}
    >
      <WImgBox className="w-16 h-14 shrink-0" label="景点图" />
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-medium text-gray-800 leading-tight">{name}</p>
          <span className="text-[10px] font-mono text-gray-400 border border-gray-300 px-1.5 py-0.5 shrink-0">{type}</span>
        </div>
        <p className="text-xs font-mono text-gray-500 mt-1">{time}</p>
        <div className="flex items-center gap-2 mt-2">
          <div className="flex gap-0.5">
            {[1,2,3,4,5].map(i => <div key={i} className={`w-2 h-2 ${i <= 4 ? "bg-gray-600" : "bg-gray-300"}`} />)}
          </div>
          <span className="text-[10px] font-mono text-gray-500">4.2 · 预计 2 小时 · ¥80</span>
        </div>
      </div>
      <div className="flex flex-col gap-1 shrink-0">
        <button className="text-[10px] font-mono text-gray-500 border border-gray-300 px-2 py-0.5 hover:bg-gray-50">编辑</button>
        <button className="text-[10px] font-mono text-gray-500 border border-gray-300 px-2 py-0.5 hover:bg-gray-50">删除</button>
        <button className="text-[10px] font-mono text-gray-500 border border-gray-300 px-2 py-0.5 hover:bg-gray-50">⇅</button>
      </div>
    </div>
  );
}

// ─── 右侧可折叠面板 ──────────────────────────────────────────────────────────

function CollapsibleSection({
  title,
  badge,
  defaultOpen = false,
  children,
}: {
  title: string;
  badge?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-gray-200">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-3 py-2.5 cursor-pointer hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-gray-700">{title}</span>
          {badge && (
            <span className="text-[10px] font-mono text-gray-400 border border-gray-200 px-1.5 py-0.5 bg-gray-50">
              {badge}
            </span>
          )}
        </div>
        <span className="text-gray-400 font-mono text-xs">{open ? "▲" : "▼"}</span>
      </button>
      {open && <div className="px-3 pb-3">{children}</div>}
    </div>
  );
}

function RightPanel({ onOutput }: { onOutput: () => void }) {
  return (
    <div className="w-60 border-l border-gray-300 bg-white flex flex-col shrink-0 overflow-auto">

      {/* 地图 — 主要信息，默认展开 */}
      <CollapsibleSection title="地图预览" badge="路线" defaultOpen={true}>
        <WImgBox className="w-full h-36" label="地图占位 / 路线可视化" />
        <button className="text-[10px] font-mono text-gray-400 mt-1.5 underline cursor-pointer hover:text-gray-700">
          查看大图
        </button>
        <div className="mt-2 space-y-0.5">
          {[["总距离","12.4 km"],["步行","3.2 km"],["地铁","9.2 km"],["耗时","~8.5h"]].map(([k,v])=>(
            <div key={k} className="flex justify-between text-[10px] font-mono text-gray-500">
              <span>{k}</span><span className="font-medium text-gray-700">{v}</span>
            </div>
          ))}
        </div>
      </CollapsibleSection>

      {/* 天气 — 默认展开 */}
      <CollapsibleSection title="天气预报" badge="3月15日 晴" defaultOpen={true}>
        <div className="flex gap-1.5">
          {[["15日","☀️","晴","12–18"],["16日","⛅","多云","10–15"],["17日","🌧","小雨","9–13"]].map(([d,icon,desc,temp])=>(
            <div key={d} className="flex-1 border border-gray-200 p-1.5 text-center">
              <p className="text-[10px] font-mono text-gray-400">{d}</p>
              <p className="text-base my-0.5">{icon}</p>
              <p className="text-[10px] font-mono text-gray-600">{desc}</p>
              <p className="text-[10px] font-mono text-gray-400">{temp}°</p>
            </div>
          ))}
        </div>
        <p className="text-[10px] font-mono text-gray-400 mt-2">💡 早晚温差大，建议携带外套</p>
      </CollapsibleSection>

      {/* 预算 — 默认折叠 */}
      <CollapsibleSection title="预算概览" badge="¥ 8,200" defaultOpen={false}>
        <div className="space-y-1.5">
          {[["交通","¥ 2,400",30],["餐饮","¥ 1,800",22],["景点门票","¥ 1,200",15],["住宿","¥ 2,800",35]].map(([k,v,pct])=>(
            <div key={k as string}>
              <div className="flex justify-between text-[10px] font-mono text-gray-600 mb-0.5">
                <span>{k}</span><span>{v}</span>
              </div>
              <div className="h-1 bg-gray-100 border border-gray-200">
                <div className="h-full bg-gray-500" style={{ width: `${pct}%` }} />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-2 pt-2 border-t border-gray-200 flex justify-between text-xs font-semibold font-mono text-gray-800">
          <span>合计</span><span>¥ 8,200</span>
        </div>
      </CollapsibleSection>

      {/* 路线备注 — 默认折叠 */}
      <CollapsibleSection title="路线备注" defaultOpen={false}>
        <div className="space-y-1.5">
          {[
            "浅草寺建议 9 点前到达，避开人流",
            "秋叶原步行街周末关闭部分路段",
            "上野公园 3 月樱花季可能拥挤",
          ].map((note, i) => (
            <div key={i} className="flex gap-2 text-[10px] font-mono text-gray-600">
              <span className="text-gray-300 shrink-0">·</span>
              <span>{note}</span>
            </div>
          ))}
        </div>
      </CollapsibleSection>

      {/* 输出按钮 — 固定底部 */}
      <div className="mt-auto border-t border-gray-200 p-3">
        <WBtn label="输出行程方案 →" primary className="w-full" onClick={onOutput} />
        <WAnnotation text="导出 PDF / 分享链接" />
      </div>
    </div>
  );
}

function PageWorkspace({
  onOpenModal,
  onOutput,
}: {
  onOpenModal: () => void;
  onOutput: () => void;
}) {
  const [activeDay, setActiveDay] = useState(0);
  const days = ["第1天", "第2天", "第3天", "第4天", "第5天", "第6天", "第7天"];
  const attractions = [
    { name: "浅草寺", time: "09:00 – 11:00", type: "文化" },
    { name: "秋叶原电器街", time: "13:00 – 15:30", type: "购物" },
    { name: "上野公园", time: "16:00 – 17:30", type: "自然" },
    { name: "居酒屋晚餐 — 新宿", time: "19:00 – 21:00", type: "美食" },
  ];

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Left: Day sidebar */}
      <div className="w-36 border-r border-gray-300 bg-white flex flex-col shrink-0">
        <div className="p-3 border-b border-gray-200">
          <WAnnotation text="日程导航" />
          <p className="text-xs font-semibold text-gray-700 mt-0.5">东京 · 7天</p>
        </div>
        {days.map((d, i) => (
          <button
            key={d}
            onClick={() => setActiveDay(i)}
            className={`text-left px-3 py-2.5 text-xs font-mono border-b border-gray-100 cursor-pointer transition-colors ${
              i === activeDay ? "bg-gray-900 text-white" : "text-gray-600 hover:bg-gray-50"
            }`}
          >
            <span className="block font-semibold">{d}</span>
            <span className="text-[10px] opacity-70">3月{15 + i}日</span>
          </button>
        ))}
        <div className="p-3 mt-auto border-t border-gray-200">
          <button className="w-full border border-dashed border-gray-400 text-xs font-mono text-gray-500 py-2 hover:bg-gray-50 cursor-pointer">
            + 添加天数
          </button>
        </div>
      </div>

      {/* Center: Timeline */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Toolbar */}
        <div className="border-b border-gray-300 bg-white px-4 py-2 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-gray-800">第1天 · 3月15日 · 浅草 / 秋叶原 / 上野</span>
            <WAnnotation text="← 当天主题自动生成" />
          </div>
          <div className="flex items-center gap-2">
            <WBtn label="+ 添加景点" small />
            <WBtn label="AI 优化路线" small />
          </div>
        </div>

        {/* Timeline content */}
        <div className="flex-1 overflow-auto p-4">
          <div className="flex items-center gap-2 mb-4">
            <WImgBox className="w-4 h-4" label="" />
            <span className="text-xs font-mono text-gray-500">出发点：新宿酒店</span>
          </div>

          {attractions.map((a, i) => (
            <div key={a.name} className="flex gap-3 mb-3">
              {/* Timeline line */}
              <div className="flex flex-col items-center w-8 shrink-0">
                <div className="w-3 h-3 border-2 border-gray-700 bg-white rounded-full mt-2" />
                {i < attractions.length - 1 && <div className="w-0.5 flex-1 bg-gray-300 my-1" />}
              </div>
              <div className="flex-1">
                <AttractionCard {...a} onClick={onOpenModal} />
                {i < attractions.length - 1 && (
                  <div className="flex items-center gap-2 my-2 ml-2">
                    <div className="w-3 h-3 bg-gray-300 flex items-center justify-center">
                      <div className="w-1.5 h-1.5 bg-gray-500" />
                    </div>
                    <span className="text-[10px] font-mono text-gray-400">地铁 · 约 25 分钟 · ¥ 200</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* AI chat input */}
          <div className="mt-6 pt-4 border-t border-dashed border-gray-300">
            <WAnnotation text="AI 调整输入框" />
            <div className="border border-gray-400 bg-white p-3 flex items-center gap-3 mt-1">
              <WImgBox className="w-6 h-6 rounded-full shrink-0" label="" />
              <div className="flex-1 border-b border-gray-300 pb-1">
                <span className="text-xs text-gray-400 font-mono">告诉 AI 你想调整什么，例如：第三天景点太多，帮我拆成两天……</span>
              </div>
              <WBtn label="发送" small primary />
            </div>
          </div>
        </div>
      </div>

      {/* Right: collapsible info panels */}
      <RightPanel onOutput={onOutput} />
    </div>
  );
}

// ─── Page 5: 景点详情弹窗 ──────────────────────────────────────────────────

function ModalAttraction({ onClose }: { onClose: () => void }) {
  return (
    <div className="absolute inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="w-[640px] bg-white border border-gray-400 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-300 px-5 py-3">
          <div>
            <WAnnotation text="景点详情弹窗" />
            <h2 className="text-base font-bold text-gray-900">浅草寺</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 text-lg font-mono hover:text-gray-900 border border-gray-300 w-7 h-7 flex items-center justify-center"
          >
            ×
          </button>
        </div>

        <div className="p-5">
          {/* Top: image + meta */}
          <div className="flex gap-4 mb-4">
            <WImgBox className="w-52 h-36 shrink-0" label="景点主图" />
            <div className="flex-1">
              <div className="flex flex-wrap gap-1.5 mb-3">
                {["文化", "历史", "寺庙", "东京"].map(t => (
                  <span key={t} className="text-[10px] font-mono border border-gray-300 px-2 py-0.5 text-gray-600">{t}</span>
                ))}
              </div>
              <div className="space-y-1.5">
                {[
                  ["开放时间", "06:00 – 17:00"],
                  ["门票", "免费（部分区域收费）"],
                  ["建议游览", "1.5 – 2 小时"],
                  ["评分", "★★★★☆  4.6 / 5.0"],
                  ["地址", "东京都台东区浅草 2-3-1"],
                ].map(([k, v]) => (
                  <div key={k} className="flex gap-2 text-xs font-mono">
                    <span className="text-gray-400 w-20 shrink-0">{k}</span>
                    <span className="text-gray-700">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Description */}
          <div className="mb-4">
            <p className="text-xs font-semibold text-gray-700 mb-1">景点介绍</p>
            <div className="bg-gray-50 border border-gray-200 p-3">
              <p className="text-xs text-gray-600 leading-relaxed">
                浅草寺是东京最古老、最具代表性的佛教寺院，始建于公元628年。雷门前那把巨大的红灯笼是东京的标志性景观之一，每年吸引超过3000万游客前来参观。
              </p>
            </div>
          </div>

          {/* Photo strip */}
          <div className="mb-4">
            <p className="text-xs font-semibold text-gray-700 mb-1">景点图集</p>
            <div className="flex gap-2">
              {[1,2,3,4].map(i => (
                <WImgBox key={i} className="w-20 h-16 flex-1" label={`图${i}`} />
              ))}
            </div>
          </div>

          {/* Nearby */}
          <div className="mb-4">
            <p className="text-xs font-semibold text-gray-700 mb-1">附近景点</p>
            <div className="flex gap-2">
              {["仲见世购物街", "浅草神社", "隅田公园"].map(n => (
                <div key={n} className="flex-1 border border-gray-300 p-2 text-center">
                  <WImgBox className="w-full h-10 mb-1" label="" />
                  <p className="text-[10px] font-mono text-gray-600">{n}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <Divider className="mb-4" />
          <div className="flex gap-2 justify-end">
            <WBtn label="查看官网" small />
            <WBtn label="复制位置" small />
            <WBtn label="从行程中移除" small />
            <WBtn label="✓ 已在行程中" primary small />
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Page 6: 输出方案预览（一天一页） ────────────────────────────────────────

const OUTPUT_DAYS = [
  {
    day: "第1天", date: "3月15日", title: "浅草 · 秋叶原 · 上野",
    weather: { desc: "晴", range: "12–18°C", icon: "☀️" },
    transport: "地铁 · 合计约 ¥400 · 建议购买一日通票",
    budget: { 交通: 400, 餐饮: 320, 门票: 80, 其他: 100 },
    spots: [
      { name: "浅草寺", time: "09:00–11:00", type: "文化", duration: "2h", cost: 0, transit: null },
      { name: "仲见世购物街", time: "11:00–12:00", type: "购物", duration: "1h", cost: 0, transit: "步行 5 分钟" },
      { name: "秋叶原电器街", time: "13:30–15:30", type: "购物", duration: "2h", cost: 0, transit: "地铁 20 分钟 · ¥180" },
      { name: "上野公园 / 博物馆", time: "16:00–18:00", type: "自然", duration: "2h", cost: 80, transit: "地铁 10 分钟 · ¥140" },
      { name: "居酒屋晚餐", time: "19:00–21:00", type: "美食", duration: "2h", cost: 200, transit: "步行 8 分钟" },
    ],
  },
  {
    day: "第2天", date: "3月16日", title: "新宿 · 涩谷 · 代官山",
    weather: { desc: "多云", range: "10–15°C", icon: "⛅" },
    transport: "地铁 + 步行 · 合计约 ¥350",
    budget: { 交通: 350, 餐饮: 380, 门票: 500, 其他: 150 },
    spots: [
      { name: "新宿御苑", time: "09:00–11:00", type: "自然", duration: "2h", cost: 500, transit: null },
      { name: "新宿购物街", time: "11:30–13:00", type: "购物", duration: "1.5h", cost: 0, transit: "步行 10 分钟" },
      { name: "涩谷十字路口", time: "14:30–15:30", type: "地标", duration: "1h", cost: 0, transit: "地铁 15 分钟 · ¥180" },
      { name: "代官山 T-SITE", time: "16:00–18:00", type: "文化", duration: "2h", cost: 0, transit: "步行 12 分钟" },
      { name: "惠比寿花园广场", time: "18:30–20:00", type: "休闲", duration: "1.5h", cost: 0, transit: "步行 10 分钟" },
    ],
  },
  {
    day: "第3天", date: "3月17日", title: "银座 · 筑地 · 台场",
    weather: { desc: "小雨", range: "9–13°C", icon: "🌧️" },
    transport: "地铁 + 百合鸥线 · 合计约 ¥500",
    budget: { 交通: 500, 餐饮: 500, 门票: 3200, 其他: 200 },
    spots: [
      { name: "筑地市场早餐", time: "08:00–09:30", type: "美食", duration: "1.5h", cost: 200, transit: null },
      { name: "银座购物", time: "10:30–12:30", type: "购物", duration: "2h", cost: 0, transit: "地铁 15 分钟 · ¥200" },
      { name: "台场海滨公园", time: "14:00–15:30", type: "自然", duration: "1.5h", cost: 0, transit: "百合鸥线 30 分钟 · ¥300" },
      { name: "teamLab 数字艺术", time: "16:00–19:00", type: "艺术", duration: "3h", cost: 3200, transit: "步行 5 分钟" },
    ],
  },
];

// 打印纸张模拟容器
function PrintPage({ pageNum, total, children }: {
  pageNum: number; total: number; children: React.ReactNode;
}) {
  return (
    <div className="relative mb-2">
      {/* 水印 */}
      <div
        className="absolute inset-0 flex items-center justify-center pointer-events-none z-10 select-none"
        style={{ transform: "rotate(-30deg)" }}
      >
        <span className="text-5xl font-bold text-gray-200 tracking-widest opacity-60 whitespace-nowrap">
          预览草稿
        </span>
      </div>

      {/* 纸张主体 */}
      <div className="bg-white shadow-lg border border-gray-300 relative overflow-hidden"
        style={{ minHeight: "297mm", width: "210mm", margin: "0 auto" }}>

        {/* 页眉 */}
        <div className="border-b-2 border-gray-900 px-10 py-3 flex items-center justify-between">
          <span className="text-xs font-mono font-bold tracking-widest text-gray-900 uppercase">
            东京 7 日深度文化之旅
          </span>
          <span className="text-xs font-mono text-gray-400">
            AI 行程规划 · 仅供参考
          </span>
        </div>

        {/* 内容区 */}
        <div className="px-10 py-8">{children}</div>

        {/* 页脚 */}
        <div className="absolute bottom-0 left-0 right-0 border-t border-gray-200 px-10 py-2 flex items-center justify-between bg-white">
          <span className="text-[10px] font-mono text-gray-400">由 AI 行程规划生成 · 2024-03-01</span>
          <span className="text-[10px] font-mono text-gray-400">{pageNum} / {total}</span>
        </div>
      </div>

      {/* 分页线 */}
      <div className="flex items-center gap-3 my-4 px-4">
        <div className="flex-1 border-t-2 border-dashed border-gray-400" />
        <span className="text-[10px] font-mono text-gray-400 bg-gray-300 px-2 py-0.5 whitespace-nowrap">
          ✂ 分页线 · 第 {pageNum} 页结束
        </span>
        <div className="flex-1 border-t-2 border-dashed border-gray-400" />
      </div>
    </div>
  );
}

function OutputDayPage({ data, pageNum, total }: {
  data: typeof OUTPUT_DAYS[0]; pageNum: number; total: number;
}) {
  const dayBudgetTotal = Object.values(data.budget).reduce((a, b) => a + b, 0);

  return (
    <PrintPage pageNum={pageNum} total={total}>
      {/* 日期标题块 */}
      <div className="flex items-end justify-between mb-6 pb-4 border-b border-gray-200">
        <div>
          <p className="text-[11px] font-mono text-gray-400 uppercase tracking-widest mb-1">DAY {pageNum}</p>
          <h2 className="text-2xl font-bold text-gray-900 leading-tight">{data.title}</h2>
          <p className="text-sm font-mono text-gray-500 mt-1">2024年 {data.date} · 东京</p>
        </div>
        <div className="text-right">
          <div className="text-3xl mb-1">{data.weather.icon}</div>
          <p className="text-sm font-mono text-gray-700">{data.weather.desc}</p>
          <p className="text-xs font-mono text-gray-400">{data.weather.range}</p>
        </div>
      </div>

      {/* 两栏：时间轴 + 侧栏 */}
      <div className="flex gap-8">
        {/* 左：时间轴景点 */}
        <div className="flex-1">
          <p className="text-[10px] font-mono text-gray-400 uppercase tracking-widest mb-3">行程安排</p>
          {data.spots.map((spot, i) => (
            <div key={spot.name} className="flex gap-3 mb-4">
              <div className="flex flex-col items-center w-5 shrink-0">
                <div className="w-3 h-3 border-2 border-gray-700 bg-white mt-1 shrink-0" />
                {i < data.spots.length - 1 && <div className="w-px flex-1 bg-gray-300 mt-1" />}
              </div>
              <div className="flex-1 pb-2">
                {spot.transit && (
                  <p className="text-[10px] font-mono text-gray-400 mb-1 -mt-0.5">↳ {spot.transit}</p>
                )}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{spot.name}</p>
                    <div className="flex items-center gap-3 mt-0.5 text-[11px] font-mono text-gray-500">
                      <span>{spot.time}</span>
                      <span>· 约 {spot.duration}</span>
                      <span>· {spot.cost === 0 ? "免费" : `¥ ${spot.cost}`}</span>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono border border-gray-300 px-1.5 py-0.5 text-gray-500 shrink-0">{spot.type}</span>
                </div>
              </div>
            </div>
          ))}
          <div className="flex items-center gap-2 mt-1 ml-8">
            <span className="text-[10px] font-mono text-gray-400">↩ 返回酒店</span>
          </div>
        </div>

        {/* 右：地图 + 天气 + 预算 */}
        <div className="w-44 shrink-0 space-y-5">
          {/* 地图 */}
          <div>
            <p className="text-[10px] font-mono text-gray-400 uppercase tracking-widest mb-2">当日路线</p>
            <WImgBox className="w-full h-32" label="地图占位" />
            <div className="mt-1.5 space-y-0.5">
              {[["总距离","10.2 km"],["步行","2.8 km"],["地铁","7.4 km"]].map(([k,v])=>(
                <div key={k} className="flex justify-between text-[10px] font-mono text-gray-500">
                  <span>{k}</span><span className="font-medium">{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 天气 */}
          <div>
            <p className="text-[10px] font-mono text-gray-400 uppercase tracking-widest mb-2">天气详情</p>
            <div className="space-y-0.5">
              {[["湿度","65%"],["降水","20%"],["风力","3级"],["紫外线","较弱"]].map(([k,v])=>(
                <div key={k} className="flex justify-between text-[10px] font-mono text-gray-500">
                  <span>{k}</span><span>{v}</span>
                </div>
              ))}
            </div>
            <p className="text-[10px] font-mono text-gray-400 mt-1.5 leading-relaxed">{data.transport}</p>
          </div>

          {/* 预算 */}
          <div>
            <p className="text-[10px] font-mono text-gray-400 uppercase tracking-widest mb-2">当日预算</p>
            {Object.entries(data.budget).map(([k, v]) => (
              <div key={k} className="mb-1">
                <div className="flex justify-between text-[10px] font-mono text-gray-600 mb-0.5">
                  <span>{k}</span><span>¥ {v}</span>
                </div>
                <div className="h-1 bg-gray-100">
                  <div className="h-full bg-gray-500" style={{ width: `${Math.round(v / dayBudgetTotal * 100)}%` }} />
                </div>
              </div>
            ))}
            <div className="flex justify-between text-[11px] font-mono font-bold text-gray-800 mt-1.5 pt-1.5 border-t border-gray-300">
              <span>合计</span><span>¥ {dayBudgetTotal}</span>
            </div>
          </div>
        </div>
      </div>
    </PrintPage>
  );
}

function PageOutput({ onBack }: { onBack: () => void }) {
  const [activeDay, setActiveDay] = useState<number>(-1);
  const allDays = OUTPUT_DAYS;

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Left: readonly nav panel */}
      <div className="w-40 border-r border-gray-300 bg-white flex flex-col shrink-0">
        {/* 只读标识 */}
        <div className="p-3 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-1.5 mb-1">
            <div className="w-2 h-2 bg-gray-400" />
            <span className="text-[10px] font-mono text-gray-500 uppercase tracking-widest">只读预览</span>
          </div>
          <p className="text-xs font-semibold text-gray-700">输出方案</p>
        </div>

        <div className="flex-1 overflow-auto">
          {[
            { id: -1, label: "封面总览", sub: "行程概要" },
            ...allDays.map((d, i) => ({ id: i, label: d.day, sub: d.date })),
            { id: 99, label: "预算总表", sub: "费用明细" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveDay(item.id)}
              className={`w-full text-left px-3 py-2.5 text-xs font-mono border-b border-gray-100 cursor-pointer transition-colors ${
                activeDay === item.id ? "bg-gray-900 text-white" : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              <span className="block font-semibold">{item.label}</span>
              <span className="text-[10px] opacity-70">{item.sub}</span>
            </button>
          ))}
        </div>

        {/* 导出操作 — 唯一可操作区 */}
        <div className="border-t border-gray-200 p-3 space-y-1.5 bg-gray-50">
          <p className="text-[10px] font-mono text-gray-400 uppercase tracking-widest mb-2">导出</p>
          <WBtn label="导出 PDF" primary small className="w-full" />
          <WBtn label="分享链接" small className="w-full" />
          <WBtn label="同步日历" small className="w-full" />
          <Divider className="my-1" />
          <WBtn label="← 返回编辑" small className="w-full" onClick={onBack} />
        </div>
      </div>

      {/* Right: 打印预览区 — 深色背景突出纸张感 */}
      <div className="flex-1 overflow-auto bg-gray-500 py-8 px-6">
        {/* 只读提示条 */}
        <div className="flex items-center justify-between mb-6 max-w-[210mm] mx-auto">
          <div className="flex items-center gap-2 bg-gray-700 text-gray-200 text-[11px] font-mono px-3 py-1.5">
            <span>🔒</span>
            <span>只读模式 · 如需修改请返回行程工作区</span>
          </div>
          <div className="flex gap-1.5">
            <button
              onClick={() => setActiveDay(d => Math.max(-1, d === 99 ? allDays.length - 1 : d - 1))}
              className="bg-gray-600 text-white text-xs font-mono px-3 py-1.5 cursor-pointer hover:bg-gray-500"
            >← 上一页</button>
            <button
              onClick={() => setActiveDay(d => d === -1 ? 0 : d >= allDays.length - 1 ? 99 : d + 1)}
              className="bg-gray-600 text-white text-xs font-mono px-3 py-1.5 cursor-pointer hover:bg-gray-500"
            >下一页 →</button>
          </div>
        </div>

        {/* 封面页 */}
        {activeDay === -1 && (
          <PrintPage pageNum={0} total={allDays.length + 2}>
            <div className="text-center mb-8">
              <WImgBox className="w-full h-40 mb-6" label="封面大图占位" />
              <h1 className="text-3xl font-bold text-gray-900 mb-2 leading-tight">
                东京 7 日深度文化之旅
              </h1>
              <p className="text-sm font-mono text-gray-500 mb-5">
                2024年3月15日 – 3月21日 · 成人 2 人 · 预算约 ¥9,800
              </p>
              <div className="flex justify-center gap-3 mb-8">
                {["文化历史", "美食探索", "自然风光"].map(t => (
                  <span key={t} className="text-xs border border-gray-400 px-3 py-1 font-mono text-gray-600">{t}</span>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-4 gap-4 mb-8">
              {[["目的地","日本东京"],["出行天数","7 天"],["旅行人数","2 人"],["总预算","¥ 9,800"]].map(([k,v])=>(
                <div key={k} className="border border-gray-200 p-4 text-center">
                  <p className="text-[10px] font-mono text-gray-400 mb-1 uppercase tracking-widest">{k}</p>
                  <p className="text-base font-bold text-gray-900">{v}</p>
                </div>
              ))}
            </div>
            <p className="text-[10px] font-mono text-gray-400 uppercase tracking-widest mb-3">每日概要</p>
            {allDays.map((d, i) => (
              <div key={d.day} className="flex items-center gap-4 py-2.5 border-b border-gray-100">
                <span className="text-xs font-mono font-bold text-gray-700 w-12 shrink-0">{d.day}</span>
                <span className="text-xs font-mono text-gray-400 w-16 shrink-0">{d.date}</span>
                <span className="text-sm text-gray-800 flex-1">{d.title}</span>
                <span className="text-sm">{d.weather.icon}</span>
                <span className="text-xs font-mono text-gray-500">¥ {Object.values(d.budget).reduce((a,b)=>a+b,0)}</span>
              </div>
            ))}
          </PrintPage>
        )}

        {/* 日程页 */}
        {activeDay >= 0 && activeDay < allDays.length && (
          <OutputDayPage data={allDays[activeDay]} pageNum={activeDay + 2} total={allDays.length + 2} />
        )}

        {/* 预算总表页 */}
        {activeDay === 99 && (
          <PrintPage pageNum={allDays.length + 2} total={allDays.length + 2}>
            <div className="text-center mb-8 pb-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900 mb-1">预算总表</h2>
              <p className="text-sm font-mono text-gray-500">东京 7 日深度文化之旅</p>
            </div>
            <table className="w-full font-mono border-collapse mb-8">
              <thead>
                <tr className="border-b-2 border-gray-900">
                  {["类别", "金额（¥）", "人均（¥）", "占比", "备注"].map(h => (
                    <th key={h} className="py-2 px-3 text-left text-xs text-gray-700 font-bold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  ["机票","3,200","1,600","33%","往返经济舱"],
                  ["住宿","2,800","1,400","29%","新宿商务酒店 7晚"],
                  ["餐饮","1,800","900","18%","含早餐 + 特色餐厅"],
                  ["景点门票","1,200","600","12%","含 teamLab"],
                  ["市内交通","800","400","8%","含地铁 7日通票"],
                ].map(([k,v,p2,pct,note], ri) => (
                  <tr key={k} className={ri % 2 === 0 ? "bg-gray-50" : "bg-white"}>
                    {[k,v,p2,pct,note].map((c, ci) => (
                      <td key={ci} className="py-2.5 px-3 text-sm text-gray-700 border-b border-gray-100">{c}</td>
                    ))}
                  </tr>
                ))}
                <tr className="border-t-2 border-gray-900">
                  <td className="py-3 px-3 text-sm font-bold text-gray-900">合计</td>
                  <td className="py-3 px-3 text-sm font-bold text-gray-900">¥ 9,800</td>
                  <td className="py-3 px-3 text-sm font-bold text-gray-900">¥ 4,900</td>
                  <td className="py-3 px-3 text-sm text-gray-500">100%</td>
                  <td className="py-3 px-3 text-sm text-gray-400">—</td>
                </tr>
              </tbody>
            </table>
            <p className="text-center text-[10px] font-mono text-gray-400">
              以上费用仅供参考，实际价格以当地为准 · 汇率以出行日期为准
            </p>
          </PrintPage>
        )}
      </div>
    </div>
  );
}

// ─── Page 7: 我的行程 ──────────────────────────────────────────────────────

function EmptyTrips({ onOpen }: { onOpen: () => void }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 px-6">
      {/* 插图占位 */}
      <div className="w-64 h-44 bg-white border border-gray-200 flex flex-col items-center justify-center gap-3 mb-8 relative overflow-hidden">
        {/* 装饰性线条模拟地图感 */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-6 left-8 right-8 h-px bg-gray-600" />
          <div className="absolute top-12 left-12 right-12 h-px bg-gray-600" />
          <div className="absolute top-18 left-6 right-20 h-px bg-gray-600" />
          <div className="absolute bottom-10 left-10 right-6 h-px bg-gray-600" />
          <div className="absolute bottom-6 left-16 right-10 h-px bg-gray-600" />
          <div className="absolute top-4 bottom-4 left-10 w-px bg-gray-600" />
          <div className="absolute top-8 bottom-8 right-16 w-px bg-gray-600" />
          {/* 地图图钉 */}
          <div className="absolute top-8 left-16 w-3 h-3 border-2 border-gray-700 rounded-full bg-white" />
          <div className="absolute top-16 right-14 w-3 h-3 border-2 border-gray-700 rounded-full bg-white" />
          <div className="absolute bottom-12 left-20 w-3 h-3 border-2 border-gray-700 rounded-full bg-white" />
        </div>
        {/* 主图标 */}
        <div className="w-14 h-14 border-2 border-dashed border-gray-400 flex items-center justify-center bg-gray-50 z-10">
          <span className="text-2xl">✈</span>
        </div>
        <span className="text-xs font-mono text-gray-400 z-10">插图占位</span>
      </div>

      {/* 文案 */}
      <h2 className="text-xl font-bold text-gray-900 mb-2 text-center">还没有行程，出发规划吧</h2>
      <p className="text-sm text-gray-500 font-mono text-center max-w-xs leading-relaxed mb-8">
        告诉 AI 你想去哪、几天、和谁去，<br />几秒内生成专属行程方案
      </p>

      {/* 主 CTA */}
      <button
        onClick={onOpen}
        className="bg-gray-900 text-white text-sm font-semibold px-8 py-3 cursor-pointer hover:bg-gray-700 transition-colors mb-4"
      >
        + 创建我的第一个行程
      </button>

      {/* 次要操作 */}
      <div className="flex items-center gap-4 text-xs font-mono text-gray-400">
        <button className="hover:text-gray-700 cursor-pointer transition-colors underline underline-offset-2">
          浏览热门行程模板
        </button>
        <span>·</span>
        <button className="hover:text-gray-700 cursor-pointer transition-colors underline underline-offset-2">
          导入已有行程
        </button>
      </div>

      {/* 功能亮点提示 */}
      <div className="mt-12 grid grid-cols-3 gap-6 max-w-lg">
        {[
          { icon: "◈", title: "个性化偏好", desc: "根据兴趣、节奏、预算智能推荐" },
          { icon: "▦", title: "可视化编辑", desc: "拖拽调整景点，实时预览路线" },
          { icon: "⬡", title: "一键导出", desc: "PDF、日历、分享链接多格式输出" },
        ].map((f) => (
          <div key={f.title} className="text-center">
            <div className="w-8 h-8 border border-gray-300 flex items-center justify-center mx-auto mb-2 text-gray-500">
              {f.icon}
            </div>
            <p className="text-xs font-semibold text-gray-700 mb-1">{f.title}</p>
            <p className="text-[11px] font-mono text-gray-400 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function PageMyTrips({ onOpen, onEdit }: { onOpen: () => void; onEdit: () => void }) {
  const [isEmpty, setIsEmpty] = useState(false);

  const statusColors: Record<string, string> = {
    "计划中": "border-gray-700 text-gray-700",
    "草稿": "border-gray-400 text-gray-400",
    "已完成": "border-gray-500 bg-gray-100 text-gray-600",
  };

  if (isEmpty) {
    return (
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 顶栏保留，含切换开关 */}
        <div className="border-b border-gray-300 bg-white px-6 py-3 flex items-center justify-between shrink-0">
          <h1 className="text-sm font-semibold text-gray-800">我的行程</h1>
          <button
            onClick={() => setIsEmpty(false)}
            className="text-[11px] font-mono text-gray-400 border border-dashed border-gray-300 px-3 py-1 cursor-pointer hover:border-gray-500 hover:text-gray-600 transition-colors"
          >
            预览：有行程状态 →
          </button>
        </div>
        <EmptyTrips onOpen={onOpen} />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto bg-gray-50">
      <div className="max-w-5xl mx-auto py-8 px-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <WAnnotation text="我的行程页" />
            <h1 className="text-xl font-bold text-gray-900">我的行程</h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsEmpty(true)}
              className="text-[11px] font-mono text-gray-400 border border-dashed border-gray-300 px-3 py-1 cursor-pointer hover:border-gray-500 hover:text-gray-600 transition-colors"
            >
              ← 预览：空状态
            </button>
            <WBtn label="+ 创建新行程" primary onClick={onOpen} />
          </div>
        </div>

        {/* Filter / sort bar */}
        <div className="flex items-center gap-3 mb-5">
          <div className="flex gap-1">
            {["全部", "计划中", "草稿", "已完成"].map((f) => (
              <button
                key={f}
                className={`text-xs font-mono px-3 py-1.5 border cursor-pointer ${
                  f === "全部" ? "bg-gray-900 text-white border-gray-900" : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
          <div className="flex-1" />
          <WAnnotation text="排序：" />
          <div className="border border-gray-300 bg-white px-3 py-1.5 flex items-center gap-2">
            <span className="text-xs font-mono text-gray-600">最近修改</span>
            <span className="text-xs font-mono text-gray-400">▾</span>
          </div>
          <div className="border border-gray-300 bg-white px-2 py-1.5 flex items-center gap-1.5">
            <span className="text-xs font-mono text-gray-500">🔍</span>
            <span className="text-xs font-mono text-gray-400">搜索行程</span>
          </div>
        </div>

        {/* Trip cards grid */}
        <div className="grid grid-cols-3 gap-4">
          {trips.map((t) => (
            <WBox
              key={t.name}
              className="cursor-pointer hover:border-gray-500 transition-colors"
              onClick={onOpen}
            >
              <WImgBox className="w-full h-32" label={`封面 · ${t.dest}`} />
              <div className="p-3">
                <div className="flex items-start justify-between gap-1 mb-1">
                  <p className="text-sm font-semibold text-gray-800 leading-tight">{t.name}</p>
                  <span className={`text-[10px] font-mono border px-1.5 py-0.5 shrink-0 ${statusColors[t.status]}`}>
                    {t.status}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[10px] font-mono text-gray-500 mb-2">
                  <span>📍 {t.dest}</span>
                  <span>📅 {t.days}天</span>
                </div>
                <p className="text-[10px] font-mono text-gray-400 mb-3">{t.date}</p>
                <Divider className="mb-2" />
                <div className="flex gap-1.5">
                  <WBtn label="继续编辑" small className="flex-1 text-center" onClick={onEdit} />
                  <WBtn label="分享" small />
                  <WBtn label="···" small />
                </div>
              </div>
            </WBox>
          ))}

          {/* New trip card */}
          <div
            className="border border-dashed border-gray-400 bg-white flex flex-col items-center justify-center min-h-48 cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={onOpen}
          >
            <div className="w-10 h-10 border-2 border-dashed border-gray-400 flex items-center justify-center text-2xl text-gray-400 mb-2">+</div>
            <p className="text-sm font-medium text-gray-500">创建新行程</p>
            <p className="text-xs font-mono text-gray-400 mt-1">AI 帮你规划</p>
          </div>
        </div>

        {/* Stats bar */}
        <div className="mt-8 border border-gray-300 bg-white p-4 flex gap-8">
          {[
            ["行程总数", "6"],
            ["出行天数", "41 天"],
            ["到访国家", "5 个"],
            ["规划景点", "128 个"],
          ].map(([k, v]) => (
            <div key={k}>
              <p className="text-[10px] font-mono text-gray-400 mb-0.5">{k}</p>
              <p className="text-lg font-bold text-gray-800">{v}</p>
            </div>
          ))}
          <WAnnotation text="  ← 旅行统计数据" />
        </div>
      </div>
    </div>
  );
}

// ─── App Shell ──────────────────────────────────────────────────────────────

export default function App() {
  const [page, setPage] = useState<"mytrips" | "workspace" | "output">("mytrips");
  const [showAttractionModal, setShowAttractionModal] = useState(false);
  const [showWizard, setShowWizard] = useState(false);

  const navigate = (id: string) => {
    if (id === "mytrips" || id === "workspace" || id === "output") {
      setPage(id);
      setShowWizard(false);
      setShowAttractionModal(false);
    }
  };

  const openWizard = () => setShowWizard(true);
  const closeWizard = () => setShowWizard(false);
  const finishWizard = () => {
    setShowWizard(false);
    setPage("workspace");
  };

  return (
    <div
      className="flex flex-col h-screen bg-gray-50 relative overflow-hidden"
      style={{ fontFamily: "'Inter', sans-serif" }}
    >
      {/* Wireframe label strip */}
      <div className="bg-gray-900 text-white text-[10px] font-mono text-center py-1 tracking-widest shrink-0">
        LOW-FIDELITY WIREFRAME · AI 旅行规划应用 · 仅用于产品设计评审
      </div>

      <TopNav />

      {/* Body: sidebar + page content */}
      <div className="flex-1 flex overflow-hidden relative">
        <LeftSidebar current={page} onNavigate={navigate} onCreateTrip={openWizard} />

        <div className="flex-1 flex overflow-hidden relative">
          {page === "mytrips" && (
            <PageMyTrips onOpen={openWizard} onEdit={() => navigate("workspace")} />
          )}
          {page === "workspace" && (
            <PageWorkspace
              onOpenModal={() => setShowAttractionModal(true)}
              onOutput={() => navigate("output")}
            />
          )}
          {page === "output" && <PageOutput onBack={() => navigate("workspace")} />}

          {showAttractionModal && (
            <ModalAttraction onClose={() => setShowAttractionModal(false)} />
          )}

          {/* Wizard overlay: mounts on top of everything inside this pane */}
          {showWizard && (
            <WizardOverlay onClose={closeWizard} onDone={finishWizard} />
          )}
        </div>
      </div>
    </div>
  );
}
