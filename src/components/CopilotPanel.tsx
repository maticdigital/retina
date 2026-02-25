import { useState, useRef, useEffect } from 'react';
import { color, font, space, radius } from '../tokens';

/* ── Types ────────────────────────────────────────── */

export interface CopilotMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface CopilotPanelProps {
  open: boolean;
  onClose: () => void;
  lensName: string;
  currentObservations: string;
  onCommit: (text: string) => void;
  /** Optional async send function — if omitted, hardcoded placeholder response is used */
  onSend?: (message: string, history: CopilotMessage[]) => Promise<string>;
}

/* ── Panel Component ─────────────────────────────── */

export function CopilotPanel({
  open,
  onClose,
  lensName,
  currentObservations,
  onCommit,
  onSend,
}: CopilotPanelProps) {
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [contextExpanded, setContextExpanded] = useState(false);
  const [committed, setCommitted] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Reset when panel opens
  useEffect(() => {
    if (open) {
      setMessages([]);
      setInput('');
      setCommitted(false);
      setContextExpanded(false);
    }
  }, [open]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMsg: CopilotMessage = { role: 'user', content: trimmed };
    const updatedHistory = [...messages, userMsg];
    setMessages(updatedHistory);
    setInput('');
    setLoading(true);

    try {
      let response: string;
      if (onSend) {
        response = await onSend(trimmed, updatedHistory);
      } else {
        // Hardcoded placeholder for UI testing
        await new Promise((r) => setTimeout(r, 800));
        response =
          `Based on the current observations for ${lensName}, here are some suggestions:\n\n` +
          `1. **Strengthen the opening** — Lead with specific evidence from the site rather than generic statements.\n\n` +
          `2. **Quantify gaps** — Where possible, reference specific elements (e.g., "the hero section lacks a clear CTA") rather than abstract assessments.\n\n` +
          `3. **Add competitive framing** — Position findings relative to what best-in-class sites in this vertical do.\n\n` +
          `This is a placeholder response. Wire the Claude API in Step 5 to get real AI-powered refinement.`;
      }
      setMessages((prev) => [...prev, { role: 'assistant', content: response }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' },
      ]);
    }
    setLoading(false);
  };

  const lastAiMessage = [...messages].reverse().find((m) => m.role === 'assistant');

  const handleCommit = () => {
    if (lastAiMessage) {
      onCommit(lastAiMessage.content);
      setCommitted(true);
      setTimeout(() => {
        onClose();
      }, 1200);
    }
  };

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          style={panelStyles.backdrop}
          onClick={onClose}
        />
      )}

      {/* Panel */}
      <div
        style={{
          ...panelStyles.panel,
          transform: open ? 'translateX(0)' : 'translateX(100%)',
        }}
      >
        {/* Header */}
        <div style={panelStyles.header}>
          <div style={{ display: 'flex', alignItems: 'center', gap: space.sm, flex: 1 }}>
            <span style={panelStyles.headerTitle}>Retina Copilot</span>
            <span style={panelStyles.lensBadge}>{lensName}</span>
          </div>
          <button style={panelStyles.closeBtn} onClick={onClose}>×</button>
        </div>

        {/* Context */}
        <div style={panelStyles.contextSection}>
          <button
            style={panelStyles.contextToggle}
            onClick={() => setContextExpanded(!contextExpanded)}
          >
            <span style={{ fontSize: font.sizeXs, color: color.textMuted }}>
              Current Observations Context
            </span>
            <span style={{ fontSize: font.sizeXs, color: color.textDim }}>
              {contextExpanded ? '▲' : '▼'}
            </span>
          </button>
          {contextExpanded && (
            <div style={panelStyles.contextBody}>
              {currentObservations || (
                <span style={{ color: color.textDim, fontStyle: 'italic' }}>No observations yet</span>
              )}
            </div>
          )}
        </div>

        {/* Chat Messages */}
        <div style={panelStyles.chatArea}>
          {messages.length === 0 && (
            <div style={panelStyles.emptyChat}>
              <p style={{ margin: 0, fontWeight: font.weightMedium, color: color.text }}>
                How can I help refine these observations?
              </p>
              <p style={{ margin: `${space.xs} 0 0`, fontSize: font.sizeXs, color: color.textMuted }}>
                Ask me to improve the tone, add specifics, reframe gaps as opportunities, or suggest new angles.
              </p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                ...panelStyles.messageBubble,
                ...(msg.role === 'user' ? panelStyles.userBubble : panelStyles.aiBubble),
              }}
            >
              {msg.content.split('\n').map((line, j) => (
                <p key={j} style={{ margin: j === 0 ? 0 : `${space.xs} 0 0` }}>{line}</p>
              ))}
            </div>
          ))}
          {loading && (
            <div style={{ ...panelStyles.messageBubble, ...panelStyles.aiBubble }}>
              <span style={{ color: color.textMuted }}>Thinking…</span>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Committed confirmation */}
        {committed && (
          <div style={panelStyles.commitConfirm}>
            ✓ Observations updated
          </div>
        )}

        {/* Input Area */}
        <div style={panelStyles.inputArea}>
          <div style={{ display: 'flex', gap: space.xs }}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask Retina Copilot…"
              style={panelStyles.inputField}
              rows={2}
            />
            <button
              style={{
                ...panelStyles.sendBtn,
                opacity: input.trim() && !loading ? 1 : 0.5,
              }}
              onClick={handleSend}
              disabled={!input.trim() || loading}
            >
              Send
            </button>
          </div>

          {/* Commit button — only after AI has responded */}
          {lastAiMessage && !committed && (
            <button style={panelStyles.commitBtn} onClick={handleCommit}>
              Commit to Observations
            </button>
          )}

          <button
            style={panelStyles.closeLink}
            onClick={onClose}
          >
            Close without saving
          </button>
        </div>
      </div>
    </>
  );
}

/* ── Styles ─────────────────────────────────────── */

const panelStyles: Record<string, React.CSSProperties> = {
  backdrop: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.2)',
    zIndex: 999,
  },
  panel: {
    position: 'fixed',
    top: 0,
    right: 0,
    width: 420,
    height: '100vh',
    backgroundColor: color.bgCard,
    boxShadow: '-4px 0 24px rgba(0,0,0,0.12)',
    zIndex: 1000,
    display: 'flex',
    flexDirection: 'column',
    transition: 'transform 0.25s ease',
    fontFamily: font.family,
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: `${space.md} ${space.lg}`,
    borderBottom: `1px solid ${color.border}`,
    flexShrink: 0,
  },
  headerTitle: {
    fontWeight: font.weightBold,
    fontSize: font.sizeLg,
    color: color.text,
  },
  lensBadge: {
    padding: `2px ${space.sm}`,
    borderRadius: radius.pill,
    backgroundColor: color.accentLight,
    color: color.accent,
    fontSize: font.sizeXs,
    fontWeight: font.weightMedium,
  },
  closeBtn: {
    width: 32,
    height: 32,
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    fontSize: '1.25rem',
    color: color.textMuted,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.md,
    flexShrink: 0,
  } as React.CSSProperties,
  contextSection: {
    borderBottom: `1px solid ${color.border}`,
    flexShrink: 0,
  },
  contextToggle: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    padding: `${space.sm} ${space.lg}`,
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    fontFamily: font.family,
  } as React.CSSProperties,
  contextBody: {
    padding: `0 ${space.lg} ${space.sm}`,
    fontSize: font.sizeXs,
    color: color.textMuted,
    lineHeight: 1.5,
    maxHeight: 120,
    overflow: 'auto',
    whiteSpace: 'pre-wrap' as const,
  },
  chatArea: {
    flex: 1,
    overflow: 'auto',
    padding: space.lg,
    display: 'flex',
    flexDirection: 'column',
    gap: space.sm,
  },
  emptyChat: {
    textAlign: 'center',
    padding: `${space.xxl} ${space.lg}`,
    color: color.textMuted,
    fontSize: font.sizeSm,
  },
  messageBubble: {
    padding: `${space.sm} ${space.md}`,
    borderRadius: radius.lg,
    fontSize: font.sizeSm,
    lineHeight: 1.6,
    maxWidth: '85%',
    wordWrap: 'break-word' as const,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: color.accent,
    color: '#fff',
  },
  aiBubble: {
    alignSelf: 'flex-start',
    backgroundColor: color.bgPage,
    color: color.text,
  },
  inputArea: {
    padding: space.lg,
    borderTop: `1px solid ${color.border}`,
    flexShrink: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: space.sm,
  },
  inputField: {
    flex: 1,
    padding: space.sm,
    borderRadius: radius.md,
    border: `1px solid ${color.border}`,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    resize: 'none' as const,
    outline: 'none',
    lineHeight: 1.5,
  },
  sendBtn: {
    padding: `${space.sm} ${space.md}`,
    borderRadius: radius.md,
    border: 'none',
    backgroundColor: color.accent,
    color: '#fff',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    cursor: 'pointer',
    flexShrink: 0,
    alignSelf: 'flex-end',
  } as React.CSSProperties,
  commitBtn: {
    width: '100%',
    padding: `${space.sm} ${space.md}`,
    borderRadius: radius.pill,
    border: 'none',
    backgroundColor: color.accent,
    color: '#fff',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightSemibold,
    cursor: 'pointer',
  } as React.CSSProperties,
  commitConfirm: {
    textAlign: 'center',
    padding: space.sm,
    backgroundColor: '#F0FDF4',
    color: '#16A34A',
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    fontFamily: font.family,
  },
  closeLink: {
    background: 'none',
    border: 'none',
    color: color.textMuted,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    cursor: 'pointer',
    textDecoration: 'underline',
    padding: 0,
    textAlign: 'center',
  } as React.CSSProperties,
};
