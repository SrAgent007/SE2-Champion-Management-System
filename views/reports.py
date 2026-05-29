import customtkinter as ctk
from tkinter import messagebox
from database import get_connection
import os
import tempfile
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime


class ReportsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_ui()

    def build_ui(self):
        # Tab bar (matches existing system style)
        tab_bar = ctk.CTkFrame(self, fg_color="white",
                               corner_radius=10, height=50)
        tab_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tab_bar.grid_propagate(False)

        self.tab_content = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_content.grid(row=1, column=0, sticky="nsew")
        self.tab_content.grid_columnconfigure(0, weight=1)
        self.tab_content.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        tabs = [
            ("Inventory ABC Analysis", "abc"),
            ("Tool Usage Report", "usage"),
            ("Employee Activity", "activity"),
        ]

        self.tab_buttons = {}
        for text, key in tabs:
            btn = ctk.CTkButton(
                tab_bar, text=text,
                fg_color="#1E4528" if key == "abc" else "transparent",
                text_color="white" if key == "abc" else "#1A1A1A",
                hover_color="#2A6038",
                font=("Inter", 12, "bold"),
                command=lambda k=key: self.switch_tab(k, tabs)
            )
            btn.pack(side="left", padx=10, pady=8)
            self.tab_buttons[key] = btn

        self.render_abc_tab()

    def switch_tab(self, key, tabs):
        for widget in self.tab_content.winfo_children():
            widget.destroy()

        for _, k in tabs:
            btn = self.tab_buttons.get(k)
            if btn:
                if k == key:
                    btn.configure(fg_color="#1E4528", text_color="white")
                else:
                    btn.configure(fg_color="transparent", text_color="#1A1A1A")

        if key == "abc":
            self.render_abc_tab()
        elif key == "usage":
            self.render_usage_tab()
        elif key == "activity":
            self.render_activity_tab()

    # ==========================================
    # TAB 1: ABC Analysis (preserves original logic)
    # ==========================================
    def render_abc_tab(self):
        frame = ctk.CTkFrame(
            self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(20, 5))

        ctk.CTkLabel(top, text="Inventory Analytics (ABC Analysis)",
                     font=("Inter", 20, "bold"), text_color="#1E4528").pack(side="left")
        ctk.CTkButton(top, text="⎙ Export PDF", width=110,
                      fg_color="#1E4528", hover_color="#14301C",
                      font=("Inter", 11, "bold"),
                      command=lambda: self.export_pdf("abc")).pack(side="right")

        ctk.CTkLabel(frame,
                     text="Algorithm dynamically categorizes tools based on the Pareto Principle (80/20 usage).",
                     font=("Inter", 12), text_color="gray").pack(anchor="w", padx=30, pady=(0, 20))

        headers = ["Rank", "Tool ID", "Tool Name",
                   "Times Borrowed", "Cumulative %", "ABC Category"]
        weights = [1, 1, 3, 2, 2, 2]

        hdr = ctk.CTkFrame(frame, fg_color="#1E4528",
                           corner_radius=5, height=40)
        hdr.pack(fill="x", padx=(30, 46))
        hdr.pack_propagate(False)

        for col, (h, w) in enumerate(zip(headers, weights)):
            hdr.grid_columnconfigure(col, weight=w)
            ctk.CTkLabel(hdr, text=h, font=("Inter", 12, "bold"),
                         text_color="white").grid(row=0, column=col, padx=10, pady=10, sticky="w")

        self._abc_scroll = ctk.CTkScrollableFrame(
            frame, fg_color="transparent")
        self._abc_scroll.pack(fill="both", expand=True, padx=30, pady=(10, 30))

        self.run_abc_algorithm()

    def run_abc_algorithm(self):
        """Implements Figure 96 (ABC Inventory Categorization)"""
        scroll = self._abc_scroll
        for w in scroll.winfo_children():
            w.destroy()

        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT t.tool_id, t.name, COUNT(tr.transaction_id) as usage_count
                FROM tool t
                LEFT JOIN transaction tr ON t.tool_id = tr.tool_id AND tr.type = 'Borrow'
                WHERE t.is_archived = 0
                GROUP BY t.tool_id, t.name
                ORDER BY usage_count DESC
            """)
            tools = cursor.fetchall()

            total_usage = sum(t['usage_count'] for t in tools) or 1
            cumulative = 0

            self._abc_data = []

            for i, tool in enumerate(tools):
                cumulative += tool['usage_count']
                cum_pct = (cumulative / total_usage) * 100

                if cum_pct <= 70:
                    category = "A (High Priority)"
                    color = "#2ECC71"
                elif cum_pct <= 90:
                    category = "B (Medium Priority)"
                    color = "#F1C40F"
                else:
                    category = "C (Low Priority)"
                    color = "#E74C3C"

                self._abc_data.append({
                    "rank": f"#{i+1}",
                    "tool_id": str(tool['tool_id']),
                    "name": tool['name'],
                    "usage": str(tool['usage_count']),
                    "cum_pct": f"{cum_pct:.1f}%",
                    "category": category,
                })

                display_data = [f"#{i+1}", str(tool['tool_id']), tool['name'],
                                str(tool['usage_count']), f"{cum_pct:.1f}%", category]

                rf = ctk.CTkFrame(scroll,
                                  fg_color="#F9FAFB" if i % 2 == 0 else "white",
                                  height=40)
                rf.pack(fill="x", pady=2)
                rf.pack_propagate(False)

                for col, (text, w) in enumerate(zip(display_data, [1, 1, 3, 2, 2, 2])):
                    rf.grid_columnconfigure(col, weight=w)
                    txt_col = color if col == 5 else "black"
                    ctk.CTkLabel(rf, text=text,
                                 font=("Inter", 11, "bold" if col ==
                                       5 else "normal"),
                                 text_color=txt_col).grid(
                        row=0, column=col, padx=10, pady=5, sticky="w")

        except Exception as e:
            ctk.CTkLabel(
                scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    # ==========================================
    # TAB 2: Tool Usage Report
    # ==========================================
    def render_usage_tab(self):
        frame = ctk.CTkFrame(
            self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(20, 5))

        ctk.CTkLabel(top, text="Tool Usage Report",
                     font=("Inter", 20, "bold"), text_color="#1E4528").pack(side="left")
        ctk.CTkButton(top, text="⎙ Export PDF", width=110,
                      fg_color="#1E4528", hover_color="#14301C",
                      font=("Inter", 11, "bold"),
                      command=lambda: self.export_pdf("usage")).pack(side="right")

        ctk.CTkLabel(frame,
                     text="Summary of all tool transactions, availability, and condition status.",
                     font=("Inter", 12), text_color="gray").pack(anchor="w", padx=30, pady=(0, 15))

        headers = ["Tool ID", "Tool Name", "Tag ID", "Total Borrowed",
                   "Currently Out", "Qty Available", "Condition"]
        weights = [1, 2, 2, 2, 2, 2, 2]

        hdr = ctk.CTkFrame(frame, fg_color="#1E4528",
                           corner_radius=5, height=40)
        hdr.pack(fill="x", padx=30)
        hdr.pack_propagate(False)

        for col, (h, w) in enumerate(zip(headers, weights)):
            hdr.grid_columnconfigure(col, weight=w)
            ctk.CTkLabel(hdr, text=h, font=("Inter", 12, "bold"),
                         text_color="white").grid(row=0, column=col, padx=10, pady=10, sticky="w")

        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=30, pady=(10, 30))

        self._usage_data = []

        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT t.tool_id, t.name,
                       IFNULL(t.tag_id,'Unassigned') as tag_id,
                       COUNT(tr.transaction_id) as total_borrowed,
                       SUM(CASE WHEN tr.status='Active' THEN 1 ELSE 0 END) as currently_out,
                       IFNULL(i.quantity_available,0) as qty_avail,
                       t.`condition`
                FROM tool t
                LEFT JOIN transaction tr ON t.tool_id = tr.tool_id AND tr.type='Borrow'
                LEFT JOIN inventory i ON t.tool_id = i.tool_id
                WHERE t.is_archived = 0
                GROUP BY t.tool_id, t.name, t.tag_id, i.quantity_available, t.`condition`
                ORDER BY total_borrowed DESC
            """)
            rows = cursor.fetchall()

            for i, row in enumerate(rows):
                vals = [
                    str(row['tool_id']),
                    row['name'],
                    row['tag_id'],
                    str(row['total_borrowed']),
                    str(row['currently_out'] or 0),
                    str(row['qty_avail']),
                    row['condition'],
                ]
                self._usage_data.append(vals)

                rf = ctk.CTkFrame(scroll,
                                  fg_color="#F9FAFB" if i % 2 == 0 else "white",
                                  height=40)
                rf.pack(fill="x", pady=2)
                rf.pack_propagate(False)

                for col, (val, w) in enumerate(zip(vals, weights)):
                    rf.grid_columnconfigure(col, weight=w)
                    color = "#1A1A1A"
                    if col == 6:
                        color = "#2ECC71" if val == "Good" else "#D8000C"
                    ctk.CTkLabel(rf, text=val, font=("Inter", 11),
                                 text_color=color).grid(
                        row=0, column=col, padx=10, pady=5, sticky="w")

        except Exception as e:
            ctk.CTkLabel(
                scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    # ==========================================
    # TAB 3: Employee Activity Report
    # ==========================================
    def render_activity_tab(self):
        frame = ctk.CTkFrame(
            self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(20, 5))

        ctk.CTkLabel(top, text="Employee Activity Report",
                     font=("Inter", 20, "bold"), text_color="#1E4528").pack(side="left")
        ctk.CTkButton(top, text="⎙ Export PDF", width=110,
                      fg_color="#1E4528", hover_color="#14301C",
                      font=("Inter", 11, "bold"),
                      command=lambda: self.export_pdf("activity")).pack(side="right")

        ctk.CTkLabel(frame,
                     text="Aggregated borrowing activity per employee for accountability monitoring.",
                     font=("Inter", 12), text_color="gray").pack(anchor="w", padx=30, pady=(0, 15))

        headers = ["Employee ID", "Full Name", "Role",
                   "Total Borrows", "Currently Active", "Total Returned"]
        weights = [2, 3, 2, 2, 2, 2]

        hdr = ctk.CTkFrame(frame, fg_color="#1E4528",
                           corner_radius=5, height=40)
        hdr.pack(fill="x", padx=30)
        hdr.pack_propagate(False)

        for col, (h, w) in enumerate(zip(headers, weights)):
            hdr.grid_columnconfigure(col, weight=w)
            ctk.CTkLabel(hdr, text=h, font=("Inter", 12, "bold"),
                         text_color="white").grid(row=0, column=col, padx=10, pady=10, sticky="w")

        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=30, pady=(10, 30))

        self._activity_data = []

        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT u.employee_id, u.full_name, u.role,
                       COUNT(tr.transaction_id) as total_borrows,
                       SUM(CASE WHEN tr.status='Active' THEN 1 ELSE 0 END) as active_borrows,
                       SUM(CASE WHEN tr.status='Returned' THEN 1 ELSE 0 END) as total_returned
                FROM user u
                LEFT JOIN transaction tr ON u.user_id = tr.user_id AND tr.type = 'Borrow'
                GROUP BY u.user_id, u.employee_id, u.full_name, u.role
                ORDER BY total_borrows DESC
            """)
            rows = cursor.fetchall()

            for i, row in enumerate(rows):
                vals = [
                    row['employee_id'],
                    row['full_name'],
                    row['role'],
                    str(row['total_borrows']),
                    str(row['active_borrows'] or 0),
                    str(row['total_returned'] or 0),
                ]
                self._activity_data.append(vals)

                rf = ctk.CTkFrame(scroll,
                                  fg_color="#F9FAFB" if i % 2 == 0 else "white",
                                  height=40)
                rf.pack(fill="x", pady=2)
                rf.pack_propagate(False)

                for col, (val, w) in enumerate(zip(vals, weights)):
                    rf.grid_columnconfigure(col, weight=w)
                    color = "#1A1A1A"
                    if col == 4 and int(val) > 0:
                        color = "#D8000C"
                    ctk.CTkLabel(rf, text=val, font=("Inter", 11),
                                 text_color=color).grid(
                        row=0, column=col, padx=10, pady=5, sticky="w")

        except Exception as e:
            ctk.CTkLabel(
                scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    # ==========================================
    # PDF Export (shared across all tabs)
    # ==========================================
    def export_pdf(self, report_type):
        try:
            canvas_width = 900
            line_h = 28
            timestamp = datetime.now().strftime("%B %d, %Y %I:%M %p")

            if report_type == "abc":
                data = getattr(self, "_abc_data", [])
                title = "Inventory ABC Analysis Report"
                col_labels = ["Rank", "Tool ID", "Tool Name",
                              "Times Borrowed", "Cumulative%", "Category"]
                rows = [[d["rank"], d["tool_id"], d["name"], d["usage"], d["cum_pct"], d["category"]]
                        for d in data]

            elif report_type == "usage":
                data = getattr(self, "_usage_data", [])
                title = "Tool Usage Report"
                col_labels = ["Tool ID", "Name", "Tag ID", "Total Borrowed",
                              "Currently Out", "Qty Avail", "Condition"]
                rows = data

            else:
                data = getattr(self, "_activity_data", [])
                title = "Employee Activity Report"
                col_labels = ["Employee ID", "Full Name", "Role",
                              "Total Borrows", "Active", "Returned"]
                rows = data

            total_rows = len(rows)
            canvas_height = 160 + (total_rows * line_h) + 80

            canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
            draw = ImageDraw.Draw(canvas)

            try:
                font_title = ImageFont.truetype("arialbd.ttf", 26)
                font_header = ImageFont.truetype("arialbd.ttf", 16)
                font_body = ImageFont.truetype("arial.ttf", 14)
            except IOError:
                font_title = font_header = font_body = ImageFont.load_default()

            # Title block
            draw.text((30, 20), "CHAMPION FINE TOOLING CORPORATION",
                      fill="#1E4528", font=font_title)
            draw.text((30, 60), title, fill="black", font=font_header)
            draw.text(
                (30, 90), f"Generated: {timestamp}", fill="gray", font=font_body)
            draw.line((30, 120, canvas_width - 30, 120),
                      fill="#1E4528", width=2)

            # Column headers
            col_x = [30 + i * ((canvas_width - 60) // len(col_labels))
                     for i in range(len(col_labels))]
            y = 135
            for j, label in enumerate(col_labels):
                draw.text((col_x[j], y), label,
                          fill="#1E4528", font=font_header)

            draw.line((30, y + 20, canvas_width - 30, y + 20),
                      fill="#CCCCCC", width=1)
            y += 28

            # Data rows
            for r_idx, row in enumerate(rows):
                fill = "#F9FAFB" if r_idx % 2 == 0 else "white"
                draw.rectangle([30, y - 2, canvas_width - 30, y + line_h - 4],
                               fill=fill)
                for j, cell in enumerate(row):
                    draw.text((col_x[j], y), str(cell),
                              fill="black", font=font_body)
                y += line_h

            draw.line((30, y + 10, canvas_width - 30, y + 10),
                      fill="#CCCCCC", width=1)
            draw.text((30, y + 20), f"Total Records: {total_rows}",
                      fill="gray", font=font_body)

            temp_dir = tempfile.gettempdir()
            fname = f"Report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            fpath = os.path.join(temp_dir, fname)
            canvas.save(fpath, "PDF", resolution=100.0)
            os.startfile(fpath)

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to generate PDF:\n{e}",
                                 parent=self.winfo_toplevel())
