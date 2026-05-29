import customtkinter as ctk
from tkinter import messagebox
from database import get_connection, log_action
from datetime import datetime
import cv2
from pyzbar.pyzbar import decode, ZBarSymbol

class ProjectsView(ctk.CTkFrame):
    def __init__(self, parent, user_info):
        super().__init__(parent, fg_color="transparent")

        self.user_info = user_info
        self.is_admin = self.user_info.get("role", "Staff") == "Admin"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.grid(row=0, column=0, sticky="nsew")
        self.inner.grid_columnconfigure(0, weight=1, minsize=380)
        self.inner.grid_columnconfigure(1, weight=2, minsize=600)
        self.inner.grid_rowconfigure(0, weight=1)

        self.req_cart = []
        self.build_form_panel()
        self.build_table_panel()

        uid = self.user_info.get("user_id")
        if uid:
            log_action(uid, "Viewed", "Projects", "Opened Project Management module")
            
        self.p_name.focus_set()

    def build_form_panel(self):
        form_card = ctk.CTkScrollableFrame(self.inner, fg_color="white", corner_radius=10, width=380)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(form_card, text="Draft Project Plan", font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20, pady=(20, 10))

        def field(label, ph):
            ctk.CTkLabel(form_card, text=label, font=("Inter", 11, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20)
            e = ctk.CTkEntry(form_card, placeholder_text=ph, takefocus=True)
            e.pack(fill="x", padx=20, pady=(5, 10))
            return e

        self.p_name = field("Project Name *", "e.g., Ayala Alabang Phase 2")
        
        ctk.CTkLabel(form_card, text="Project Description", font=("Inter", 11, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20)
        self.p_desc = ctk.CTkTextbox(form_card, height=80, fg_color="#F9FAFB", border_width=1, border_color="#E0E0E0")
        self.p_desc.pack(fill="x", padx=20, pady=(5, 10))

        self.p_head = field("Project Head / Manager *", "e.g., Engr. Juan Santos")
        self.p_client = field("Client / Company *", "e.g., Makati Dev Corp")
        self.p_location = field("Site Location", "e.g., Block 4, Alabang")

        ctk.CTkLabel(form_card, text="Assigned Workers", font=("Inter", 11, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20)

        worker_input_row = ctk.CTkFrame(form_card, fg_color="transparent")
        worker_input_row.pack(fill="x", padx=20, pady=(5, 5))

        self.worker_single_entry = ctk.CTkEntry(worker_input_row, placeholder_text="Employee ID or name...", takefocus=True)
        self.worker_single_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.worker_single_entry.bind("<Return>", lambda e: self._add_worker_from_entry())

        ctk.CTkButton(worker_input_row, text="+ Add", width=55, height=32, fg_color="#1E4528", hover_color="#14301C", font=("Inter", 11, "bold"), command=self._add_worker_from_entry).pack(side="left", padx=(0, 5))
        ctk.CTkButton(worker_input_row, text="📷 Scan", width=65, height=32, fg_color="#3498DB", hover_color="#2980B9", font=("Inter", 11, "bold"), command=self.scan_worker).pack(side="left")

        self.worker_tags_frame = ctk.CTkScrollableFrame(form_card, fg_color="#F9FAFB", corner_radius=6, height=80)
        self.worker_tags_frame.pack(fill="x", padx=20, pady=(0, 12))
        self.workers_list = []  
        self._refresh_worker_tags()

        ctk.CTkLabel(form_card, text="Tools & Equipment Needed *", font=("Inter", 11, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20)
        ctk.CTkButton(form_card, text="🔍 Browse Inventory Catalog", fg_color="#F1C40F", text_color="black", hover_color="#D4AC0D", font=("Inter", 12, "bold"), command=self.open_tool_picker).pack(fill="x", padx=20, pady=(5, 10))

        cart_bg = ctk.CTkFrame(form_card, fg_color="#F9FAFB", corner_radius=8)
        cart_bg.pack(fill="x", padx=20, pady=(0, 15))
        self.cart_scroll = ctk.CTkScrollableFrame(cart_bg, fg_color="white", height=120)
        self.cart_scroll.pack(fill="x", padx=10, pady=10)
        self.refresh_req_cart()

        row_dates = ctk.CTkFrame(form_card, fg_color="transparent")
        row_dates.pack(fill="x", padx=20, pady=(5, 10))
        row_dates.grid_columnconfigure(0, weight=1)
        row_dates.grid_columnconfigure(1, weight=1)

        start_f = ctk.CTkFrame(row_dates, fg_color="transparent")
        start_f.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkLabel(start_f, text="Start Date", font=("Inter", 11, "bold"), text_color="#1A1A1A").pack(anchor="w")
        self.p_start = ctk.CTkEntry(start_f, placeholder_text="YYYY-MM-DD", takefocus=True)
        self.p_start.pack(fill="x", pady=(5, 0))

        end_f = ctk.CTkFrame(row_dates, fg_color="transparent")
        end_f.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ctk.CTkLabel(end_f, text="End Date", font=("Inter", 11, "bold"), text_color="#1A1A1A").pack(anchor="w")
        self.p_end = ctk.CTkEntry(end_f, placeholder_text="YYYY-MM-DD", takefocus=True)
        self.p_end.pack(fill="x", pady=(5, 0))

        ctk.CTkButton(form_card, text="Submit for Approval", height=40, fg_color="#1E4528", hover_color="#14301C", font=("Inter", 13, "bold"), command=self.save_project).pack(fill="x", padx=20, pady=(20, 20))

    def _add_worker_from_entry(self):
        val = self.worker_single_entry.get().strip()
        if val and val not in self.workers_list:
            self.workers_list.append(val)
            self._refresh_worker_tags()
        self.worker_single_entry.delete(0, 'end')

    def _refresh_worker_tags(self):
        for w in self.worker_tags_frame.winfo_children(): w.destroy()
        if not self.workers_list:
            ctk.CTkLabel(self.worker_tags_frame, text="No workers added yet.", text_color="gray", font=("Inter", 11)).pack(pady=8)
            return
        for idx, worker in enumerate(self.workers_list):
            tag_row = ctk.CTkFrame(self.worker_tags_frame, fg_color="white", corner_radius=5, height=28)
            tag_row.pack(fill="x", pady=2, padx=5)
            tag_row.pack_propagate(False)
            ctk.CTkLabel(tag_row, text=f"👷 {worker}", font=("Inter", 11), text_color="#1E4528").pack(side="left", padx=8)
            ctk.CTkButton(tag_row, text="✕", width=22, height=22, fg_color="#FFEAEA", text_color="#D8000C", hover_color="#FFC0C0", command=lambda i=idx: self._remove_worker(i)).pack(side="right", padx=5)

    def _remove_worker(self, idx):
        if 0 <= idx < len(self.workers_list):
            self.workers_list.pop(idx)
            self._refresh_worker_tags()

    def open_tool_picker(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Inventory Requisition Catalog")
        modal.geometry("720x560")
        modal.configure(fg_color="white")
        modal.attributes("-topmost", True)
        modal.grab_set()
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (720 // 2)
        y = (modal.winfo_screenheight() // 2) - (560 // 2)
        modal.geometry(f"+{x}+{y}")

        ctk.CTkLabel(modal, text="Select Items for Project Requisition", font=("Inter", 16, "bold"), text_color="black").pack(pady=(20, 5))
        ctk.CTkLabel(modal, text="Search by Name or PID, then set quantity and click + Add.", font=("Inter", 11), text_color="gray").pack(pady=(0, 10))

        search_frame = ctk.CTkFrame(modal, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkLabel(search_frame, text="Name:", font=("Inter", 11, "bold"), text_color="gray").pack(side="left")
        search_name = ctk.CTkEntry(search_frame, placeholder_text="Item name...", width=180, takefocus=True)
        search_name.pack(side="left", padx=(5, 10))

        ctk.CTkLabel(search_frame, text="PID:", font=("Inter", 11, "bold"), text_color="gray").pack(side="left")
        search_pid = ctk.CTkEntry(search_frame, placeholder_text="Product ID...", width=100, takefocus=True)
        search_pid.pack(side="left", padx=(5, 10))

        def do_search(): load_catalog(name_q=search_name.get().strip(), pid_q=search_pid.get().strip())
        def do_reset(): search_name.delete(0, 'end'); search_pid.delete(0, 'end'); load_catalog()

        ctk.CTkButton(search_frame, text="Search", width=80, fg_color="#1E4528", hover_color="#14301C", font=("Inter", 11, "bold"), command=do_search).pack(side="left", padx=5)
        ctk.CTkButton(search_frame, text="↻ Reset", width=80, fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC", font=("Inter", 11, "bold"), command=do_reset).pack(side="left", padx=5)

        search_name.bind("<Return>", lambda e: do_search())
        search_pid.bind("<Return>", lambda e: do_search())

        hdr = ctk.CTkFrame(modal, fg_color="#1E4528", height=40, corner_radius=5)
        hdr.pack(fill="x", padx=(20, 36))
        hdr.pack_propagate(False)
        weights = [1, 1, 2, 1, 1, 1, 1]
        cols = ["PID", "Type", "Item Name", "UoM", "Avail/Tot", "Req Qty", "Action"]
        for col, (w, text) in enumerate(zip(weights, cols)):
            hdr.grid_columnconfigure(col, weight=w)
            ctk.CTkLabel(hdr, text=text, font=("Inter", 11, "bold"), text_color="white").grid(row=0, column=col, padx=5, pady=10, sticky="w")

        list_scroll = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        list_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        def load_catalog(name_q="", pid_q=""):
            for w in list_scroll.winfo_children(): w.destroy()
            conn = get_connection()
            if not conn: return
            try:
                cursor = conn.cursor(dictionary=True)
                query = """
                    SELECT t.tool_id, t.name, IFNULL(t.item_type,'Equipment') as type,
                           IFNULL(t.unit_of_measure,'pcs') as uom,
                           IFNULL(i.quantity_available, 0) as avail,
                           IFNULL(i.quantity_total, 0) as total
                    FROM tool t JOIN inventory i ON t.tool_id = i.tool_id
                    WHERE t.is_archived = 0
                """
                params = []
                if name_q and pid_q:
                    query += " AND (t.name LIKE %s AND t.tool_id LIKE %s)"
                    params = [f"%{name_q}%", f"%{pid_q}%"]
                elif name_q:
                    query += " AND t.name LIKE %s"
                    params = [f"%{name_q}%"]
                elif pid_q:
                    query += " AND t.tool_id LIKE %s"
                    params = [f"%{pid_q}%"]

                cursor.execute(query, params)

                for i, row in enumerate(cursor.fetchall()):
                    rf = ctk.CTkFrame(list_scroll, fg_color="#F9FAFB" if i % 2 == 0 else "white", height=40)
                    rf.pack(fill="x", pady=2)
                    rf.pack_propagate(False)
                    for col, w in enumerate(weights): rf.grid_columnconfigure(col, weight=w)

                    ctk.CTkLabel(rf, text=str(row['tool_id']), font=("Inter", 10), text_color="gray").grid(row=0, column=0, padx=5, pady=8, sticky="w")
                    type_color = "#D35400" if row['type'] == "Consumable" else "#1A1A1A"
                    ctk.CTkLabel(rf, text=row['type'], font=("Inter", 10, "bold"), text_color=type_color).grid(row=0, column=1, padx=5, pady=8, sticky="w")
                    ctk.CTkLabel(rf, text=row['name'], font=("Inter", 11, "bold"), text_color="black").grid(row=0, column=2, padx=5, pady=8, sticky="w")
                    ctk.CTkLabel(rf, text=row['uom'], font=("Inter", 10), text_color="gray").grid(row=0, column=3, padx=5, pady=8, sticky="w")

                    avail = f"{row['avail']:g}" if row['avail'] else "0"
                    tot = f"{row['total']:g}" if row['total'] else "0"
                    stock_color = "#D8000C" if float(row['avail']) <= 0 else "#2ECC71"
                    ctk.CTkLabel(rf, text=f"{avail}/{tot}", font=("Inter", 11, "bold"), text_color=stock_color).grid(row=0, column=4, padx=5, pady=8, sticky="w")

                    qty_entry = ctk.CTkEntry(rf, width=55, height=26, takefocus=True)
                    qty_entry.grid(row=0, column=5, padx=5, pady=8, sticky="w")
                    ctk.CTkButton(rf, text="+ Add", width=55, height=26, fg_color="#3498DB", hover_color="#2980B9", font=("Inter", 10, "bold"), command=lambda r=row, q_e=qty_entry: self.add_from_catalog(r, q_e, modal)).grid(row=0, column=6, padx=5, pady=8, sticky="w")

                if not list_scroll.winfo_children():
                    ctk.CTkLabel(list_scroll, text="No items found. Try a different search.", text_color="gray").pack(pady=20)
            except Exception as e: ctk.CTkLabel(list_scroll, text=f"Error: {e}", text_color="red").pack(pady=10)
            finally:
                if conn.is_connected(): cursor.close(); conn.close()

        load_catalog()
        ctk.CTkButton(modal, text="Done / Close Catalog", height=35, fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC", font=("Inter", 11, "bold"), command=modal.destroy).pack(pady=(5, 15))

    def add_from_catalog(self, row_data, qty_entry, modal):
        try: req_qty = float(qty_entry.get())
        except ValueError: return messagebox.showwarning("Invalid", "Please enter a valid number.", parent=modal)

        if req_qty <= 0: return

        if req_qty > float(row_data['total']):
            return messagebox.showerror("Denied", f"Cannot request {req_qty}. The company only owns {row_data['total']:g} {row_data['uom']} total.", parent=modal)

        needs_retrieval = False
        if req_qty > float(row_data['avail']):
            warn_msg = (f"⚠️ TIMELINE CONFLICT RISK\n\nYou requested {req_qty}, but only {row_data['avail']:g} are in the warehouse.\n\nMissing items are deployed elsewhere. If not returned before your Start Date, the project may be delayed.\n\nAdd anyway?")
            if not messagebox.askyesno("Stock Conflict", warn_msg, parent=modal): return
            needs_retrieval = True

        for item in self.req_cart:
            if item['tool_id'] == row_data['tool_id']:
                item['qty'] += req_qty
                item['needs_retrieval'] = item['needs_retrieval'] or needs_retrieval
                self.refresh_req_cart(); qty_entry.delete(0, 'end')
                messagebox.showinfo("Updated", f"Updated {row_data['name']} quantity to {item['qty']:g} {row_data['uom']}.", parent=modal)
                return

        self.req_cart.append({
            'tool_id': row_data['tool_id'], 'name': row_data['name'],
            'uom': row_data['uom'], 'qty': req_qty, 'needs_retrieval': needs_retrieval
        })
        self.refresh_req_cart()
        qty_entry.delete(0, 'end')
        messagebox.showinfo("Added", f"Successfully added {req_qty:g} {row_data['uom']} of {row_data['name']} to project requirements.", parent=modal)

    def refresh_req_cart(self):
        for w in self.cart_scroll.winfo_children(): w.destroy()
        if not self.req_cart:
            ctk.CTkLabel(self.cart_scroll, text="No items selected.", text_color="gray", font=("Inter", 11)).pack(pady=20)
            return
        for i, item in enumerate(self.req_cart):
            row = ctk.CTkFrame(self.cart_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            warning_icon = "⚠️ " if item.get('needs_retrieval') else "✓ "
            text_col = "#D35400" if item.get('needs_retrieval') else "black"
            info = f"{warning_icon}{item['name']} ({item['qty']:g} {item['uom']})"
            ctk.CTkLabel(row, text=info, font=("Inter", 11, "bold"), text_color=text_col).pack(side="left", padx=5)
            ctk.CTkButton(row, text="✕", width=20, height=20, fg_color="#FFEAEA", text_color="#D8000C", hover_color="#FFC0C0", command=lambda idx=i: [self.req_cart.pop(idx), self.refresh_req_cart()]).pack(side="right")

    def scan_worker(self):
        try: cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        except Exception: cap = cv2.VideoCapture(0)
        if not cap.isOpened(): return messagebox.showerror("Camera Error", "No webcam detected.", parent=self.winfo_toplevel())

        detected_data = None
        cv2.namedWindow('Scan Worker ID', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('Scan Worker ID', cv2.WND_PROP_TOPMOST, 1)

        while True:
            ret, frame = cap.read()
            if not ret: break
            cv2.putText(frame, "Scan Employee ID (Press 'Q' to Cancel)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            for barcode in decode(frame, symbols=[ZBarSymbol.QRCODE]):
                detected_data = barcode.data.decode('utf-8').strip()
                break
            cv2.imshow('Scan Worker ID', frame)
            if detected_data or cv2.waitKey(1) & 0xFF == ord('q'): break

        cap.release()
        cv2.destroyAllWindows()

        if detected_data:
            if detected_data not in self.workers_list:
                self.workers_list.append(detected_data)
                self._refresh_worker_tags()

    def _validate_date(self, date_str, field_name):
        if not date_str:
            return True
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            messagebox.showerror("Invalid Date",
                f"{field_name} must be in YYYY-MM-DD format (e.g., 2025-01-15).",
                parent=self.winfo_toplevel())
            return False

    def save_project(self):
        name = self.p_name.get().strip()
        client = self.p_client.get().strip()
        project_head = self.p_head.get().strip()
        workers_str = ", ".join(self.workers_list) if self.workers_list else ""
        desc_text = self.p_desc.get("1.0", "end-1c").strip()
        start_date = self.p_start.get().strip() or None
        end_date = self.p_end.get().strip() or None

        if not name or not client: return messagebox.showerror("Error", "Project Name and Client are required.", parent=self.winfo_toplevel())
        if not self._validate_date(start_date, "Start Date"): return
        if not self._validate_date(end_date, "End Date"): return
        if not self.req_cart: return messagebox.showerror("Error", "Please add at least one tool requirement.", parent=self.winfo_toplevel())

        conn = get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            editing_id = getattr(self, "editing_project_id", None)
            
            if editing_id:
                old_status = getattr(self, "editing_project_status", "Pending")
                new_status = old_status.replace(' (OVERDUE)', '')
                if 'Approved' in old_status and not self.is_admin:
                    new_status = 'Pending'
                    messagebox.showwarning("Notice", "Modifying an approved project reverts it to Pending status for Admin review.", parent=self.winfo_toplevel())
                
                cursor.execute('''
                    UPDATE projects
                    SET name=%s, description=%s, project_head=%s, client=%s, location=%s, workers_assigned=%s, start_date=%s, end_date=%s, status=%s
                    WHERE project_id=%s
                ''', (name, desc_text, project_head, client, self.p_location.get(), workers_str, start_date, end_date, new_status, editing_id))
                
                cursor.execute("DELETE FROM project_requirements WHERE project_id=%s", (editing_id,)) 
                project_id = editing_id
                action_text = "Updated"
            else:
                cursor.execute('''
                    INSERT INTO projects (name, description, project_head, client, location, workers_assigned, start_date, end_date, manager_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending')
                ''', (name, desc_text, project_head, client, self.p_location.get(), workers_str, start_date, end_date, self.user_info['user_id']))
                project_id = cursor.lastrowid
                action_text = "Submitted"

            for item in self.req_cart:
                req_status = 'Warning' if item.get('needs_retrieval') else 'Clear'
                cursor.execute('''
                    INSERT INTO project_requirements (project_id, tool_id, quantity, status)
                    VALUES (%s, %s, %s, %s)
                ''', (project_id, item['tool_id'], item['qty'], req_status))

            conn.commit()
            if self.user_info.get("user_id"): log_action(self.user_info['user_id'], action_text, "Projects", f"{action_text} project '{name}' (ID: {project_id}).")

            messagebox.showinfo("Success", f"Project successfully {action_text.lower()}!", parent=self.winfo_toplevel())

            self.p_name.delete(0, 'end'); self.p_desc.delete("1.0", "end")
            self.p_head.delete(0, 'end'); self.p_client.delete(0, 'end')
            self.p_location.delete(0, 'end')
            self.p_start.delete(0, 'end'); self.p_end.delete(0, 'end')
            self.workers_list.clear()
            self._refresh_worker_tags(); self.req_cart.clear()
            self.refresh_req_cart()
            self.editing_project_id = None; self.editing_project_status = None
            self.load_projects()

        except Exception as e: messagebox.showerror("DB Error", str(e), parent=self.winfo_toplevel())
        finally:
            if conn.is_connected(): cursor.close(); conn.close()

    def build_table_panel(self):
        table_card = ctk.CTkFrame(self.inner, fg_color="white", corner_radius=10)
        table_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(table_card, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(top, text="Project Deployment Plans", font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(side="left")

        self.proj_search = ctk.CTkEntry(top, placeholder_text="Search project or client...", width=250, takefocus=True)
        self.proj_search.pack(side="right", padx=(5, 0))
        self.proj_search.bind("<Return>", lambda e: self.load_projects(self.proj_search.get().strip()))
        
        ctk.CTkButton(top, text="Search", width=80, fg_color="#F1C40F", text_color="black", hover_color="#D4AC0D", font=("Inter", 11, "bold"), command=lambda: self.load_projects(self.proj_search.get().strip())).pack(side="right", padx=5)
        ctk.CTkButton(top, text="↻ Reset", width=70, fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC", font=("Inter", 11, "bold"), command=lambda: [self.proj_search.delete(0, "end"), self.load_projects()]).pack(side="right")

        hdr = ctk.CTkFrame(table_card, fg_color="#1E4528", corner_radius=5, height=40)
        hdr.pack(fill="x", padx=(20, 36))
        hdr.pack_propagate(False)

        headers = ["ID", "Project Name", "Client", "Project Head", "Status", "Actions"]
        weights = [1, 3, 2, 2, 1, 1]

        for col, (h, w) in enumerate(zip(headers, weights)):
            hdr.grid_columnconfigure(col, weight=w)
            ctk.CTkLabel(hdr, text=h, font=("Inter", 11, "bold"), text_color="white").grid(row=0, column=col, padx=10, pady=10, sticky="w")

        self.project_scroll = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self.project_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        self.load_projects()

    def load_projects(self, search_q=""):
        for w in self.project_scroll.winfo_children(): w.destroy()
        conn = get_connection()
        if not conn: return
        try:
            cursor = conn.cursor(dictionary=True)
            sql = '''
                SELECT p.*, a.full_name as admin_approver,
                       CASE 
                           WHEN p.status IN ('Approved', 'Ongoing') AND p.end_date < CURDATE() THEN CONCAT(p.status, ' (OVERDUE)')
                           ELSE p.status 
                       END as display_status
                FROM projects p
                LEFT JOIN user a ON p.approved_by = a.user_id
            '''
            params = []
            if search_q:
                sql += " WHERE p.name LIKE %s OR p.client LIKE %s OR p.project_head LIKE %s"
                params = [f"%{search_q}%", f"%{search_q}%", f"%{search_q}%"]
                
            sql += " ORDER BY p.project_id DESC"
            cursor.execute(sql, tuple(params))
            
            for i, row in enumerate(cursor.fetchall()):
                row["status"] = row["display_status"]
                rf = ctk.CTkFrame(self.project_scroll, fg_color="#F9FAFB" if i % 2 == 0 else "white", height=45)
                rf.pack(fill="x", pady=2)
                rf.pack_propagate(False)

                vals = [str(row["project_id"]), row["name"], row["client"], row.get("project_head") or "—", row["status"]]
                weights = [1, 3, 2, 2, 1]

                for col, (val, w) in enumerate(zip(vals, weights)):
                    rf.grid_columnconfigure(col, weight=w)
                    txt_color = "#D35400" if col == 4 and val == "Pending" else ("#2ECC71" if col == 4 and val == "Approved" else "#1A1A1A")
                    ctk.CTkLabel(rf, text=val, font=("Inter", 11, "bold" if col == 4 else "normal"), text_color=txt_color).grid(row=0, column=col, padx=10, pady=12, sticky="w")

                rf.grid_columnconfigure(5, weight=1)
                btn_color = "#3498DB" if row['status'] == 'Pending' else "#BDC3C7"
                btn_text = "Review" if row['status'] == 'Pending' else "View"
                ctk.CTkButton(rf, text=btn_text, width=65, height=28, fg_color=btn_color, hover_color="#2980B9", font=("Inter", 11, "bold"), command=lambda r=row: self.open_project_modal(r)).grid(row=0, column=5, padx=10, pady=10, sticky="w")

        finally:
            if conn.is_connected(): cursor.close(); conn.close()

    def open_project_modal(self, row):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Project Overview: {row['name']}")
        modal.geometry("580x720")
        modal.configure(fg_color="white")
        modal.attributes("-topmost", True)
        modal.grab_set()
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (580 // 2)
        y = (modal.winfo_screenheight() // 2) - (720 // 2)
        modal.geometry(f"+{x}+{y}")

        ctk.CTkLabel(modal, text=row['name'], font=("Inter", 18, "bold"), text_color="black").pack(pady=(20, 3))
        status_color = "#D35400" if row['status'] == "Pending" else "#2ECC71"
        ctk.CTkLabel(modal, text=f"Status: {row['status']}", font=("Inter", 12, "bold"), text_color=status_color).pack(pady=(0, 5))

        scroll = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        details_frame = ctk.CTkFrame(scroll, fg_color="#F9FAFB", corner_radius=8)
        details_frame.pack(fill="x", pady=(0, 10))

        def add_detail(lbl, val):
            row_f = ctk.CTkFrame(details_frame, fg_color="transparent")
            row_f.pack(fill="x", padx=15, pady=(5, 0))
            ctk.CTkLabel(row_f, text=lbl, font=("Inter", 11, "bold"), text_color="#1E4528", width=140, anchor="w").pack(side="left")
            ctk.CTkLabel(row_f, text=val or "None specified", font=("Inter", 11), text_color="black", wraplength=360, justify="left").pack(side="left")

        add_detail("Client:", row['client'])
        add_detail("Site Location:", row['location'])
        add_detail("Description:", row.get('description') or "—")
        add_detail("Project Head:", row.get('project_head') or "—")
        add_detail("Assigned Workers:", row.get('workers_assigned') or "None assigned")
        add_detail("Schedule:", f"Start: {row['start_date']}   →   End: {row['end_date']}")

        ctk.CTkFrame(details_frame, height=8, fg_color="transparent").pack()

        ctk.CTkLabel(scroll, text="Tools & Equipment Requisition", font=("Inter", 12, "bold"), text_color="#1E4528").pack(anchor="w", pady=(8, 3))
        tools_scroll = ctk.CTkScrollableFrame(scroll, fg_color="white", corner_radius=8, height=160)
        tools_scroll.pack(fill="x", pady=(0, 10))

        reqs = []
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT t.tool_id, t.name, t.item_type, t.unit_of_measure, pr.quantity, pr.status
                FROM project_requirements pr
                JOIN tool t ON pr.tool_id = t.tool_id
                WHERE pr.project_id = %s
            ''', (row['project_id'],))
            reqs = cursor.fetchall()
            cursor.close(); conn.close()

        if reqs:
            for req in reqs:
                warning_icon = "⚠️ " if req['status'] == 'Warning' else "✓ "
                text_col = "#D35400" if req['status'] == 'Warning' else "#1A1A1A"
                row_str = f"{warning_icon}{req['name']}  |  {req['quantity']:g} {req['unit_of_measure']} ({req['item_type']})"
                req_row = ctk.CTkFrame(tools_scroll, fg_color="transparent", height=30)
                req_row.pack(fill="x", pady=1)
                ctk.CTkLabel(req_row, text=row_str, font=("Inter", 11, "bold" if req['status'] == 'Warning' else "normal"), text_color=text_col).pack(anchor="w", padx=8)
        else:
            ctk.CTkLabel(tools_scroll, text="No tools listed.", text_color="gray").pack(pady=10)

        if 'Approved' in row['status'] and row.get('admin_approver'):
            ctk.CTkLabel(scroll, text=f"✅ Approved by: {row['admin_approver']}", font=("Inter", 11, "bold"), text_color="#2ECC71").pack(anchor="w", pady=(0, 5))

        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=20, pady=15)

        def update_proj_status(new_status):
            has_warnings = any(r['status'] == 'Warning' for r in reqs)
            msg = f"Mark this project as {new_status}?"
            if new_status == 'Approved' and has_warnings:
                msg = "⚠️ WARNING: Tools are deployed elsewhere. Approve anyway?"
                
            if messagebox.askyesno("Confirm Status", msg, parent=modal):
                conn = get_connection()
                if conn:
                    c = conn.cursor()
                    if new_status == 'Approved':
                        c.execute("UPDATE projects SET status=%s, approved_by=%s WHERE project_id=%s", (new_status, self.user_info['user_id'], row['project_id']))
                    else:
                        c.execute("UPDATE projects SET status=%s WHERE project_id=%s", (new_status, row['project_id']))
                    conn.commit()
                    c.close(); conn.close()
                    if self.user_info.get("user_id"): log_action(self.user_info['user_id'], "Updated", "Projects", f"Project '{row['name']}' status changed to {new_status}.")
                    modal.destroy()
                    self.load_projects()

        def trigger_edit_mode():
            self.editing_project_id = row['project_id']
            self.editing_project_status = row['status']
            
            self.p_name.delete(0, 'end'); self.p_name.insert(0, row['name'])
            self.p_desc.delete("1.0", "end"); self.p_desc.insert("1.0", row.get('description') or "")
            self.p_head.delete(0, 'end'); self.p_head.insert(0, row.get('project_head') or "")
            self.p_client.delete(0, 'end'); self.p_client.insert(0, row['client'])
            self.p_location.delete(0, 'end'); self.p_location.insert(0, row['location'])
            self.p_start.delete(0, 'end'); self.p_start.insert(0, str(row['start_date']) if row.get('start_date') else "")
            self.p_end.delete(0, 'end'); self.p_end.insert(0, str(row['end_date']) if row.get('end_date') else "")
            
            self.workers_list = [w.strip() for w in (row.get('workers_assigned') or "").split(',') if w.strip()]
            self._refresh_worker_tags()
            
            self.req_cart = [{'tool_id': r['tool_id'], 'name': r['name'], 'uom': r['unit_of_measure'], 'qty': r['quantity'], 'needs_retrieval': r['status'] == 'Warning'} for r in reqs]
            self.refresh_req_cart()
            
            modal.destroy()
            messagebox.showinfo("Edit Mode", "Project data loaded into the draft form.\nThe Submit button will now update this project.", parent=self.winfo_toplevel())

        raw_status = row['status'].replace(' (OVERDUE)', '')
        if raw_status in ['Pending', 'Approved']:
            ctk.CTkButton(btn_frame, text="Edit Project", width=90, fg_color="#F1C40F", hover_color="#D4AC0D", text_color="black", font=("Inter", 11, "bold"), command=trigger_edit_mode).pack(side="left", padx=5)
        if raw_status == 'Pending' and self.is_admin:
            ctk.CTkButton(btn_frame, text="Approve", fg_color="#2ECC71", hover_color="#27AE60", text_color="black", font=("Inter", 11, "bold"), command=lambda: update_proj_status('Approved')).pack(side="left", padx=5)
        if raw_status == 'Approved' and self.is_admin:
            ctk.CTkButton(btn_frame, text="Mark Ongoing", fg_color="#3498DB", hover_color="#2980B9", font=("Inter", 11, "bold"), command=lambda: update_proj_status('Ongoing')).pack(side="left", padx=5)
        if raw_status == 'Ongoing' and self.is_admin:
            ctk.CTkButton(btn_frame, text="Complete Project", fg_color="#27AE60", hover_color="#1E8449", font=("Inter", 11, "bold"), command=lambda: update_proj_status('Completed')).pack(side="left", padx=5)
        if raw_status in ['Pending', 'Approved', 'Ongoing'] and self.is_admin:
            ctk.CTkButton(btn_frame, text="Cancel", fg_color="#E74C3C", hover_color="#C0392B", font=("Inter", 11, "bold"), command=lambda: update_proj_status('Cancelled')).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Close", width=70, fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC", font=("Inter", 11, "bold"), command=modal.destroy).pack(side="right", padx=5)