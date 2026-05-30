import customtkinter as ctk
from tkinter import messagebox
from database import get_connection, log_action
from datetime import datetime

class MaintenanceView(ctk.CTkFrame):
    def __init__(self, parent, user_info=None):
        super().__init__(parent, fg_color="transparent")

        self.user_info = user_info or {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.build_view()

        uid = self.user_info.get("user_id")
        if uid:
            log_action(uid, "Viewed", "Maintenance", "Opened Maintenance module")

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

    def _ensure_user_archive_columns(self, cursor):
        cursor.execute("SHOW COLUMNS FROM `user` LIKE 'status'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE `user` ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'Active'")

        cursor.execute("SHOW COLUMNS FROM `user` LIKE 'archived_at'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE `user` ADD COLUMN archived_at DATETIME NULL")

    def build_view(self):
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

        tabs = [
            ("Active Issues & Repairs", "issues"),
            ("Archived Tools",          "tools"),
            ("Archived Employees",      "employees"),
            ("Archived Projects",       "projects"),
        ]

        self.tab_buttons = {}
        for text, key in tabs:
            btn = ctk.CTkButton(
                tab_bar, text=text,
                fg_color="#1E4528" if key == "issues" else "transparent",
                text_color="white" if key == "issues" else "#1A1A1A",
                hover_color="#2A6038",
                font=("Inter", 12, "bold"),
                command=lambda k=key: self.switch_tab(k, tabs)
            )
            btn.pack(side="left", padx=10, pady=8)
            self.tab_buttons[key] = btn

        self.render_issues_tab()

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
        if key == "issues":
            self.render_issues_tab()
        elif key == "tools":
            self.render_tools_tab()
        elif key == "employees":
            self.render_employees_tab()
        elif key == "projects":
            self.render_projects_tab()

    # ------------------------------------------
    # TAB 1: Manage Issues (With Auto-Sync Fix)
    # ------------------------------------------
    def render_issues_tab(self):
        frame = ctk.CTkFrame(self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(top, text="Tool Issue Management",
                     font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(side="left")

        ctk.CTkLabel(frame,
                     text="Flag damaged or lost tools, track discrepancies, and manage resolutions. "
                          "Flagging a tool automatically updates its condition in the inventory.",
                     font=("Inter", 11), text_color="gray",
                     wraplength=900, justify="left").pack(anchor="w", padx=20, pady=(0, 10))

        flag_card = ctk.CTkFrame(frame, fg_color="#F9FAFB", corner_radius=10)
        flag_card.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(flag_card, text="🚩  Flag a Tool Issue",
                     font=("Inter", 13, "bold"), text_color="#D8000C").pack(anchor="w", padx=15, pady=(12, 8))

        form_grid = ctk.CTkFrame(flag_card, fg_color="transparent")
        form_grid.pack(fill="x", padx=15, pady=(0, 8))
        form_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(form_grid, text="Tool PID or Tag ID", font=("Inter", 11, "bold"),
                     text_color="#1A1A1A").grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(form_grid, text="Reported By (Employee ID)", font=("Inter", 11, "bold"),
                     text_color="#1A1A1A").grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(form_grid, text="Issue / Condition Type", font=("Inter", 11, "bold"),
                     text_color="#1A1A1A").grid(row=0, column=2, sticky="w", padx=5)

        self.flag_tool_id = ctk.CTkEntry(form_grid, placeholder_text="e.g., TAG-003 or PID 42")
        self.flag_tool_id.grid(row=1, column=0, sticky="ew", padx=5, pady=(3, 8))
        self.flag_reported_by = ctk.CTkEntry(form_grid, placeholder_text="e.g., EMP-001")
        self.flag_reported_by.grid(row=1, column=1, sticky="ew", padx=5, pady=(3, 8))
        self.flag_condition = ctk.CTkOptionMenu(
            form_grid,
            values=["Damaged", "Lost", "Needs Repair", "Discrepancy",
                    "Missing Parts", "Stolen", "Other"],
            fg_color="#F9FAFB", text_color="black"
        )
        self.flag_condition.grid(row=1, column=2, sticky="ew", padx=5, pady=(3, 8))

        notes_row = ctk.CTkFrame(flag_card, fg_color="transparent")
        notes_row.pack(fill="x", padx=15, pady=(0, 12))
        notes_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(notes_row, text="Issue Description / Notes",
                     font=("Inter", 11, "bold"), text_color="#1A1A1A").grid(
            row=0, column=0, sticky="w", pady=(0, 3))
        self.flag_notes = ctk.CTkEntry(notes_row, placeholder_text="Describe the issue in detail...")
        self.flag_notes.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        ctk.CTkButton(notes_row, text="Submit Flag", width=130,
                      fg_color="#D8000C", hover_color="#B00000",
                      text_color="white", font=("Inter", 12, "bold"),
                      command=self.submit_flag).grid(row=1, column=1, padx=(0, 0))

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
                log_action(uid, "Flagged", "Maintenance",
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
            conn.commit()

            # --- THE AUTO-SYNC FIX ---
            # Automatically generates a repair ticket for any tool marked Damaged/Needs Repair 
            # if it doesn't already have an open ticket. This perfectly syncs the Graph and this table!
            cursor.execute("""
                INSERT INTO tool_issues (tool_id, reported_by, condition_flag, notes, is_resolved)
                SELECT tool_id, 'System Auto-Sync', `condition`, 'Automatically flagged by system due to inventory condition.', 0
                FROM tool t
                WHERE `condition` IN ('Needs Repair', 'Damaged', 'Lost')
                  AND is_archived = 0
                  AND NOT EXISTS (
                      SELECT 1 FROM tool_issues ti WHERE ti.tool_id = t.tool_id AND ti.is_resolved = 0
                  )
            """)
            conn.commit()

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
            sql += " ORDER BY ti.is_resolved ASC, ti.flagged_at DESC"
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
                ctk.CTkLabel(scroll, text="No issues found. Inventory is clean.", text_color="gray").pack(pady=20)
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
                rf.configure(cursor="hand2")
                for col, (val, w) in enumerate(zip(vals, weights)):
                    color = "#1A1A1A"
                    if col == 3:
                        color = condition_colors.get(val, "#D35400")
                    elif col == 6:
                        color = "#2ECC71" if "Resolved" in val else "#D8000C"
                    font_style = "bold" if col in (3, 6) else "normal"
                    lbl = ctk.CTkLabel(rf, text=val,
                                       font=("Inter", 11, font_style), text_color=color, cursor="hand2")
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

        status_color = "#2ECC71" if row["is_resolved"] else "#D8000C"
        status_text = "✓ RESOLVED" if row["is_resolved"] else "⚠ PENDING"
        ctk.CTkLabel(modal, text=f"Issue #{row['issue_id']}: {row['tool_name']}",
                     font=("Inter", 15, "bold"), text_color="black").pack(pady=(20, 3))
        ctk.CTkLabel(modal, text=f"{status_text}  |  Flagged by: {row['reported_by']}",
                     font=("Inter", 11, "bold"), text_color=status_color).pack(pady=(0, 5))
        ctk.CTkLabel(modal, text=f"Flagged At: {row['flagged_at']}",
                     font=("Inter", 11), text_color="gray").pack(pady=(0, 10))

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
        notes_entry = ctk.CTkEntry(form, placeholder_text="e.g., Sent to repair, replaced, etc.")
        notes_entry.pack(fill="x", pady=(5, 10))

        def resolve_issue():
            conn = get_connection()
            if not conn: return
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
                    log_action(uid, "Resolved", "Maintenance",
                               f"Resolved issue #{row['issue_id']} for '{row['tool_name']}'. "
                               f"New condition: {cond_menu.get()}")

                messagebox.showinfo("Resolved", "Issue marked as resolved and inventory updated.", parent=modal)
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

    # ------------------------------------------
    # TAB 2: Archived Tools
    # ------------------------------------------
    def render_tools_tab(self):
        frame = ctk.CTkFrame(self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(top, text="Archived & Decommissioned Tools",
                     font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(side="left")

        headers = ["Tool ID", "Name", "Category", "Qty", "Archived At", "Action"]
        weights = [1, 3, 2, 1, 2, 1]
        self._tools_weights = weights
        self._make_header(frame, headers, weights)

        self._tools_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self._tools_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        self.load_archived_tools()

    def load_archived_tools(self):
        for w in self._tools_scroll.winfo_children(): w.destroy()
        conn = get_connection()
        if not conn: return
        try:
            cursor = conn.cursor(dictionary=True)
            # Fetch exact timestamps and include quantity_total from inventory
            cursor.execute("""
                SELECT t.tool_id, t.name, t.category, t.`condition`,
                       IFNULL(t.archived_at, t.date_acquired) as archived_date,
                       IFNULL(i.quantity_total, 0) as qty_total
                FROM tool t
                LEFT JOIN inventory i ON t.tool_id = i.tool_id
                WHERE t.is_archived = 1
                ORDER BY t.archived_at DESC
            """)
            rows = cursor.fetchall()
            
            if not rows:
                ctk.CTkLabel(self._tools_scroll, text="No archived tools found.", text_color="gray").pack(pady=20)
                return

            for i, row in enumerate(rows):
                archived_ts = row["archived_date"].strftime("%Y-%m-%d %H:%M") if row["archived_date"] else "—"
                vals = [str(row["tool_id"]), row["name"], row["category"], f"{row['qty_total']:g}", archived_ts, "Restore"]
                bg = "#F9FAFB" if i % 2 == 0 else "white"
                rf = self._make_row(self._tools_scroll, vals, self._tools_weights, bg)
                
                for col, (val, w) in enumerate(zip(vals, self._tools_weights)):
                    if col == 5:
                        btn = ctk.CTkButton(rf, text="Restore", width=60, fg_color="#2980B9", hover_color="#1F618D", 
                                            command=lambda r=row["tool_id"]: self.restore_tool(r))
                        btn.grid(row=0, column=col, padx=8, pady=4, sticky="w")
                    else:
                        ctk.CTkLabel(rf, text=val, font=("Inter", 11), text_color="#1A1A1A").grid(row=0, column=col, padx=8, pady=6, sticky="w")
        except Exception as e:
            ctk.CTkLabel(self._tools_scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def restore_tool(self, tool_id):
        if not messagebox.askyesno("Confirm Restore", f"Are you sure you want to restore Tool PID: {tool_id}?"): return
        conn = get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE tool SET is_archived = 0 WHERE tool_id = %s", (tool_id,))
            conn.commit()
            
            uid = self.user_info.get("user_id")
            if uid: log_action(uid, "Edited", "Maintenance", f"Restored Tool PID: {tool_id} from Archive")
            
            messagebox.showinfo("Success", "Tool restored to active inventory.")
            self.load_archived_tools()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    # ------------------------------------------
    # TAB 3: Archived Employees
    # ------------------------------------------
    def render_employees_tab(self):
        frame = ctk.CTkFrame(self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(top, text="Inactive / Archived Employees",
                     font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(side="left")

        headers = ["User ID", "Employee ID", "Full Name", "Role", "Status", "Archived At", "Action"]
        weights = [1, 2, 3, 2, 2, 2, 1]
        self._emp_weights = weights
        self._make_header(frame, headers, weights)

        self._emp_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self._emp_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        self.load_archived_employees()

    def load_archived_employees(self):
        for w in self._emp_scroll.winfo_children(): w.destroy()
        conn = get_connection()
        if not conn: return
        try:
            cursor = conn.cursor(dictionary=True)
            self._ensure_user_archive_columns(cursor)
            conn.commit()

            cursor.execute("""
                SELECT user_id, employee_id, full_name, role, status, archived_at
                FROM `user`
                WHERE IFNULL(status, 'Inactive') != 'Active'
                ORDER BY IFNULL(archived_at, user_id) DESC
            """)
            rows = cursor.fetchall()
            
            if not rows:
                ctk.CTkLabel(self._emp_scroll, text="No archived employees found.", text_color="gray").pack(pady=20)
                return

            for i, row in enumerate(rows):
                status_display = row["status"] if row.get("status") else "Inactive"
                archived_at = row.get("archived_at")
                archived_display = archived_at.strftime("%Y-%m-%d %H:%M:%S") if archived_at else "—"
                vals = [str(row["user_id"]), row["employee_id"], row["full_name"], row["role"], status_display, archived_display, "Restore"]
                bg = "#F9FAFB" if i % 2 == 0 else "white"
                rf = self._make_row(self._emp_scroll, vals, self._emp_weights, bg)
                
                for col, (val, w) in enumerate(zip(vals, self._emp_weights)):
                    if col == 6:
                        btn = ctk.CTkButton(rf, text="Restore", width=60, fg_color="#2980B9", hover_color="#1F618D", 
                                            command=lambda r=row["user_id"]: self.restore_employee(r))
                        btn.grid(row=0, column=col, padx=8, pady=4, sticky="w")
                    else:
                        ctk.CTkLabel(rf, text=val, font=("Inter", 11), text_color="#1A1A1A").grid(row=0, column=col, padx=8, pady=6, sticky="w")
        except Exception as e:
            ctk.CTkLabel(self._emp_scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def restore_employee(self, user_id):
        if not messagebox.askyesno("Confirm Restore", f"Restore employee access for User ID: {user_id}?"): return
        conn = get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SHOW COLUMNS FROM `user` LIKE 'archived_at'")
            archived_col = cursor.fetchone() is not None
            if archived_col:
                cursor.execute("UPDATE `user` SET status = 'Active', archived_at = NULL WHERE user_id = %s", (user_id,))
            else:
                cursor.execute("UPDATE `user` SET status = 'Active' WHERE user_id = %s", (user_id,))
            conn.commit()
            
            uid = self.user_info.get("user_id")
            if uid: log_action(uid, "Edited", "Maintenance", f"Restored Employee UID: {user_id} from Archive")
            
            messagebox.showinfo("Success", "Employee access restored.")
            self.load_archived_employees()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    # ------------------------------------------
    # TAB 4: Archived Projects
    # ------------------------------------------
    def render_projects_tab(self):
        frame = ctk.CTkFrame(self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(top, text="Completed / Archived Projects",
                     font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(side="left")

        headers = ["Project ID", "Project Name", "Client/Dept", "Status", "End/Archived At", "Action"]
        weights = [1, 3, 2, 1, 2, 1]
        self._proj_weights = weights
        self._make_header(frame, headers, weights)

        self._proj_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self._proj_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        self.load_archived_projects()

    def load_archived_projects(self):
        for w in self._proj_scroll.winfo_children(): w.destroy()
        conn = get_connection()
        if not conn: return
        try:
            cursor = conn.cursor(dictionary=True)
            # Fetch completed, cancelled, and archived projects
            cursor.execute("""
                SELECT project_id, name, client, status, end_date, archived_at
                FROM projects 
                WHERE status IN ('Completed', 'Cancelled') OR archived_at IS NOT NULL
                ORDER BY IFNULL(archived_at, end_date) DESC
            """)
                    
            rows = cursor.fetchall()
            
            if not rows:
                ctk.CTkLabel(self._proj_scroll, text="No completed or archived projects found.", text_color="gray").pack(pady=20)
                return

            for i, row in enumerate(rows):
                display_date = None
                if row.get("archived_at"):
                    display_date = row["archived_at"].strftime("%Y-%m-%d %H:%M:%S")
                elif row.get("end_date"):
                    display_date = row["end_date"].strftime("%Y-%m-%d")
                else:
                    display_date = "—"

                client_display = row.get("client") or "—"
                vals = [str(row["project_id"]), row["name"], client_display, row["status"], display_date, "Restore"]
                bg = "#F9FAFB" if i % 2 == 0 else "white"
                rf = self._make_row(self._proj_scroll, vals, self._proj_weights, bg)
                
                for col, (val, w) in enumerate(zip(vals, self._proj_weights)):
                    if col == 5:
                        btn = ctk.CTkButton(rf, text="Restore", width=60, fg_color="#2980B9", hover_color="#1F618D", 
                                            command=lambda r=row["project_id"]: self.restore_project(r))
                        btn.grid(row=0, column=col, padx=8, pady=4, sticky="w")
                    else:
                        ctk.CTkLabel(rf, text=val, font=("Inter", 11), text_color="#1A1A1A").grid(row=0, column=col, padx=8, pady=6, sticky="w")
        except Exception as e:
            ctk.CTkLabel(self._proj_scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def restore_project(self, project_id):
        if not messagebox.askyesno("Confirm Restore", f"Restore Project ID: {project_id} to Active status?"): return
        conn = get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            # Clear the archived_at timestamp to restore to active
            cursor.execute("UPDATE projects SET status = 'Approved', archived_at = NULL WHERE project_id = %s", (project_id,))
            conn.commit()
            
            uid = self.user_info.get("user_id")
            if uid: log_action(uid, "Edited", "Maintenance", f"Restored Project ID: {project_id} from Archive")
            
            messagebox.showinfo("Success", "Project marked as Approved and restored from archive.")
            self.load_archived_projects()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()