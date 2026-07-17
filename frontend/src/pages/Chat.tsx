import { useEffect, useRef, useState } from "react";
import { Bot, Send, User, Sparkles } from "lucide-react";
import { api } from "../api";
import { PageHeader } from "../components/ui";

interface ChatMessage {
  role: "user" | "assistant" | "error";
  content: string;
}

const EXAMPLES = [
  "What's the current clearance rate and total case count?",
  "Which districts are predicted high-risk next week?",
  "Are there any emerging crime trend alerts right now?",
  "Who are the top repeat offenders?",
];

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const threadId = useRef<string | undefined>(undefined);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const send = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setMessages((m) => [...m, { role: "user", content: trimmed }]);
    setInput("");
    setBusy(true);
    api
      .chat(trimmed, threadId.current)
      .then((r) => {
        threadId.current = r.thread_id;
        setMessages((m) => [...m, { role: "assistant", content: r.response }]);
      })
      .catch((e) => {
        const detail = e?.response?.data?.detail ?? "The chatbot is unavailable right now.";
        setMessages((m) => [...m, { role: "error", content: detail }]);
      })
      .finally(() => setBusy(false));
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-[1000px] mx-auto flex flex-col h-full">
      <PageHeader title="Astra Assistant" subtitle="Ask questions about crime stats, risk, hotspots, and offenders — in plain language" />

      <div className="card flex-1 flex flex-col min-h-0">
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center py-10">
              <div className="h-12 w-12 rounded-2xl bg-accent/15 border border-accent/30 flex items-center justify-center mb-3">
                <Bot className="h-6 w-6 text-accent" />
              </div>
              <p className="text-sm text-slate-400 max-w-sm">
                Ask about KPIs, hotspots, predictive risk, offender networks, or paste an FIR
                narrative to classify it.
              </p>
              <div className="flex flex-wrap gap-1.5 justify-center mt-4">
                {EXAMPLES.map((e) => (
                  <button
                    key={e}
                    onClick={() => send(e)}
                    className="text-[11px] px-2.5 py-1.5 rounded-lg bg-ink-700/60 border border-ink-600 text-slate-400 hover:text-white"
                  >
                    {e}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <ChatBubble key={i} message={m} />
          ))}

          {busy && (
            <div className="flex items-center gap-2 text-slate-500 text-xs pl-9">
              <div className="h-3.5 w-3.5 rounded-full border-2 border-ink-600 border-t-accent animate-spin" />
              thinking…
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="border-t border-ink-700 p-3 flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder="Ask Astra…"
            className="flex-1 bg-ink-800 border border-ink-600 rounded-xl p-3 text-sm text-slate-200 resize-none focus:outline-none focus:border-accent max-h-32"
          />
          <button
            onClick={() => send(input)}
            disabled={busy || !input.trim()}
            className="inline-flex items-center gap-2 px-4 py-3 rounded-xl bg-accent/15 border border-accent/40 text-accent text-sm font-medium hover:bg-accent/25 disabled:opacity-50 shrink-0"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isError = message.role === "error";

  return (
    <div className={`flex items-start gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`h-7 w-7 rounded-lg flex items-center justify-center shrink-0 ${
          isUser
            ? "bg-ink-700 text-slate-300"
            : isError
              ? "bg-accent-red/15 text-accent-red border border-accent-red/30"
              : "bg-accent/15 text-accent border border-accent/30"
        }`}
      >
        {isUser ? <User className="h-3.5 w-3.5" /> : isError ? <Sparkles className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
      </div>
      <div
        className={`max-w-[75%] rounded-xl px-3.5 py-2.5 text-sm whitespace-pre-wrap leading-relaxed ${
          isUser
            ? "bg-accent/15 text-slate-100"
            : isError
              ? "bg-accent-red/10 text-accent-red border border-accent-red/30"
              : "bg-ink-800 border border-ink-700 text-slate-200"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}
