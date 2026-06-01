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
            "The system has three operational tiers: Admin, Staff, and Worker.",
            "Admin — Full system access: approvals, role management, maintenance, and reporting.",
            "Staff — Day-to-day operations: drafting projects, issuing/retrieving tools, viewing tracking logs.",
            "Worker — Field personnel. Workers do NOT log into the desktop system. They are registered so their IDs can be scanned for tool accountability on project sites.",
            "Use 'Forgot Password?' to send a reset request directly to the Admin Dashboard.",
        ]),
        (False, "2. Dashboard", [
            "The Dashboard shows four live metrics: Asset Utilization %, Active Workforce, Action Items, and Total Inventory.",
            "Action Items automatically count tools flagged as Damaged/Needs Repair/Lost plus overdue active projects.",
            "The 'Recent Activity Feed' shows a live log of recent system events.",
            "The 'Tool Condition Metrics' bar chart breaks down assets by condition (Good, Repair, Damaged, Lost).",
            "The Action Items card is clickable and opens Maintenance directly.",
            "The dashboard auto-refreshes every 5 seconds.",
            "For security, inactivity for 5 minutes triggers a warning; if ignored for 30 seconds, auto-logout executes.",
        ]),
        (True, "3. Products / Inventory (Admin)", [
            "Use the left form to register new tools or consumables into the system.",
            "Consumables (e.g., boxes of nails) support fractional quantities (e.g., 0.5 boxes).",
            "Click any row in the table to open the Edit/Archive modal.",
            "'Archive' safely removes a tool from active use and sends it to Maintenance → Archived Tools. The tool can be restored at any time.",
            "Archiving a tool does NOT delete transaction history — borrow/return records remain auditable.",
            "If quantity available is lower than total and tied to an active transaction, location may show as deployed to project.",
        ]),
        (False, "4. Project Management (Requisition Workflow)", [
            "Step 1 — Drafting: Fill Project Name, Client, Site Location, Project Head, and schedule dates.",
            "Step 2 — Worker Assignment: Assign workers by scanning or typing Employee IDs.",
            "Step 3 — Requisition: Browse inventory and select required tools/quantities.",
            "Step 4 — Submission: Click 'Submit for Approval' (project enters Pending).",
            "Step 5 — Admin Workflow: Approve → Ongoing → Complete → Archive to Maintenance when finished.",
            "Tools cannot be deployed until project status is Approved or Ongoing.",
            "Overdue active projects are surfaced in Dashboard and Action Items.",
        ]),
        (False, "5. QR Tag & Badge Format Explained", [
            "Tool Tag IDs generally follow organization-defined patterns (example: CFT-XXXX or TAG-###-CAT-SUP).",
            "PID means Product ID (internal tool_id in the database).",
            "TID/Tag ID is the scannable identifier attached to the physical item.",
            "A tool QR payload may include Tag ID, PID, Name, Location, and current Status/Condition.",
            "Employee QR badges include Employee ID and identity fields used for issuance/retrieval verification.",
            "TRN means Transaction Receipt Number used to trace issuance/retrieval records.",
            "If a QR label is damaged, manual entry of Tag ID, PID, Employee ID, or TRN is supported.",
        ]),
        (False, "6. Tagging (Tool Identity Management)", [
            "Open Tagging to assign, update, or unlink Tag IDs from tools.",
            "Use Universal Search and filter by Needs Tag / Already Tagged to narrow records.",
            "Click a row to open Tag Manager, then scan/type a Tag ID.",
            "Use Auto-Generate to build a smart tag from PID/category/supplier tokens.",
            "Save Tag Link writes tag_id to the tool record; unlink clears it.",
            "Use 'Scan & Test QR' to validate whether a scanned label maps to an active tool.",
            "Print label output can generate a PDF with QR and human-readable tag text.",
        ]),
        (False, "7. Tool Issuance (Deployment)", [
            "Issuance is project-gated: only approved/ongoing projects can receive tools.",
            "Step 1: Scan/enter assignee Employee ID and verify identity.",
            "Step 2: Select an eligible project assigned to that worker.",
            "Step 3: Review requisition requirements shown for the selected project.",
            "Step 4: Scan tool tag(s); non-requisition tools are blocked by the system.",
            "Step 5: Add tools to cart; quantity is validated against approved limits and available stock.",
            "Step 6: Click 'Issue Tools & Print Receipt' to create transactions and update inventory.",
            "A receipt is generated with TRN range and printable PDF preview.",
        ]),
        (False, "8. Tool Retrieval", [
            "Step 1: Scan surrendering Employee ID to authenticate return context.",
            "Step 2: Scan Tool Tag or enter TRN to locate active deployment records.",
            "Step 3: Set return condition (Good, Needs Repair, Damaged, Lost).",
            "Step 4: Add Condition Details for maintenance context.",
            "Step 5: Enter quantity to return (supports partial consumable returns where applicable).",
            "Step 6: Confirm retrieval to restock inventory and close active transactions.",
            "On confirmation, tool.condition is updated and reflected across modules.",
        ]),
        (False, "9. Tool Condition System", [
            "Good — Item is fully operational and available for normal deployment.",
            "Needs Repair — Item has a serviceable defect; route to maintenance workflow.",
            "Damaged — Item has major damage requiring repair or replacement decision.",
            "Lost — Item is missing/unrecoverable and should be flagged for accountability action.",
            "When condition is changed during retrieval or maintenance flagging, tool.condition updates in database immediately.",
            "Condition changes propagate to Inventory status, Dashboard condition chart, and Action Items counts.",
            "Maintenance issue rows can be resolved with updated condition and resolution notes.",
        ]),
        (True, "10. Tracking & Accountability (Admin)", [
            "Borrow/Return Logs — chronological record of tool movements; click rows for receipt detail.",
            "Audit Records — compare Active vs Returned states to detect discrepancies.",
            "Activity Log — full trail of logins, edits, searches, and navigation events.",
            "Use filters and keyword search to isolate users, tools, statuses, modules, or date-time context.",
        ]),
        (False, "11. Reports", [
            "ABC Analysis: Categorizes tools by deployment frequency using Pareto distribution.",
            "Tool Usage Report: Summarizes borrow totals, currently out count, quantity available, and condition.",
            "Employee Activity: Aggregates borrow/active/returned counts by employee.",
            "Export flow: Click '⎙ Export PDF' on a report tab, set optional date range/notes, then click '⎙ Export Now'.",
            "Date range is optional; leave blank to export all records.",
        ]),
        (True, "12. Maintenance & Centralized Archive (Admin Only)", [
            "Issues & Repairs: Submit flags (Damaged, Lost, Needs Repair, etc.) and investigate active issues.",
            "Important connectivity: flagging a tool updates tool.condition in database immediately.",
            "Because of this, flagged conditions appear in Inventory, Dashboard condition chart, and Action Items badge automatically.",
            "Archived Tools: restore previously archived inventory items.",
            "Archived Employees: restore deactivated users back to active status.",
            "Archived Projects: only explicitly archived projects appear; restore sets project back to active workflow state.",
        ]),
        (True, "13. Role Management (Admin Only)", [
            "Register users as Admin, Staff, or Worker.",
            "Workers are assignable/scannable personnel and do not receive desktop login credentials by default.",
            "Edit users to change role, update profile fields, and reset password policies.",
            "Deactivated users move to Maintenance → Archived Employees and can be restored later.",
        ]),
        (False, "14. Profile", [
            "View/update your name and email.",
            "Change password with current-password verification.",
            "Upload avatar image from local files.",
            "Print your Employee ID QR badge for site verification workflows.",
            "Borrowing history table shows your recent transactions and statuses.",
        ]),
    ]

    FAQS = [
        (False, "How do I issue a tool to a worker?",
         "Verify employee ID, select an approved/ongoing assigned project, scan tools listed in requisition, then click Issue to generate TRN and update stock."),
        (False, "What is the 'Worker' role and why can't they log in?",
         "Workers are field personnel identifiers used for accountability scanning. They are typically non-login accounts unless role is changed by Admin."),
        (False, "How do I add a description when returning a tool?",
         "Use the Condition Details box in Tool Retrieval before confirming return."),
        (True, "Where do completed projects or broken tools go?",
         "Archived objects go to Maintenance archive tabs; broken/repair/lost states are managed in Issues & Repairs."),
        (True, "Why is a project still showing in Project Management after I archived it?",
         "A project must be explicitly archived; status alone (Completed/Cancelled) does not move it to archive list."),
        (False, "I scanned a QR code but it didn't read. What do I do?",
         "Improve lighting/alignment and retry; if label is damaged, type Tag ID/PID/TRN manually."),
        (False, "Why can't I approve a Project Requisition?",
         "Only Admin accounts can approve pending requisitions."),
        (False, "Can I return only a partial amount of consumables?",
         "Yes, enter the exact return quantity (e.g., 0.5) where supported by the retrieval workflow."),
        (False, "How do I filter reports by date when exporting to PDF?",
         "Open export dialog, fill From/To dates in YYYY-MM-DD, then click Export Now."),
        (False, "Is my password stored securely?",
         "Yes, password hashes use bcrypt; plaintext passwords are not stored."),
        (False, "What does the Tag ID format look like and what do the parts mean?",
         "Tag formats are organization-defined (e.g., CFT-XXXX or TAG-###-CAT-SUP). Segments commonly represent sequence, category, and supplier tokens."),
        (False, "What happens when I mark a tool as 'Damaged' on return?",
         "The transaction closes, inventory restocks (if quantity returned), and tool.condition updates to Damaged for visibility in Inventory/Dashboard/Maintenance."),
        (False, "Can I issue the same tool to multiple projects simultaneously?",
         "Only within available quantity and requisition approvals. The system enforces stock and requirement constraints."),
        (False, "How do I see which tools are currently deployed and where?",
         "Use Inventory and Tracking logs; deployed items may display active project location/context."),
        (False, "What is the difference between 'Archive' and 'Delete' for a tool?",
         "Archive hides from active operations but preserves history and enables restore; delete is destructive and generally avoided for auditable assets."),
        (False, "Can a Worker be assigned to multiple projects at once?",
         "Yes, assignment depends on project planning and administrative controls."),
        (False, "What happens if I lose a physical QR tag label?",
         "Use manual entry (PID/Tag/TRN), then reprint and relink a replacement label in Tagging."),
        (False, "How does the ABC analysis categorize tools?",
         "By cumulative usage share: A (highest), B (middle), C (lowest), based on Pareto-style thresholds."),
        (True, "Who can see the Activity Log?",
         "Admins can access full activity logs in Tracking & Accountability."),
        (False, "What does 'Overdue' mean for a project?",
         "Project end date has passed while project is still active/not archived."),
        (True, "How do I restore an archived tool/employee/project?",
         "Go to Maintenance archive tabs and click Restore on the corresponding row."),
        (False, "What is a TRN and where do I find it?",
         "TRN is Transaction Receipt Number shown during issuance/retrieval history and receipt output."),
        (False, "Can I export reports without setting a date range?",
         "Yes, leave dates blank to export all records."),
        (False, "Why does a tool show as 'unavailable' even though it's in the warehouse?",
         "It may be reserved/deployed, quantity_available may be zero, or condition/status prevents issuance."),
        (False, "Why is Action Items non-zero on the dashboard?",
         "One or more tools are in Needs Repair/Damaged/Lost condition and/or active projects are overdue."),
        (False, "Does maintenance flagging really update inventory data?",
         "Yes. Maintenance flagging writes to tool.condition; connected modules reflect the change immediately."),
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
        ctk.CTkLabel(top_bar, text="Looking to export data? Use the 'Reports' module for PDF generation.", font=("Inter", 11, "italic"), text_color="#3498DB").pack(side="left", padx=10)

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