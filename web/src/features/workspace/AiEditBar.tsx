import { useEffect, useRef, useState } from "react";
import { chatEditTrip, getUndoState, undoTripEdit } from "../../api/trips";
import type { Itinerary } from "../../types/itinerary";

/** 一条对话记录。system 用于「已撤销」这类由前端自己产生的提示。 */
type Message = {
  id: number;
  role: "user" | "assistant" | "system";
  text: string;
  /** 后端依据实际执行成功的操作生成的回执。模型的话在 text 里，两者分开显示。 */
  changes?: string[];
  failed?: boolean;
};

const EXAMPLES = ["第二天太赶了，删掉一个景点", "第一天下午加个婺源博物馆", "把午饭改成 90 分钟"];

export function AiEditBar({
  tripId,
  onItineraryChange,
  onHighlight,
}: {
  tripId: string;
  onItineraryChange: (itinerary: Itinerary) => void;
  onHighlight: (itemIds: string[]) => void;
}) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [undoRemaining, setUndoRemaining] = useState(0);
  const streamRef = useRef<HTMLDivElement>(null);
  const nextId = useRef(0);

  // 撤销按钮的初始状态要在页面加载时就正确——用户可能上次会话改过东西
  useEffect(() => {
    let ignore = false;
    getUndoState(tripId)
      .then((state) => !ignore && setUndoRemaining(state.remaining))
      .catch(() => undefined);
    return () => {
      ignore = true;
    };
  }, [tripId]);

  useEffect(() => {
    streamRef.current?.scrollTo({ top: streamRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const push = (message: Omit<Message, "id">) => {
    nextId.current += 1;
    setMessages((current) => [...current, { ...message, id: nextId.current }]);
  };

  const send = async (text: string) => {
    const message = text.trim();
    if (!message || isSending) return;

    setInput("");
    push({ role: "user", text: message });
    setIsSending(true);

    try {
      const result = await chatEditTrip(tripId, message);
      push({ role: "assistant", text: result.reply, changes: result.changes });
      setUndoRemaining(result.undoRemaining);

      // 后端只在真的改了东西时才返回行程；模型只是澄清或答复时 itinerary 为 null
      if (result.itinerary) {
        onItineraryChange(result.itinerary);
        onHighlight(result.changedItemIds);
      }
    } catch (error) {
      // 后端把「查不到这个地方」「没找到那个条目」这类原因放在 detail 里，
      // 原样显示——用户需要知道为什么没改成，而不是一句「失败了」
      push({ role: "assistant", text: error instanceof Error ? error.message : "改动失败", failed: true });
    } finally {
      setIsSending(false);
    }
  };

  const undo = async () => {
    if (!undoRemaining || isSending) return;
    setIsSending(true);
    try {
      const result = await undoTripEdit(tripId);
      setUndoRemaining(result.remaining);
      if (result.itinerary) {
        onItineraryChange(result.itinerary);
        onHighlight([]);
      }
      push({ role: "system", text: "已撤销上一次改动" });
    } catch (error) {
      push({ role: "assistant", text: error instanceof Error ? error.message : "撤销失败", failed: true });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="shrink-0 border-t border-slate-200 bg-white/95 backdrop-blur">
      {messages.length > 0 && (
        <div ref={streamRef} className="max-h-44 space-y-2 overflow-auto px-4 pt-3">
          {messages.map((message) => (
            <MessageRow key={message.id} message={message} />
          ))}
          {isSending && <p className="text-[11px] text-slate-400">正在处理…</p>}
        </div>
      )}

      <div className="px-4 py-3">
        {messages.length === 0 && (
          <div className="mb-2 flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] text-slate-400">试试：</span>
            {EXAMPLES.map((example) => (
              <button
                key={example}
                onClick={() => void send(example)}
                disabled={isSending}
                className="rounded-full border border-slate-200 px-2.5 py-1 text-[10px] text-slate-500 transition-colors hover:border-sky-300 hover:text-sky-700 disabled:opacity-50"
              >
                {example}
              </button>
            ))}
          </div>
        )}

        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.nativeEvent.isComposing) void send(input);
            }}
            placeholder="用一句话修改行程，例如「第二天太赶了，删掉一个景点」"
            disabled={isSending}
            className="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-sky-400 disabled:bg-slate-50"
          />
          <button
            onClick={() => void send(input)}
            disabled={isSending || !input.trim()}
            className="shrink-0 rounded-lg bg-slate-900 px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-slate-700 disabled:opacity-40"
          >
            {isSending ? "处理中" : "发送"}
          </button>
          <button
            onClick={() => void undo()}
            disabled={!undoRemaining || isSending}
            title={undoRemaining ? `还能撤销 ${undoRemaining} 步` : "没有可撤销的改动"}
            className="shrink-0 rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-600 transition-colors hover:bg-slate-50 disabled:opacity-40"
          >
            ↩ 撤销{undoRemaining ? ` (${undoRemaining})` : ""}
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageRow({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <span className="max-w-[80%] rounded-lg bg-sky-600 px-2.5 py-1.5 text-[11px] text-white">{message.text}</span>
      </div>
    );
  }

  if (message.role === "system") {
    return <p className="text-center text-[10px] text-slate-400">{message.text}</p>;
  }

  return (
    <div className="max-w-[85%] space-y-1">
      {/* 回执与模型的话分开：回执是代码依据实际执行的操作生成的事实，
          模型的话只是补充说明——它描述的是它以为自己做了什么 */}
      {message.changes?.map((change) => (
        <p key={change} className="text-[11px] font-medium text-emerald-700">
          ✓ {change}
        </p>
      ))}
      {message.text && (
        <p className={`text-[11px] ${message.failed ? "text-red-600" : "text-slate-600"}`}>
          {message.failed ? "✕ " : ""}
          {message.text}
        </p>
      )}
    </div>
  );
}
