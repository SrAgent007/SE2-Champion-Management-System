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

        self._ensure_custom_table()
        self.build_ui()

    # ------------------------------------------------------------------
    # DB helpers for custom help content
    # ------------------------------------------------------------------
    def _ensure_custom_table(self):
        """Create help_custom_items table if it does not yet exist."""
        conn = get_connection()
        if not conn:
            return
        try:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS help_custom_items (
                    item_id     INT AUTO_INCREMENT PRIMARY KEY,
                    item_type   VARCHAR(10)  NOT NULL COMMENT 'guide or faq',
                    admin_only  TINYINT(1)   NOT NULL DEFAULT 0,
                    title       VARCHAR(255) NOT NULL,
                    content     TEXT         NOT NULL,
                    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        except Exception as e:
            print(f"help_custom_items init error: {e}")
        finally:
            if conn.is_connected():
                c.close()
                conn.close()

    def _fetch_custom_items(self, item_type):
        """Return list of dicts for the given item_type ('guide' or 'faq')."""
        rows = []
        conn = get_connection()
        if not conn:
            return rows
        try:
            c = conn.cursor(dictionary=True)
            c.execute(
                "SELECT * FROM help_custom_items WHERE item_type = %s ORDER BY item_id ASC",
                (item_type,)
            )
            rows = c.fetchall()
        except Exception as e:
            print(f"_fetch_custom_items error: {e}")
        finally:
            if conn.is_connected():
                c.close()
                conn.close()
        return rows

    def _delete_custom_item(self, item_id):
        conn = get_connection()
        if not conn:
            return
        try:
            c = conn.cursor()
            c.execute(
                "DELETE FROM help_custom_items WHERE item_id = %s", (item_id,))
            conn.commit()
        except Exception as e:
            print(f"_delete_custom_item error: {e}")
        finally:
            if conn.is_connected():
                c.close()
                conn.close()

    def build_ui(self):
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(top_bar, text="Help & Support Hub", font=(
            "Inter", 20, "bold"), text_color="#1A1A1A").pack(side="left", padx=20)
        ctk.CTkLabel(top_bar, text="Looking to export data? Use the 'Reports' module for PDF generation.", font=(
            "Inter", 11, "italic"), text_color="#3498DB").pack(side="left", padx=10)

        tabs = ["Help Guide", "FAQs", "System Requirements", "Support Tickets"]
        if self.is_admin:
            tabs.append("Manage Help Content")
        self.tab_var = ctk.StringVar(value=tabs[0])

        self.seg_btn = ctk.CTkSegmentedButton(
            top_bar, values=tabs, variable=self.tab_var, command=self.switch_tab,
            fg_color="#F0F0F0", selected_color="#1E4528", selected_hover_color="#14301C"
        )
        self.seg_btn.pack(side="right", padx=20)
        self.seg_btn.set(tabs[0])

        self.tab_content = ctk.CTkFrame(
            self, fg_color="white", corner_radius=10)
        self.tab_content.grid(
            row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.tab_content.grid_columnconfigure(0, weight=1)
        self.tab_content.grid_rowconfigure(0, weight=1)

        self.switch_tab(tabs[0])

    def switch_tab(self, selected_tab):
        for widget in self.tab_content.winfo_children():
            widget.destroy()
        if selected_tab == "Help Guide":
            self.render_guide_tab()
        elif selected_tab == "FAQs":
            self.render_faq_tab()
        elif selected_tab == "System Requirements":
            self.render_sysreq_tab()
        elif selected_tab == "Support Tickets":
            self.render_tickets_tab()
        elif selected_tab == "Manage Help Content":
            self.render_manage_tab()

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

        # Custom DB guide entries
        for row in self._fetch_custom_items("guide"):
            if row["admin_only"] and not self.is_admin:
                continue
            points_db = [p.strip()
                         for p in row["content"].split("\n") if p.strip()]
            if keyword and not self._section_matches(row["title"], points_db, keyword):
                continue

            found_any = True
            card = ctk.CTkFrame(scroll, fg_color="#EFF9F3", corner_radius=8,
                                border_width=1, border_color="#B2DFCA")
            card.pack(fill="x", padx=10, pady=(0, 6))

            ctk.CTkLabel(card, text=row["title"], font=("Inter", 12, "bold"),
                         text_color="#1E4528").pack(anchor="w", padx=14, pady=(8, 3))
            for point in points_db:
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

        # Custom DB FAQ entries
        for row in self._fetch_custom_items("faq"):
            if row["admin_only"] and not self.is_admin:
                continue
            if keyword and not self._section_matches(row["title"], [row["content"]], keyword):
                continue

            found_any = True
            card = ctk.CTkFrame(scroll, fg_color="#EFF9F3", corner_radius=8,
                                border_width=1, border_color="#B2DFCA")
            card.pack(fill="x", padx=10, pady=(0, 6))

            ctk.CTkLabel(card, text=f"Q{idx}.  {row['title']}",
                         font=("Inter", 11, "bold"), text_color="#1E4528",
                         wraplength=780, justify="left").pack(anchor="w", padx=14, pady=(10, 2))
            ctk.CTkLabel(card, text=f"      {row['content']}",
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
        outer = ctk.CTkFrame(
            self.tab_content, fg_color="white", corner_radius=10)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=1)

        # Top bar: title + admin button
        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(hdr, text="System Requirements",
                     font=("Inter", 18, "bold"), text_color="#1E4528").pack(side="left")
        if self.is_admin:
            ctk.CTkButton(
                hdr, text="+ Add / Edit Requirement", width=170, height=30,
                fg_color="#1E4528", hover_color="#14301C",
                font=("Inter", 11, "bold"),
                command=self._open_sysreq_form
            ).pack(side="right")

        frame = ctk.CTkScrollableFrame(outer, fg_color="transparent")
        frame.pack(fill="both", expand=True)
        self._sysreq_scroll_frame = frame

        self._render_sysreq_content()

    def _render_sysreq_content(self):
        frame = self._sysreq_scroll_frame
        for w in frame.winfo_children():
            w.destroy()

        hardware_specs = [
            ("Processor",        "Intel Core i3 or equivalent (64-bit)"),
            ("RAM",              "Minimum 8 GB"),
            ("Storage",          "At least 500 MB free disk space"),
            ("Operating System", "Windows 10 (64-bit) — recommended and tested"),
            ("Display",          "Minimum 1280×720 resolution (1920×1080 recommended)"),
            ("Webcam",           "HD Webcam 1080P — required for QR scanning features"),
            ("Printer",
             "Any standard printer — required for label and receipt printing"),
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

        def render_table(parent, title, specs, custom_rows=None, editable=False):
            ctk.CTkLabel(parent, text=title, font=("Inter", 13, "bold"),
                         text_color="#1A1A1A").pack(anchor="w", padx=20, pady=(6, 4))
            card = ctk.CTkFrame(parent, fg_color="#F9FAFB", corner_radius=8)
            card.pack(fill="x", padx=20, pady=(0, 12))

            # Built-in rows (read-only)
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

            # Custom DB rows
            if custom_rows:
                for i, db_row in enumerate(custom_rows):
                    base_i = len(specs) + i
                    row = ctk.CTkFrame(card,
                                       fg_color="#EFF9F3" if base_i % 2 == 0 else "#E8F5EE",
                                       height=34)
                    row.pack(fill="x")
                    row.pack_propagate(False)
                    row.grid_columnconfigure(0, weight=1)
                    row.grid_columnconfigure(1, weight=2)
                    row.grid_columnconfigure(2, weight=0)
                    ctk.CTkLabel(row, text=db_row["title"], font=("Inter", 11, "bold"),
                                 text_color="#1E4528").grid(row=0, column=0, padx=14, pady=6, sticky="w")
                    ctk.CTkLabel(row, text=db_row["content"], font=("Inter", 11),
                                 text_color="#1A1A1A").grid(row=0, column=1, padx=14, pady=6, sticky="w")
                    if editable:
                        act = ctk.CTkFrame(row, fg_color="transparent")
                        act.grid(row=0, column=2, padx=8, pady=4, sticky="e")
                        ctk.CTkButton(act, text="✎", width=28, height=24,
                                      fg_color="#3498DB", hover_color="#2980B9",
                                      font=("Inter", 10, "bold"),
                                      command=lambda r=db_row: self._open_sysreq_form(
                                          r)
                                      ).pack(side="left", padx=(0, 4))
                        ctk.CTkButton(act, text="🗑", width=28, height=24,
                                      fg_color="#D8000C", hover_color="#B00000",
                                      font=("Inter", 10, "bold"),
                                      command=lambda r=db_row: self._delete_sysreq_row(
                                          r)
                                      ).pack(side="left")

        # Fetch custom sysreq rows and split by category stored in admin_only field trick:
        # We store category in the title prefix — "Hardware: ..." or "Software: ..."
        # The category is stored as item_type="sysreq" and we use the title field to carry
        # the component label and content to carry the value.
        # admin_only=0 → Hardware table, admin_only=1 → Software table
        hw_custom = [r for r in self._fetch_custom_items(
            "sysreq") if r["admin_only"] == 0]
        sw_custom = [r for r in self._fetch_custom_items(
            "sysreq") if r["admin_only"] == 1]

        render_table(frame, "Hardware Requirements", hardware_specs,
                     custom_rows=hw_custom, editable=self.is_admin)
        render_table(frame, "Software Requirements", software_specs,
                     custom_rows=sw_custom, editable=self.is_admin)

        ctk.CTkLabel(
            frame,
            text="Note: The system is a LAN-based desktop application. No internet connection is required "
                 "for normal operation. All data is stored locally in the MySQL database.",
            font=("Inter", 11), text_color="gray", wraplength=780, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 20))

    def _open_sysreq_form(self, existing_row=None):
        """Popup dialog to add or edit a sysreq row."""
        dialog = ctk.CTkToplevel(self.winfo_toplevel())
        dialog.title("Edit Requirement" if existing_row else "Add Requirement")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        # Centre the dialog
        dialog.update_idletasks()
        sw, sh = dialog.winfo_screenwidth(), dialog.winfo_screenheight()
        dialog.geometry(f"420x310+{(sw-420)//2}+{(sh-310)//2}")

        bg = ctk.CTkFrame(dialog, fg_color="white", corner_radius=10,
                          border_width=1, border_color="#E0E0E0")
        bg.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(bg, text="Edit Requirement" if existing_row else "Add New Requirement",
                     font=("Inter", 14, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=15, pady=(12, 8))

        # Category selector (Hardware vs Software)
        cat_row = ctk.CTkFrame(bg, fg_color="transparent")
        cat_row.pack(fill="x", padx=15, pady=(0, 8))
        ctk.CTkLabel(cat_row, text="Category:", font=("Inter", 11, "bold"),
                     text_color="#555555", width=80, anchor="w").pack(side="left")
        cat_var = ctk.IntVar(
            value=existing_row["admin_only"] if existing_row else 0)
        ctk.CTkRadioButton(cat_row, text="Hardware", variable=cat_var, value=0,
                           font=("Inter", 11), text_color="#1A1A1A").pack(side="left", padx=(0, 12))
        ctk.CTkRadioButton(cat_row, text="Software", variable=cat_var, value=1,
                           font=("Inter", 11), text_color="#1A1A1A").pack(side="left")

        # Component label
        ctk.CTkLabel(bg, text="Component / Label:",
                     font=("Inter", 11, "bold"), text_color="#555555").pack(anchor="w", padx=15, pady=(0, 2))
        lbl_entry = ctk.CTkEntry(
            bg, placeholder_text="e.g.  GPU  or  Database")
        lbl_entry.pack(fill="x", padx=15, pady=(0, 8))
        if existing_row:
            lbl_entry.insert(0, existing_row["title"])

        # Value / specification
        ctk.CTkLabel(bg, text="Specification / Value:",
                     font=("Inter", 11, "bold"), text_color="#555555").pack(anchor="w", padx=15, pady=(0, 2))
        val_entry = ctk.CTkEntry(
            bg, placeholder_text="e.g.  NVIDIA GTX 1060 or higher")
        val_entry.pack(fill="x", padx=15, pady=(0, 8))
        if existing_row:
            val_entry.insert(0, existing_row["content"])

        status_lbl = ctk.CTkLabel(bg, text="", font=(
            "Inter", 11), text_color="#D8000C")
        status_lbl.pack(anchor="w", padx=15)

        def save():
            label_val = lbl_entry.get().strip()
            spec_val = val_entry.get().strip()
            if not label_val or not spec_val:
                status_lbl.configure(text="⚠ Both fields are required.")
                return
            conn = get_connection()
            if not conn:
                status_lbl.configure(text="⚠ Database connection failed.")
                return
            try:
                c = conn.cursor()
                if existing_row:
                    c.execute(
                        "UPDATE help_custom_items SET admin_only=%s, title=%s, content=%s WHERE item_id=%s",
                        (cat_var.get(), label_val,
                         spec_val, existing_row["item_id"])
                    )
                else:
                    c.execute(
                        "INSERT INTO help_custom_items (item_type, admin_only, title, content) VALUES ('sysreq', %s, %s, %s)",
                        (cat_var.get(), label_val, spec_val)
                    )
                conn.commit()
            except Exception as e:
                status_lbl.configure(text=f"⚠ Error: {e}")
                return
            finally:
                if conn.is_connected():
                    c.close()
                    conn.close()
            dialog.destroy()
            self._render_sysreq_content()

        btn_row = ctk.CTkFrame(bg, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(4, 12))
        ctk.CTkButton(btn_row, text="✔ Save", width=100, height=32,
                      fg_color="#1E4528", hover_color="#14301C",
                      font=("Inter", 11, "bold"), command=save).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Cancel", width=80, height=32,
                      fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC",
                      font=("Inter", 11), command=dialog.destroy).pack(side="left")

    def _delete_sysreq_row(self, row):
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete requirement:\n\"{row['title']} — {row['content']}\"\n\nThis cannot be undone.",
            parent=self.winfo_toplevel()
        ):
            return
        self._delete_custom_item(row["item_id"])
        self._render_sysreq_content()

    # ==========================================
    # SUPPORT TICKETS TAB
    # ==========================================
    def render_tickets_tab(self):
        frame = ctk.CTkFrame(
            self.tab_content, fg_color="white", corner_radius=10)
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
            except Exception:
                pass
            finally:
                if conn.is_connected():
                    c.close()
                    conn.close()

        if not self.is_admin:
            form_bg = ctk.CTkFrame(frame, fg_color="#F9FAFB", corner_radius=10)
            form_bg.pack(fill="x", padx=20, pady=(20, 10))

            ctk.CTkLabel(form_bg, text="Submit an Inquiry", font=(
                "Inter", 14, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=15, pady=(15, 5))

            subj_entry = ctk.CTkEntry(form_bg, placeholder_text="Subject...")
            subj_entry.pack(fill="x", padx=15, pady=5)

            msg_entry = ctk.CTkTextbox(form_bg, height=60)
            msg_entry.pack(fill="x", padx=15, pady=5)

            def submit_ticket():
                subj = subj_entry.get().strip()
                msg = msg_entry.get("1.0", "end-1c").strip()
                if not subj or not msg:
                    messagebox.showerror(
                        "Error", "Subject and message required.", parent=self.winfo_toplevel())
                    return

                db = get_connection()
                if db:
                    c = db.cursor()
                    c.execute("INSERT INTO help_tickets (user_id, subject, message) VALUES (%s, %s, %s)", (
                        self.user_info['user_id'], subj, msg))
                    db.commit()
                    c.close()
                    db.close()
                    messagebox.showinfo(
                        "Success", "Ticket submitted to the Admin.", parent=self.winfo_toplevel())
                    subj_entry.delete(0, 'end')
                    msg_entry.delete("1.0", "end")
                    load_ticket_list()

            ctk.CTkButton(form_bg, text="Send to Admin", fg_color="#1E4528", hover_color="#14301C",
                          command=submit_ticket).pack(anchor="e", padx=15, pady=(5, 15))

        ctk.CTkLabel(frame, text="Ticket Inbox" if self.is_admin else "My Previous Tickets", font=(
            "Inter", 14, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20, pady=(10, 5))

        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        def load_ticket_list():
            for w in scroll.winfo_children():
                w.destroy()
            db = get_connection()
            if not db:
                return
            try:
                c = db.cursor(dictionary=True)
                if self.is_admin:
                    c.execute(
                        "SELECT h.*, u.full_name FROM help_tickets h JOIN user u ON h.user_id = u.user_id ORDER BY h.status ASC, h.created_at DESC")
                else:
                    c.execute(
                        "SELECT h.*, u.full_name FROM help_tickets h JOIN user u ON h.user_id = u.user_id WHERE h.user_id = %s ORDER BY h.created_at DESC", (self.user_info['user_id'],))

                for t in c.fetchall():
                    card = ctk.CTkFrame(
                        scroll, fg_color="#F9FAFB", corner_radius=8, border_width=1, border_color="#E0E0E0")
                    card.pack(fill="x", pady=5)

                    header = ctk.CTkFrame(card, fg_color="transparent")
                    header.pack(fill="x", padx=15, pady=(10, 5))

                    status_col = "#D8000C" if t['status'] == 'Open' else "#2ECC71"
                    ctk.CTkLabel(header, text=f"[{t['status']}]", font=(
                        "Inter", 12, "bold"), text_color=status_col).pack(side="left", padx=(0, 10))
                    ctk.CTkLabel(header, text=t['subject'], font=(
                        "Inter", 12, "bold"), text_color="#1A1A1A").pack(side="left")
                    if self.is_admin:
                        ctk.CTkLabel(header, text=f"From: {t['full_name']}", font=(
                            "Inter", 11), text_color="gray").pack(side="right")

                    ctk.CTkLabel(card, text=t['message'], font=(
                        "Inter", 11), text_color="#555555", justify="left", wraplength=700).pack(anchor="w", padx=15, pady=5)

                    if t['admin_reply']:
                        reply_box = ctk.CTkFrame(
                            card, fg_color="#E8F8F5", corner_radius=5)
                        reply_box.pack(fill="x", padx=15, pady=(5, 10))
                        ctk.CTkLabel(reply_box, text=f"Admin Reply: {t['admin_reply']}", font=(
                            "Inter", 11, "bold"), text_color="#1E4528", justify="left", wraplength=650).pack(anchor="w", padx=10, pady=10)
                    elif self.is_admin and t['status'] == 'Open':
                        reply_entry = ctk.CTkEntry(
                            card, placeholder_text="Type reply here...")
                        reply_entry.pack(fill="x", padx=15, pady=5)

                        def send_reply(tid=t['ticket_id'], e=reply_entry):
                            rep = e.get().strip()
                            if not rep:
                                return
                            cx = get_connection()
                            cur = cx.cursor()
                            cur.execute(
                                "UPDATE help_tickets SET admin_reply = %s, status = 'Resolved' WHERE ticket_id = %s", (rep, tid))
                            cx.commit()
                            cur.close()
                            cx.close()
                            load_ticket_list()

                        ctk.CTkButton(card, text="Reply & Resolve", width=120, height=28, fg_color="#3498DB",
                                      hover_color="#2980B9", command=send_reply).pack(anchor="e", padx=15, pady=(0, 10))
            except Exception:
                pass
            finally:
                if db.is_connected():
                    c.close()
                    db.close()

        load_ticket_list()

    # ==========================================
    # MANAGE HELP CONTENT TAB  (Admin only)
    # ==========================================
    def render_manage_tab(self):
        """
        Full CRUD panel for custom Help Guide sections and FAQ entries.
        Hard-coded GUIDE_SECTIONS / FAQS are read-only; only DB rows
        (help_custom_items) are editable here.
        """
        outer = ctk.CTkFrame(
            self.tab_content, fg_color="white", corner_radius=10)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        ctk.CTkLabel(hdr, text="Manage Help Content",
                     font=("Inter", 18, "bold"), text_color="#1E4528").pack(side="left")
        ctk.CTkLabel(hdr,
                     text="Add, edit, or delete custom Guide sections and FAQs. Built-in entries are read-only.",
                     font=("Inter", 11, "italic"), text_color="gray").pack(side="left", padx=12)

        # Split: left = form, right = existing custom items list
        body = ctk.CTkFrame(outer, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=15, pady=10)
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        # ── LEFT: Add / Edit Form ──────────────────────────────────────
        form_card = ctk.CTkFrame(body, fg_color="#F9FAFB", corner_radius=8)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self._manage_editing_id = None  # None = Add mode, int = Edit mode

        ctk.CTkLabel(form_card, text="Add / Edit Item",
                     font=("Inter", 13, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=15, pady=(14, 6))

        # Type selector
        type_row = ctk.CTkFrame(form_card, fg_color="transparent")
        type_row.pack(fill="x", padx=15, pady=(0, 6))
        ctk.CTkLabel(type_row, text="Type:", font=("Inter", 11, "bold"),
                     text_color="#555555", width=80, anchor="w").pack(side="left")
        self._manage_type_var = ctk.StringVar(value="guide")
        ctk.CTkRadioButton(type_row, text="Help Guide Section",
                           variable=self._manage_type_var, value="guide",
                           font=("Inter", 11), text_color="#1A1A1A").pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(type_row, text="FAQ Entry",
                           variable=self._manage_type_var, value="faq",
                           font=("Inter", 11), text_color="#1A1A1A").pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(type_row, text="System Requirement",
                           variable=self._manage_type_var, value="sysreq",
                           font=("Inter", 11), text_color="#1A1A1A").pack(side="left")

        # Admin-only toggle
        admin_row = ctk.CTkFrame(form_card, fg_color="transparent")
        admin_row.pack(fill="x", padx=15, pady=(0, 6))
        self._manage_admin_var = ctk.IntVar(value=0)
        ctk.CTkCheckBox(admin_row, text="Admin-only (hidden from Staff)",
                        variable=self._manage_admin_var,
                        font=("Inter", 11), text_color="#1A1A1A",
                        checkbox_width=18, checkbox_height=18,
                        border_color="#D1D5DB").pack(anchor="w")

        # Title field
        ctk.CTkLabel(form_card, text="Title / Question:",
                     font=("Inter", 11, "bold"), text_color="#555555").pack(anchor="w", padx=15, pady=(4, 2))
        self._manage_title_entry = ctk.CTkEntry(
            form_card, placeholder_text="e.g.  15. Custom Section Title")
        self._manage_title_entry.pack(fill="x", padx=15, pady=(0, 8))

        # Content field
        ctk.CTkLabel(form_card,
                     text="Content / Answer / Specification:\n(Guide: one bullet per line  |  FAQ: single answer  |  Sysreq: spec value)",
                     font=("Inter", 11, "bold"), text_color="#555555", justify="left").pack(anchor="w", padx=15, pady=(0, 2))
        self._manage_content_box = ctk.CTkTextbox(form_card, height=160)
        self._manage_content_box.pack(fill="x", padx=15, pady=(0, 12))

        # Form status label
        self._manage_status_lbl = ctk.CTkLabel(form_card, text="",
                                               font=("Inter", 11), text_color="#D8000C")
        self._manage_status_lbl.pack(anchor="w", padx=15)

        # Action buttons row
        btn_row = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(4, 14))

        self._manage_save_btn = ctk.CTkButton(
            btn_row, text="+ Add Item", width=110, height=32,
            fg_color="#1E4528", hover_color="#14301C",
            font=("Inter", 11, "bold"),
            command=self._save_manage_item
        )
        self._manage_save_btn.pack(side="left", padx=(0, 8))

        self._manage_cancel_btn = ctk.CTkButton(
            btn_row, text="✕ Cancel", width=80, height=32,
            fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC",
            font=("Inter", 11),
            command=self._reset_manage_form
        )
        self._manage_cancel_btn.pack(side="left")

        # ── RIGHT: Existing Custom Items List ─────────────────────────
        list_card = ctk.CTkFrame(body, fg_color="#F9FAFB", corner_radius=8)
        list_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        list_card.grid_rowconfigure(1, weight=1)
        list_card.grid_columnconfigure(0, weight=1)

        list_hdr = ctk.CTkFrame(list_card, fg_color="transparent")
        list_hdr.grid(row=0, column=0, sticky="ew", padx=15, pady=(14, 4))
        ctk.CTkLabel(list_hdr, text="Custom Items",
                     font=("Inter", 13, "bold"), text_color="#1A1A1A").pack(side="left")
        ctk.CTkLabel(list_hdr, text="(Built-in entries not shown here)",
                     font=("Inter", 10, "italic"), text_color="gray").pack(side="left", padx=8)

        self._manage_list_scroll = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent")
        self._manage_list_scroll.grid(
            row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self._render_manage_list()

    # ── helpers ──────────────────────────────────────────────────────────

    def _render_manage_list(self):
        scroll = self._manage_list_scroll
        for w in scroll.winfo_children():
            w.destroy()

        guide_rows = self._fetch_custom_items("guide")
        faq_rows = self._fetch_custom_items("faq")
        all_rows = guide_rows + faq_rows

        if not all_rows:
            ctk.CTkLabel(scroll, text="No custom items yet. Use the form to add one.",
                         text_color="gray", font=("Inter", 11)).pack(pady=20)
            return

        for i, row in enumerate(all_rows):
            bg = "#FFFFFF" if i % 2 == 0 else "#F0F0F0"
            card = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=6,
                                border_width=1, border_color="#E0E0E0")
            card.pack(fill="x", pady=(0, 5))

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8, 2))

            # Type badge
            type_color = {"guide": "#1E4528", "faq": "#2980B9",
                          "sysreq": "#7D3C98"}.get(row["item_type"], "#555555")
            type_label = {"guide": "Guide", "faq": "FAQ", "sysreq": "Sys Req"}.get(
                row["item_type"], row["item_type"])
            ctk.CTkLabel(top, text=type_label,
                         fg_color=type_color, text_color="white",
                         font=("Inter", 10, "bold"), corner_radius=4,
                         padx=6, pady=2).pack(side="left", padx=(0, 8))

            if row["admin_only"] and row["item_type"] != "sysreq":
                ctk.CTkLabel(top, text="Admin Only",
                             fg_color="#E67E22", text_color="white",
                             font=("Inter", 10, "bold"), corner_radius=4,
                             padx=6, pady=2).pack(side="left", padx=(0, 8))
            elif row["item_type"] == "sysreq":
                cat_label = "Hardware" if row["admin_only"] == 0 else "Software"
                ctk.CTkLabel(top, text=cat_label,
                             fg_color="#E67E22", text_color="white",
                             font=("Inter", 10, "bold"), corner_radius=4,
                             padx=6, pady=2).pack(side="left", padx=(0, 8))

            ctk.CTkLabel(top, text=row["title"],
                         font=("Inter", 11, "bold"), text_color="#1A1A1A",
                         wraplength=340, justify="left").pack(side="left")

            # Content preview
            preview = row["content"][:120] + \
                ("…" if len(row["content"]) > 120 else "")
            ctk.CTkLabel(card, text=preview,
                         font=("Inter", 10), text_color="#555555",
                         wraplength=380, justify="left").pack(anchor="w", padx=12, pady=(0, 6))

            # Edit / Delete buttons
            btn_bar = ctk.CTkFrame(card, fg_color="transparent")
            btn_bar.pack(anchor="e", padx=12, pady=(0, 8))

            ctk.CTkButton(
                btn_bar, text="✎ Edit", width=65, height=26,
                fg_color="#3498DB", hover_color="#2980B9",
                font=("Inter", 10, "bold"),
                command=lambda r=row: self._load_item_for_edit(r)
            ).pack(side="left", padx=(0, 6))

            ctk.CTkButton(
                btn_bar, text="🗑 Delete", width=72, height=26,
                fg_color="#D8000C", hover_color="#B00000",
                font=("Inter", 10, "bold"),
                command=lambda r=row: self._confirm_delete_item(r)
            ).pack(side="left")

    def _save_manage_item(self):
        """Insert (Add) or UPDATE (Edit) a custom help item."""
        title = self._manage_title_entry.get().strip()
        content = self._manage_content_box.get("1.0", "end-1c").strip()
        itype = self._manage_type_var.get()
        admin_only = self._manage_admin_var.get()

        if not title or not content:
            self._manage_status_lbl.configure(
                text="⚠ Title and content are required.")
            return

        conn = get_connection()
        if not conn:
            self._manage_status_lbl.configure(
                text="⚠ Database connection failed.")
            return

        try:
            c = conn.cursor()
            if self._manage_editing_id is None:
                # INSERT
                c.execute(
                    "INSERT INTO help_custom_items (item_type, admin_only, title, content) VALUES (%s, %s, %s, %s)",
                    (itype, admin_only, title, content)
                )
                msg = "Item added successfully."
            else:
                # UPDATE
                c.execute(
                    "UPDATE help_custom_items SET item_type=%s, admin_only=%s, title=%s, content=%s WHERE item_id=%s",
                    (itype, admin_only, title, content, self._manage_editing_id)
                )
                msg = "Item updated successfully."
            conn.commit()
            self._manage_status_lbl.configure(
                text=f"✔ {msg}", text_color="#2ECC71")
        except Exception as e:
            self._manage_status_lbl.configure(text=f"⚠ Error: {e}")
            return
        finally:
            if conn.is_connected():
                c.close()
                conn.close()

        self._reset_manage_form()
        self._render_manage_list()

    def _load_item_for_edit(self, row):
        """Populate the form with an existing item for editing."""
        self._manage_editing_id = row["item_id"]
        self._manage_type_var.set(row["item_type"])
        self._manage_admin_var.set(int(row["admin_only"]))

        self._manage_title_entry.delete(0, "end")
        self._manage_title_entry.insert(0, row["title"])

        self._manage_content_box.delete("1.0", "end")
        self._manage_content_box.insert("1.0", row["content"])

        self._manage_save_btn.configure(text="✔ Save Changes")
        self._manage_status_lbl.configure(
            text="Editing item — make changes and click Save.", text_color="#3498DB")

    def _confirm_delete_item(self, row):
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete custom item:\n\"{row['title']}\"\n\nThis action cannot be undone.",
            parent=self.winfo_toplevel()
        ):
            return
        self._delete_custom_item(row["item_id"])
        # If we were editing this item, reset the form
        if self._manage_editing_id == row["item_id"]:
            self._reset_manage_form()
        self._render_manage_list()

    def _reset_manage_form(self):
        """Clear the form and return to Add mode."""
        self._manage_editing_id = None
        self._manage_type_var.set("guide")
        self._manage_admin_var.set(0)
        self._manage_title_entry.delete(0, "end")
        self._manage_content_box.delete("1.0", "end")
        self._manage_save_btn.configure(text="+ Add Item")
        self._manage_status_lbl.configure(text="", text_color="#D8000C")


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

        self._ensure_custom_table()
        self.build_ui()

    # ------------------------------------------------------------------
    # DB helpers for help content  (defaults + custom)
    # ------------------------------------------------------------------
    def _ensure_custom_table(self):
        """
        Create / migrate help_custom_items and seed all built-in items as
        default rows (is_default=1) on first run.  Safe to call every time —
        seeding is skipped when defaults already exist.
        """
        conn = get_connection()
        if not conn:
            return
        try:
            c = conn.cursor()
            # Base table
            c.execute("""
                CREATE TABLE IF NOT EXISTS help_custom_items (
                    item_id         INT AUTO_INCREMENT PRIMARY KEY,
                    item_type       VARCHAR(10)  NOT NULL COMMENT 'guide | faq | sysreq',
                    admin_only      TINYINT(1)   NOT NULL DEFAULT 0,
                    title           VARCHAR(255) NOT NULL,
                    content         TEXT         NOT NULL,
                    is_default      TINYINT(1)   NOT NULL DEFAULT 0,
                    default_content TEXT         NULL COMMENT 'original value for reset',
                    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

            # Migration: add columns if upgrading from previous version
            for col, defn in [
                ("is_default",      "TINYINT(1) NOT NULL DEFAULT 0"),
                ("default_content", "TEXT NULL"),
            ]:
                try:
                    c.execute(
                        f"ALTER TABLE help_custom_items ADD COLUMN {col} {defn}")
                    conn.commit()
                except Exception:
                    pass  # column already exists — fine

            # Seed defaults only once
            c.execute(
                "SELECT COUNT(*) FROM help_custom_items WHERE is_default = 1")
            if c.fetchone()[0] > 0:
                return  # already seeded

            rows_to_seed = []

            # Guide sections → content = bullet points joined by \n
            for admin_only, title, points in self.GUIDE_SECTIONS:
                content = "\n".join(points)
                rows_to_seed.append(
                    ("guide", int(admin_only), title, content, 1, content))

            # FAQs → content = answer string
            for admin_only, question, answer in self.FAQS:
                rows_to_seed.append(
                    ("faq", int(admin_only), question, answer, 1, answer))

            # System Requirements → admin_only reused as category (0=HW, 1=SW)
            hardware_specs = [
                ("Processor",        "Intel Core i3 or equivalent (64-bit)"),
                ("RAM",              "Minimum 8 GB"),
                ("Storage",          "At least 500 MB free disk space"),
                ("Operating System", "Windows 10 (64-bit) — recommended and tested"),
                ("Display",          "Minimum 1280×720 resolution (1920×1080 recommended)"),
                ("Webcam",           "HD Webcam 1080P — required for QR scanning features"),
                ("Printer",
                 "Any standard printer — required for label and receipt printing"),
                ("Network",
                 "LAN connection for database access (no internet required)"),
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
            for label, val in hardware_specs:
                rows_to_seed.append(("sysreq", 0, label, val, 1, val))
            for label, val in software_specs:
                rows_to_seed.append(("sysreq", 1, label, val, 1, val))

            c.executemany(
                "INSERT INTO help_custom_items "
                "(item_type, admin_only, title, content, is_default, default_content) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                rows_to_seed
            )
            conn.commit()

        except Exception as e:
            print(f"help_custom_items init error: {e}")
        finally:
            if conn.is_connected():
                c.close()
                conn.close()

    def _fetch_custom_items(self, item_type):
        """Return all rows for the given item_type, ordered by item_id."""
        rows = []
        conn = get_connection()
        if not conn:
            return rows
        try:
            c = conn.cursor(dictionary=True)
            c.execute(
                "SELECT * FROM help_custom_items WHERE item_type = %s ORDER BY item_id ASC",
                (item_type,)
            )
            rows = c.fetchall()
        except Exception as e:
            print(f"_fetch_custom_items error: {e}")
        finally:
            if conn.is_connected():
                c.close()
                conn.close()
        return rows

    def _delete_custom_item(self, item_id):
        """Delete a non-default row.  Default rows cannot be deleted."""
        conn = get_connection()
        if not conn:
            return
        try:
            c = conn.cursor()
            c.execute(
                "DELETE FROM help_custom_items WHERE item_id = %s AND is_default = 0",
                (item_id,)
            )
            conn.commit()
        except Exception as e:
            print(f"_delete_custom_item error: {e}")
        finally:
            if conn.is_connected():
                c.close()
                conn.close()

    def _reset_item_to_default(self, item_id):
        """Restore title+content to the original seeded default_content."""
        conn = get_connection()
        if not conn:
            return
        try:
            c = conn.cursor()
            c.execute(
                "UPDATE help_custom_items SET content = default_content WHERE item_id = %s AND is_default = 1",
                (item_id,)
            )
            conn.commit()
        except Exception as e:
            print(f"_reset_item_to_default error: {e}")
        finally:
            if conn.is_connected():
                c.close()
                conn.close()

    def build_ui(self):
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(top_bar, text="Help & Support Hub", font=(
            "Inter", 20, "bold"), text_color="#1A1A1A").pack(side="left", padx=20)
        ctk.CTkLabel(top_bar, text="Looking to export data? Use the 'Reports' module for PDF generation.", font=(
            "Inter", 11, "italic"), text_color="#3498DB").pack(side="left", padx=10)

        tabs = ["Help Guide", "FAQs", "System Requirements", "Support Tickets"]
        if self.is_admin:
            tabs.append("Manage Help Content")
        self.tab_var = ctk.StringVar(value=tabs[0])

        self.seg_btn = ctk.CTkSegmentedButton(
            top_bar, values=tabs, variable=self.tab_var, command=self.switch_tab,
            fg_color="#F0F0F0", selected_color="#1E4528", selected_hover_color="#14301C"
        )
        self.seg_btn.pack(side="right", padx=20)
        self.seg_btn.set(tabs[0])

        self.tab_content = ctk.CTkFrame(
            self, fg_color="white", corner_radius=10)
        self.tab_content.grid(
            row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.tab_content.grid_columnconfigure(0, weight=1)
        self.tab_content.grid_rowconfigure(0, weight=1)

        self.switch_tab(tabs[0])

    def switch_tab(self, selected_tab):
        for widget in self.tab_content.winfo_children():
            widget.destroy()
        if selected_tab == "Help Guide":
            self.render_guide_tab()
        elif selected_tab == "FAQs":
            self.render_faq_tab()
        elif selected_tab == "System Requirements":
            self.render_sysreq_tab()
        elif selected_tab == "Support Tickets":
            self.render_tickets_tab()
        elif selected_tab == "Manage Help Content":
            self.render_manage_tab()

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
        for row in self._fetch_custom_items("guide"):
            if row["admin_only"] and not self.is_admin:
                continue
            points = [p.strip()
                      for p in row["content"].split("\n") if p.strip()]
            if keyword and not self._section_matches(row["title"], points, keyword):
                continue

            found_any = True
            is_default = bool(row["is_default"])
            card_bg = "#F9FAFB" if is_default else "#EFF9F3"
            card_border = {} if is_default else {"border_width": 1, "border_color": "#B2DFCA"}
            card = ctk.CTkFrame(scroll, fg_color=card_bg,
                                corner_radius=8, **card_border)
            card.pack(fill="x", padx=10, pady=(0, 6))

            title_row = ctk.CTkFrame(card, fg_color="transparent")
            title_row.pack(fill="x", padx=14, pady=(8, 3))
            ctk.CTkLabel(title_row, text=row["title"], font=("Inter", 12, "bold"),
                         text_color="#1E4528").pack(side="left")
            if self.is_admin:
                ctk.CTkButton(
                    title_row, text="✎ Edit", width=60, height=22,
                    fg_color="#3498DB", hover_color="#2980B9",
                    font=("Inter", 10, "bold"),
                    command=lambda r=row: self._open_item_edit_dialog(r)
                ).pack(side="right", padx=(0, 4))

            for point in points:
                ctk.CTkLabel(card, text=f"  •  {point}",
                             font=("Inter", 11), text_color="#1A1A1A",
                             wraplength=760, justify="left").pack(anchor="w", padx=14, pady=1)
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
        for row in self._fetch_custom_items("faq"):
            if row["admin_only"] and not self.is_admin:
                continue
            if keyword and not self._section_matches(row["title"], [row["content"]], keyword):
                continue

            found_any = True
            is_default = bool(row["is_default"])
            card_bg = "#F9FAFB" if is_default else "#EFF9F3"
            card_border = {} if is_default else {"border_width": 1, "border_color": "#B2DFCA"}
            card = ctk.CTkFrame(scroll, fg_color=card_bg,
                                corner_radius=8, **card_border)
            card.pack(fill="x", padx=10, pady=(0, 6))

            q_row = ctk.CTkFrame(card, fg_color="transparent")
            q_row.pack(fill="x", padx=14, pady=(10, 2))
            ctk.CTkLabel(q_row, text=f"Q{idx}.  {row['title']}",
                         font=("Inter", 11, "bold"), text_color="#1E4528",
                         wraplength=700, justify="left").pack(side="left")
            if self.is_admin:
                ctk.CTkButton(
                    q_row, text="✎ Edit", width=60, height=22,
                    fg_color="#3498DB", hover_color="#2980B9",
                    font=("Inter", 10, "bold"),
                    command=lambda r=row: self._open_item_edit_dialog(r)
                ).pack(side="right", padx=(0, 4))

            ctk.CTkLabel(card, text=f"      {row['content']}",
                         font=("Inter", 11), text_color="#1A1A1A",
                         wraplength=760, justify="left").pack(anchor="w", padx=14, pady=(0, 10))
            idx += 1

        if not found_any:
            ctk.CTkLabel(scroll, text=f'No FAQs found for "{keyword}".',
                         text_color="gray").pack(pady=20)

    # ==========================================
    # SYSTEM REQUIREMENTS TAB
    # ==========================================
    def render_sysreq_tab(self):
        outer = ctk.CTkFrame(
            self.tab_content, fg_color="white", corner_radius=10)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=1)

        # Top bar: title + admin button
        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(hdr, text="System Requirements",
                     font=("Inter", 18, "bold"), text_color="#1E4528").pack(side="left")
        if self.is_admin:
            ctk.CTkButton(
                hdr, text="+ Add / Edit Requirement", width=170, height=30,
                fg_color="#1E4528", hover_color="#14301C",
                font=("Inter", 11, "bold"),
                command=self._open_sysreq_form
            ).pack(side="right")

        frame = ctk.CTkScrollableFrame(outer, fg_color="transparent")
        frame.pack(fill="both", expand=True)
        self._sysreq_scroll_frame = frame

        self._render_sysreq_content()

    def _render_sysreq_content(self):
        frame = self._sysreq_scroll_frame
        for w in frame.winfo_children():
            w.destroy()

        all_sysreq = self._fetch_custom_items("sysreq")
        hw_rows = [r for r in all_sysreq if r["admin_only"] == 0]
        sw_rows = [r for r in all_sysreq if r["admin_only"] == 1]

        def render_table(parent, title, rows):
            ctk.CTkLabel(parent, text=title, font=("Inter", 13, "bold"),
                         text_color="#1A1A1A").pack(anchor="w", padx=20, pady=(6, 4))
            card = ctk.CTkFrame(parent, fg_color="#F9FAFB", corner_radius=8)
            card.pack(fill="x", padx=20, pady=(0, 12))

            for i, db_row in enumerate(rows):
                is_default = bool(db_row["is_default"])
                row_bg = "#F0F0F0" if i % 2 == 0 else "#F9FAFB"
                if not is_default:
                    row_bg = "#EFF9F3" if i % 2 == 0 else "#E8F5EE"

                row_h = 34 if not self.is_admin else 38
                row_frame = ctk.CTkFrame(card, fg_color=row_bg, height=row_h)
                row_frame.pack(fill="x")
                row_frame.pack_propagate(False)
                row_frame.grid_columnconfigure(0, weight=1)
                row_frame.grid_columnconfigure(1, weight=2)
                row_frame.grid_columnconfigure(2, weight=0)

                lbl_color = "#1E4528" if not is_default else "#555555"
                ctk.CTkLabel(row_frame, text=db_row["title"],
                             font=("Inter", 11, "bold"), text_color=lbl_color
                             ).grid(row=0, column=0, padx=14, pady=6, sticky="w")
                ctk.CTkLabel(row_frame, text=db_row["content"],
                             font=("Inter", 11), text_color="#1A1A1A"
                             ).grid(row=0, column=1, padx=14, pady=6, sticky="w")

                if self.is_admin:
                    act = ctk.CTkFrame(row_frame, fg_color="transparent")
                    act.grid(row=0, column=2, padx=8, pady=4, sticky="e")
                    ctk.CTkButton(act, text="✎", width=28, height=24,
                                  fg_color="#3498DB", hover_color="#2980B9",
                                  font=("Inter", 10, "bold"),
                                  command=lambda r=db_row: self._open_sysreq_form(
                                      r)
                                  ).pack(side="left", padx=(0, 4))
                    if not is_default:
                        ctk.CTkButton(act, text="🗑", width=28, height=24,
                                      fg_color="#D8000C", hover_color="#B00000",
                                      font=("Inter", 10, "bold"),
                                      command=lambda r=db_row: self._delete_sysreq_row(
                                          r)
                                      ).pack(side="left")
                    else:
                        ctk.CTkButton(act, text="↺", width=28, height=24,
                                      fg_color="#E67E22", hover_color="#CA6F1E",
                                      font=("Inter", 10, "bold"),
                                      command=lambda r=db_row: self._confirm_reset_item(
                                          r)
                                      ).pack(side="left")

        render_table(frame, "Hardware Requirements", hw_rows)
        render_table(frame, "Software Requirements", sw_rows)

        ctk.CTkLabel(
            frame,
            text="Note: The system is a LAN-based desktop application. No internet connection is required "
                 "for normal operation. All data is stored locally in the MySQL database.",
            font=("Inter", 11), text_color="gray", wraplength=780, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 20))

    def _open_item_edit_dialog(self, row):
        """
        Shared edit popup for Guide section and FAQ items.
        Works for both default (is_default=1) and custom rows.
        """
        is_guide = row["item_type"] == "guide"
        is_default = bool(row["is_default"])

        dialog = ctk.CTkToplevel(self.winfo_toplevel())
        dialog.title("Edit Guide Section" if is_guide else "Edit FAQ")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.attributes("-topmost", True)
        dialog.update_idletasks()
        sw, sh = dialog.winfo_screenwidth(), dialog.winfo_screenheight()
        dlg_h = 420 if is_guide else 360
        dialog.geometry(f"500x{dlg_h}+{(sw-500)//2}+{(sh-dlg_h)//2}")

        bg = ctk.CTkFrame(dialog, fg_color="white", corner_radius=10,
                          border_width=1, border_color="#E0E0E0")
        bg.pack(fill="both", expand=True, padx=15, pady=15)

        lbl_type = "Guide Section" if is_guide else "FAQ"
        ctk.CTkLabel(bg, text=f"Edit {lbl_type}",
                     font=("Inter", 14, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=15, pady=(12, 4))
        if is_default:
            ctk.CTkLabel(bg, text="This is a built-in default item. You can edit it freely — use ↺ Reset to restore original.",
                         font=("Inter", 10, "italic"), text_color="#E67E22",
                         wraplength=460, justify="left").pack(anchor="w", padx=15, pady=(0, 8))

        # Admin-only toggle (only for custom rows; defaults keep their flag)
        if not is_default:
            ao_row = ctk.CTkFrame(bg, fg_color="transparent")
            ao_row.pack(fill="x", padx=15, pady=(0, 6))
            ao_var = ctk.IntVar(value=int(row["admin_only"]))
            ctk.CTkCheckBox(ao_row, text="Admin-only (hidden from Staff)",
                            variable=ao_var, font=("Inter", 11), text_color="#1A1A1A",
                            checkbox_width=18, checkbox_height=18,
                            border_color="#D1D5DB").pack(anchor="w")
        else:
            ao_var = ctk.IntVar(value=int(row["admin_only"]))

        # Title
        title_lbl = "Section Title:" if is_guide else "Question:"
        ctk.CTkLabel(bg, text=title_lbl, font=("Inter", 11, "bold"),
                     text_color="#555555").pack(anchor="w", padx=15, pady=(0, 2))
        title_entry = ctk.CTkEntry(bg)
        title_entry.pack(fill="x", padx=15, pady=(0, 8))
        title_entry.insert(0, row["title"])

        # Content
        content_lbl = "Bullet Points (one per line):" if is_guide else "Answer:"
        ctk.CTkLabel(bg, text=content_lbl, font=("Inter", 11, "bold"),
                     text_color="#555555").pack(anchor="w", padx=15, pady=(0, 2))
        content_h = 140 if is_guide else 80
        content_box = ctk.CTkTextbox(bg, height=content_h)
        content_box.pack(fill="x", padx=15, pady=(0, 8))
        content_box.insert("1.0", row["content"])

        status_lbl = ctk.CTkLabel(bg, text="", font=(
            "Inter", 11), text_color="#D8000C")
        status_lbl.pack(anchor="w", padx=15)

        def save():
            new_title = title_entry.get().strip()
            new_content = content_box.get("1.0", "end-1c").strip()
            if not new_title or not new_content:
                status_lbl.configure(text="⚠ Both fields are required.")
                return
            conn = get_connection()
            if not conn:
                status_lbl.configure(text="⚠ Database connection failed.")
                return
            try:
                c = conn.cursor()
                c.execute(
                    "UPDATE help_custom_items SET admin_only=%s, title=%s, content=%s WHERE item_id=%s",
                    (ao_var.get(), new_title, new_content, row["item_id"])
                )
                conn.commit()
            except Exception as e:
                status_lbl.configure(text=f"⚠ Error: {e}")
                return
            finally:
                if conn.is_connected():
                    c.close()
                    conn.close()
            dialog.destroy()
            # Refresh whichever tab is live
            if is_guide and hasattr(self, "_guide_scroll"):
                self._render_guide_sections("")
            elif not is_guide and hasattr(self, "_faq_scroll"):
                self._render_faq_items("")

        btn_row = ctk.CTkFrame(bg, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(4, 12))
        ctk.CTkButton(btn_row, text="✔ Save", width=100, height=32,
                      fg_color="#1E4528", hover_color="#14301C",
                      font=("Inter", 11, "bold"), command=save).pack(side="left", padx=(0, 8))
        if is_default:
            ctk.CTkButton(btn_row, text="↺ Reset to Default", width=140, height=32,
                          fg_color="#E67E22", hover_color="#CA6F1E",
                          font=("Inter", 11, "bold"),
                          command=lambda: [dialog.destroy(),
                                           self._confirm_reset_item(row)]).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Cancel", width=80, height=32,
                      fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC",
                      font=("Inter", 11), command=dialog.destroy).pack(side="left")

    def _confirm_reset_item(self, row):
        """Ask confirmation then restore a default item's content."""
        if not messagebox.askyesno(
            "Reset to Default",
            f"Restore \"{row['title']}\" to its original built-in content?\n\nYour edits will be lost.",
            parent=self.winfo_toplevel()
        ):
            return
        self._reset_item_to_default(row["item_id"])
        # Refresh whichever surface called this
        itype = row["item_type"]
        if itype == "guide" and hasattr(self, "_guide_scroll"):
            self._render_guide_sections("")
        elif itype == "faq" and hasattr(self, "_faq_scroll"):
            self._render_faq_items("")
        elif itype == "sysreq" and hasattr(self, "_sysreq_scroll_frame"):
            self._render_sysreq_content()
        # Also refresh manage list if open
        if hasattr(self, "_manage_list_scroll"):
            self._render_manage_list()

    def _open_sysreq_form(self, existing_row=None):
        """Popup dialog to add or edit a sysreq row."""
        dialog = ctk.CTkToplevel(self.winfo_toplevel())
        dialog.title("Edit Requirement" if existing_row else "Add Requirement")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        # Centre the dialog
        dialog.update_idletasks()
        sw, sh = dialog.winfo_screenwidth(), dialog.winfo_screenheight()
        dialog.geometry(f"420x310+{(sw-420)//2}+{(sh-310)//2}")

        bg = ctk.CTkFrame(dialog, fg_color="white", corner_radius=10,
                          border_width=1, border_color="#E0E0E0")
        bg.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(bg, text="Edit Requirement" if existing_row else "Add New Requirement",
                     font=("Inter", 14, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=15, pady=(12, 8))

        # Category selector (Hardware vs Software)
        cat_row = ctk.CTkFrame(bg, fg_color="transparent")
        cat_row.pack(fill="x", padx=15, pady=(0, 8))
        ctk.CTkLabel(cat_row, text="Category:", font=("Inter", 11, "bold"),
                     text_color="#555555", width=80, anchor="w").pack(side="left")
        cat_var = ctk.IntVar(
            value=existing_row["admin_only"] if existing_row else 0)
        ctk.CTkRadioButton(cat_row, text="Hardware", variable=cat_var, value=0,
                           font=("Inter", 11), text_color="#1A1A1A").pack(side="left", padx=(0, 12))
        ctk.CTkRadioButton(cat_row, text="Software", variable=cat_var, value=1,
                           font=("Inter", 11), text_color="#1A1A1A").pack(side="left")

        # Component label
        ctk.CTkLabel(bg, text="Component / Label:",
                     font=("Inter", 11, "bold"), text_color="#555555").pack(anchor="w", padx=15, pady=(0, 2))
        lbl_entry = ctk.CTkEntry(
            bg, placeholder_text="e.g.  GPU  or  Database")
        lbl_entry.pack(fill="x", padx=15, pady=(0, 8))
        if existing_row:
            lbl_entry.insert(0, existing_row["title"])

        # Value / specification
        ctk.CTkLabel(bg, text="Specification / Value:",
                     font=("Inter", 11, "bold"), text_color="#555555").pack(anchor="w", padx=15, pady=(0, 2))
        val_entry = ctk.CTkEntry(
            bg, placeholder_text="e.g.  NVIDIA GTX 1060 or higher")
        val_entry.pack(fill="x", padx=15, pady=(0, 8))
        if existing_row:
            val_entry.insert(0, existing_row["content"])

        status_lbl = ctk.CTkLabel(bg, text="", font=(
            "Inter", 11), text_color="#D8000C")
        status_lbl.pack(anchor="w", padx=15)

        def save():
            label_val = lbl_entry.get().strip()
            spec_val = val_entry.get().strip()
            if not label_val or not spec_val:
                status_lbl.configure(text="⚠ Both fields are required.")
                return
            conn = get_connection()
            if not conn:
                status_lbl.configure(text="⚠ Database connection failed.")
                return
            try:
                c = conn.cursor()
                if existing_row:
                    c.execute(
                        "UPDATE help_custom_items SET admin_only=%s, title=%s, content=%s WHERE item_id=%s",
                        (cat_var.get(), label_val,
                         spec_val, existing_row["item_id"])
                    )
                else:
                    c.execute(
                        "INSERT INTO help_custom_items (item_type, admin_only, title, content) VALUES ('sysreq', %s, %s, %s)",
                        (cat_var.get(), label_val, spec_val)
                    )
                conn.commit()
            except Exception as e:
                status_lbl.configure(text=f"⚠ Error: {e}")
                return
            finally:
                if conn.is_connected():
                    c.close()
                    conn.close()
            dialog.destroy()
            self._render_sysreq_content()

        btn_row = ctk.CTkFrame(bg, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(4, 12))
        ctk.CTkButton(btn_row, text="✔ Save", width=100, height=32,
                      fg_color="#1E4528", hover_color="#14301C",
                      font=("Inter", 11, "bold"), command=save).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Cancel", width=80, height=32,
                      fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC",
                      font=("Inter", 11), command=dialog.destroy).pack(side="left")

    def _delete_sysreq_row(self, row):
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete requirement:\n\"{row['title']} — {row['content']}\"\n\nThis cannot be undone.",
            parent=self.winfo_toplevel()
        ):
            return
        self._delete_custom_item(row["item_id"])
        self._render_sysreq_content()

    # ==========================================
    # SUPPORT TICKETS TAB
    # ==========================================
    def render_tickets_tab(self):
        frame = ctk.CTkFrame(
            self.tab_content, fg_color="white", corner_radius=10)
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
            except Exception:
                pass
            finally:
                if conn.is_connected():
                    c.close()
                    conn.close()

        if not self.is_admin:
            form_bg = ctk.CTkFrame(frame, fg_color="#F9FAFB", corner_radius=10)
            form_bg.pack(fill="x", padx=20, pady=(20, 10))

            ctk.CTkLabel(form_bg, text="Submit an Inquiry", font=(
                "Inter", 14, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=15, pady=(15, 5))

            subj_entry = ctk.CTkEntry(form_bg, placeholder_text="Subject...")
            subj_entry.pack(fill="x", padx=15, pady=5)

            msg_entry = ctk.CTkTextbox(form_bg, height=60)
            msg_entry.pack(fill="x", padx=15, pady=5)

            def submit_ticket():
                subj = subj_entry.get().strip()
                msg = msg_entry.get("1.0", "end-1c").strip()
                if not subj or not msg:
                    messagebox.showerror(
                        "Error", "Subject and message required.", parent=self.winfo_toplevel())
                    return

                db = get_connection()
                if db:
                    c = db.cursor()
                    c.execute("INSERT INTO help_tickets (user_id, subject, message) VALUES (%s, %s, %s)", (
                        self.user_info['user_id'], subj, msg))
                    db.commit()
                    c.close()
                    db.close()
                    messagebox.showinfo(
                        "Success", "Ticket submitted to the Admin.", parent=self.winfo_toplevel())
                    subj_entry.delete(0, 'end')
                    msg_entry.delete("1.0", "end")
                    load_ticket_list()

            ctk.CTkButton(form_bg, text="Send to Admin", fg_color="#1E4528", hover_color="#14301C",
                          command=submit_ticket).pack(anchor="e", padx=15, pady=(5, 15))

        ctk.CTkLabel(frame, text="Ticket Inbox" if self.is_admin else "My Previous Tickets", font=(
            "Inter", 14, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20, pady=(10, 5))

        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        def load_ticket_list():
            for w in scroll.winfo_children():
                w.destroy()
            db = get_connection()
            if not db:
                return
            try:
                c = db.cursor(dictionary=True)
                if self.is_admin:
                    c.execute(
                        "SELECT h.*, u.full_name FROM help_tickets h JOIN user u ON h.user_id = u.user_id ORDER BY h.status ASC, h.created_at DESC")
                else:
                    c.execute(
                        "SELECT h.*, u.full_name FROM help_tickets h JOIN user u ON h.user_id = u.user_id WHERE h.user_id = %s ORDER BY h.created_at DESC", (self.user_info['user_id'],))

                for t in c.fetchall():
                    card = ctk.CTkFrame(
                        scroll, fg_color="#F9FAFB", corner_radius=8, border_width=1, border_color="#E0E0E0")
                    card.pack(fill="x", pady=5)

                    header = ctk.CTkFrame(card, fg_color="transparent")
                    header.pack(fill="x", padx=15, pady=(10, 5))

                    status_col = "#D8000C" if t['status'] == 'Open' else "#2ECC71"
                    ctk.CTkLabel(header, text=f"[{t['status']}]", font=(
                        "Inter", 12, "bold"), text_color=status_col).pack(side="left", padx=(0, 10))
                    ctk.CTkLabel(header, text=t['subject'], font=(
                        "Inter", 12, "bold"), text_color="#1A1A1A").pack(side="left")
                    if self.is_admin:
                        ctk.CTkLabel(header, text=f"From: {t['full_name']}", font=(
                            "Inter", 11), text_color="gray").pack(side="right")

                    ctk.CTkLabel(card, text=t['message'], font=(
                        "Inter", 11), text_color="#555555", justify="left", wraplength=700).pack(anchor="w", padx=15, pady=5)

                    if t['admin_reply']:
                        reply_box = ctk.CTkFrame(
                            card, fg_color="#E8F8F5", corner_radius=5)
                        reply_box.pack(fill="x", padx=15, pady=(5, 10))
                        ctk.CTkLabel(reply_box, text=f"Admin Reply: {t['admin_reply']}", font=(
                            "Inter", 11, "bold"), text_color="#1E4528", justify="left", wraplength=650).pack(anchor="w", padx=10, pady=10)
                    elif self.is_admin and t['status'] == 'Open':
                        reply_entry = ctk.CTkEntry(
                            card, placeholder_text="Type reply here...")
                        reply_entry.pack(fill="x", padx=15, pady=5)

                        def send_reply(tid=t['ticket_id'], e=reply_entry):
                            rep = e.get().strip()
                            if not rep:
                                return
                            cx = get_connection()
                            cur = cx.cursor()
                            cur.execute(
                                "UPDATE help_tickets SET admin_reply = %s, status = 'Resolved' WHERE ticket_id = %s", (rep, tid))
                            cx.commit()
                            cur.close()
                            cx.close()
                            load_ticket_list()

                        ctk.CTkButton(card, text="Reply & Resolve", width=120, height=28, fg_color="#3498DB",
                                      hover_color="#2980B9", command=send_reply).pack(anchor="e", padx=15, pady=(0, 10))
            except Exception:
                pass
            finally:
                if db.is_connected():
                    c.close()
                    db.close()

        load_ticket_list()

    # ==========================================
    # MANAGE HELP CONTENT TAB  (Admin only)
    # ==========================================
    def render_manage_tab(self):
        """
        Full CRUD panel for custom Help Guide sections and FAQ entries.
        Hard-coded GUIDE_SECTIONS / FAQS are read-only; only DB rows
        (help_custom_items) are editable here.
        """
        outer = ctk.CTkFrame(
            self.tab_content, fg_color="white", corner_radius=10)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        ctk.CTkLabel(hdr, text="Manage Help Content",
                     font=("Inter", 18, "bold"), text_color="#1E4528").pack(side="left")
        ctk.CTkLabel(hdr,
                     text="Add, edit, or delete custom Guide sections and FAQs. Built-in entries are read-only.",
                     font=("Inter", 11, "italic"), text_color="gray").pack(side="left", padx=12)

        # Split: left = form, right = existing custom items list
        body = ctk.CTkFrame(outer, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=15, pady=10)
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        # ── LEFT: Add / Edit Form ──────────────────────────────────────
        form_card = ctk.CTkFrame(body, fg_color="#F9FAFB", corner_radius=8)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self._manage_editing_id = None  # None = Add mode, int = Edit mode

        ctk.CTkLabel(form_card, text="Add / Edit Item",
                     font=("Inter", 13, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=15, pady=(14, 6))

        # Type selector
        type_row = ctk.CTkFrame(form_card, fg_color="transparent")
        type_row.pack(fill="x", padx=15, pady=(0, 6))
        ctk.CTkLabel(type_row, text="Type:", font=("Inter", 11, "bold"),
                     text_color="#555555", width=80, anchor="w").pack(side="left")
        self._manage_type_var = ctk.StringVar(value="guide")
        ctk.CTkRadioButton(type_row, text="Help Guide Section",
                           variable=self._manage_type_var, value="guide",
                           font=("Inter", 11), text_color="#1A1A1A").pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(type_row, text="FAQ Entry",
                           variable=self._manage_type_var, value="faq",
                           font=("Inter", 11), text_color="#1A1A1A").pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(type_row, text="System Requirement",
                           variable=self._manage_type_var, value="sysreq",
                           font=("Inter", 11), text_color="#1A1A1A").pack(side="left")

        # Admin-only toggle
        admin_row = ctk.CTkFrame(form_card, fg_color="transparent")
        admin_row.pack(fill="x", padx=15, pady=(0, 6))
        self._manage_admin_var = ctk.IntVar(value=0)
        ctk.CTkCheckBox(admin_row, text="Admin-only (hidden from Staff)",
                        variable=self._manage_admin_var,
                        font=("Inter", 11), text_color="#1A1A1A",
                        checkbox_width=18, checkbox_height=18,
                        border_color="#D1D5DB").pack(anchor="w")

        # Title field
        ctk.CTkLabel(form_card, text="Title / Question:",
                     font=("Inter", 11, "bold"), text_color="#555555").pack(anchor="w", padx=15, pady=(4, 2))
        self._manage_title_entry = ctk.CTkEntry(
            form_card, placeholder_text="e.g.  15. Custom Section Title")
        self._manage_title_entry.pack(fill="x", padx=15, pady=(0, 8))

        # Content field
        ctk.CTkLabel(form_card,
                     text="Content / Answer / Specification:\n(Guide: one bullet per line  |  FAQ: single answer  |  Sysreq: spec value)",
                     font=("Inter", 11, "bold"), text_color="#555555", justify="left").pack(anchor="w", padx=15, pady=(0, 2))
        self._manage_content_box = ctk.CTkTextbox(form_card, height=160)
        self._manage_content_box.pack(fill="x", padx=15, pady=(0, 12))

        # Form status label
        self._manage_status_lbl = ctk.CTkLabel(form_card, text="",
                                               font=("Inter", 11), text_color="#D8000C")
        self._manage_status_lbl.pack(anchor="w", padx=15)

        # Action buttons row
        btn_row = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(4, 14))

        self._manage_save_btn = ctk.CTkButton(
            btn_row, text="+ Add Item", width=110, height=32,
            fg_color="#1E4528", hover_color="#14301C",
            font=("Inter", 11, "bold"),
            command=self._save_manage_item
        )
        self._manage_save_btn.pack(side="left", padx=(0, 8))

        self._manage_cancel_btn = ctk.CTkButton(
            btn_row, text="✕ Cancel", width=80, height=32,
            fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC",
            font=("Inter", 11),
            command=self._reset_manage_form
        )
        self._manage_cancel_btn.pack(side="left")

        # ── RIGHT: Existing Custom Items List ─────────────────────────
        list_card = ctk.CTkFrame(body, fg_color="#F9FAFB", corner_radius=8)
        list_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        list_card.grid_rowconfigure(1, weight=1)
        list_card.grid_columnconfigure(0, weight=1)

        list_hdr = ctk.CTkFrame(list_card, fg_color="transparent")
        list_hdr.grid(row=0, column=0, sticky="ew", padx=15, pady=(14, 4))
        ctk.CTkLabel(list_hdr, text="All Help Items",
                     font=("Inter", 13, "bold"), text_color="#1A1A1A").pack(side="left")
        ctk.CTkLabel(list_hdr, text="(Built-in defaults shown with ↺ Reset option)",
                     font=("Inter", 10, "italic"), text_color="gray").pack(side="left", padx=8)

        self._manage_list_scroll = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent")
        self._manage_list_scroll.grid(
            row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self._render_manage_list()

    # ── helpers ──────────────────────────────────────────────────────────

    def _render_manage_list(self):
        scroll = self._manage_list_scroll
        for w in scroll.winfo_children():
            w.destroy()

        all_rows = (
            self._fetch_custom_items("guide") +
            self._fetch_custom_items("faq") +
            self._fetch_custom_items("sysreq")
        )

        if not all_rows:
            ctk.CTkLabel(scroll, text="No items found.",
                         text_color="gray", font=("Inter", 11)).pack(pady=20)
            return

        for i, row in enumerate(all_rows):
            is_default = bool(row["is_default"])
            bg = "#FFFDE7" if is_default else (
                "#FFFFFF" if i % 2 == 0 else "#F0F0F0")
            card = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=6,
                                border_width=1, border_color="#E0E0E0")
            card.pack(fill="x", pady=(0, 5))

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8, 2))

            # Type badge
            type_color = {"guide": "#1E4528", "faq": "#2980B9",
                          "sysreq": "#7D3C98"}.get(row["item_type"], "#555555")
            type_label = {"guide": "Guide", "faq": "FAQ", "sysreq": "Sys Req"}.get(
                row["item_type"], row["item_type"])
            ctk.CTkLabel(top, text=type_label,
                         fg_color=type_color, text_color="white",
                         font=("Inter", 10, "bold"), corner_radius=4,
                         padx=6, pady=2).pack(side="left", padx=(0, 6))

            # Default badge
            if is_default:
                ctk.CTkLabel(top, text="Default",
                             fg_color="#888888", text_color="white",
                             font=("Inter", 10, "bold"), corner_radius=4,
                             padx=6, pady=2).pack(side="left", padx=(0, 6))

            # Category / admin-only badge
            if row["item_type"] == "sysreq":
                cat_label = "Hardware" if row["admin_only"] == 0 else "Software"
                ctk.CTkLabel(top, text=cat_label,
                             fg_color="#E67E22", text_color="white",
                             font=("Inter", 10, "bold"), corner_radius=4,
                             padx=6, pady=2).pack(side="left", padx=(0, 6))
            elif row["admin_only"]:
                ctk.CTkLabel(top, text="Admin Only",
                             fg_color="#E67E22", text_color="white",
                             font=("Inter", 10, "bold"), corner_radius=4,
                             padx=6, pady=2).pack(side="left", padx=(0, 6))

            ctk.CTkLabel(top, text=row["title"],
                         font=("Inter", 11, "bold"), text_color="#1A1A1A",
                         wraplength=300, justify="left").pack(side="left")

            # Content preview
            preview = row["content"][:110] + \
                ("…" if len(row["content"]) > 110 else "")
            ctk.CTkLabel(card, text=preview,
                         font=("Inter", 10), text_color="#555555",
                         wraplength=380, justify="left").pack(anchor="w", padx=12, pady=(0, 6))

            # Action buttons — Edit always shown; Reset for defaults, Delete for custom
            btn_bar = ctk.CTkFrame(card, fg_color="transparent")
            btn_bar.pack(anchor="e", padx=12, pady=(0, 8))

            # Edit button routes to the right dialog
            if row["item_type"] == "sysreq":
                def edit_cmd(r=row): return self._open_sysreq_form(r)
            else:
                def edit_cmd(r=row): return self._open_item_edit_dialog(r)

            ctk.CTkButton(
                btn_bar, text="✎ Edit", width=65, height=26,
                fg_color="#3498DB", hover_color="#2980B9",
                font=("Inter", 10, "bold"),
                command=edit_cmd
            ).pack(side="left", padx=(0, 6))

            if is_default:
                ctk.CTkButton(
                    btn_bar, text="↺ Reset", width=68, height=26,
                    fg_color="#E67E22", hover_color="#CA6F1E",
                    font=("Inter", 10, "bold"),
                    command=lambda r=row: self._confirm_reset_item(r)
                ).pack(side="left")
            else:
                ctk.CTkButton(
                    btn_bar, text="🗑 Delete", width=72, height=26,
                    fg_color="#D8000C", hover_color="#B00000",
                    font=("Inter", 10, "bold"),
                    command=lambda r=row: self._confirm_delete_item(r)
                ).pack(side="left")

    def _save_manage_item(self):
        """Insert (Add) or UPDATE (Edit) a custom help item."""
        title = self._manage_title_entry.get().strip()
        content = self._manage_content_box.get("1.0", "end-1c").strip()
        itype = self._manage_type_var.get()
        admin_only = self._manage_admin_var.get()

        if not title or not content:
            self._manage_status_lbl.configure(
                text="⚠ Title and content are required.")
            return

        conn = get_connection()
        if not conn:
            self._manage_status_lbl.configure(
                text="⚠ Database connection failed.")
            return

        try:
            c = conn.cursor()
            if self._manage_editing_id is None:
                # INSERT
                c.execute(
                    "INSERT INTO help_custom_items (item_type, admin_only, title, content) VALUES (%s, %s, %s, %s)",
                    (itype, admin_only, title, content)
                )
                msg = "Item added successfully."
            else:
                # UPDATE
                c.execute(
                    "UPDATE help_custom_items SET item_type=%s, admin_only=%s, title=%s, content=%s WHERE item_id=%s",
                    (itype, admin_only, title, content, self._manage_editing_id)
                )
                msg = "Item updated successfully."
            conn.commit()
            self._manage_status_lbl.configure(
                text=f"✔ {msg}", text_color="#2ECC71")
        except Exception as e:
            self._manage_status_lbl.configure(text=f"⚠ Error: {e}")
            return
        finally:
            if conn.is_connected():
                c.close()
                conn.close()

        self._reset_manage_form()
        self._render_manage_list()

    def _load_item_for_edit(self, row):
        """Populate the form with an existing item for editing."""
        self._manage_editing_id = row["item_id"]
        self._manage_type_var.set(row["item_type"])
        self._manage_admin_var.set(int(row["admin_only"]))

        self._manage_title_entry.delete(0, "end")
        self._manage_title_entry.insert(0, row["title"])

        self._manage_content_box.delete("1.0", "end")
        self._manage_content_box.insert("1.0", row["content"])

        self._manage_save_btn.configure(text="✔ Save Changes")
        self._manage_status_lbl.configure(
            text="Editing item — make changes and click Save.", text_color="#3498DB")

    def _confirm_delete_item(self, row):
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete custom item:\n\"{row['title']}\"\n\nThis action cannot be undone.",
            parent=self.winfo_toplevel()
        ):
            return
        self._delete_custom_item(row["item_id"])
        # If we were editing this item, reset the form
        if self._manage_editing_id == row["item_id"]:
            self._reset_manage_form()
        self._render_manage_list()

    def _reset_manage_form(self):
        """Clear the form and return to Add mode."""
        self._manage_editing_id = None
        self._manage_type_var.set("guide")
        self._manage_admin_var.set(0)
        self._manage_title_entry.delete(0, "end")
        self._manage_content_box.delete("1.0", "end")
        self._manage_save_btn.configure(text="+ Add Item")
        self._manage_status_lbl.configure(text="", text_color="#D8000C")
