import os
import customtkinter as ctk
import sys
from tkinter import messagebox
from datetime import datetime
from PIL import Image
from database import get_connection, log_action

# Data Visualization
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import Views
from views.projects import ProjectsView
from views.inventory import InventoryView
from views.profile import ProfileView
from views.tagging import TaggingView
from views.borrowing import BorrowingView
from views.tracking import TrackingView
from views.reports import ReportsView
from views.maintenance import MaintenanceView
from views.role_management import RoleManagementView
from views.help import HelpView


class DashboardApp(ctk.CTkToplevel):
    def __init__(self, parent, user_info):
        super().__init__(master=parent)

        self.user_info = user_info
        self.title("Champion Fine Tooling - Automated Management System")

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = int(sw * 0.85)
        h = int(sh * 0.85)
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(1100, 700)

        self.protocol("WM_DELETE_WINDOW", self.confirm_logout)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.build_sidebar()
        self.build_topbar()

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=1, sticky="nsew", padx=30, pady=30)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.current_frame = None
        self.current_page_name = None
        self.dashboard_refresh_job = None
        
        self.show_frame("Dashboard")

    def build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#1A3B22")
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        self.icon_path = os.path.join(os.path.dirname(__file__), "assets", "login_logo.png")
        try:
            self.sidebar_icon_img = ctk.CTkImage(light_image=Image.open(self.icon_path), size=(50, 50))
            self.sidebar_logo = ctk.CTkLabel(self.sidebar_frame, image=self.sidebar_icon_img, text="")
            self.sidebar_logo.pack(pady=(30, 10))
        except FileNotFoundError:
            self.sidebar_logo = ctk.CTkLabel(self.sidebar_frame, text="🟢", font=("Inter", 40))
            self.sidebar_logo.pack(pady=(30, 10))

        ctk.CTkLabel(self.sidebar_frame, text="Automated Management\nSystem",
                     font=("Inter", 14, "bold"), text_color="white").pack(pady=(0, 30))

        is_admin = self.user_info.get("role", "Staff") == "Admin"

        nav_items = [
            "Dashboard",
            "Project Management",
            "Products / Inventory",
            "Tagging",
            "Issuance & Retrieval",
            "Tracking & Accountability",
        ]
        
        if is_admin:
            nav_items += ["Reports", "Maintenance", "Role Management"]
            
        nav_items.append("Help")

        self.nav_buttons = {}
        for item in nav_items:
            btn = ctk.CTkButton(
                self.sidebar_frame, text=item, anchor="w",
                fg_color="transparent", hover_color="#2A6038",
                text_color="white", font=("Inter", 13, "bold"),
                command=lambda m=item: self.show_frame(m)
            )
            btn.pack(fill="x", pady=2, padx=10)
            self.nav_buttons[item] = btn

        ctk.CTkButton(
            self.sidebar_frame, text="Exit", anchor="w",
            fg_color="transparent", hover_color="#8B0000",
            text_color="white", font=("Inter", 13, "bold"),
            command=self.confirm_logout
        ).pack(side="bottom", fill="x", pady=20, padx=10)

    def build_topbar(self):
        self.topbar_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="white")
        self.topbar_frame.grid(row=0, column=1, sticky="ew")
        self.topbar_frame.pack_propagate(False)

        self.logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        try:
            self.topbar_logo_img = ctk.CTkImage(light_image=Image.open(self.logo_path), size=(30, 30))
            self.header_logo = ctk.CTkLabel(
                self.topbar_frame, image=self.topbar_logo_img,
                text=" Champion Fine Tooling", compound="left",
                font=("Inter", 14, "bold"), text_color="#1A3B22"
            )
            self.header_logo.pack(side="left", padx=30)
        except FileNotFoundError:
            self.header_logo = ctk.CTkLabel(
                self.topbar_frame, text="Champion Fine Tooling",
                font=("Inter", 14, "bold"), text_color="#1A3B22"
            )
            self.header_logo.pack(side="left", padx=30)

        self.time_label = ctk.CTkLabel(self.topbar_frame, text="", font=("Inter", 12), text_color="#666666")
        self.time_label.pack(side="right", padx=(10, 30), pady=20)
        self._update_clock()

        self.user_frame = ctk.CTkFrame(self.topbar_frame, fg_color="transparent", cursor="hand2")
        self.user_frame.pack(side="right", padx=15, pady=5)
        self.user_frame.bind("<Button-1>", lambda e: self.show_frame("Profile"))

        self.user_text_frame = ctk.CTkFrame(self.user_frame, fg_color="transparent", cursor="hand2")
        self.user_text_frame.pack(side="right", padx=(10, 0))
        self.user_text_frame.bind("<Button-1>", lambda e: self.show_frame("Profile"))

        self.user_name_label = ctk.CTkLabel(
            self.user_text_frame, text=f"{self.user_info['full_name']}",
            font=("Inter", 14, "bold"), text_color="black"
        )
        self.user_name_label.pack(anchor="w")
        self.user_name_label.bind("<Button-1>", lambda e: self.show_frame("Profile"))

        self.user_role_label = ctk.CTkLabel(
            self.user_text_frame, text=f"{self.user_info['role']}",
            font=("Inter", 12, "bold"), text_color="#2ECC71"
        )
        self.user_role_label.pack(anchor="w")
        self.user_role_label.bind("<Button-1>", lambda e: self.show_frame("Profile"))

        self.profile_pic_label = ctk.CTkLabel(self.user_frame, text="")
        self.profile_pic_label.pack(side="right")
        self.profile_pic_label.bind("<Button-1>", lambda e: self.show_frame("Profile"))

        self.refresh_topbar()

    def _update_clock(self):
        current_time = datetime.now().strftime("%a, %b %d, %Y  %I:%M:%S %p")
        self.time_label.configure(text=current_time)
        self._clock_job = self.after(1000, self._update_clock)

    def refresh_topbar(self):
        self.user_name_label.configure(text=f"{self.user_info['full_name']}")
        self.user_role_label.configure(text=f"{self.user_info['role']}")
        pic_path = os.path.join(
            os.path.dirname(__file__), "assets", "profiles",
            f"{self.user_info['employee_id']}.png"
        )
        if not os.path.exists(pic_path):
            pic_path = os.path.join(os.path.dirname(__file__), "assets", "login_logo.png")
        try:
            self.topbar_profile_img = ctk.CTkImage(light_image=Image.open(pic_path), size=(40, 40))
            self.profile_pic_label.configure(image=self.topbar_profile_img)
        except Exception:
            self.profile_pic_label.configure(text="👤")

    def confirm_logout(self):
        if hasattr(self, "_clock_job"):
            self.after_cancel(self._clock_job)
        if hasattr(self, "dashboard_refresh_job") and self.dashboard_refresh_job:
            self.after_cancel(self.dashboard_refresh_job)
            
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out of your account?"):
            log_action(self.user_info.get("user_id"), "Logout", "Authentication",
                       f"User {self.user_info.get('full_name')} logged out.")
            self.destroy()
            self.master.deiconify()
            self.master.pass_entry.delete(0, "end")
            self.master.error_banner.configure(text="", fg_color="transparent")
            self.master.failed_attempts = 0

    def show_frame(self, page_name):
        self.current_page_name = page_name
        
        # Stop auto-refresh if we navigate away from Dashboard
        if hasattr(self, 'dashboard_refresh_job') and self.dashboard_refresh_job:
            self.after_cancel(self.dashboard_refresh_job)
            self.dashboard_refresh_job = None

        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.configure(fg_color="#2A6038", text_color="#F1C40F")
            else:
                btn.configure(fg_color="transparent", text_color="white")

        if self.current_frame is not None:
            self.current_frame.destroy()

        uid = self.user_info.get("user_id")
        if uid and page_name != "Dashboard":
            log_action(uid, "Viewed", page_name, f"Navigated to {page_name}")

        if page_name == "Profile":
            self.current_frame = ProfileView(self.main_container, self.user_info, self)
        elif page_name == "Project Management":
            self.current_frame = ProjectsView(self.main_container, self.user_info)
        elif page_name == "Products / Inventory":
            self.current_frame = InventoryView(self.main_container, self.user_info)
        elif page_name == "Tagging":
            self.current_frame = TaggingView(self.main_container)
        elif page_name == "Issuance & Retrieval":
            self.current_frame = BorrowingView(self.main_container, self.user_info)
        elif page_name == "Tracking & Accountability":
            self.current_frame = TrackingView(self.main_container, self.user_info)
        elif page_name == "Reports":
            self.current_frame = ReportsView(self.main_container)
        elif page_name == "Maintenance":
            self.current_frame = MaintenanceView(self.main_container)
        elif page_name == "Role Management":
            self.current_frame = RoleManagementView(self.main_container)
        elif page_name == "Help":
            self.current_frame = HelpView(self.main_container, self.user_info)
        elif page_name == "Dashboard":
            self.current_frame = self.create_home_dashboard()
        else:
            self.current_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
            ctk.CTkLabel(self.current_frame, text=f"{page_name.upper()} MODULE",
                         font=("Inter", 20), text_color="gray").pack(expand=True)

        self.current_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0, relheight=1.0)

    def get_live_metrics(self):
        metrics = {
            "total_employees": 0,
            "active_workforce": 0,
            "available_qty": 0, 
            "borrowed_qty": 0, 
            "total_physical": 0,
            "utilization_pct": 0,
            "pending_issues": 0,
            "overdue_projects": 0,
            "action_items": 0
        }
        activities = []
        chart_data = [0, 0, 0, 0]

        conn = get_connection()
        if not conn:
            return metrics, activities, chart_data

        try:
            cursor = conn.cursor(dictionary=True)
            
            # 1. Total Registered Employees
            cursor.execute("SELECT COUNT(*) as cnt FROM user")
            metrics["total_employees"] = int(cursor.fetchone()["cnt"] or 0)

            # 2. Active Workforce
            cursor.execute("SELECT COUNT(DISTINCT user_id) as cnt FROM transaction WHERE status = 'Active'")
            metrics["active_workforce"] = int(cursor.fetchone()["cnt"] or 0)

            # 3. Asset Utilization
            cursor.execute("SELECT IFNULL(SUM(quantity_available), 0) as qty FROM inventory")
            metrics["available_qty"] = int(cursor.fetchone()["qty"] or 0)

            cursor.execute("SELECT COUNT(*) as cnt FROM transaction WHERE status = 'Active'")
            metrics["borrowed_qty"] = int(cursor.fetchone()["cnt"] or 0)

            metrics["total_physical"] = metrics["available_qty"] + metrics["borrowed_qty"]
            if metrics["total_physical"] > 0:
                metrics["utilization_pct"] = int((metrics["borrowed_qty"] / metrics["total_physical"]) * 100)

            # 4. Action Items (EXACT SYNC WITH GRAPH: Count physical conditions, not just tickets)
            try:
                # This guarantees that if a tool is "Damaged" or "Needs Repair" in the graph, it counts here as an action item.
                cursor.execute("SELECT COUNT(*) as cnt FROM tool WHERE `condition` IN ('Needs Repair', 'Damaged', 'Lost') AND is_archived = 0")
                metrics["pending_issues"] = int(cursor.fetchone()["cnt"] or 0)
            except Exception as e:
                pass 

            try:
                cursor.execute("SELECT COUNT(*) as cnt FROM project WHERE status = 'Active' AND end_date < CURDATE()")
                metrics["overdue_projects"] = int(cursor.fetchone()["cnt"] or 0)
            except:
                try:
                    cursor.execute("SELECT COUNT(*) as cnt FROM projects WHERE status = 'Active' AND end_date < CURDATE()")
                    metrics["overdue_projects"] = int(cursor.fetchone()["cnt"] or 0)
                except:
                    pass

            metrics["action_items"] = metrics["pending_issues"] + metrics["overdue_projects"]

            # 5. Fix Recent Activity (Pulling exactly from system_logs as requested)
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(DATE_ADD(sl.timestamp, INTERVAL 8 HOUR), '%Y-%m-%d %I:%M %p') as ts,
                    sl.action_type as action,
                    IFNULL(sl.module, '—') as item,
                    IFNULL(u.full_name, 'System') as actor
                FROM system_logs sl
                LEFT JOIN user u ON sl.user_id = u.user_id
                ORDER BY sl.log_id DESC 
                LIMIT 8
            """)
            for row in cursor.fetchall():
                activities.append((row["ts"], row["action"], row["item"], row["actor"]))
            
            # 6. Chart Data
            cursor.execute("SELECT `condition`, COUNT(*) as cnt FROM tool WHERE is_archived = 0 GROUP BY `condition`")
            cond_map = {"Good": 0, "Needs Repair": 1, "Damaged": 2, "Lost": 3}
            for row in cursor.fetchall():
                c = row["condition"]
                if c in cond_map: chart_data[cond_map[c]] = row["cnt"]

        except Exception as e:
            print(f"Dashboard Sync Error: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

        return metrics, activities, chart_data

    def create_home_dashboard(self):
        frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent", orientation="vertical")

        inner_frame = ctk.CTkFrame(frame, fg_color="transparent")
        inner_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(inner_frame, text="EXECUTIVE BRIEFING", font=("Inter", 24, "bold"),
                     text_color="#1A1A1A").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(inner_frame, text="High-level overview of system health and asset utilization. Auto-updates live.",
                     font=("Inter", 13), text_color="gray").pack(anchor="w", pady=(0, 20))

        metrics, activities, chart_data = self.get_live_metrics()

        cards_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 20))
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)

        # 1. Asset Utilization Card (Stored reference for auto-update)
        c1 = ctk.CTkFrame(cards_frame, fg_color="#1E4528", corner_radius=10, height=100)
        c1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        c1.pack_propagate(False)
        self.dash_util_lbl = ctk.CTkLabel(c1, text=f"{metrics['utilization_pct']}%", font=("Inter", 28, "bold"), text_color="white")
        self.dash_util_lbl.pack(anchor="w", padx=20, pady=(15, 0))
        ctk.CTkLabel(c1, text="Asset Utilization", font=("Inter", 13, "bold"), text_color="white").pack(anchor="w", padx=20)
        ctk.CTkLabel(c1, text="Deployed vs Warehouse", font=("Inter", 11), text_color="white").pack(anchor="w", padx=20)

        # 2. Active Workforce Card
        c2 = ctk.CTkFrame(cards_frame, fg_color="#2980B9", corner_radius=10, height=100)
        c2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        c2.pack_propagate(False)
        self.dash_wf_lbl = ctk.CTkLabel(c2, text=f"{metrics['active_workforce']} / {metrics['total_employees']}", font=("Inter", 28, "bold"), text_color="white")
        self.dash_wf_lbl.pack(anchor="w", padx=20, pady=(15, 0))
        ctk.CTkLabel(c2, text="Active Workforce", font=("Inter", 13, "bold"), text_color="white").pack(anchor="w", padx=20)
        ctk.CTkLabel(c2, text="Employees currently deployed", font=("Inter", 11), text_color="white").pack(anchor="w", padx=20)

        # 3. Action Items Card
        c3_bg = "#FFF5F5" if metrics["action_items"] > 0 else "#F9FAFB"
        c3_border = "#D8000C" if metrics["action_items"] > 0 else "#E0E0E0"
        self.dash_action_card = ctk.CTkFrame(cards_frame, fg_color=c3_bg, corner_radius=10, height=100, border_width=1, border_color=c3_border)
        self.dash_action_card.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.dash_action_card.pack_propagate(False)

        self.dash_action_top = ctk.CTkFrame(self.dash_action_card, fg_color="transparent")
        self.dash_action_top.pack(fill="x", padx=20, pady=(15, 0))
        
        self._render_action_badges(metrics)

        ctk.CTkLabel(self.dash_action_card, text="Action Items", font=("Inter", 13, "bold"), text_color="black").pack(anchor="w", padx=20, pady=(0,0))
        ctk.CTkLabel(self.dash_action_card, text="Requires immediate attention", font=("Inter", 11), text_color="gray").pack(anchor="w", padx=20)

        # 4. Total Inventory Card
        c4 = ctk.CTkFrame(cards_frame, fg_color="#F1C40F", corner_radius=10, height=100)
        c4.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        c4.pack_propagate(False)
        self.dash_inv_lbl = ctk.CTkLabel(c4, text=str(metrics['total_physical']), font=("Inter", 28, "bold"), text_color="black")
        self.dash_inv_lbl.pack(anchor="w", padx=20, pady=(15, 0))
        ctk.CTkLabel(c4, text="Total Inventory", font=("Inter", 13, "bold"), text_color="black").pack(anchor="w", padx=20)
        ctk.CTkLabel(c4, text="Total physical items logged", font=("Inter", 11), text_color="black").pack(anchor="w", padx=20)

        # Bottom Split (Activity Feed & Chart)
        bottom_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True)
        bottom_frame.grid_columnconfigure(0, weight=2)
        bottom_frame.grid_columnconfigure(1, weight=1)
        bottom_frame.grid_rowconfigure(0, weight=1)

        # Recent Activity Feed
        activity_card = ctk.CTkFrame(bottom_frame, fg_color="white", corner_radius=10)
        activity_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        ctk.CTkLabel(activity_card, text="Recent Activity Feed",
                     font=("Inter", 14, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20, pady=20)

        header_frame = ctk.CTkFrame(activity_card, fg_color="#1E4528", corner_radius=5, height=35)
        header_frame.pack(fill="x", padx=(20, 36))
        header_frame.pack_propagate(False)
        for col, text in enumerate(["Date & Time", "Action Type", "Module / Item", "User"]):
            header_frame.grid_columnconfigure(col, weight=1)
            ctk.CTkLabel(header_frame, text=text, font=("Inter", 11, "bold"),
                         text_color="white").grid(row=0, column=col, padx=10, pady=5, sticky="w")

        self.dash_activity_frame = ctk.CTkFrame(activity_card, fg_color="transparent")
        self.dash_activity_frame.pack(fill="both", expand=True)
        self._render_activity_feed(activities)

        # Chart Frame
        analytics_card = ctk.CTkFrame(bottom_frame, fg_color="white", corner_radius=10)
        analytics_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        ctk.CTkLabel(analytics_card, text="Tool Condition Metrics",
                     font=("Inter", 14, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20, pady=(20, 5))
        
        self.dash_fig, self.dash_ax, self.dash_canvas = self.embed_chart(analytics_card, chart_data)
        
        # Start Auto Update Loop
        self.dashboard_refresh_job = self.after(5000, self._auto_refresh_dashboard)
        
        return frame

    def _render_action_badges(self, metrics):
        for w in self.dash_action_top.winfo_children(): w.destroy()
        
        if metrics["action_items"] == 0:
            ctk.CTkLabel(self.dash_action_top, text="0", font=("Inter", 28, "bold"), text_color="black").pack(side="left")
            ctk.CTkLabel(self.dash_action_top, text="✓ All Clear", fg_color="#2ECC71", text_color="white", font=("Inter", 11, "bold"), corner_radius=6, padx=10, pady=3).pack(side="left", padx=(15, 0), pady=(5,0))
            self.dash_action_card.configure(fg_color="#F9FAFB", border_color="#E0E0E0")
        else:
            ctk.CTkLabel(self.dash_action_top, text=str(metrics['action_items']), font=("Inter", 28, "bold"), text_color="#D8000C").pack(side="left")
            self.dash_action_card.configure(fg_color="#FFF5F5", border_color="#D8000C")
            
            if metrics['pending_issues'] > 0:
                ctk.CTkLabel(self.dash_action_top, text=f"⚠ {metrics['pending_issues']} Tools Need Maint.", fg_color="#D8000C", text_color="white", font=("Inter", 10, "bold"), corner_radius=6, padx=8, pady=3).pack(side="left", padx=(10, 0), pady=(5,0))
                
            if metrics['overdue_projects'] > 0:
                ctk.CTkLabel(self.dash_action_top, text=f"⚠ {metrics['overdue_projects']} Overdue", fg_color="#D8000C", text_color="white", font=("Inter", 10, "bold"), corner_radius=6, padx=8, pady=3).pack(side="left", padx=(5, 0), pady=(5,0))

    def _render_activity_feed(self, activities):
        for w in self.dash_activity_frame.winfo_children(): w.destroy()
        
        if not activities:
            activities = [("-", "No recent activity recorded.", "-", "-")]

        for i, row_data in enumerate(activities):
            row_frame = ctk.CTkFrame(self.dash_activity_frame,
                                     fg_color="#F9FAFB" if i % 2 == 0 else "white",
                                     height=35)
            row_frame.pack(fill="x", padx=20)
            row_frame.pack_propagate(False)
            for col, text in enumerate(row_data):
                row_frame.grid_columnconfigure(col, weight=1)
                
                font_weight = "normal"
                color = "#1A1A1A"
                if col == 1:
                    if text in ["Flagged", "Resolved", "Archived"]:
                        color = "#D8000C" if text == "Flagged" else ("#2ECC71" if text == "Resolved" else "#E67E22")
                        font_weight = "bold"
                    elif text == "Issued":
                        color = "#2980B9"
                        font_weight = "bold"
                    elif text == "Retrieved":
                        color = "#2ECC71"
                        font_weight = "bold"
                
                ctk.CTkLabel(row_frame, text=text, font=("Inter", 11, font_weight),
                             text_color=color).grid(row=0, column=col, padx=10, pady=5, sticky="w")

    def _auto_refresh_dashboard(self):
        # Stop looping if user navigated away
        if self.current_page_name != "Dashboard":
            return
            
        metrics, activities, chart_data = self.get_live_metrics()
        
        # 1. Live Update Metric Labels
        self.dash_util_lbl.configure(text=f"{metrics['utilization_pct']}%")
        self.dash_wf_lbl.configure(text=f"{metrics['active_workforce']} / {metrics['total_employees']}")
        self.dash_inv_lbl.configure(text=str(metrics['total_physical']))
        
        # 2. Live Update Badges
        self._render_action_badges(metrics)
        
        # 3. Live Update Activity Feed
        self._render_activity_feed(activities)
        
        # 4. Live Update Matplotlib Chart
        self.dash_ax.clear()
        categories = ["Good", "Repair", "Damaged", "Lost"]
        colors = ["#2ECC71", "#F1C40F", "#E67E22", "#95A5A6"]
        bars = self.dash_ax.bar(categories, chart_data, color=colors, width=0.6)
        self.dash_ax.spines["top"].set_visible(False)
        self.dash_ax.spines["right"].set_visible(False)
        self.dash_ax.spines["left"].set_visible(False)
        self.dash_ax.get_yaxis().set_ticks([])

        for bar in bars:
            yval = bar.get_height()
            offset = max(chart_data) * 0.05 + 0.1 if max(chart_data) > 0 else 0.1
            self.dash_ax.text(bar.get_x() + bar.get_width() / 2, yval + offset,
                    int(yval), ha="center", va="bottom",
                    fontdict={"family": "sans-serif", "weight": "bold", "color": "#333333"})

        self.dash_canvas.draw()
        
        # Re-trigger background loop
        self.dashboard_refresh_job = self.after(5000, self._auto_refresh_dashboard)

    def embed_chart(self, parent_frame, chart_data):
        fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor("#FFFFFF")
        ax.set_facecolor("#FFFFFF")

        categories = ["Good", "Repair", "Damaged", "Lost"]
        colors = ["#2ECC71", "#F1C40F", "#E67E22", "#95A5A6"]

        bars = ax.bar(categories, chart_data, color=colors, width=0.6)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.get_yaxis().set_ticks([])

        for bar in bars:
            yval = bar.get_height()
            offset = max(chart_data) * 0.05 + 0.1 if max(chart_data) > 0 else 0.1
            ax.text(bar.get_x() + bar.get_width() / 2, yval + offset,
                    int(yval), ha="center", va="bottom",
                    fontdict={"family": "sans-serif", "weight": "bold", "color": "#333333"})

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        return fig, ax, canvas