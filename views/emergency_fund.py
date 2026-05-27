import customtkinter as ctk
import data_manager as dm
from i18n import t, tr_text
import theme

class EmergencyFundView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.mode_var = ctk.StringVar(value="personal")
        self.settings_data = {}
        
        self.setup_ui()
        self.refresh()
        
    def setup_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(40, 20))
        
        title = ctk.CTkLabel(
            header_frame, 
            text=t("nav.emergency_fund"), 
            font=theme.FONT_DISPLAY, 
            text_color=theme.COLOR_TEXT
        )
        title.pack(side="left")
        
        # Mode Switcher
        mode_frame = ctk.CTkFrame(header_frame, fg_color=theme.COLOR_SURFACE, corner_radius=8)
        mode_frame.pack(side="right")
        
        self.btn_personal = ctk.CTkButton(
            mode_frame, text=tr_text("Personal (JA)"), width=120, height=32, corner_radius=8,
            fg_color=theme.COLOR_PRIMARY, text_color=theme.COLOR_SURFACE, hover_color=theme.COLOR_PRIMARY_HOVER,
            command=lambda: self.set_mode("personal")
        )
        self.btn_personal.pack(side="left", padx=2, pady=2)
        
        self.btn_shared = ctk.CTkButton(
            mode_frame, text=tr_text("Shared (WSPÓLNE)"), width=120, height=32, corner_radius=8,
            fg_color="transparent", text_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_SURFACE_2,
            command=lambda: self.set_mode("shared")
        )
        self.btn_shared.pack(side="left", padx=2, pady=2)
        
        # Main Card
        self.card = ctk.CTkFrame(self, fg_color=theme.COLOR_SURFACE, corner_radius=16, border_width=1, border_color=theme.COLOR_BORDER)
        self.card.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        
        # Summary Header
        self.goal_label = ctk.CTkLabel(self.card, text="", font=theme.FONT_SECTION, text_color=theme.COLOR_TEXT)
        self.goal_label.pack(pady=(40, 10))
        
        self.amount_label = ctk.CTkLabel(self.card, text="", font=ctk.CTkFont(family=theme.FONT_MONO_FAMILY, size=48, weight="bold"), text_color=theme.COLOR_PRIMARY)
        self.amount_label.pack(pady=(0, 40))
        
        # Progress Bar
        self.progress_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=60, pady=20)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=24, corner_radius=12, progress_color=theme.COLOR_PRIMARY, fg_color=theme.COLOR_BORDER)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        
        # Stats below progress
        stats_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(10, 0))
        
        self.actual_label = ctk.CTkLabel(stats_frame, text="", font=theme.FONT_BODY, text_color=theme.COLOR_TEXT_MUTED)
        self.actual_label.pack(side="left")
        
        self.percent_label = ctk.CTkLabel(stats_frame, text="", font=theme.FONT_LABEL, text_color=theme.COLOR_TEXT)
        self.percent_label.pack(side="right")
        
        self.missing_label = ctk.CTkLabel(self.card, text="", font=theme.FONT_BODY, text_color=theme.COLOR_EXPENSE)
        self.missing_label.pack(pady=20)

    def set_mode(self, mode):
        self.mode_var.set(mode)
        if mode == "personal":
            self.btn_personal.configure(fg_color=theme.COLOR_PRIMARY, text_color=theme.COLOR_SURFACE)
            self.btn_shared.configure(fg_color="transparent", text_color=theme.COLOR_TEXT_MUTED)
        else:
            self.btn_shared.configure(fg_color=theme.COLOR_PRIMARY, text_color=theme.COLOR_SURFACE)
            self.btn_personal.configure(fg_color="transparent", text_color=theme.COLOR_TEXT_MUTED)
        self.refresh()

    def calculate_target(self, mode_data):
        salary = mode_data.get("salary", 0.0)
        mortgage = mode_data.get("mortgage", 0.0)
        living = mode_data.get("living_expenses", 0.0)
        goal = mode_data.get("selected_goal", "3msc_zycia")
        
        if goal == "3msc_zycia":
            return 3 * living
        elif goal == "6msc_zycia":
            return 6 * living
        elif goal == "3msc_kredytu":
            return 3 * mortgage
        elif goal == "6msc_kredytu":
            return 6 * mortgage
        elif goal == "3msc_zycia_kredytu":
            return 3 * (living + mortgage)
        elif goal == "6msc_zycia_kredytu":
            return 6 * (living + mortgage)
        elif goal == "3msc_wyplaty":
            return 3 * salary
        elif goal == "6msc_wyplaty":
            return 6 * salary
        return 0.0

    def get_goal_text(self, goal):
        mapping = {
            "3msc_zycia": "3 months of living",
            "6msc_zycia": "6 months of living",
            "3msc_kredytu": "3 months of loan",
            "6msc_kredytu": "6 months of loan",
            "3msc_zycia_kredytu": "3 months of living + loan",
            "6msc_zycia_kredytu": "6 months of living + loan",
            "3msc_wyplaty": "3 months of salary",
            "6msc_wyplaty": "6 months of salary"
        }
        return tr_text(mapping.get(goal, goal))

    def refresh(self):
        self.settings_data = dm.get_emergency_fund_settings()
        mode = self.mode_var.get()
        data = self.settings_data.get(mode, {})
        
        target = self.calculate_target(data)
        actual = data.get("actual_saved", 0.0)
        
        goal_code = data.get("selected_goal", "3msc_zycia")
        goal_text = self.get_goal_text(goal_code)
        
        self.goal_label.configure(text=f"{tr_text('Goal:')} {goal_text}")
        self.amount_label.configure(text=f"{target:,.2f} PLN")
        
        pct = 0.0
        if target > 0:
            pct = actual / target
        if pct > 1.0:
            pct = 1.0
            
        self.progress_bar.set(pct)
        
        self.actual_label.configure(text=f"{tr_text('Actual Saved:')} {actual:,.2f} PLN")
        self.percent_label.configure(text=f"{pct*100:.1f}%")
        
        missing = target - actual
        if missing > 0:
            self.missing_label.configure(text=f"{tr_text('Missing to goal')}: {missing:,.2f} PLN")
        else:
            self.missing_label.configure(text=f"✓ {tr_text('Target Goal')} {tr_text('Saved')}")
