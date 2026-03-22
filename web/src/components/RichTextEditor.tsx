import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import BulletList from '@tiptap/extension-bullet-list';
import ListItem from '@tiptap/extension-list-item';
import { useState, useCallback, useEffect } from 'react';
import { color, font, space, radius } from '../tokens';

/* ── Types ──────────────────────────────────────── */

interface RichTextEditorProps {
  initialContent: string;
  onChange: (html: string) => void;
  placeholder?: string;
  minHeight?: number;
}

/* ── Link Popover ───────────────────────────────── */

function LinkPopover({
  onSubmit,
  onCancel,
  initialUrl,
  initialText,
}: {
  onSubmit: (url: string, text: string) => void;
  onCancel: () => void;
  initialUrl?: string;
  initialText?: string;
}) {
  const [url, setUrl] = useState(initialUrl || '');
  const [text, setText] = useState(initialText || '');

  return (
    <div style={popoverStyles.overlay} onClick={onCancel}>
      <div style={popoverStyles.box} onClick={(e) => e.stopPropagation()}>
        <div style={popoverStyles.title}>Insert Link</div>
        <label style={popoverStyles.label}>
          Display text
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Link text"
            style={popoverStyles.input}
            autoFocus
          />
        </label>
        <label style={popoverStyles.label}>
          URL
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            style={popoverStyles.input}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                if (url.trim()) onSubmit(url.trim(), text.trim() || url.trim());
              }
            }}
          />
        </label>
        <div style={popoverStyles.actions}>
          <button style={popoverStyles.cancelBtn} onClick={onCancel}>Cancel</button>
          <button
            style={{
              ...popoverStyles.insertBtn,
              opacity: url.trim() ? 1 : 0.5,
            }}
            onClick={() => {
              if (url.trim()) onSubmit(url.trim(), text.trim() || url.trim());
            }}
            disabled={!url.trim()}
          >
            Insert
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Toolbar ────────────────────────────────────── */

function Toolbar({ editor }: { editor: ReturnType<typeof useEditor> }) {
  const [showLinkPopover, setShowLinkPopover] = useState(false);

  if (!editor) return null;

  const handleLinkInsert = (url: string, text: string) => {
    let href = url;
    if (!/^https?:\/\//i.test(href)) {
      href = 'https://' + href;
    }

    const { from, to } = editor.state.selection;
    const hasSelection = from !== to;

    if (hasSelection) {
      editor.chain().focus().setLink({ href }).run();
    } else {
      editor
        .chain()
        .focus()
        .insertContent(`<a href="${href}">${text}</a>`)
        .run();
    }
    setShowLinkPopover(false);
  };

  const selectedText = (() => {
    const { from, to } = editor.state.selection;
    return editor.state.doc.textBetween(from, to, ' ');
  })();

  return (
    <div style={toolbarStyles.bar}>
      <button
        type="button"
        style={{
          ...toolbarStyles.btn,
          ...(editor.isActive('bold') ? toolbarStyles.btnActive : {}),
        }}
        onClick={() => editor.chain().focus().toggleBold().run()}
        title="Bold (Ctrl+B)"
      >
        <strong>B</strong>
      </button>
      <button
        type="button"
        style={{
          ...toolbarStyles.btn,
          ...(editor.isActive('italic') ? toolbarStyles.btnActive : {}),
        }}
        onClick={() => editor.chain().focus().toggleItalic().run()}
        title="Italic (Ctrl+I)"
      >
        <em>I</em>
      </button>
      <button
        type="button"
        style={{
          ...toolbarStyles.btn,
          ...(editor.isActive('bulletList') ? toolbarStyles.btnActive : {}),
        }}
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        title="Bullet list"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="8" y1="6" x2="21" y2="6" />
          <line x1="8" y1="12" x2="21" y2="12" />
          <line x1="8" y1="18" x2="21" y2="18" />
          <circle cx="3" cy="6" r="1.5" fill="currentColor" />
          <circle cx="3" cy="12" r="1.5" fill="currentColor" />
          <circle cx="3" cy="18" r="1.5" fill="currentColor" />
        </svg>
      </button>
      <button
        type="button"
        style={{
          ...toolbarStyles.btn,
          ...(editor.isActive('link') ? toolbarStyles.btnActive : {}),
        }}
        onClick={() => {
          if (editor.isActive('link')) {
            editor.chain().focus().unsetLink().run();
          } else {
            setShowLinkPopover(true);
          }
        }}
        title="Insert link"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
        </svg>
      </button>

      {showLinkPopover && (
        <LinkPopover
          onSubmit={handleLinkInsert}
          onCancel={() => setShowLinkPopover(false)}
          initialText={selectedText}
        />
      )}
    </div>
  );
}

/* ── Main Component ─────────────────────────────── */

export function RichTextEditor({ initialContent, onChange, placeholder, minHeight = 160 }: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        // Disable extensions we don't want
        heading: false,
        codeBlock: false,
        code: false,
        blockquote: false,
        horizontalRule: false,
        orderedList: false,
        bulletList: false,
        listItem: false,
      }),
      BulletList,
      ListItem,
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          style: `color: #076EFF; text-decoration: underline;`,
          target: '_blank',
          rel: 'noopener noreferrer',
        },
      }),
    ],
    content: initialContent || '',
    onUpdate: ({ editor: e }) => {
      onChange(e.getHTML());
    },
    editorProps: {
      attributes: {
        style: [
          `min-height: ${minHeight}px`,
          `padding: ${space.sm}`,
          `font-family: ${font.family}`,
          `font-size: ${font.sizeSm}`,
          `line-height: 1.7`,
          `color: ${color.text}`,
          'outline: none',
        ].join('; '),
        ...(placeholder ? { 'data-placeholder': placeholder } : {}),
      },
    },
  });

  // Sync external content changes (e.g., from AI refinement)
  useEffect(() => {
    if (editor && initialContent !== undefined) {
      const currentHTML = editor.getHTML();
      // Only update if content actually changed from outside
      if (currentHTML !== initialContent && !editor.isFocused) {
        editor.commands.setContent(initialContent || '');
      }
    }
  }, [initialContent, editor]);

  const handleWrapperClick = useCallback(() => {
    editor?.chain().focus().run();
  }, [editor]);

  return (
    <div
      style={editorStyles.wrapper}
      onClick={handleWrapperClick}
    >
      <Toolbar editor={editor} />
      <EditorContent editor={editor} />
      <style>{tiptapCSS}</style>
    </div>
  );
}

/* ── HTML Renderer (read mode) ──────────────────── */

export function RichTextDisplay({ html }: { html: string }) {
  // Sanitize HTML to prevent XSS
  const sanitize = useCallback((dirty: string) => {
    // Lightweight sanitization: only allow safe tags
    const div = document.createElement('div');
    div.innerHTML = dirty;
    // Remove script tags and event handlers
    div.querySelectorAll('script').forEach((el) => el.remove());
    div.querySelectorAll('*').forEach((el) => {
      const attrs = el.attributes;
      for (let i = attrs.length - 1; i >= 0; i--) {
        const name = attrs[i].name;
        if (name.startsWith('on') || (name === 'href' && attrs[i].value.startsWith('javascript:'))) {
          el.removeAttribute(name);
        }
      }
    });
    return div.innerHTML;
  }, []);

  if (!html || html === '<p></p>') {
    return null;
  }

  // Check if content is plain text (no HTML tags)
  const isPlainText = !/<[a-z][\s\S]*>/i.test(html);
  if (isPlainText) {
    return (
      <>
        {html.split('\n\n').map((para, i) => (
          <p key={i} style={displayStyles.paragraph}>{para}</p>
        ))}
      </>
    );
  }

  return (
    <div
      className="rich-text-display"
      style={displayStyles.content}
      dangerouslySetInnerHTML={{ __html: sanitize(html) }}
    />
  );
}

/* ── Styles ─────────────────────────────────────── */

const tiptapCSS = `
  .tiptap p {
    margin: 0 0 0.5em 0;
  }
  .tiptap p:last-child {
    margin-bottom: 0;
  }
  .tiptap ul {
    padding-left: 1.5em;
    margin: 0.5em 0;
  }
  .tiptap li {
    margin-bottom: 0.25em;
  }
  .tiptap li p {
    margin: 0;
  }
  .tiptap a {
    color: #076EFF;
    text-decoration: underline;
  }
  .tiptap:focus {
    outline: none;
  }
  .tiptap p.is-editor-empty:first-child::before {
    content: attr(data-placeholder);
    float: left;
    color: ${color.textDim};
    pointer-events: none;
    height: 0;
    font-style: italic;
  }
`;

const editorStyles: Record<string, React.CSSProperties> = {
  wrapper: {
    width: '100%',
    borderRadius: radius.md,
    border: `1px solid ${color.border}`,
    backgroundColor: '#fff',
    boxSizing: 'border-box',
    cursor: 'text',
    overflow: 'hidden',
  },
};

const toolbarStyles: Record<string, React.CSSProperties> = {
  bar: {
    display: 'flex',
    gap: '2px',
    padding: `${space.xxs} ${space.xs}`,
    backgroundColor: '#F7FAFC',
    borderBottom: `1px solid ${color.border}`,
    position: 'relative',
  },
  btn: {
    width: 28,
    height: 28,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: 'none',
    background: 'none',
    borderRadius: radius.sm,
    cursor: 'pointer',
    color: color.textMuted,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    padding: 0,
  } as React.CSSProperties,
  btnActive: {
    backgroundColor: '#E2E8F0',
    color: color.text,
  },
};

const popoverStyles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.15)',
    zIndex: 9999,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  box: {
    backgroundColor: '#fff',
    borderRadius: radius.lg,
    padding: space.lg,
    width: 340,
    boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
    fontFamily: font.family,
  },
  title: {
    fontSize: font.sizeMd,
    fontWeight: font.weightSemibold,
    color: color.text,
    marginBottom: space.md,
  },
  label: {
    display: 'block',
    fontSize: font.sizeXs,
    color: color.textMuted,
    marginBottom: space.sm,
    fontWeight: font.weightMedium,
  },
  input: {
    display: 'block',
    width: '100%',
    padding: `${space.xs} ${space.sm}`,
    borderRadius: radius.md,
    border: `1px solid ${color.border}`,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    marginTop: space.xxs,
    boxSizing: 'border-box' as const,
    outline: 'none',
  },
  actions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: space.xs,
    marginTop: space.md,
  },
  cancelBtn: {
    padding: `${space.xxs} ${space.md}`,
    borderRadius: 999,
    border: `1px solid ${color.border}`,
    background: 'none',
    color: color.textMuted,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    cursor: 'pointer',
  } as React.CSSProperties,
  insertBtn: {
    padding: `${space.xxs} ${space.md}`,
    borderRadius: 999,
    border: 'none',
    background: color.accent,
    color: '#fff',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    cursor: 'pointer',
  } as React.CSSProperties,
};

const displayStyles: Record<string, React.CSSProperties> = {
  content: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    lineHeight: 1.7,
    color: color.text,
  },
  paragraph: {
    margin: `0 0 ${space.sm} 0`,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    lineHeight: 1.7,
    color: color.text,
  },
};
