import customtkinter as ctk
from tkinter import messagebox
from database import get_connection
import bcrypt
import secrets
import os
import tempfile
import qrcode
from PIL import Image, ImageDraw, ImageFont


class RoleManagementView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_ui()

    def build_ui(self):
        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.grid(row=0, column=0, sticky="nsew")
        self.inner.grid_columnconfigure(0, weight=1, minsize=320)
        self.inner.grid_columnconfigure(1, weight=2, minsize=600)
        self.inner.grid_rowconfigure(0, weight=1)

        self.build_form_panel()
        self.build_table_panel()

    # ==========================================
    # LEFT: Register / Add User Form
    # ==========================================
    def build_form_panel(self):
        self._form_card = ctk.CTkScrollableFrame(
            self.inner, fg_color="white", corner_radius=10, width=300)
        self._form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        form_card = self._form_card

        ctk.CTkLabel(form_card, text="Register New User",
                     font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(
            anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(form_card,
                     text="Fill in all required fields to create a new account.",
                     font=("Inter", 11), text_color="gray", wraplength=240,
                     justify="left").pack(anchor="w", padx=20, pady=(0, 15))

        def field(parent, label, ph, show=None):
            ctk.CTkLabel(parent, text=label, font=("Inter", 12, "bold"),
                         text_color="#1A1A1A").pack(anchor="w", padx=20)
            kw = dict(placeholder_text=ph)
            if show:
                kw["show"] = show
            e = ctk.CTkEntry(parent, **kw)
            e.pack(fill="x", padx=20, pady=(5, 10))
            return e

        self.reg_emp_id = field(form_card, "Employee ID *", "e.g., EMP-001")
        self.reg_name   = field(form_card, "Full Name *",   "Juan Dela Cruz")
        self.reg_email  = field(form_card, "Email Address", "employee@champion.com")

        ctk.CTkLabel(form_card, text="Role *",
                     font=("Inter", 12, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20)
        self.reg_role = ctk.CTkOptionMenu(
            form_card, values=["Staff", "Admin", "Worker"],
            fg_color="#F9FAFB", text_color="black",
            command=self._on_reg_role_change)
        self.reg_role.pack(fill="x", padx=20, pady=(5, 10))

        # Bottom section (password fields OR worker notice + buttons) — rebuilt on role change
        self._reg_bottom = ctk.CTkFrame(form_card, fg_color="transparent")
        self._reg_bottom.pack(fill="x")
        self._build_reg_bottom("Staff")

    def _build_reg_bottom(self, role):
        for w in self._reg_bottom.winfo_children():
            w.destroy()

        if role == "Worker":
            ctk.CTkLabel(self._reg_bottom,
                         text="Workers cannot log into the system.\nNo password is required.",
                         font=("Inter", 11), text_color="#D35400",
                         wraplength=240, justify="left").pack(anchor="w", padx=20, pady=(0, 12))
            self.reg_pass    = None
            self.reg_confirm = None
        else:
            ctk.CTkLabel(self._reg_bottom, text="Password *",
                         font=("Inter", 12, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20)
            self.reg_pass = ctk.CTkEntry(self._reg_bottom,
                                         placeholder_text="Min. 8 characters", show="•")
            self.reg_pass.pack(fill="x", padx=20, pady=(5, 10))

            ctk.CTkLabel(self._reg_bottom, text="Confirm Password *",
                         font=("Inter", 12, "bold"), text_color="#1A1A1A").pack(anchor="w", padx=20)
            self.reg_confirm = ctk.CTkEntry(self._reg_bottom,
                                            placeholder_text="Re-enter password", show="•")
            self.reg_confirm.pack(fill="x", padx=20, pady=(5, 10))

        btn_row = ctk.CTkFrame(self._reg_bottom, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(5, 20))
        btn_row.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(btn_row, text="Register",
                      fg_color="#1E4528", hover_color="#14301C",
                      font=("Inter", 12, "bold"),
                      command=self.execute_register).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(btn_row, text="Clear",
                      fg_color="white", text_color="black",
                      border_width=1, border_color="#E0E0E0", hover_color="#F0F0F0",
                      font=("Inter", 12, "bold"),
                      command=self.clear_form).grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _on_reg_role_change(self, role):
        self._build_reg_bottom(role)

    def execute_register(self):
        emp_id = self.reg_emp_id.get().strip()
        name   = self.reg_name.get().strip()
        email  = self.reg_email.get().strip()
        role   = self.reg_role.get()
        pwd    = self.reg_pass.get().strip()    if self.reg_pass    else ""
        cpwd   = self.reg_confirm.get().strip() if self.reg_confirm else ""

        if not emp_id or not name:
            messagebox.showerror("Validation Error",
                                 "Employee ID and Full Name are required.",
                                 parent=self.winfo_toplevel())
            return

        if role != "Worker":
            if not pwd or not cpwd:
                messagebox.showerror("Validation Error",
                                     "Password is required for Staff and Admin accounts.",
                                     parent=self.winfo_toplevel())
                return
            if pwd != cpwd:
                messagebox.showerror("Password Mismatch", "Passwords do not match.",
                                     parent=self.winfo_toplevel())
                return
            if len(pwd) < 8:
                messagebox.showerror("Weak Password", "Password must be at least 8 characters.",
                                     parent=self.winfo_toplevel())
                return
            hashed = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        else:
            # Workers have no login — store an unguessable placeholder hash
            hashed = bcrypt.hashpw(secrets.token_bytes(32), bcrypt.gensalt()).decode("utf-8")

        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id FROM user WHERE employee_id = %s", (emp_id,))
            if cursor.fetchone():
                messagebox.showerror("Duplicate",
                                     "An account with that Employee ID already exists.",
                                     parent=self.winfo_toplevel())
                return

            cursor.execute("""
                INSERT INTO user (employee_id, full_name, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
            """, (emp_id, name, email or None, hashed, role))
            conn.commit()

            messagebox.showinfo("Success", f"Account registered successfully as {role}.",
                                parent=self.winfo_toplevel())
            self.clear_form()
            self.load_user_table()
        except Exception as e:
            messagebox.showerror("Database Error", str(e),
                                 parent=self.winfo_toplevel())
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def clear_form(self):
        self.reg_emp_id.delete(0, "end")
        self.reg_name.delete(0, "end")
        self.reg_email.delete(0, "end")
        self.reg_role.set("Staff")
        self._build_reg_bottom("Staff")

    # ==========================================
    # RIGHT: User Management Table
    # ==========================================
    def build_table_panel(self):
        table_card = ctk.CTkFrame(
            self.inner, fg_color="white", corner_radius=10)
        table_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(table_card, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(top, text="Registered Users",
                     font=("Inter", 16, "bold"), text_color="#1A1A1A").pack(side="left")

        self.user_search = ctk.CTkEntry(
            top, placeholder_text="Search name or ID...", width=200)
        self.user_search.pack(side="right", padx=(5, 0))
        self.user_search.bind("<Return>", lambda e: self.load_user_table())
        ctk.CTkButton(top, text="Search", width=70,
                      fg_color="#1E4528", hover_color="#14301C",
                      font=("Inter", 11, "bold"),
                      command=self.load_user_table).pack(side="right", padx=5)
        ctk.CTkButton(top, text="↻", width=40,
                      fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC",
                      command=lambda: [self.user_search.delete(0, "end"),
                                       self.load_user_table()]).pack(side="right")

        headers = ["Employee ID", "Full Name", "Email", "Role", "Actions"]
        weights = [2,             3,            3,       1,      3]

        hdr = ctk.CTkFrame(table_card, fg_color="#1E4528",
                           corner_radius=5, height=38)
        hdr.pack(fill="x", padx=(20, 36))
        hdr.pack_propagate(False)
        for col, (h, w) in enumerate(zip(headers, weights)):
            hdr.grid_columnconfigure(col, weight=w)
            ctk.CTkLabel(hdr, text=h, font=("Inter", 11, "bold"),
                         text_color="white").grid(row=0, column=col, padx=10, pady=8, sticky="w")

        self.user_scroll = ctk.CTkScrollableFrame(
            table_card, fg_color="transparent")
        self.user_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 20))

        self.load_user_table()

    def load_user_table(self):
        for w in self.user_scroll.winfo_children():
            w.destroy()

        q = self.user_search.get().strip() if hasattr(self, "user_search") else ""
        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT user_id, employee_id, full_name,
                       IFNULL(email,'—') as email, role
                FROM user WHERE 1=1
            """
            params = []
            if q:
                sql += " AND (full_name LIKE %s OR employee_id LIKE %s)"
                params = [f"%{q}%", f"%{q}%"]
            sql += " ORDER BY full_name ASC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            weights = [2, 3, 3, 1, 3]

            if not rows:
                ctk.CTkLabel(self.user_scroll, text="No users found.",
                             text_color="gray").pack(pady=20)
                return

            for i, row in enumerate(rows):
                rf = ctk.CTkFrame(self.user_scroll,
                                  fg_color="#F9FAFB" if i % 2 == 0 else "white",
                                  height=44)
                rf.pack(fill="x", pady=2)
                rf.pack_propagate(False)

                vals = [row["employee_id"], row["full_name"],
                        row["email"], row["role"]]
                for col, (val, w) in enumerate(zip(vals, weights)):
                    rf.grid_columnconfigure(col, weight=w)
                    if col == 3 and val == "Admin":
                        color = "#2ECC71"
                    elif col == 3 and val == "Worker":
                        color = "#D35400"
                    else:
                        color = "#1A1A1A"
                    ctk.CTkLabel(rf, text=val, font=("Inter", 11),
                                 text_color=color).grid(row=0, column=col, padx=10, pady=8, sticky="w")

                rf.grid_columnconfigure(4, weight=weights[4])
                action_frame = ctk.CTkFrame(rf, fg_color="transparent")
                action_frame.grid(row=0, column=4, padx=5, pady=4, sticky="w")
                ctk.CTkButton(action_frame, text="Edit", width=50, height=28,
                              fg_color="#F1C40F", text_color="black",
                              hover_color="#D4AC0D", font=("Inter", 10, "bold"),
                              command=lambda r=row: self.open_edit_modal(r)).pack(side="left", padx=(0, 3))
                ctk.CTkButton(action_frame, text="🔖", width=32, height=28,
                              fg_color="#3498DB", text_color="white",
                              hover_color="#2980B9", font=("Inter", 12),
                              command=lambda r=row: self.print_user_badge(r)).pack(side="left", padx=(0, 3))
                ctk.CTkButton(action_frame, text="Delete", width=50, height=28,
                              fg_color="#FFEAEA", text_color="#D8000C",
                              hover_color="#FFC0C0", font=("Inter", 10, "bold"),
                              command=lambda r=row: self.delete_user(r)).pack(side="left")

        except Exception as e:
            ctk.CTkLabel(self.user_scroll,
                         text=f"Error: {e}", text_color="red").pack(pady=10)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def open_edit_modal(self, row):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Edit User — {row['full_name']}")
        modal.geometry("500x500")
        modal.configure(fg_color="white")
        modal.resizable(False, False)
        modal.attributes("-topmost", True)
        modal.grab_set()
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - 250
        y = (modal.winfo_screenheight() // 2) - 250
        modal.geometry(f"+{x}+{y}")

        ctk.CTkLabel(modal, text=f"Edit: {row['full_name']}",
                     font=("Inter", 15, "bold"), text_color="black").pack(pady=(20, 3))
        ctk.CTkLabel(modal, text=f"Employee ID: {row['employee_id']}",
                     font=("Inter", 11), text_color="gray").pack(pady=(0, 15))

        form = ctk.CTkFrame(modal, fg_color="transparent")
        form.pack(fill="x", padx=30)

        def make_field(lbl, val):
            ctk.CTkLabel(form, text=lbl, font=("Inter", 11, "bold"),
                         text_color="#1A1A1A").pack(anchor="w")
            e = ctk.CTkEntry(form, height=35)
            e.insert(0, val)
            e.pack(fill="x", pady=(4, 10))
            return e

        name_e  = make_field("Full Name",  row["full_name"])
        email_e = make_field("Email",      row["email"] if row["email"] != "—" else "")

        ctk.CTkLabel(form, text="Role", font=("Inter", 11, "bold"),
                     text_color="#1A1A1A").pack(anchor="w")
        role_menu = ctk.CTkOptionMenu(form, values=["Staff", "Admin", "Worker"],
                                      fg_color="#F9FAFB", text_color="black", height=35)
        role_menu.set(row["role"])
        role_menu.pack(fill="x", pady=(4, 10))

        # Dynamic password section — hidden for Worker
        pass_section = ctk.CTkFrame(form, fg_color="transparent")
        pass_e_holder = [None]  # mutable container so inner functions can update reference

        def build_pass_section(target_role):
            for w in pass_section.winfo_children():
                w.destroy()
            if target_role == "Worker":
                ctk.CTkLabel(pass_section,
                             text="Workers cannot log into the system. Password is not used.",
                             font=("Inter", 11), text_color="#D35400",
                             wraplength=400, justify="left").pack(anchor="w", pady=(0, 8))
                pass_e_holder[0] = None
            else:
                ctk.CTkLabel(pass_section,
                             text="New Password (leave blank to keep current)",
                             font=("Inter", 11, "bold"), text_color="#1A1A1A").pack(anchor="w")
                e = ctk.CTkEntry(pass_section, placeholder_text="Optional new password",
                                 show="•", height=35)
                e.pack(fill="x", pady=(4, 15))
                pass_e_holder[0] = e

        role_menu.configure(command=lambda r: build_pass_section(r))
        build_pass_section(row["role"])
        pass_section.pack(fill="x")

        def save_edit():
            new_name  = name_e.get().strip()
            new_email = email_e.get().strip()
            new_role  = role_menu.get()
            new_pass  = pass_e_holder[0].get().strip() if pass_e_holder[0] else ""

            if not new_name:
                messagebox.showerror("Error", "Full Name is required.", parent=modal)
                return

            # If promoting a Worker to a login role, a password is required
            old_role = row["role"]
            if new_role != "Worker" and old_role == "Worker" and not new_pass:
                messagebox.showerror("Password Required",
                                     "Assigning a login role requires setting a password.",
                                     parent=modal)
                return

            conn = get_connection()
            if not conn:
                return
            try:
                cursor = conn.cursor()
                if new_role == "Worker":
                    # Keep existing hash or store placeholder — Workers never log in
                    cursor.execute("""
                        UPDATE user SET full_name=%s, email=%s, role=%s
                        WHERE user_id=%s
                    """, (new_name, new_email or None, new_role, row["user_id"]))
                elif new_pass:
                    if len(new_pass) < 8:
                        messagebox.showerror("Weak Password",
                                             "Password must be at least 8 characters.",
                                             parent=modal)
                        return
                    hashed = bcrypt.hashpw(new_pass.encode("utf-8"),
                                           bcrypt.gensalt()).decode("utf-8")
                    cursor.execute("""
                        UPDATE user SET full_name=%s, email=%s, role=%s, password_hash=%s
                        WHERE user_id=%s
                    """, (new_name, new_email or None, new_role, hashed, row["user_id"]))
                else:
                    cursor.execute("""
                        UPDATE user SET full_name=%s, email=%s, role=%s
                        WHERE user_id=%s
                    """, (new_name, new_email or None, new_role, row["user_id"]))
                conn.commit()
                messagebox.showinfo("Updated", "User account updated successfully.", parent=modal)
                modal.destroy()
                self.load_user_table()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=modal)
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()

        btn_row = ctk.CTkFrame(modal, fg_color="transparent")
        btn_row.pack(fill="x", padx=30, pady=(5, 20))
        ctk.CTkButton(btn_row, text="Save Changes", height=38,
                      fg_color="#1E4528", hover_color="#14301C",
                      command=save_edit).pack(side="left", padx=(0, 10), fill="x", expand=True)
        ctk.CTkButton(btn_row, text="Cancel", height=38,
                      fg_color="#E0E0E0", text_color="black", hover_color="#CCCCCC",
                      command=modal.destroy).pack(side="right", fill="x", expand=True)

    def print_user_badge(self, row):
        try:
            emp_id   = str(row["employee_id"])
            emp_name = row["full_name"]
            emp_role = row["role"]

            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=14, border=2)
            qr.add_data(emp_id)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="#1E4528", back_color="white").convert("RGB")

            # Canvas
            W = 420
            H = qr_img.height + 220
            canvas = Image.new("RGB", (W, H), "white")

            # Header band
            draw_bg = ImageDraw.Draw(canvas)
            draw_bg.rectangle([(0, 0), (W, 50)], fill="#1E4528")

            # Paste QR centred below header
            qr_x = (W - qr_img.width) // 2
            canvas.paste(qr_img, (qr_x, 60))

            draw = ImageDraw.Draw(canvas)

            # Fonts — try Windows system fonts, fall back gracefully
            fonts_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
            def _font(filename, size):
                for path in [os.path.join(fonts_dir, filename), filename]:
                    try:
                        return ImageFont.truetype(path, size)
                    except (IOError, OSError):
                        continue
                try:
                    return ImageFont.load_default(size=size)
                except TypeError:
                    return ImageFont.load_default()

            f_company = _font("arialbd.ttf", 16)
            f_name    = _font("arialbd.ttf", 28)
            f_role    = _font("arial.ttf",   18)
            f_id      = _font("arial.ttf",   14)

            def cx(text, font):
                bbox = draw.textbbox((0, 0), text, font=font)
                return (W - (bbox[2] - bbox[0])) // 2

            # Header text
            draw.text((cx("Champion Fine Tooling Corp.", f_company), 14),
                      "Champion Fine Tooling Corp.", fill="white", font=f_company)

            # Employee info below QR
            y = qr_img.height + 75
            draw.text((cx(emp_name, f_name), y),     emp_name, fill="#1A1A1A", font=f_name)
            draw.text((cx(emp_role, f_role), y + 42), emp_role, fill="#1E4528", font=f_role)
            draw.text((cx(f"ID: {emp_id}", f_id), y + 76),
                      f"ID: {emp_id}", fill="gray", font=f_id)

            # Save & open
            path = os.path.join(tempfile.gettempdir(), f"Badge_{emp_id}.pdf")
            canvas.save(path, "PDF", resolution=150.0)
            os.startfile(path)

        except Exception as e:
            messagebox.showerror("Badge Error", f"Could not generate badge:\n{e}",
                                 parent=self.winfo_toplevel())

    def delete_user(self, row):
        if messagebox.askyesno(
            "Confirm Delete",
            f"Permanently delete the account for '{row['full_name']}' ({row['employee_id']})?\n"
            "Their transaction history will remain in the system.",
            parent=self.winfo_toplevel()
        ):
            conn = get_connection()
            if not conn:
                return
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM user WHERE user_id = %s", (row["user_id"],))
                conn.commit()
                messagebox.showinfo("Deleted", "User account deleted.",
                                    parent=self.winfo_toplevel())
                self.load_user_table()
            except Exception as e:
                messagebox.showerror("Error", str(
                    e), parent=self.winfo_toplevel())
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
