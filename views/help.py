import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import data_manager as dm
from datetime import datetime, date
import uuid
import json
import os
import sys
from i18n import t, tr_text as tx, month_full, get_language
from theme import *
from main import ui_text, format_money, signed_money, make_pill, make_card, display_name, display_category_name, category_color, parse_money, month_year_label, item_count, weekday_abbr

class HelpView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller
        self._sections = []  # [(heading, content_text, frame_widget)]

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(24, 12))
        ctk.CTkLabel(hdr, text=t("help.title"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left")

        # Search box
        self._search_var = ctk.StringVar()
        self._search_job = None
        self._search_var.trace_add("write", lambda *_: self._schedule_filter())

    def _schedule_filter(self):
        if self._search_job is not None:
            self.after_cancel(self._search_job)
        self._search_job = self.after(300, self._filter)
        search = ctk.CTkEntry(hdr, textvariable=self._search_var, placeholder_text=t("help.search_placeholder"), width=220)
        search.pack(side="right")

        # Scrollable content
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        self._render_markdown()

    def _load_help_text(self):
        filename = "HELP.pl.md" if get_language() == "pl" else "HELP.md"
        help_path = Path(__file__).parent / filename
        try:
            return help_path.read_text(encoding="utf-8")
        except:
            return f"# {t('help.title')}\n\n{t('help.file_not_found')}"

    def _render_markdown(self):
        text = self._load_help_text()
        lines = text.split("\n")
        current_heading = ""
        current_lines = []
        sections = []

        def flush():
            if current_heading or current_lines:
                sections.append((current_heading, "\n".join(current_lines)))

        for line in lines:
            if line.startswith("# "):
                flush()
                current_heading = line[2:].strip()
                current_lines = []
            elif line.startswith("## "):
                flush()
                current_heading = line[3:].strip()
                current_lines = []
            elif line.startswith("### "):
                flush()
                current_heading = line[4:].strip()
                current_lines = []
            else:
                current_lines.append(line)
        flush()

        for heading, body in sections:
            frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
            frame.pack(fill="x", pady=(8, 0), anchor="w")

            if heading:
                ctk.CTkLabel(frame, text=heading, font=FONT_TITLE, text_color=COLOR_PRIMARY, anchor="w").pack(fill="x")

            if body.strip():
                rendered = self._format_body(body.strip())
                lbl = ctk.CTkLabel(frame, text=rendered, font=FONT_BODY, text_color=COLOR_TEXT, anchor="w", justify="left", wraplength=700)
                lbl.pack(fill="x", padx=(10, 0), pady=(2, 0))

            self._sections.append((heading.lower(), body.lower(), frame))

    def _format_body(self, text):
        """Light formatting: strip markdown bold/table syntax for display."""
        lines = []
        for line in text.split("\n"):
            line = line.replace("**", "")
            if line.startswith("- "):
                line = "  • " + line[2:]
            elif line.startswith("| ") and "---" not in line:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                line = "  " + "  |  ".join(cells)
            elif line.startswith("|") and "---" in line:
                continue
            elif line.startswith("---"):
                continue
            lines.append(line)
        return "\n".join(lines)

    def _filter(self):
        query = self._search_var.get().lower().strip()
        any_visible = False
        for heading, body, frame in self._sections:
            if not query or query in heading or query in body:
                frame.pack(fill="x", pady=(8, 0), anchor="w")
                any_visible = True
            else:
                frame.pack_forget()
        # Show "no results" if nothing matches
        if hasattr(self, "_no_results_lbl"):
            self._no_results_lbl.destroy()
        if not any_visible and query:
            self._no_results_lbl = ctk.CTkLabel(self._scroll, text=t("help.no_results"), font=FONT_BODY, text_color=COLOR_TEXT_MUTED)
            self._no_results_lbl.pack(pady=20)


    def refresh(self):
        pass  # Static content, no refresh needed


