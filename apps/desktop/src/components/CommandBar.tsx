import { useState, useRef } from "react";
import type { FormEvent, ClipboardEvent, DragEvent, ChangeEvent } from "react";
import type { Attachment } from "@/state/types";
import "./command-bar.css";

interface CommandBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (text: string, attachments?: Attachment[]) => void;
  micActive: boolean;
  cameraActive: boolean;
  onToggleMic: () => void;
  onToggleCamera: () => void;
  activeMode?: string;
  disabled?: boolean;
}

export function CommandBar({
  value,
  onChange,
  onSubmit,
  micActive,
  cameraActive,
  onToggleMic,
  onToggleCamera,
  activeMode,
  disabled,
}: CommandBarProps) {
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    const reader = new FileReader();
    const isText = file.type.startsWith("text/") || file.name.endsWith(".md") || file.name.endsWith(".txt");
    
    if (isText) {
      reader.onload = (e) => {
        if (typeof e.target?.result === "string") {
          const newAtt: Attachment = {
            id: `att_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
            mime_type: file.type || "text/plain",
            storage: "inline",
            name: file.name,
            content: e.target.result,
            size_bytes: file.size,
          };
          setAttachments((prev) => [...prev, newAtt]);
        }
      };
      reader.readAsText(file);
    } else {
      reader.onload = (e) => {
        if (typeof e.target?.result === "string") {
          const base64Data = e.target.result.includes(",") ? e.target.result.split(",")[1] : e.target.result;
          const newAtt: Attachment = {
            id: `att_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
            mime_type: file.type || "image/png",
            storage: "inline",
            name: file.name,
            data_b64: base64Data,
            size_bytes: file.size,
            metadata: { dataUrl: e.target.result },
          };
          setAttachments((prev) => [...prev, newAtt]);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLDivElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf("image") !== -1) {
        const file = items[i].getAsFile();
        if (file) {
          handleFile(file);
          break;
        }
      }
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      for (let i = 0; i < files.length; i++) {
        handleFile(files[i]);
      }
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      for (let i = 0; i < files.length; i++) {
        handleFile(files[i]);
      }
    }
  };

  const handleRemoveAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed && attachments.length === 0) return;
    onSubmit(trimmed, attachments.length > 0 ? attachments : undefined);
    setAttachments([]);
  };

  return (
    <div
      className="command-bar-wrapper"
      onPaste={handlePaste}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      {attachments.length > 0 && (
        <div className="command-bar__image-preview">
          {attachments.map((att) => (
            <div key={att.id} style={{ display: "inline-flex", alignItems: "center", position: "relative", marginRight: "8px" }}>
              {att.metadata?.dataUrl ? (
                <img src={att.metadata.dataUrl} alt={att.name || "Attachment"} />
              ) : (
                <span style={{ fontSize: "12px", background: "rgba(255,255,255,0.1)", padding: "4px 8px", borderRadius: "4px" }}>
                  📄 {att.name || att.mime_type}
                </span>
              )}
              <button
                type="button"
                className="command-bar__image-remove"
                onClick={() => handleRemoveAttachment(att.id)}
                title="Remove attachment"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      <form className="command-bar" onSubmit={handleSubmit}>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileInputChange}
          multiple
          style={{ display: "none" }}
        />

        <button
          type="button"
          className="command-bar__icon-btn"
          onClick={() => fileInputRef.current?.click()}
          aria-label="Attach file"
          title="Attach files or images"
        >
          <PaperclipIcon />
        </button>

        <button
          type="button"
          className={`command-bar__icon-btn${micActive ? " command-bar__icon-btn--active" : ""}`}
          onClick={onToggleMic}
          aria-pressed={micActive}
          aria-label="Toggle microphone"
          title="Microphone (Phase 4 Voice)"
        >
          <MicIcon />
        </button>

        <button
          type="button"
          className={`command-bar__icon-btn${cameraActive ? " command-bar__icon-btn--active" : ""}`}
          onClick={onToggleCamera}
          aria-pressed={cameraActive}
          aria-label="Toggle camera"
          title="Camera (Phase 5 Vision)"
        >
          <CameraIcon />
        </button>

        {activeMode === "screen" && (
          <button
            type="button"
            className="command-bar__icon-btn command-bar__icon-btn--screen"
            aria-label="Screen capture mode"
            title="Screen Capture — auto-captures on submit"
          >
            <ScreenIcon />
          </button>
        )}


        <input
          className="command-bar__input"
          type="text"
          placeholder="Send a command or attach an image/file…"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          aria-label="Command input"
        />

        <button
          type="submit"
          className="command-bar__submit"
          disabled={disabled || (!value.trim() && attachments.length === 0)}
          aria-label="Send"
        >
          <SendIcon />
        </button>
      </form>
    </div>
  );
}

function PaperclipIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function MicIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="9" y="2" width="6" height="12" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0" strokeLinecap="round" />
      <path d="M12 18v3" strokeLinecap="round" />
    </svg>
  );
}

function CameraIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 8a2 2 0 0 1 2-2h2l1.5-2h5L16 6h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z" />
      <circle cx="12" cy="13" r="3.2" />
    </svg>
  );
}

function ScreenIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="3" y="5" width="18" height="13" rx="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M9 18l-1 3h8l-1-3" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 12h15" strokeLinecap="round" />
      <path d="M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
