import customtkinter as ctk
from tkinter import messagebox
from database import get_connection


class HelpView(ctk.CTkFrame):
    """
    Help Module — Figure 4 in the procedural flowchart.
    Provides Help Guide, FAQs, and System Requirements.
    Keyword search uses a linear scan (O(n)) over section/FAQ text.
    Admin-only sections are hidden from Staff users.
    """

    # Sections tagged True are shown only to Admins
    GUIDE_SECTIONS = [
        (False, "1. Logging In & System Roles", [
            "Enter your Employee ID (username) and password on the login screen.",
            "The system recognizes three operational tiers: Admin, Staff, and Worker.",
            "Admins have full approval and maintenance access. Staff manage daily transactions. Workers are field personnel assigned to projects who receive tool deployments.",
            "Use 'Forgot Password?' to reset your credentials via email verification.",
        ]),
        (False, "2. Dashboard", [
            "The Dashboard shows live metrics: total inventory, active deployments, and system users.",
            "The 'Recent Activity' table provides a live feed of the latest system events.",
            "The 'Tool Condition Metrics' bar chart gives a quick visual health snapshot of the company's assets.",
        ]),
        (True, "3. Products / Inventory (Admin)", [
            "Use the left form to register new tools or consumables into the system.",
            "Consumables (e.g., boxes of nails) support fractional quantities (e.g., 0.5 boxes).",
            "Click any row in the table to open the Edit/Archive modal.",
            "'Archive' safely removes a tool from the active list and moves it to the Centralized Archive in Maintenance.",
        ]),
        (False, "4. Project Management (Requisition Workflow)", [
            "Step 1 (Drafting): Enter the client, site location, and schedule to create a Project Plan.",
            "Step 2 (Worker Assignment): Assign Workers to the project by scanning their Employee ID or typing it manually.",
            "Step 3 (Requisition): Click 'Browse Inventory Catalog' to add the required tools to the project's cart.",
            "Step 4 (Approval): Submit the plan. Tools CANNOT be deployed until an Admin changes the status to 'Approved'."
        ]),
        (False, "5. Tool Issuance (Deployment)", [
            "Tools are strictly tied to approved projects. You cannot arbitrarily borrow a tool.",
            "1. Scan the assigned Worker's Employee ID to authenticate them.",
            "2. Select the specific Project they are deploying for.",
            "3. Scan the exact Tool Tags required. The system will block items that were not approved in the Project Requisition.",
            "4. Issue the tools and generate the deployment receipt."
        ]),
        (False, "6. Tool Retrieval", [
            "To retrieve a deployed tool, scan the returning Worker's ID.",
            "Scan the Tool Tag (or type the TRN from the receipt).",
            "Record the return condition (Good, Damaged, Lost) and quantity to restock the central inventory."
        ]),
        (True, "7. Tracking & Accountability (Admin)", [
            "Borrow/Return Logs: A chronological history of every physical tool movement.",
            "Audit Records: Filter by 'Active' or 'Returned' to detect discrepancies in site deployments.",
            "Activity Log: Tracks every login, edit, and search performed by any user in the system.",
        ]),
        (False, "8. Reports", [
            "ABC Analysis: Categorizes tools by deployment frequency (A = top 20% high usage, B = middle, C = rarely used).",
            "Tool Usage Report: Shows total lifetime deployments and current available stock.",
            "Employee Activity: Tracks accountability by showing active item counts per worker.",
        ]),
        (True, "9. Maintenance & Centralized Archive (Admin Only)", [
            "Data Backups: Select specific tables to export a secure JSON backup file.",
            "Data Restoration: Upload a JSON backup to restore previous database states.",
            "Centralized Archive: Contains two vaults — 'Archived Tools' (retired/broken equipment) and 'Archived Projects' (completed/cancelled sites).",
        ]),
        (True, "10. Role Management (Admin Only)", [
            "Register new user accounts (Admins, Staff, or Workers) via the left panel.",
            "Click 'Edit' on any user row to update their Role or force a Password Reset.",
        ]),
        (False, "11. Profile", [
            "View and edit your Full Name and Email address.",
            "Update your password securely.",
            "Click your profile picture to upload a new avatar.",
            "Click '⎙ Print My ID QR Badge' to generate your scannable Employee ID card."
        ]),
    ]

    FAQS = [
        (False, "How do I issue a tool to a worker?",
         "Under the strict Requisition workflow, you can no longer 'just borrow' an item. The worker must be assigned to a Project, and that Project must be 'Approved' by an Admin. Only then can you go to Tool Issuance, scan the worker's ID, select the project, and scan the tools."),
        (False, "What is the 'Worker' role?",
         "Workers are field personnel. While they don't necessarily log into the desktop app, their Employee IDs are registered in the system so they can be tagged to Projects and held accountable for scanned tool deployments."),
        (True, "Where do completed projects or broken tools go?",
         "They are sent to the Centralized Archive within the Maintenance module. This keeps your active Inventory and Project boards clean while preserving historical records and audit trails."),
        (False, "I scanned a QR code but it didn't read. What do I do?",
         "Ensure the QR code is well-lit and aligned inside the green targeting box on the screen. If the physical label is damaged, you can manually type the Tag ID or Employee ID into the entry field and press Enter."),
        (False, "Why can't I approve a Project Requisition?",
         "Only Admin accounts have the authority to switch a Project from 'Pending' to 'Approved'. Staff accounts can draft plans, but require an Admin to greenlight the deployment."),
        (False, "Can I return only a partial amount of consumables?",
         "Yes. When retrieving consumables (like boxes of nails or wire spools), scan the item and manually adjust the Qty field to reflect exactly how much is being restocked (e.g., 0.5 for half a box)."),
        (True, "How do I back up the system data?",
         "Navigate to Maintenance -> Backup Data. Check the boxes for the tables you want to secure, click 'Select Backup Destination', and save the .json file to a secure drive."),
        (False, "Is my password stored securely?",
         "Yes. All passwords are automatically encrypted using bcrypt hashing. Administrators cannot view your password, ensuring compliance with data privacy standards."),
    ]

    def __init__(self, parent, user_info=None):
        super().__init__(parent, fg_color="transparent")

        self.user_info = user_info or {}
        self.is_admin = self.user_info.get("role", "Staff") == "Admin"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.build_ui()

    def build_ui(self):
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(top_bar, text="Help & Support Hub", font=("Inter", 20, "bold"), text_color="#1A1A1A").pack(side="left", padx=20)

        tabs = ["Help Guide", "FAQs", "System Requirements", "Support Tickets"]
        self.tab_var = ctk.StringVar(value=tabs[0])
        
        self.seg_btn = ctk.CTkSegmentedButton(
            top_bar, values=tabs, variable=self.tab_var, command=self.switch_tab,
            fg_color="#F0F0F0", selected_color="#1E4528", selected_hover_color="#14301C"
        )
        self.seg_btn.pack(side="right", padx=20)
        self.seg_btn.set(tabs[0])

        self.tab_content = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        self.tab_content.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.tab_content.grid_columnconfigure(0, weight=1)
        self.tab_content.grid_rowconfigure(0, weight=1)
        
        self.switch_tab(tabs[0])

    def switch_tab(self, selected_tab):
        for widget in self.tab_content.winfo_children(): widget.destroy()
        if selected_tab == "Help Guide": self.render_guide_tab()
        elif selected_tab == "FAQs": self.render_faq_tab()
        elif selected_tab == "System Requirements": self.render_sysreq_tab()
        elif selected_tab == "Support Tickets": self.render_tickets_tab()

    def _build_search_bar(self, parent, on_search, placeholder="Search keywords..."):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(12, 4))
        entry = ctk.CTkEntry(bar, placeholder_text=placeholder, width=300)
        entry.pack(side="left", padx=(0, 8))
        entry.bind("<Return>", lambda e: on_search(entry.get().strip()))
        ctk.CTkButton(bar, text="Search", width=75, fg_color="#1E4528",
                      hover_color="#14301C", font=("Inter", 11, "bold"),
                      command=lambda: on_search(entry.get().strip())).pack(side="left", padx=(0, 6))
        ctk.CTkButton(bar, text="↻ Clear", width=70, fg_color="#E0E0E0",
                      text_color="black", hover_color="#CCCCCC",
                      command=lambda: [entry.delete(0, "end"), on_search("")]).pack(side="left")
        return entry

    @staticmethod
    def _section_matches(title, points, keyword):
        kw = keyword.lower()
        if kw in title.lower():
            return True
        for p in points:
            if kw in p.lower():
                return True
        return False

    # ==========================================
    # HELP GUIDE TAB
    # ==========================================
    def render_guide_tab(self):
        outer = ctk.CTkFrame(
            self.tab_content, fg_color="white", corner_radius=10)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        ctk.CTkLabel(hdr, text="User Guide — Automated Management System",
                     font=("Inter", 18, "bold"), text_color="#1E4528").pack(side="left")

        self._guide_search_entry = self._build_search_bar(
            outer, self._filter_guide, "Search guide sections..."
        )

        self._guide_scroll = ctk.CTkScrollableFrame(
            outer, fg_color="transparent")
        self._guide_scroll.pack(
            fill="both", expand=True, padx=10, pady=(0, 10))

        self._render_guide_sections("")

    def _filter_guide(self, keyword):
        self._render_guide_sections(keyword)

    def _render_guide_sections(self, keyword):
        scroll = self._guide_scroll
        for w in scroll.winfo_children():
            w.destroy()

        found_any = False
        for admin_only, title, points in self.GUIDE_SECTIONS:
            if admin_only and not self.is_admin:
                continue
            if keyword and not self._section_matches(title, points, keyword):
                continue

            found_any = True
            card = ctk.CTkFrame(scroll, fg_color="#F9FAFB", corner_radius=8)
            card.pack(fill="x", padx=10, pady=(0, 6))

            ctk.CTkLabel(card, text=title, font=("Inter", 12, "bold"),
                         text_color="#1E4528").pack(anchor="w", padx=14, pady=(8, 3))
            for point in points:
                ctk.CTkLabel(card, text=f"  •  {point}",
                             font=("Inter", 11), text_color="#1A1A1A",
                             wraplength=780, justify="left").pack(anchor="w", padx=14, pady=1)
            ctk.CTkFrame(card, height=6, fg_color="transparent").pack()

        if not found_any:
            ctk.CTkLabel(scroll, text=f'No sections found for "{keyword}".',
                         text_color="gray").pack(pady=20)

    # ==========================================
    # FAQs TAB
    # ==========================================
    def render_faq_tab(self):
        outer = ctk.CTkFrame(
            self.tab_content, fg_color="white", corner_radius=10)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        ctk.CTkLabel(hdr, text="Frequently Asked Questions",
                     font=("Inter", 18, "bold"), text_color="#1E4528").pack(side="left")

        self._build_search_bar(outer, self._filter_faq, "Search FAQs...")

        self._faq_scroll = ctk.CTkScrollableFrame(
            outer, fg_color="transparent")
        self._faq_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._render_faq_items("")

    def _filter_faq(self, keyword):
        self._render_faq_items(keyword)

    def _render_faq_items(self, keyword):
        scroll = self._faq_scroll
        for w in scroll.winfo_children():
            w.destroy()

        idx = 1
        found_any = False
        for admin_only, q, a in self.FAQS:
            if admin_only and not self.is_admin:
                continue
            if keyword and not self._section_matches(q, [a], keyword):
                continue

            found_any = True
            card = ctk.CTkFrame(scroll, fg_color="#F9FAFB", corner_radius=8)
            card.pack(fill="x", padx=10, pady=(0, 6))

            ctk.CTkLabel(card, text=f"Q{idx}.  {q}",
                         font=("Inter", 11, "bold"), text_color="#1E4528",
                         wraplength=780, justify="left").pack(anchor="w", padx=14, pady=(10, 2))
            ctk.CTkLabel(card, text=f"      {a}",
                         font=("Inter", 11), text_color="#1A1A1A",
                         wraplength=780, justify="left").pack(anchor="w", padx=14, pady=(0, 10))
            idx += 1

        if not found_any:
            ctk.CTkLabel(scroll, text=f'No FAQs found for "{keyword}".',
                         text_color="gray").pack(pady=20)

    # ==========================================
    # SYSTEM REQUIREMENTS TAB
    # ==========================================
    def render_sysreq_tab(self):
        frame = ctk.CTkScrollableFrame(
            self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(frame, text="System Requirements",
                     font=("Inter", 18, "bold"), text_color="#1E4528").pack(
            anchor="w", padx=20, pady=(16, 10))

        hardware_specs = [
            ("Processor",        "Intel Core i3 or equivalent (64-bit)"),
            ("RAM",              "Minimum 8 GB"),
            ("Storage",          "At least 500 MB free disk space"),
            ("Operating System", "Windows 10 (64-bit) — recommended and tested"),
            ("Display",          "Minimum 1280×720 resolution (1920×1080 recommended)"),
            ("Webcam",           "HD Webcam 1080P — required for QR scanning features"),
            ("Printer",          "Any standard printer — required for label and receipt printing"),
            ("Network",          "LAN connection for database access (no internet required)"),
        ]
        software_specs = [
            ("Python",            "3.11"),
            ("Database",          "MySQL 8.0"),
            ("GUI Framework",     "Tkinter 8.6 + CustomTkinter 5.2.2"),
            ("IDE (Dev)",         "PyCharm Community Edition 2023.3"),
            ("QR Code Library",   "qrcode, pyzbar"),
            ("Image Processing",  "Pillow (PIL)"),
            ("CV Scanner",        "OpenCV (cv2)"),
            ("Password Hashing",  "bcrypt"),
        ]

        def render_table(parent, title, specs):
            ctk.CTkLabel(parent, text=title, font=("Inter", 13, "bold"),
                         text_color="#1A1A1A").pack(anchor="w", padx=20, pady=(6, 4))
            card = ctk.CTkFrame(parent, fg_color="#F9FAFB", corner_radius=8)
            card.pack(fill="x", padx=20, pady=(0, 12))
            for i, (label, val) in enumerate(specs):
                row = ctk.CTkFrame(card, fg_color="#F0F0F0" if i %
                                   2 == 0 else "#F9FAFB", height=34)
                row.pack(fill="x")
                row.pack_propagate(False)
                row.grid_columnconfigure(0, weight=1)
                row.grid_columnconfigure(1, weight=2)
                ctk.CTkLabel(row, text=label, font=("Inter", 11, "bold"),
                             text_color="#555555").grid(row=0, column=0, padx=14, pady=6, sticky="w")
                ctk.CTkLabel(row, text=val, font=("Inter", 11),
                             text_color="#1A1A1A").grid(row=0, column=1, padx=14, pady=6, sticky="w")

        render_table(frame, "Hardware Requirements", hardware_specs)
        render_table(frame, "Software Requirements", software_specs)

        ctk.CTkLabel(
            frame,
            text="Note: The system is a LAN-based desktop application. No internet connection is required "
                 "for normal operation. All data is stored locally in the MySQL database.",
            font=("Inter", 11), text_color="gray", wraplength=780, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 20))

    # ==========================================
    # SUPPORT TICKETS TAB
    # ==========================================
    def render_tickets_tab(self):
        frame = ctk.CTkFrame(self.tab_content, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        conn = get_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute('''CREATE TABLE IF NOT EXISTS help_tickets (
                    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    subject VARCHAR(255),
                    message TEXT,
                    admin_reply TEXT,
                    status VARCHAR(50) DEFAULT 'Open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
                conn.commit()
            except Exception: pass
            finally:
                if conn.is_connected(): c.close(); conn.close()

        if not self.is_admin:
            form_bg = ctk.CTkFrame(frame, fg_color="#F9FAFB", corner_radius=10)
            form_bg.pack(fill="x", padx=20, pady=(20, 10))
            
            ctk.CTkLabel(form_bg, text="Submit an Inquiry", font=("Inter", 14, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=15, pady=(15, 5))
            
            subj_entry = ctk.CTkEntry(form_bg, placeholder_text="Subject...")
            subj_entry.pack(fill="x", padx=15, pady=5)
            
            msg_entry = ctk.CTkTextbox(form_bg, height=60)
            msg_entry.pack(fill="x", padx=15, pady=5)
            
            def submit_ticket():
                subj = subj_entry.get().strip()
                msg = msg_entry.get("1.0", "end-1c").strip()
                if not subj or not msg:
                    messagebox.showerror("Error", "Subject and message required.", parent=self.winfo_toplevel())
                    return
                
                db = get_connection()
                if db:
                    c = db.cursor()
                    c.execute("INSERT INTO help_tickets (user_id, subject, message) VALUES (%s, %s, %s)", (self.user_info['user_id'], subj, msg))
                    db.commit(); c.close(); db.close()
                    messagebox.showinfo("Success", "Ticket submitted to the Admin.", parent=self.winfo_toplevel())
                    subj_entry.delete(0, 'end'); msg_entry.delete("1.0", "end")
                    load_ticket_list()

            ctk.CTkButton(form_bg, text="Send to Admin", fg_color="#1E4528", hover_color="#14301C", command=submit_ticket).pack(anchor="e", padx=15, pady=(5, 15))

        ctk.CTkLabel(frame, text="Ticket Inbox" if self.is_admin else "My Previous Tickets", font=("Inter", 14, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20, pady=(10, 5))
        
        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        def load_ticket_list():
            for w in scroll.winfo_children(): w.destroy()
            db = get_connection()
            if not db: return
            try:
                c = db.cursor(dictionary=True)
                if self.is_admin:
                    c.execute("SELECT h.*, u.full_name FROM help_tickets h JOIN user u ON h.user_id = u.user_id ORDER BY h.status ASC, h.created_at DESC")
                else:
                    c.execute("SELECT h.*, u.full_name FROM help_tickets h JOIN user u ON h.user_id = u.user_id WHERE h.user_id = %s ORDER BY h.created_at DESC", (self.user_info['user_id'],))
                
                for t in c.fetchall():
                    card = ctk.CTkFrame(scroll, fg_color="#F9FAFB", corner_radius=8, border_width=1, border_color="#E0E0E0")
                    card.pack(fill="x", pady=5)
                    
                    header = ctk.CTkFrame(card, fg_color="transparent")
                    header.pack(fill="x", padx=15, pady=(10, 5))
                    
                    status_col = "#D8000C" if t['status'] == 'Open' else "#2ECC71"
                    ctk.CTkLabel(header, text=f"[{t['status']}]", font=("Inter", 12, "bold"), text_color=status_col).pack(side="left", padx=(0, 10))
                    ctk.CTkLabel(header, text=t['subject'], font=("Inter", 12, "bold"), text_color="#1A1A1A").pack(side="left")
                    if self.is_admin:
                        ctk.CTkLabel(header, text=f"From: {t['full_name']}", font=("Inter", 11), text_color="gray").pack(side="right")
                        
                    ctk.CTkLabel(card, text=t['message'], font=("Inter", 11), text_color="#555555", justify="left", wraplength=700).pack(anchor="w", padx=15, pady=5)
                    
                    if t['admin_reply']:
                        reply_box = ctk.CTkFrame(card, fg_color="#E8F8F5", corner_radius=5)
                        reply_box.pack(fill="x", padx=15, pady=(5, 10))
                        ctk.CTkLabel(reply_box, text=f"Admin Reply: {t['admin_reply']}", font=("Inter", 11, "bold"), text_color="#1E4528", justify="left", wraplength=650).pack(anchor="w", padx=10, pady=10)
                    elif self.is_admin and t['status'] == 'Open':
                        reply_entry = ctk.CTkEntry(card, placeholder_text="Type reply here...")
                        reply_entry.pack(fill="x", padx=15, pady=5)
                        
                        def send_reply(tid=t['ticket_id'], e=reply_entry):
                            rep = e.get().strip()
                            if not rep: return
                            cx = get_connection()
                            cur = cx.cursor()
                            cur.execute("UPDATE help_tickets SET admin_reply = %s, status = 'Resolved' WHERE ticket_id = %s", (rep, tid))
                            cx.commit(); cur.close(); cx.close()
                            load_ticket_list()
                            
                        ctk.CTkButton(card, text="Reply & Resolve", width=120, height=28, fg_color="#3498DB", hover_color="#2980B9", command=send_reply).pack(anchor="e", padx=15, pady=(0, 10))
            except Exception: pass
            finally:
                if db.is_connected(): c.close(); db.close()
                
        load_ticket_list()