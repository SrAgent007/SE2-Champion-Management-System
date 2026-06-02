import customtkinter as ctk


def _truncate_text(text, max_chars):
    s = str(text) if text is not None else ""
    if len(s) <= max_chars:
        return s, False
    return s[: max(0, max_chars - 1)] + "…", True


def _show_full_text_modal(parent, full_text, title="Details"):
    modal = ctk.CTkToplevel(parent)
    modal.title(title)
    modal.geometry("560x320")
    modal.configure(fg_color="white")
    modal.attributes("-topmost", True)
    modal.grab_set()
    modal.update_idletasks()
    # Read-only scrollable text
    txt = ctk.CTkTextbox(modal, wrap="word")
    txt.pack(fill="both", expand=True, padx=12, pady=12)
    txt.insert("0.0", full_text)
    txt.configure(state="disabled")
    ctk.CTkButton(modal, text="Close", command=modal.destroy).pack(pady=(0, 12))


def make_trunc_label(parent, text, max_chars=40, title="Details", **label_kwargs):
    """Create a CTkLabel that shows truncated text and opens a modal with full text when clicked.

    parent: parent widget to attach label to
    text: original text
    max_chars: maximum characters to show before truncation
    title: modal title when showing full text
    label_kwargs: forwarded to CTkLabel constructor
    """
    full = str(text) if text is not None else ""
    short, truncated = _truncate_text(full, max_chars)
    lbl = ctk.CTkLabel(parent, text=short, **label_kwargs)
    if truncated:
        lbl.configure(cursor="hand2")
        lbl.bind("<Button-1>", lambda e, ft=full, p=parent: _show_full_text_modal(p.winfo_toplevel(), ft, title=title))
    return lbl
