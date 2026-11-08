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
import theme as theme_module
from main import ui_text, format_money, signed_money, make_pill, make_card, display_name, display_category_name, category_color, parse_money, month_year_label, item_count, weekday_abbr, display_type

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller

        topbar = ctk.CTkFrame(self, fg_color=COLOR_BG, height=60, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        ctk.CTkLabel(topbar, text=t("screen.settings"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left", padx=24)
        ctk.CTkLabel(topbar, text=t("status.auto_save"), font=FONT_MONO, text_color=COLOR_TEXT_MUTED).pack(side="right", padx=24)
        ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=24)
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.section_widgets = {}
        self.settings_nav_buttons = {}
        nav = ctk.CTkFrame(body, fg_color="transparent", width=200)
        nav.grid(row=0, column=0, sticky="nsw", padx=(0, 24))
        nav.grid_propagate(False)
        sections = [
            ("Default income", "settings.nav.default_income"),
            ("Cash-flow targets", "settings.nav.cashflow"),
            ("Categories", "settings.nav.categories"),
            ("Appearance", "settings.nav.appearance"),
            ("Language", "settings.nav.language"),
            ("Data & backup", "settings.nav.data"),
        ]
        for i, (section_key, label_key) in enumerate(sections):
            button = ctk.CTkButton(
                nav, text=t(label_key), height=40, anchor="w",
                fg_color="transparent",
                text_color=COLOR_TEXT_MUTED,
                hover_color=COLOR_SURFACE_2,
                border_width=0,
                border_color=COLOR_BORDER,
                corner_radius=RADIUS_BUTTON,
                font=FONT_BODY,
                command=lambda key=section_key: self.scroll_to_section(key),
            )
            button.pack(fill="x", pady=4)
            self.settings_nav_buttons[section_key] = button
        self._set_active_settings_section(sections[0][0])

        self.scroll = ctk.CTkScrollableFrame(body, fg_color="transparent")
        self.scroll.grid(row=0, column=1, sticky="nsew")

        # === Default Income Items ===
        inc_card = make_card(self.scroll)
        inc_card.pack(fill="x", pady=(0, 24))
        self.section_widgets["Default income"] = inc_card

        inc_hdr = ctk.CTkFrame(inc_card, fg_color="transparent")
        inc_hdr.pack(fill="x", padx=24, pady=(24, 12))
        ctk.CTkLabel(inc_hdr, text=t("settings.default_income.title"), font=FONT_SECTION, text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(inc_hdr, text=t("settings.default_income.desc"), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(4, 0))
        ctk.CTkFrame(inc_card, height=1, fg_color=COLOR_BORDER).pack(fill="x")

        self.inc_items_frame = ctk.CTkFrame(inc_card, fg_color="transparent")
        self.inc_items_frame.pack(fill="x", padx=24, pady=(16, 10))

        inc_add_frame = ctk.CTkFrame(inc_card, fg_color="transparent")
        inc_add_frame.pack(fill="x", padx=24, pady=(0, 24))
        self.inc_new_name = ctk.CTkEntry(inc_add_frame, placeholder_text=t("settings.default_income.item_name"), width=220, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER)
        self.inc_new_name.pack(side="left", padx=(0, 5))
        self.inc_type_var = ctk.StringVar(value=tx("Addition"))
        self.inc_type_options = {tx("Addition"): "addition", tx("Deduction"): "deduction"}
        ctk.CTkOptionMenu(inc_add_frame, values=list(self.inc_type_options.keys()), variable=self.inc_type_var, width=130).pack(side="left", padx=(0, 5))
        ctk.CTkButton(inc_add_frame, text=f"+ {t('common.add')}", width=80, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=self.add_income_item).pack(side="left")

        # === Cash Flow Targets ===
        card = make_card(self.scroll)
        card.pack(fill="x", pady=(0, 24))
        self.section_widgets["Cash-flow targets"] = card

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(24, 12))
        top_h = ctk.CTkFrame(hdr, fg_color="transparent")
        top_h.pack(fill="x")
        ctk.CTkLabel(top_h, text=ui_text("Default Cash-flow Targets (Templates)", "Domyślne cele przepływów (szablony)"), font=FONT_SECTION, text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkButton(
            top_h,
            text=ui_text("Go to Cash Flow tab →", "Przejdź do Przepływów →"),
            width=160,
            height=28,
            fg_color=COLOR_PRIMARY,
            text_color=COLOR_SURFACE,
            hover_color=COLOR_PRIMARY_HOVER,
            command=lambda: self.controller.show_view("Cash Flow")
        ).pack(side="right")
        ctk.CTkLabel(
            hdr,
            text=ui_text(
                "These are default templates applied when creating new months. Month-specific buffer targets are managed directly in the Cash Flow tab.",
                "Domyślne szablony buforów używane przy tworzeniu nowych miesięcy. Cele dla konkretnego miesiąca edytuje się i dodaje bezpośrednio w zakładce Przepływy."
            ),
            font=FONT_BODY,
            text_color=COLOR_TEXT_MUTED,
            wraplength=620,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))
        ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x")

        self.targets_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.targets_frame.pack(fill="x", padx=24, pady=(16, 10))

        add_frame = ctk.CTkFrame(card, fg_color="transparent")
        add_frame.pack(fill="x", padx=24, pady=(0, 24))
        self.new_name = ctk.CTkEntry(add_frame, placeholder_text=t("settings.cashflow.account_name"), width=220, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER)
        self.new_name.pack(side="left", padx=(0, 5))
        self.new_target = ctk.CTkEntry(add_frame, placeholder_text=t("settings.cashflow.target"), width=130, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER)
        self.new_target.pack(side="left", padx=(0, 5))
        ctk.CTkButton(add_frame, text=f"+ {t('common.add')}", width=80, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=self.add_target).pack(side="left")

        # === Categories ===
        cat_card = make_card(self.scroll)
        cat_card.pack(fill="x", pady=(0, 24))
        self.section_widgets["Categories"] = cat_card
        cat_hdr = ctk.CTkFrame(cat_card, fg_color="transparent")
        cat_hdr.pack(fill="x", padx=24, pady=(24, 12))
        ctk.CTkLabel(cat_hdr, text=t("settings.categories.title"), font=FONT_SECTION, text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(cat_hdr, text=t("settings.categories.desc"), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(4, 0))
        ctk.CTkFrame(cat_card, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        self.settings_categories_frame = ctk.CTkFrame(cat_card, fg_color="transparent")
        self.settings_categories_frame.pack(fill="x", padx=24, pady=16)

        # === Appearance ===
        appearance = make_card(self.scroll)
        appearance.pack(fill="x", pady=(0, 24))
        self.section_widgets["Appearance"] = appearance
        active_theme = theme_module.normalize_theme_name(self.controller.config.get("theme", "Petal Rose"))
        self._settings_section_header(appearance, t("settings.appearance.title"), t("settings.appearance.desc").format(theme=active_theme))
        theme_grid = ctk.CTkFrame(appearance, fg_color="transparent")
        theme_grid.pack(fill="x", padx=24, pady=(16, 24))
        for idx, name in enumerate(theme_module.THEME_NAMES):
            palette = theme_module.get_theme_palette(name)
            active = name == active_theme
            bg = palette["COLOR_BG"]
            accent = palette["COLOR_PRIMARY"]
            surface = palette["COLOR_SURFACE"]
            border = palette["COLOR_BORDER"]
            preview = ctk.CTkFrame(theme_grid, fg_color=COLOR_SURFACE, border_width=2 if active else 1, border_color=COLOR_PRIMARY if active else COLOR_BORDER, corner_radius=RADIUS_CARD)
            preview.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=(0 if idx % 2 == 0 else 6, 0 if idx % 2 == 1 else 6), pady=(0, 12))
            theme_grid.grid_columnconfigure(idx % 2, weight=1)
            mock = ctk.CTkFrame(preview, fg_color=bg, border_width=1, border_color=border, corner_radius=10, height=92)
            mock.pack(fill="x", padx=14, pady=(14, 10))
            mock.pack_propagate(False)
            ctk.CTkFrame(mock, fg_color=accent, height=8, corner_radius=4).pack(fill="x", padx=12, pady=(18, 8))
            ctk.CTkFrame(mock, fg_color=surface, height=8, corner_radius=4).pack(fill="x", padx=12, pady=4)
            ctk.CTkFrame(mock, fg_color=surface, height=8, corner_radius=4).pack(fill="x", padx=12, pady=4)
            row = ctk.CTkFrame(preview, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=(0, 14))
            ctk.CTkLabel(row, text=name, font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
            ctk.CTkLabel(row, text=t("common.active") if active else t("common.preview"), font=FONT_SMALL, text_color=COLOR_PRIMARY if active else COLOR_TEXT_MUTED).pack(side="right")
            ctk.CTkButton(
                preview,
                text=t("common.active") if active else t("common.use_theme"),
                height=28,
                fg_color=COLOR_PRIMARY if not active else COLOR_SURFACE_2,
                text_color=COLOR_SURFACE if not active else COLOR_TEXT,
                hover_color=COLOR_PRIMARY_HOVER if not active else COLOR_BORDER,
                command=lambda n=name: self.set_theme_pref(n),
            ).pack(fill="x", padx=14, pady=(0, 14))

        # === Language ===
        language = make_card(self.scroll)
        language.pack(fill="x", pady=(0, 24))
        self.section_widgets["Language"] = language
        self._settings_section_header(language, t("settings.language.title"), t("settings.language.desc"))
        lang_row = ctk.CTkFrame(language, fg_color="transparent")
        lang_row.pack(fill="x", padx=24, pady=(16, 24))
        current_lang = self.controller.config.get("language", "en")
        self.language_cards = {}
        for idx, (code, flag, name, subtitle) in enumerate([
            ("en", "EN", "English", t("settings.language.english_desc")),
            ("pl", "PL", "Polski", t("settings.language.polish_desc")),
        ]):
            card = ctk.CTkFrame(lang_row, fg_color=COLOR_SURFACE, border_width=2 if current_lang == code else 1, border_color=COLOR_PRIMARY if current_lang == code else COLOR_BORDER, corner_radius=RADIUS_CARD)
            card.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 6, 0 if idx == 1 else 6))
            lang_row.grid_columnconfigure(idx, weight=1)
            badge = ctk.CTkLabel(card, text=flag, font=FONT_MONO, text_color=COLOR_PRIMARY, fg_color=COLOR_SURFACE_2, corner_radius=16, width=34, height=34)
            badge.pack(side="left", padx=16, pady=16)
            copy = ctk.CTkFrame(card, fg_color="transparent")
            copy.pack(side="left", fill="x", expand=True, pady=16)
            ctk.CTkLabel(copy, text=name, font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w")
            ctk.CTkLabel(copy, text=subtitle, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
            ctk.CTkButton(card, text=t("common.active") if current_lang == code else t("common.use"), width=74, height=30, fg_color=COLOR_PRIMARY if current_lang == code else COLOR_SURFACE_2, text_color=COLOR_SURFACE if current_lang == code else COLOR_TEXT, hover_color=COLOR_PRIMARY_SOFT, command=lambda lang=code: self.set_language_pref(lang)).pack(side="right", padx=16, pady=16)
            self.language_cards[code] = card

        # === Data & backup ===
        data_card = make_card(self.scroll)
        data_card.pack(fill="x", pady=(0, 24))
        self.section_widgets["Data & backup"] = data_card
        self._settings_section_header(data_card, t("settings.data.title"), t("settings.data.desc"))
        data_body = ctk.CTkFrame(data_card, fg_color="transparent")
        data_body.pack(fill="x", padx=24, pady=(16, 24))
        self._data_row(data_body, t("settings.data.database"), t("settings.data.database_desc"), t("common.local"), t("settings.data.open_folder"), self.open_database_folder)
        self._data_row(data_body, t("settings.data.exports"), t("settings.data.exports_desc"), t("common.manual"), t("settings.data.export_json"), self.export_current_month)

    def _settings_section_header(self, parent, title, body):
        head = ctk.CTkFrame(parent, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(24, 12))
        ctk.CTkLabel(head, text=title, font=FONT_SECTION, text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(head, text=body, font=FONT_BODY, text_color=COLOR_TEXT_MUTED, wraplength=620, justify="left").pack(anchor="w", pady=(4, 0))
        ctk.CTkFrame(parent, height=1, fg_color=COLOR_BORDER).pack(fill="x")

    def _data_row(self, parent, title, body, badge, action_label=None, action_command=None):
        row = ctk.CTkFrame(parent, fg_color=COLOR_SURFACE_2, border_width=1, border_color=COLOR_BORDER, corner_radius=12)
        row.pack(fill="x", pady=6)
        copy = ctk.CTkFrame(row, fg_color="transparent")
        copy.pack(side="left", fill="x", expand=True, padx=16, pady=14)
        ctk.CTkLabel(copy, text=title, font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(copy, text=body, font=FONT_BODY, text_color=COLOR_TEXT_MUTED, wraplength=520, justify="left").pack(anchor="w", pady=(2, 0))
        if action_label and action_command:
            ctk.CTkButton(row, text=action_label, width=112, height=32, fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, border_width=1, border_color=COLOR_BORDER, command=action_command).pack(side="right", padx=(4, 16), pady=14)
        ctk.CTkLabel(row, text=badge.upper(), font=FONT_SMALL, text_color=COLOR_PRIMARY, fg_color=COLOR_SURFACE, corner_radius=6).pack(side="right", padx=16, pady=14, ipadx=8, ipady=3)

    def scroll_to_section(self, key):
        section = self.section_widgets.get(key)
        canvas = getattr(self.scroll, "_parent_canvas", None)
        if not section or not canvas:
            return
        self.update_idletasks()
        bbox = canvas.bbox("all") or (0, 0, 1, 1)
        content_height = max(bbox[3] - bbox[1], 1)
        viewport_height = max(canvas.winfo_height(), 1)
        max_scroll = max(content_height - viewport_height, 1)
        target_y = max(0, min(section.winfo_y() - 8, max_scroll))
        canvas.yview_moveto(max(0, min(target_y / content_height, 1)))
        self._set_active_settings_section(key)

    def _set_active_settings_section(self, active_key):
        for key, button in self.settings_nav_buttons.items():
            active = key == active_key
            button.configure(
                fg_color=COLOR_SURFACE if active else "transparent",
                text_color=COLOR_PRIMARY if active else COLOR_TEXT_MUTED,
                border_width=1 if active else 0,
                border_color=COLOR_BORDER,
            )

    def set_theme_pref(self, name):
        self.controller.config["theme"] = theme_module.set_theme(name)
        sync_theme_globals()
        dm.save_config(self.controller.config)
        self.controller.rebuild_shell("Settings")

    def set_language_pref(self, lang):
        self.controller.config["language"] = lang
        dm.save_config(self.controller.config)
        set_language(lang)
        self.controller.rebuild_shell("Settings")

    def open_database_folder(self):
        open_in_file_manager(get_db_path().parent)

    def export_current_month(self):
        default_name = f"florin-{self.controller.current_month}.json"
        path = filedialog.asksaveasfilename(
            title=tx("Export current month"),
            initialfile=default_name,
            defaultextension=".json",
            filetypes=[(tx("JSON files"), "*.json"), (tx("All files"), "*.*")]
        )
        if not path:
            return
        self.controller.save_data()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.controller.data, f, ensure_ascii=False, indent=2, sort_keys=True)
        messagebox.showinfo(tx("Export complete"), t("settings.export_saved").format(name=Path(path).name))

    def build_settings_categories(self):
        for widget in self.settings_categories_frame.winfo_children():
            widget.destroy()
        cats = self.controller.data.get("categories", [])
        expenses = self.controller.data.get("expenses", [])
        for cat in cats:
            row = ctk.CTkFrame(self.settings_categories_frame, fg_color="transparent")
            row.pack(fill="x", pady=6)
            swatch = ctk.CTkFrame(row, width=24, height=24, fg_color=category_color(cat), corner_radius=6)
            swatch.pack(side="left", padx=(0, 12))
            swatch.pack_propagate(False)
            ctk.CTkLabel(row, text=display_category_name(cat), font=FONT_TITLE, text_color=COLOR_TEXT, width=130, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{cat['percent']:.0f} %", font=FONT_MONO, text_color=COLOR_TEXT, width=70).pack(side="left", padx=8)
            cat_expenses = [e for e in expenses if e.get("category_id") == cat["id"]]
            total = sum(e["amount"] for e in cat_expenses)
            ctk.CTkLabel(row, text=f"{item_count(len(cat_expenses))} · {format_money(total)}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(row, text=tx("Edit"), width=68, height=30, fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_SOFT, command=lambda c=cat: self.open_budget_category_editor(c)).pack(side="right")
            ctk.CTkFrame(self.settings_categories_frame, height=1, fg_color=COLOR_BORDER).pack(fill="x")

    def open_budget_category_editor(self, cat):
        dialog = ctk.CTkToplevel(self)
        dialog.title(tx("Edit budget category"))
        dialog.geometry("380x260")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=tx("Name:"), anchor="w").pack(fill="x", padx=20, pady=(20, 4))
        name_var = ctk.StringVar(value=cat["name"])
        ctk.CTkEntry(dialog, textvariable=name_var, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER).pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text=tx("Monthly split (%):"), anchor="w").pack(fill="x", padx=20, pady=(12, 4))
        percent_var = ctk.StringVar(value=f"{cat.get('percent', 0):.1f}")
        ctk.CTkEntry(dialog, textvariable=percent_var, font=FONT_MONO, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER).pack(fill="x", padx=20)
        error = ctk.CTkLabel(dialog, text="", font=FONT_SMALL, text_color=COLOR_ERROR)
        error.pack(fill="x", padx=20, pady=(4, 0))

        def save():
            name = name_var.get().strip()
            try:
                percent = float(percent_var.get().replace(",", "."))
            except ValueError:
                error.configure(text=tx("Enter a valid percentage."))
                return
            if not name or percent < 0:
                error.configure(text=tx("Name is required and percent cannot be negative."))
                return
            cat["name"] = name
            cat["percent"] = percent
            self.controller.save_data()
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text=tx("Save"), fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=save).pack(fill="x", padx=20, pady=(12, 20))

    # --- Default Income Items ---
    def add_income_item(self):
        name = self.inc_new_name.get().strip()
        if not name:
            return
        dm.add_default_income_item(name, self.inc_type_options.get(self.inc_type_var.get(), "addition"))
        self.inc_new_name.delete(0, "end")
        self.controller.config = dm.get_config()
        self.refresh()

    def delete_income_item(self, item_id):
        dm.delete_default_income_item(item_id)
        self.controller.config = dm.get_config()
        self.refresh()

    def build_income_items(self):
        for w in self.inc_items_frame.winfo_children():
            w.destroy()
        items = dm.get_default_income_items(self.controller.config)
        for item in items:
            row = ctk.CTkFrame(self.inc_items_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            sign = "+" if item["type"] == "addition" else "−"
            color = COLOR_SUCCESS if item["type"] == "addition" else COLOR_ERROR
            ctk.CTkLabel(row, text=sign, font=FONT_MONO, text_color=color, width=28, fg_color=COLOR_INCOME_SOFT if item["type"] == "addition" else COLOR_EXPENSE_SOFT, corner_radius=8).pack(side="left", padx=(0, 10), pady=8)
            ctk.CTkLabel(row, text=display_name(item["name"]), font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(row, text=display_type(item["type"]), font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=10, pady=8)
            ctk.CTkButton(row, text="×", width=28, height=28, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda iid=item["id"]: self.delete_income_item(iid)).pack(side="right", padx=5, pady=5)
            ctk.CTkFrame(self.inc_items_frame, height=1, fg_color=COLOR_BORDER).pack(fill="x")

    # --- Cash Flow Targets (Defaults for new months) ---
    def add_target(self):
        name = self.new_name.get().strip()
        try:
            amt = float(self.new_target.get().replace(",", "."))
        except:
            return
        if not name or amt <= 0:
            return
        dm.add_default_cashflow_target(name, amt)
        self.new_name.delete(0, "end")
        self.new_target.delete(0, "end")
        self.controller.config = dm.get_config()
        self.refresh()

    def delete_target(self, tid):
        dm.delete_default_cashflow_target(tid)
        self.controller.config = dm.get_config()
        self.refresh()

    def save_edit(self, tid, name_var, amt_var):
        name = name_var.get().strip()
        try:
            amt = float(amt_var.get().replace(",", "."))
        except:
            return
        if name and amt > 0:
            dm.edit_default_cashflow_target(tid, name=name, target_amount=amt)
            self.controller.config = dm.get_config()

    def refresh(self):
        self.build_income_items()
        self.build_settings_categories()
        for w in self.targets_frame.winfo_children():
            w.destroy()
        targets = dm.get_default_cashflow_targets()
        for t in targets:
            row = ctk.CTkFrame(self.targets_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            name_var = ctk.StringVar(value=t["name"])
            amt_var = ctk.StringVar(value=f"{t['target']:.2f}")
            ctk.CTkEntry(row, textvariable=name_var, font=FONT_BODY, width=220, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER).pack(side="left", padx=(0, 5), pady=8)
            ctk.CTkEntry(row, textvariable=amt_var, font=FONT_MONO, width=110, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER).pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(row, text="PLN", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left")
            ctk.CTkButton(row, text="OK", width=34, height=28, fg_color="transparent", text_color=COLOR_SUCCESS, hover_color=COLOR_BORDER, command=lambda tid=t["id"], n=name_var, a=amt_var: self.save_edit(tid, n, a)).pack(side="right", padx=2, pady=5)
            ctk.CTkButton(row, text="×", width=28, height=28, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda tid=t["id"]: self.delete_target(tid)).pack(side="right", padx=5, pady=5)
            ctk.CTkFrame(self.targets_frame, height=1, fg_color=COLOR_BORDER).pack(fill="x")



