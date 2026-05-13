import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { Send, Trash2 } from "lucide-react";
import api from "../lib/api";

function formatTime(iso) {
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function CommentsThread({ cpId, user }) {
  const [comments, setComments] = useState([]);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);

  const load = async () => {
    try {
      const { data } = await api.get(`/client/comments?cp_id=${cpId}`);
      setComments(data);
    } catch {
      // silent
    }
  };

  useEffect(() => {
    if (cpId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cpId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [comments]);

  const submit = async (e) => {
    e.preventDefault();
    const text = body.trim();
    if (!text) return;
    setBusy(true);
    try {
      const { data } = await api.post("/client/comments", { cp_id: cpId, body: text });
      setComments((prev) => [...prev, data]);
      setBody("");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not post comment.");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Delete this comment?")) return;
    try {
      await api.delete(`/client/comments/${id}`);
      setComments((prev) => prev.filter((c) => c.comment_id !== id));
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not delete.");
    }
  };

  const isMine = (c) => c.author_user_id === user?.user_id;
  const canDelete = (c) => user?.role === "admin" || isMine(c);

  return (
    <div className="border-t border-border bg-muted/40" data-testid={`comments-${cpId}`}>
      <div className="p-5 border-b border-border">
        <div className="overline text-muted-foreground">Conversation · {comments.length}</div>
      </div>
      <div ref={scrollRef} className="max-h-[420px] overflow-y-auto px-5 py-6 space-y-5">
        {comments.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-8">
            No messages yet. Start the conversation below.
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {comments.map((c) => (
              <motion.div
                key={c.comment_id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`flex ${isMine(c) ? "justify-end" : "justify-start"}`}
                data-testid={`comment-${c.comment_id}`}
              >
                <div className={`max-w-[80%] ${isMine(c) ? "items-end" : "items-start"} flex flex-col`}>
                  <div className="flex items-baseline gap-2 mb-1">
                    <span className={`text-xs font-bold uppercase tracking-[0.15em] ${c.author_role === "admin" ? "text-primary" : "text-foreground"}`}>
                      {c.author_name}
                    </span>
                    <span className="text-[10px] text-muted-foreground">{formatTime(c.created_at)}</span>
                  </div>
                  <div className={`px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap border ${isMine(c) ? "bg-foreground text-background border-foreground" : "bg-card border-border"}`}>
                    {c.body}
                  </div>
                  {canDelete(c) && (
                    <button
                      onClick={() => remove(c.comment_id)}
                      className="text-[10px] uppercase tracking-widest text-muted-foreground hover:text-destructive mt-1 inline-flex items-center gap-1"
                      data-testid={`delete-comment-${c.comment_id}`}
                    >
                      <Trash2 size={10} /> Delete
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>
      <form onSubmit={submit} className="border-t border-border p-4 flex gap-3 items-end" data-testid={`comment-form-${cpId}`}>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={2}
          placeholder={user?.role === "admin" ? "Reply to the client…" : "Ask a question or share an update…"}
          className="flex-1 bg-transparent border-b border-foreground/30 px-0 py-2 outline-none focus:border-foreground placeholder:text-foreground/40 text-sm resize-none"
          data-testid={`comment-input-${cpId}`}
        />
        <button type="submit" disabled={busy || !body.trim()} className="btn-primary disabled:opacity-40" data-testid={`comment-submit-${cpId}`}>
          <Send size={14} /> Send
        </button>
      </form>
    </div>
  );
}
