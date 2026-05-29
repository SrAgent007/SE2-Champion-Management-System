import customtkinter as ctk
from tkinter import messagebox
from database import get_connection, log_action
from datetime import datetime


class TrackingView(ctk.CTkFrame):
    def __init__(self, parent, user_info=None):
        super().__init__(parent, fg_color="transparent")

        self.user_info = user_info or {}
        self.is_admin = self.user_info.get("role", "Staff") == "Admin"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if self.is_admin:
            self.build_admin_view()
        else:
            self.build_staff_view()

        # Log module open
        uid = self.user_info.get("user_id")
        if uid:
            log_action(uid, "Viewed", "Tracking & Accountability", "Opened Tracking module")

    # ==========================================
    # SHARED: uniform table builders
    # ==========================================
    def _make_header(self, parent, headers, weights):
        hdr = ctk.CTkFrame(parent, fg_color="#1E4528", corner_radius=5, height=38)
        hdr.pack(fill="x", padx=(20, 36))
        hdr.pack_propagate(False)
        total = sum(weights)
        for col, (h, w) in enumerate(zip(headers, weights)):
            hdr.grid_columnconfigure(col, weight=w, minsize=max(50, int(w / total * 900)))
            ctk.CTkLabel(hdr, text=h, font=("Inter", 11, "bold"),
                         text_color="white").grid(row=0, column=col, padx=8, pady=8, sticky="w")
        return hdr

    def _make_row(self, parent, vals, weights, bg):
        rf = ctk.CTkFrame(parent, fg_color=bg, height=36)
        rf.pack(fill="x", pady=1)
        rf.pack_propagate(False)
        total = sum(weights)
        for col, (val, w) in enumerate(zip(vals, weights)):
            rf.grid_columnconfigure(col, weight=w, minsize=max(50, int(w / total * 900)))
        return rf

    # ==========================================
    # ADMIN VIEW  (4 tabs)
    # ==========================================
    def build_admin_view(self):
        notebook_frame = ctk.CTkFrame(self, fg_color="transparent")
        notebook_frame.grid(row=0, column=0, sticky="nsew")
        notebook_frame.grid_columnconfigure(0, weight=1)
        notebook_frame.grid_rowconfigure(1, weight=1)

        # ── Tab bar ──────────────────────────────────────────────
        tab_bar = ctk.CTkFrame(notebook_frame, fg_color="white", corner_radius=10, height=50)
        tab_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tab_bar.pack_propagate(False)

        self.tab_content = ctk.CTkFrame(notebook_frame, fg_color="transparent")
        self.tab_content.grid(row=1, column=0, sticky="nsew")
        self.tab_content.grid_columnconfigure(0, weight=1)
        self.tab_content.grid_rowconfigure(0, weight=1)

        tabs = [
            ("Borrow/Return Logs", "logs"),
            ("Audit Records",      "audit"),
            ("Activity Log",       "activity"),   # NEW — shows system_logs
            ("Manage Issues",      "issues"),
        ]

        self.tab_buttons = {}
        for text, key in tabs:
            btn = ctk.CTkButton(
                tab_bar, text=text,
                fg_color="#1E4528" if key == "logs" else "transparent",
                text_color="white" if key == "logs" else "#1A1A1A",
                hover_color="#2A6038",
                font=("Inter", 12, "bold"),
                
                command=lambda k=key: self.switch_tab(k, tabs)
            )
            btn.pack(side="left", padx=10, pady=8)
            self.tab_buttons[key] = btn

        self.render_logs_tab()

    def switch_tab(self, key, tabs):
        for widget in self.tab_content.winfo_children():
            widget.destroy()
        for text, k in tabs:
            btn = self.tab_buttons.get(k)
            if btn:
                btn.configure(
                    fg_color="#1E4528" if k == key else "transparent",
                    text_color="white" if k == key else "#1A1A1A"
                )
        if key == "logs":
            self.render_logs_tab()
        elif key == "audit":
            self.render_audit_tab()
        elif key == "activity":
            self.render_activity_tab()
        elif key == "issues":
            self.render_issues_tab()

    # ------------------------------------------
    # TAB 1: Borrow/Return Logs
    # ------------------------------------------
    def render_logs_tab(self):
        frame = ctk.CTkFrame(self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(top, text="Borrow / Return Transaction Logs",
                     font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(side="left")

        self.log_search = ctk.CTkEntry(top, placeholder_text="Search employee or tool...", width=220)
        self.log_search.pack(side="right", padx=(5, 0))
        self.log_search.bind("<Return>", lambda e: self.load_logs())
        ctk.CTkButton(top, text="Search", width=70, fg_color="#1E4528",
                      hover_color="#14301C", font=("Inter", 11, "bold"),
                      command=self.load_logs).pack(side="right", padx=5)
        ctk.CTkButton(top, text="↻", width=40, fg_color="#E0E0E0",
                      text_color="black", hover_color="#CCCCCC",
                      command=lambda: [self.log_search.delete(0, "end"), self.load_logs()]).pack(side="right")

        ctk.CTkLabel(frame, text="Shows all tool issuance and retrieval transactions.",
                     font=("Inter", 11), text_color="gray").pack(anchor="w", padx=20, pady=(0, 8))

        headers = ["TRN", "Type", "Tool Name", "Tag ID", "Borrower", "Borrow Date", "Return Date", "Status"]
        weights = [1,     1,      3,            2,       2,           2,             2,             1]
        self._log_weights = weights
        self._make_header(frame, headers, weights)

        self._log_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self._log_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        self.load_logs()

    def load_logs(self):
        scroll = self._log_scroll
        weights = self._log_weights
        for w in scroll.winfo_children():
            w.destroy()

        q = self.log_search.get().strip() if hasattr(self, "log_search") else ""
        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT tr.transaction_id, tr.type, t.name as tool_name,
                       IFNULL(t.tag_id,'Unassigned') as tag_id,
                       u.full_name,
                       DATE_FORMAT(DATE_ADD(tr.borrow_date, INTERVAL 8 HOUR),
                           '%b %d, %Y %I:%M %p') as borrow_date,
                       IF(tr.return_date IS NOT NULL,
                           DATE_FORMAT(DATE_ADD(tr.return_date, INTERVAL 8 HOUR),
                               '%b %d, %Y %I:%M %p'), '—') as return_date,
                       tr.status
                FROM transaction tr
                JOIN tool t ON tr.tool_id = t.tool_id
                JOIN user u ON tr.user_id = u.user_id
            """
            params = []
            if q:
                sql += " WHERE u.full_name LIKE %s OR t.name LIKE %s OR t.tag_id LIKE %s"
                params = [f"%{q}%", f"%{q}%", f"%{q}%"]
            sql += " ORDER BY tr.borrow_date DESC LIMIT 200"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            if not rows:
                ctk.CTkLabel(scroll, text="No transaction records found.",
                             text_color="gray").pack(pady=20)
                return

            for i, row in enumerate(rows):
                vals = [
                    str(row["transaction_id"]), row["type"], row["tool_name"],
                    row["tag_id"], row["full_name"],
                    row["borrow_date"], row["return_date"], row["status"],
                ]
                bg = "#F9FAFB" if i % 2 == 0 else "white"
                rf = self._make_row(scroll, vals, weights, bg)
                for col, (val, w) in enumerate(zip(vals, weights)):
                    color = "#1A1A1A"
                    if col == 7:
                        color = "#D8000C" if val == "Active" else "#2ECC71"
                    ctk.CTkLabel(rf, text=val, font=("Inter", 11),
                                 text_color=color).grid(row=0, column=col, padx=8, pady=6, sticky="w")
        except Exception as e:
            ctk.CTkLabel(scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    # ------------------------------------------
    # TAB 2: Audit Records  (fixed date format)
    # ------------------------------------------
    def render_audit_tab(self):
        frame = ctk.CTkFrame(self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(top, text="Audit Trail — Borrow & Return Records",
                     font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(side="left")

        filter_row = ctk.CTkFrame(frame, fg_color="transparent")
        filter_row.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(filter_row, text="Filter by Status:",
                     font=("Inter", 12), text_color="gray").pack(side="left")
        self.audit_filter = ctk.CTkOptionMenu(
            filter_row, values=["All", "Active", "Returned"],
            width=120, fg_color="#F9FAFB", text_color="black"
        )
        self.audit_filter.pack(side="left", padx=8)

        self.audit_search = ctk.CTkEntry(
            filter_row, placeholder_text="Search name / tool...", width=200)
        self.audit_search.pack(side="left", padx=(0, 5))
        self.audit_search.bind("<Return>", lambda e: self.load_audit())

        ctk.CTkButton(filter_row, text="Run Audit", width=80,
                      fg_color="#F1C40F", text_color="black", hover_color="#D4AC0D",
                      font=("Inter", 11, "bold"),
                      command=self.load_audit).pack(side="left", padx=5)
        ctk.CTkButton(filter_row, text="↻ Reset", width=70,
                      fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC",
                      
                      command=lambda: [self.audit_search.delete(0, "end"),
                                       self.audit_filter.set("All"), self.load_audit()]).pack(side="left")

        self.audit_summary = ctk.CTkLabel(frame, text="", font=("Inter", 11, "bold"),
                                          text_color="#1E4528")
        self.audit_summary.pack(anchor="w", padx=20, pady=(0, 5))

        # FIXED DATE FORMAT: %b %d, %Y %I:%M %p → "May 17, 2024 08:45 AM"
        headers = ["TRN", "Borrower", "Tool", "Tag ID", "Borrowed On",
                   "Return Date", "Cond@Borrow", "Cond@Return", "Status"]
        weights = [1,     2,          2,      2,       2,
                   2,           2,            2,           1]
        self._audit_weights = weights
        self._make_header(frame, headers, weights)

        self._audit_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self._audit_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        self.load_audit()

    def load_audit(self):
        scroll = self._audit_scroll
        weights = self._audit_weights
        for w in scroll.winfo_children():
            w.destroy()

        status_filter = self.audit_filter.get() if hasattr(self, "audit_filter") else "All"
        q = self.audit_search.get().strip() if hasattr(self, "audit_search") else ""

        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor(dictionary=True)
            # DATE FORMAT FIXED: removed %b%d%Y format — now uses full readable timestamp
            sql = """
                SELECT tr.transaction_id, u.full_name, t.name as tool_name,
                       IFNULL(t.tag_id,'Unassigned') as tag_id,
                       DATE_FORMAT(DATE_ADD(tr.borrow_date, INTERVAL 8 HOUR),
                           '%b %d, %Y %I:%M %p') as borrow_date,
                       IF(tr.return_date IS NOT NULL,
                           DATE_FORMAT(DATE_ADD(tr.return_date, INTERVAL 8 HOUR),
                               '%b %d, %Y %I:%M %p'), '—') as return_date,
                       IFNULL(tr.condition_at_borrow,'N/A') as cond_borrow,
                       IFNULL(tr.condition_at_return,'N/A')  as cond_return,
                       tr.status
                FROM transaction tr
                JOIN tool t ON tr.tool_id = t.tool_id
                JOIN user u ON tr.user_id = u.user_id
                WHERE 1=1
            """
            params = []
            if status_filter != "All":
                sql += " AND tr.status = %s"
                params.append(status_filter)
            if q:
                sql += " AND (u.full_name LIKE %s OR t.name LIKE %s)"
                params += [f"%{q}%", f"%{q}%"]
            sql += " ORDER BY tr.borrow_date DESC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            total = len(rows)
            active = sum(1 for r in rows if r["status"] == "Active")
            returned = sum(1 for r in rows if r["status"] == "Returned")
            self.audit_summary.configure(
                text=f"  Total: {total}   |   Active: {active}   |   Returned: {returned}"
            )

            if not rows:
                ctk.CTkLabel(scroll, text="No records match the audit criteria.",
                             text_color="gray").pack(pady=20)
                return

            for i, row in enumerate(rows):
                vals = [
                    str(row["transaction_id"]), row["full_name"], row["tool_name"],
                    row["tag_id"], row["borrow_date"], row["return_date"],
                    row["cond_borrow"], row["cond_return"], row["status"],
                ]
                bg = "#FFF8F0" if row["status"] == "Active" else (
                    "#F9FAFB" if i % 2 == 0 else "white")
                rf = self._make_row(scroll, vals, weights, bg)
                for col, (val, w) in enumerate(zip(vals, weights)):
                    color = "#1A1A1A"
                    if col == 8:
                        color = "#D8000C" if val == "Active" else "#2ECC71"
                    ctk.CTkLabel(rf, text=val, font=("Inter", 11),
                                 text_color=color).grid(row=0, column=col, padx=8, pady=6, sticky="w")
        except Exception as e:
            ctk.CTkLabel(scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    # ------------------------------------------
    # TAB 3: Activity Log  (system_logs — ALL movements)
    # ------------------------------------------
    def render_activity_tab(self):
        frame = ctk.CTkFrame(self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(top, text="Full System Activity Log",
                     font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(side="left")

        ctk.CTkLabel(frame,
                     text="Records every login, logout, module visit, edit, search, and transaction. "
                          "Auto-pruned to the latest 10,000 entries to protect the 1 GB database.",
                     font=("Inter", 11), text_color="gray",
                     wraplength=900, justify="left").pack(anchor="w", padx=20, pady=(0, 8))

        filter_row = ctk.CTkFrame(frame, fg_color="transparent")
        filter_row.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(filter_row, text="Module:", font=("Inter", 12), text_color="gray").pack(side="left")
        self.act_module_filter = ctk.CTkOptionMenu(
            filter_row,
            values=["All", "Authentication", "Dashboard", "Inventory", "Projects",
                    "Tagging", "Issuance & Retrieval", "Tracking & Accountability",
                    "Reports", "Maintenance", "Role Management", "Profile"],
            width=180, fg_color="#F9FAFB", text_color="black"
        )
        self.act_module_filter.pack(side="left", padx=8)

        self.act_search = ctk.CTkEntry(
            filter_row, placeholder_text="Search user or details...", width=200)
        self.act_search.pack(side="left", padx=(0, 5))
        self.act_search.bind("<Return>", lambda e: self.load_activity())

        ctk.CTkButton(filter_row, text="Search", width=80,
                      fg_color="#1E4528", hover_color="#14301C",
                      font=("Inter", 11, "bold"),
                      command=self.load_activity).pack(side="left", padx=5)
        ctk.CTkButton(filter_row, text="↻ Reset", width=70,
                      fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC",
                      
                      command=lambda: [
                          self.act_search.delete(0, "end"),
                          self.act_module_filter.set("All"),
                          self.load_activity()
                      ]).pack(side="left")

        self.act_summary = ctk.CTkLabel(frame, text="", font=("Inter", 11, "bold"),
                                        text_color="#1E4528")
        self.act_summary.pack(anchor="w", padx=20, pady=(0, 5))

        headers = ["Log ID", "Timestamp", "Employee", "Action Type", "Module", "Details"]
        weights = [1,        2,           2,          2,             2,        4]
        self._act_weights = weights
        self._make_header(frame, headers, weights)

        self._act_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self._act_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        self.load_activity()

    def load_activity(self):
        scroll = self._act_scroll
        weights = self._act_weights
        for w in scroll.winfo_children():
            w.destroy()

        module_filter = self.act_module_filter.get() if hasattr(self, "act_module_filter") else "All"
        q = self.act_search.get().strip() if hasattr(self, "act_search") else ""

        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT sl.log_id,
                       DATE_FORMAT(DATE_ADD(sl.timestamp, INTERVAL 8 HOUR),
                           '%b %d, %Y %I:%M %p') as ts,
                       IFNULL(u.full_name, CONCAT('UID:', sl.user_id)) as employee,
                       sl.action_type, sl.module, IFNULL(sl.details,'—') as details
                FROM system_logs sl
                LEFT JOIN user u ON sl.user_id = u.user_id
                WHERE 1=1
            """
            params = []
            if module_filter != "All":
                sql += " AND sl.module = %s"
                params.append(module_filter)
            if q:
                sql += " AND (u.full_name LIKE %s OR sl.details LIKE %s OR sl.action_type LIKE %s)"
                params += [f"%{q}%", f"%{q}%", f"%{q}%"]
            sql += " ORDER BY sl.log_id DESC LIMIT 500"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            self.act_summary.configure(text=f"  Showing {len(rows)} entries (max 500 per query)")

            if not rows:
                ctk.CTkLabel(scroll, text="No activity records found.",
                             text_color="gray").pack(pady=20)
                return

            action_colors = {
                "Login":    "#2ECC71",
                "Logout":   "#E74C3C",
                "Added":    "#3498DB",
                "Edited":   "#F39C12",
                "Archived": "#95A5A6",
                "Searched": "#9B59B6",
                "Viewed":   "#1A1A1A",
                "Issued":   "#27AE60",
                "Retrieved":"#16A085",
                "Submitted":"#2980B9",
                "Approved": "#27AE60",
                "Flagged":  "#D8000C",
                "Resolved": "#2ECC71",
            }

            for i, row in enumerate(rows):
                vals = [
                    str(row["log_id"]), row["ts"], row["employee"],
                    row["action_type"], row["module"], row["details"],
                ]
                bg = "#F9FAFB" if i % 2 == 0 else "white"
                rf = self._make_row(scroll, vals, weights, bg)
                for col, (val, w) in enumerate(zip(vals, weights)):
                    color = "#1A1A1A"
                    if col == 3:  # Action Type column — color-coded
                        color = action_colors.get(val, "#555555")
                    font_style = "bold" if col == 3 else "normal"
                    ctk.CTkLabel(rf, text=val, font=("Inter", 10, font_style),
                                 text_color=color).grid(row=0, column=col, padx=8, pady=5, sticky="w")
        except Exception as e:
            ctk.CTkLabel(scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    # ------------------------------------------
    # TAB 4: Manage Issues  (redesigned, cleaner layout)
    # ------------------------------------------
    def render_issues_tab(self):
        frame = ctk.CTkFrame(self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # ── Header ──
        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(top, text="Tool Issue Management",
                     font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(side="left")

        ctk.CTkLabel(frame,
                     text="Flag damaged or lost tools, track discrepancies, and manage resolutions. "
                          "Flagging a tool automatically updates its condition in the inventory.",
                     font=("Inter", 11), text_color="gray",
                     wraplength=900, justify="left").pack(anchor="w", padx=20, pady=(0, 10))

        # ── Flag Form (card) ──
        flag_card = ctk.CTkFrame(frame, fg_color="#F9FAFB", corner_radius=10)
        flag_card.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(flag_card, text="🚩  Flag a Tool Issue",
                     font=("Inter", 13, "bold"), text_color="#D8000C").pack(anchor="w", padx=15, pady=(12, 8))

        form_grid = ctk.CTkFrame(flag_card, fg_color="transparent")
        form_grid.pack(fill="x", padx=15, pady=(0, 8))
        form_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Row 1: Tool ID | Reported By | Issue Type | blank
        ctk.CTkLabel(form_grid, text="Tool PID or Tag ID", font=("Inter", 11, "bold"),
                     text_color="#1A1A1A").grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(form_grid, text="Reported By (Employee ID)", font=("Inter", 11, "bold"),
                     text_color="#1A1A1A").grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(form_grid, text="Issue / Condition Type", font=("Inter", 11, "bold"),
                     text_color="#1A1A1A").grid(row=0, column=2, sticky="w", padx=5)

        self.flag_tool_id = ctk.CTkEntry(form_grid, placeholder_text="e.g., TAG-003 or PID 42",
                                          )
        self.flag_tool_id.grid(row=1, column=0, sticky="ew", padx=5, pady=(3, 8))
        self.flag_reported_by = ctk.CTkEntry(form_grid, placeholder_text="e.g., EMP-001",
                                              )
        self.flag_reported_by.grid(row=1, column=1, sticky="ew", padx=5, pady=(3, 8))
        self.flag_condition = ctk.CTkOptionMenu(
            form_grid,
            values=["Damaged", "Lost", "Needs Repair", "Discrepancy",
                    "Missing Parts", "Stolen", "Other"],
            fg_color="#F9FAFB", text_color="black"
        )
        self.flag_condition.grid(row=1, column=2, sticky="ew", padx=5, pady=(3, 8))

        # Row 2: Notes + Submit button
        notes_row = ctk.CTkFrame(flag_card, fg_color="transparent")
        notes_row.pack(fill="x", padx=15, pady=(0, 12))
        notes_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(notes_row, text="Issue Description / Notes",
                     font=("Inter", 11, "bold"), text_color="#1A1A1A").grid(
            row=0, column=0, sticky="w", pady=(0, 3))
        self.flag_notes = ctk.CTkEntry(notes_row,
                                       placeholder_text="Describe the issue in detail...",
                                       )
        self.flag_notes.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        ctk.CTkButton(notes_row, text="Submit Flag", width=130,
                      fg_color="#D8000C", hover_color="#B00000",
                      text_color="white", font=("Inter", 12, "bold"),
                      command=self.submit_flag).grid(row=1, column=1, padx=(0, 0))

        # ── Filter row for the issues table ──
        filter_row = ctk.CTkFrame(frame, fg_color="transparent")
        filter_row.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkLabel(filter_row, text="Show:", font=("Inter", 12), text_color="gray").pack(side="left")
        self.issues_filter = ctk.CTkOptionMenu(
            filter_row, values=["All Issues", "Open (Pending)", "Resolved"],
            width=150, fg_color="#F9FAFB", text_color="black"
        )
        self.issues_filter.pack(side="left", padx=8)

        self.issues_search = ctk.CTkEntry(filter_row, placeholder_text="Search tool or reporter...",
                                          width=200)
        self.issues_search.pack(side="left", padx=(0, 5))
        self.issues_search.bind("<Return>", lambda e: self.load_issues())

        ctk.CTkButton(filter_row, text="Filter", width=70, fg_color="#1E4528",
                      hover_color="#14301C", font=("Inter", 11, "bold"),
                      command=self.load_issues).pack(side="left", padx=5)
        ctk.CTkButton(filter_row, text="↻ Reset", width=75,
                      fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC",
                      
                      command=lambda: [
                          self.issues_search.delete(0, "end"),
                          self.issues_filter.set("All Issues"),
                          self.load_issues()
                      ]).pack(side="left")

        self.issues_summary = ctk.CTkLabel(frame, text="", font=("Inter", 11, "bold"),
                                           text_color="#1E4528")
        self.issues_summary.pack(anchor="w", padx=20, pady=(0, 5))

        # ── Issues table ──
        headers = ["#", "Tool Name", "Reported By", "Issue Type", "Description",
                   "Flagged At", "Status"]
        weights = [1,   2,           2,             2,            3,
                   2,          1]
        self._issues_weights = weights
        self._make_header(frame, headers, weights)

        self._issues_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self._issues_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        self.load_issues()

    def submit_flag(self):
        tool_input = self.flag_tool_id.get().strip()
        reported_by = self.flag_reported_by.get().strip()
        condition = self.flag_condition.get()
        notes = self.flag_notes.get().strip()

        if not tool_input or not reported_by:
            messagebox.showerror("Error", "Tool ID/Tag and Reported By are required.",
                                 parent=self.winfo_toplevel())
            return

        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor(dictionary=True)
            if tool_input.isdigit():
                cursor.execute("SELECT tool_id, name FROM tool WHERE tool_id = %s", (tool_input,))
            else:
                cursor.execute("SELECT tool_id, name FROM tool WHERE tag_id = %s", (tool_input,))
            tool = cursor.fetchone()
            if not tool:
                messagebox.showerror("Not Found", "No tool found with that PID or Tag ID.",
                                     parent=self.winfo_toplevel())
                return

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_issues (
                    issue_id INT AUTO_INCREMENT PRIMARY KEY,
                    tool_id INT NOT NULL,
                    reported_by VARCHAR(100),
                    condition_flag VARCHAR(100),
                    notes TEXT,
                    flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_resolved TINYINT(1) DEFAULT 0,
                    FOREIGN KEY (tool_id) REFERENCES tool(tool_id)
                )
            """)
            cursor.execute("""
                INSERT INTO tool_issues (tool_id, reported_by, condition_flag, notes)
                VALUES (%s, %s, %s, %s)
            """, (tool["tool_id"], reported_by, condition, notes or "No additional details."))
            cursor.execute(
                "UPDATE tool SET `condition` = %s WHERE tool_id = %s",
                (condition, tool["tool_id"])
            )
            conn.commit()

            uid = self.user_info.get("user_id")
            if uid:
                log_action(uid, "Flagged", "Tracking & Accountability",
                           f"Flagged tool '{tool['name']}' (PID: {tool['tool_id']}) — {condition}: {notes}")

            messagebox.showinfo("Flagged",
                                f"Tool '{tool['name']}' has been flagged.\n"
                                f"Its condition has been updated to '{condition}' in the inventory.",
                                parent=self.winfo_toplevel())
            self.flag_tool_id.delete(0, "end")
            self.flag_reported_by.delete(0, "end")
            self.flag_notes.delete(0, "end")
            self.load_issues()
        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=self.winfo_toplevel())
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def load_issues(self):
        scroll = self._issues_scroll
        weights = self._issues_weights
        for w in scroll.winfo_children():
            w.destroy()

        status_filter = self.issues_filter.get() if hasattr(self, "issues_filter") else "All Issues"
        q = self.issues_search.get().strip() if hasattr(self, "issues_search") else ""

        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_issues (
                    issue_id INT AUTO_INCREMENT PRIMARY KEY,
                    tool_id INT NOT NULL,
                    reported_by VARCHAR(100),
                    condition_flag VARCHAR(100),
                    notes TEXT,
                    flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_resolved TINYINT(1) DEFAULT 0,
                    FOREIGN KEY (tool_id) REFERENCES tool(tool_id)
                )
            """)
            sql = """
                SELECT ti.issue_id, t.name as tool_name, ti.reported_by,
                       ti.condition_flag, IFNULL(ti.notes,'—') as notes,
                       DATE_FORMAT(DATE_ADD(ti.flagged_at, INTERVAL 8 HOUR),
                           '%b %d, %Y %I:%M %p') as flagged_at,
                       ti.is_resolved
                FROM tool_issues ti
                JOIN tool t ON ti.tool_id = t.tool_id
                WHERE 1=1
            """
            params = []
            if status_filter == "Open (Pending)":
                sql += " AND ti.is_resolved = 0"
            elif status_filter == "Resolved":
                sql += " AND ti.is_resolved = 1"
            if q:
                sql += " AND (t.name LIKE %s OR ti.reported_by LIKE %s OR ti.condition_flag LIKE %s)"
                params += [f"%{q}%", f"%{q}%", f"%{q}%"]
            sql += " ORDER BY ti.flagged_at DESC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            total = len(rows)
            open_cnt = sum(1 for r in rows if not r["is_resolved"])
            resolved_cnt = total - open_cnt
            if hasattr(self, "issues_summary"):
                self.issues_summary.configure(
                    text=f"  Total: {total}   |   Open: {open_cnt}   |   Resolved: {resolved_cnt}"
                )

            if not rows:
                ctk.CTkLabel(scroll, text="No issues found.", text_color="gray").pack(pady=20)
                return

            condition_colors = {
                "Damaged": "#E74C3C",
                "Lost": "#C0392B",
                "Needs Repair": "#F39C12",
                "Discrepancy": "#8E44AD",
                "Stolen": "#C0392B",
                "Missing Parts": "#D35400",
                "Other": "#7F8C8D",
            }

            for i, row in enumerate(rows):
                resolved_text = "✓ Resolved" if row["is_resolved"] else "⚠ Pending"
                vals = [
                    str(row["issue_id"]), row["tool_name"], row["reported_by"],
                    row["condition_flag"], row["notes"], row["flagged_at"], resolved_text,
                ]
                bg = "#F0FFF0" if row["is_resolved"] else ("#FFF8F0" if i % 2 == 0 else "#FFF3F3")
                rf = self._make_row(scroll, vals, weights, bg)
                rf.bind("<Button-1>", lambda e, r=row: self.open_issue_modal(r))
                for col, (val, w) in enumerate(zip(vals, weights)):
                    color = "#1A1A1A"
                    if col == 3:
                        color = condition_colors.get(val, "#D35400")
                    elif col == 6:
                        color = "#2ECC71" if "Resolved" in val else "#D8000C"
                    font_style = "bold" if col in (3, 6) else "normal"
                    lbl = ctk.CTkLabel(rf, text=val,
                                       font=("Inter", 11, font_style), text_color=color)
                    lbl.grid(row=0, column=col, padx=8, pady=6, sticky="w")
                    lbl.bind("<Button-1>", lambda e, r=row: self.open_issue_modal(r))
        except Exception as e:
            ctk.CTkLabel(scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def open_issue_modal(self, row):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Issue #{row['issue_id']} — {row['tool_name']}")
        modal.geometry("480x400")
        modal.configure(fg_color="white")
        modal.attributes("-topmost", True)
        modal.grab_set()
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - 240
        y = (modal.winfo_screenheight() // 2) - 200
        modal.geometry(f"+{x}+{y}")

        # Header
        status_color = "#2ECC71" if row["is_resolved"] else "#D8000C"
        status_text = "✓ RESOLVED" if row["is_resolved"] else "⚠ PENDING"
        ctk.CTkLabel(modal, text=f"Issue #{row['issue_id']}: {row['tool_name']}",
                     font=("Inter", 15, "bold"), text_color="black").pack(pady=(20, 3))
        ctk.CTkLabel(modal, text=f"{status_text}  |  Flagged by: {row['reported_by']}",
                     font=("Inter", 11, "bold"), text_color=status_color).pack(pady=(0, 5))
        ctk.CTkLabel(modal, text=f"Flagged At: {row['flagged_at']}",
                     font=("Inter", 11), text_color="gray").pack(pady=(0, 10))

        # Details card
        detail_card = ctk.CTkFrame(modal, fg_color="#F9FAFB", corner_radius=8)
        detail_card.pack(fill="x", padx=25, pady=(0, 10))
        ctk.CTkLabel(detail_card, text=f"Issue Type:  {row['condition_flag']}",
                     font=("Inter", 12, "bold"), text_color="#D35400").pack(anchor="w", padx=15, pady=(10, 3))
        ctk.CTkLabel(detail_card, text=f"Description:  {row['notes']}",
                     font=("Inter", 11), text_color="#1A1A1A",
                     wraplength=400, justify="left").pack(anchor="w", padx=15, pady=(0, 10))

        form = ctk.CTkFrame(modal, fg_color="transparent")
        form.pack(fill="x", padx=25)

        ctk.CTkLabel(form, text="Update Condition:", font=("Inter", 11, "bold"),
                     text_color="#1A1A1A").pack(anchor="w")
        cond_menu = ctk.CTkOptionMenu(
            form, values=["Good", "Needs Repair", "Damaged", "Lost"],
            fg_color="#F9FAFB", text_color="black")
        cond_menu.set(row["condition_flag"] if row["condition_flag"] in
                      ["Good", "Needs Repair", "Damaged", "Lost"] else "Needs Repair")
        cond_menu.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(form, text="Resolution Notes:", font=("Inter", 11, "bold"),
                     text_color="#1A1A1A").pack(anchor="w")
        notes_entry = ctk.CTkEntry(form, placeholder_text="e.g., Sent to repair, replaced, etc.",
                                   )
        notes_entry.pack(fill="x", pady=(5, 10))

        def resolve_issue():
            conn = get_connection()
            if not conn:
                return
            try:
                cursor = conn.cursor()
                resolution = notes_entry.get().strip() or "Marked resolved by Admin."
                cursor.execute("""
                    UPDATE tool_issues
                    SET is_resolved = 1, condition_flag = %s,
                        notes = CONCAT(IFNULL(notes,''), ' | Resolution: ', %s)
                    WHERE issue_id = %s
                """, (cond_menu.get(), resolution, row["issue_id"]))
                cursor.execute("""
                    UPDATE tool SET `condition` = %s
                    WHERE tool_id = (SELECT tool_id FROM tool_issues WHERE issue_id = %s)
                """, (cond_menu.get(), row["issue_id"]))
                conn.commit()

                uid = self.user_info.get("user_id")
                if uid:
                    log_action(uid, "Resolved", "Tracking & Accountability",
                               f"Resolved issue #{row['issue_id']} for '{row['tool_name']}'. "
                               f"New condition: {cond_menu.get()}")

                messagebox.showinfo("Resolved", "Issue marked as resolved and inventory updated.",
                                    parent=modal)
                modal.destroy()
                self.load_issues()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=modal)
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()

        btn_row = ctk.CTkFrame(modal, fg_color="transparent")
        btn_row.pack(fill="x", padx=25, pady=(5, 20))
        ctk.CTkButton(btn_row, text="✓ Mark Resolved & Update Inventory",
                      fg_color="#1E4528", hover_color="#14301C",
                      command=resolve_issue).pack(side="left", padx=(0, 10), fill="x", expand=True)
        ctk.CTkButton(btn_row, text="Close", fg_color="#E0E0E0",
                      text_color="black", hover_color="#CCCCCC", width=80,
                      command=modal.destroy).pack(side="right")

    # ==========================================
    # STAFF VIEW: Personal history only
    # ==========================================
    def build_staff_view(self):
        frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(top, text="My Borrowing & Return History",
                     font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(side="left")
        ctk.CTkLabel(frame, text="Showing transactions associated with your account only.",
                     font=("Inter", 11), text_color="gray").pack(anchor="w", padx=20, pady=(0, 10))

        headers = ["TRN", "Tool Name", "Tag ID", "Borrow Date",
                   "Return Date", "Cond@Return", "Status"]
        weights = [1,     2,           2,        2,
                   2,             2,             1]
        self._make_header(frame, headers, weights)

        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(5, 20))

        user_id = self.user_info.get("user_id")
        if not user_id:
            emp_id = self.user_info.get("employee_id")
            if emp_id:
                conn2 = get_connection()
                if conn2:
                    try:
                        c2 = conn2.cursor(dictionary=True)
                        c2.execute("SELECT user_id FROM user WHERE employee_id = %s", (emp_id,))
                        row2 = c2.fetchone()
                        if row2:
                            user_id = row2["user_id"]
                    except Exception:
                        pass
                    finally:
                        if conn2.is_connected():
                            c2.close()
                            conn2.close()

        if not user_id:
            ctk.CTkLabel(scroll, text="Could not resolve user session. Please log out and log back in.",
                         text_color="red").pack(pady=20)
            return

        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT tr.transaction_id, t.name as tool_name,
                       IFNULL(t.tag_id,'Unassigned') as tag_id,
                       DATE_FORMAT(DATE_ADD(tr.borrow_date, INTERVAL 8 HOUR),
                           '%b %d, %Y %I:%M %p') as borrow_date,
                       IF(tr.return_date IS NOT NULL,
                           DATE_FORMAT(DATE_ADD(tr.return_date, INTERVAL 8 HOUR),
                               '%b %d, %Y %I:%M %p'), '—') as return_date,
                       IFNULL(tr.condition_at_return,'—') as cond_return,
                       tr.status
                FROM transaction tr
                JOIN tool t ON tr.tool_id = t.tool_id
                WHERE tr.user_id = %s
                ORDER BY tr.borrow_date DESC
            """, (user_id,))
            rows = cursor.fetchall()

            if not rows:
                ctk.CTkLabel(scroll, text="You have no borrowing history.",
                             text_color="gray").pack(pady=20)
                return

            for i, row in enumerate(rows):
                vals = [
                    str(row["transaction_id"]), row["tool_name"], row["tag_id"],
                    row["borrow_date"], row["return_date"],
                    row["cond_return"], row["status"],
                ]
                bg = "#F9FAFB" if i % 2 == 0 else "white"
                rf = self._make_row(scroll, vals, weights, bg)
                for col, (val, w) in enumerate(zip(vals, weights)):
                    color = "#1A1A1A"
                    if col == 6:
                        color = "#D8000C" if val == "Active" else "#2ECC71"
                    ctk.CTkLabel(rf, text=val, font=("Inter", 11),
                                 text_color=color).grid(row=0, column=col, padx=8, pady=6, sticky="w")
        except Exception as e:
            ctk.CTkLabel(scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()