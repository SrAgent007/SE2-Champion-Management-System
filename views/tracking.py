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
    # MODAL FIX (Deployment Details)
    # ==========================================
    def view_deployment_details(self, row):
        modal = ctk.CTkToplevel(self)
        trans_id = row.get("transaction_id", "N/A")
        modal.title(f"Deployment History - Receipt #{trans_id}")
        
        modal.geometry("500x600")
        modal.minsize(500, 500)
        modal.attributes("-topmost", True)
        modal.grab_set()

        # Bottom anchored button (always visible)
        bottom_frame = ctk.CTkFrame(modal, fg_color="transparent")
        bottom_frame.pack(fill="x", side="bottom", padx=20, pady=20)
        ctk.CTkButton(
            bottom_frame, 
            text="🖨️ Reprint Receipt", 
            command=lambda: messagebox.showinfo("Print", "Receipt sent to printer.", parent=modal),
            fg_color="#1E4528", 
            hover_color="#14301C",
            height=40
        ).pack(fill="x")

        # Scrollable container for infinite items
        scroll_container = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=20, pady=(20, 0))

        ctk.CTkLabel(scroll_container, text="Champion Fine Tooling", font=("Inter", 20, "bold"), text_color="#1E4528").pack(pady=(0,2))
        ctk.CTkLabel(scroll_container, text="Official Issuance Receipt", font=("Inter", 14), text_color="gray").pack(pady=(0,20))

        issued_to = row.get("full_name", self.user_info.get("username", "N/A"))
        trans_type = row.get("type", "Issuance")

        details = (
            f"Transaction ID: {trans_id}\n"
            f"Type: {trans_type}\n"
            f"Date Out: {row.get('borrow_date', 'N/A')}\n"
            f"Date In: {row.get('return_date', 'N/A')}\n"
            f"Issued To: {issued_to}\n"
        )
        ctk.CTkLabel(scroll_container, text=details, justify="left", font=("Inter", 13)).pack(anchor="w", pady=(0,20))

        ctk.CTkLabel(scroll_container, text="Items Deployed:", font=("Inter", 13, "bold")).pack(anchor="w", pady=(0,5))
        
        tool_name = row.get("tool_name", "N/A")
        tag_id = row.get("tag_id", "N/A")
        status = row.get("status", "N/A")
        ctk.CTkLabel(scroll_container, text=f"• {tool_name} (Tag: {tag_id}) - {status}", font=("Inter", 12)).pack(anchor="w", padx=10, pady=2)

    # ==========================================
    # ADMIN VIEW
    # ==========================================
    def build_admin_view(self):
        notebook_frame = ctk.CTkFrame(self, fg_color="transparent")
        notebook_frame.grid(row=0, column=0, sticky="nsew")
        notebook_frame.grid_columnconfigure(0, weight=1)
        notebook_frame.grid_rowconfigure(1, weight=1)

        tab_bar = ctk.CTkFrame(notebook_frame, fg_color="white", corner_radius=10, height=50)
        tab_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tab_bar.pack_propagate(False)

        self.tab_content = ctk.CTkFrame(notebook_frame, fg_color="transparent")
        self.tab_content.grid(row=1, column=0, sticky="nsew")
        self.tab_content.grid_columnconfigure(0, weight=1)
        self.tab_content.grid_rowconfigure(0, weight=1)

        # Removed Manage Issues, Kept Activity Log
        tabs = [
            ("Borrow/Return Logs", "logs"),
            ("Audit Records",      "audit"),
            ("Activity Log",       "activity"),
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
            self.render_activity_tab() # Restored!

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

        ctk.CTkLabel(frame, text="Chronological History of all equipment movements.",
                     font=("Inter", 11, "italic"), text_color="gray").pack(anchor="w", padx=20, pady=(0, 8))

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
                
                def on_click(e, r=row):
                    self.view_deployment_details(r)
                    
                rf.bind("<Button-1>", on_click)
                rf.configure(cursor="hand2")

                for col, (val, w) in enumerate(zip(vals, weights)):
                    color = "#1A1A1A"
                    if col == 7:
                        color = "#D8000C" if val == "Active" else "#2ECC71"
                    lbl = ctk.CTkLabel(rf, text=val, font=("Inter", 11),
                                 text_color=color, cursor="hand2")
                    lbl.grid(row=0, column=col, padx=8, pady=6, sticky="w")
                    lbl.bind("<Button-1>", on_click)
        except Exception as e:
            ctk.CTkLabel(scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    # ------------------------------------------
    # TAB 2: Audit Records
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
    # TAB 3: Activity Log (Restored!)
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
                          "Auto-pruned to the latest 10,000 entries to protect the database.",
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
                    if col == 3:  
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
        ctk.CTkLabel(frame, text="Click on any transaction record below to view its Deployment Receipt.",
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
                
                def on_click(e, r=row):
                    self.view_deployment_details(r)
                    
                rf.bind("<Button-1>", on_click)
                rf.configure(cursor="hand2")

                for col, (val, w) in enumerate(zip(vals, weights)):
                    color = "#1A1A1A"
                    if col == 6:
                        color = "#D8000C" if val == "Active" else "#2ECC71"
                    lbl = ctk.CTkLabel(rf, text=val, font=("Inter", 11),
                                 text_color=color, cursor="hand2")
                    lbl.grid(row=0, column=col, padx=8, pady=6, sticky="w")
                    lbl.bind("<Button-1>", on_click)
        except Exception as e:
            ctk.CTkLabel(scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()