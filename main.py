import sqlite3
import hashlib
import datetime
from tkinter import ttk, messagebox
import tkinter as tk

# ==========================================
# 1. DATABASE & MODELS (SQLite)
# ==========================================
class Database:
    def __init__(self, db_file="library_app.db"):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.seed_admin()

    def create_tables(self):
        # Users Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Super Admin', 'Staff')),
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive'))
            )
        ''')
        # Books Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT UNIQUE NOT NULL,
                category TEXT,
                publisher TEXT,
                quantity INTEGER DEFAULT 0,
                price REAL DEFAULT 0.0
            )
        ''')
        # Customers Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT
            )
        ''')
        # Borrow Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS borrow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                customer_id INTEGER,
                borrow_date TEXT,
                due_date TEXT,
                return_date TEXT,
                fine REAL DEFAULT 0.0,
                FOREIGN KEY(book_id) REFERENCES books(id),
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
        ''')
        # Sales Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT,
                book_id INTEGER,
                customer_id INTEGER,
                quantity INTEGER,
                total_price REAL,
                sale_date TEXT,
                FOREIGN KEY(book_id) REFERENCES books(id)
            )
        ''')
        # Transactions / Audit Log
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def seed_admin(self):
        # Default admin: username=admin, password=admin
        self.cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
        if not self.cursor.fetchone():
            hashed = hashlib.sha256("admin".encode()).hexdigest()
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, ?, ?)",
                ("admin", hashed, "Super Admin", "Active")
            )
            self.conn.commit()

        # Default staff: username=staff, password=staff
        self.cursor.execute("SELECT * FROM users WHERE username = ?", ("staff",))
        if not self.cursor.fetchone():
            heashed = hashlib.sha256("staff".encode()).hexdigest()
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, ?, ?)",
                ("staff", heashed, "Staff", "Active")
            )
            self.conn.commit()

    def log_transaction(self, user_id, action):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO transactions (user_id, action, timestamp) VALUES (?, ?, ?)",
            (user_id, action, now)
        )
        self.conn.commit()


# ==========================================
# 2. MAIN APPLICATION CLASS
# ==========================================
class LibraryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Library & Bookstore Management System")
        self.geometry("1100x650")
        self.db = Database()
        self.current_user = None

        # Base configuration
        self.configure(bg="#191952")
        self.style = ttk.Style(self)
        
        # Apply theme compatibility override
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.configure_styles()

        # Container Frame
        self.container = tk.Frame(self, bg="#D8CD38")
        self.container.pack(fill="both", expand=True)

        self.show_login_frame()

    def configure_styles(self):
        # General widget colors
        self.style.configure("TFrame", background="#1e1e2e")
        self.style.configure("TLabel", background="#1e1e2e", foreground="#ffffff", font=("Helvetica", 10))
        self.style.configure("Header.TLabel", font=("Helvetica", 16, "bold"), foreground="#ffffff")
        self.style.configure("TButton", background="#474B18", foreground="#ffffff", borderwidth=0, font=("Helvetica", 10, "bold"))
        self.style.map("TButton", background=[("active", "#45475a")])
        self.style.configure("Nav.TButton", background="#181825", foreground="#ffffff", anchor="w", font=("Helvetica", 11))
        self.style.map("Nav.TButton", background=[("active", "#D8CD38")])
        
        # High-contrast Treeview colors (Fixes invisible text on dark UI)
        self.style.configure(
            "Treeview", 
            background="#474B18", 
            foreground="#ffffff", 
            fieldbackground="#2a2a3c", 
            rowheight=28
        )
        self.style.configure(
            "Treeview.Heading", 
            background="#474B18", 
            foreground="#ffffff", 
            font=("Helvetica", 10, "bold")
        )
        self.style.map("Treeview", background=[("selected", "#89b4fa")], foreground=[("selected", "#11111b")])

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def clear_content(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()
        self.main_content.update_idletasks()  # Force layout re-calculation

    # --- AUTHENTICATION ---
    def show_login_frame(self):
        self.clear_container()
        frame = ttk.Frame(self.container)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(frame, text="Library System Login", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=20)
        
        ttk.Label(frame, text="Username:").grid(row=1, column=0, sticky="e", padx=10, pady=5)
        username_ent = ttk.Entry(frame)
        username_ent.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Password:").grid(row=2, column=0, sticky="e", padx=10, pady=5)
        password_ent = ttk.Entry(frame, show="*")
        password_ent.grid(row=2, column=1, padx=10, pady=5)

        def login():
            u = username_ent.get()
            p = hashlib.sha256(password_ent.get().encode()).hexdigest()
            self.db.cursor.execute("SELECT id, username, role, status FROM users WHERE username=? AND password_hash=?", (u, p))
            user = self.db.cursor.fetchone()
            if user:
                if user[3] == 'Inactive':
                    messagebox.showerror("Error", "Account is deactivated.")
                    return
                self.current_user = {"id": user[0], "username": user[1], "role": user[2]}
                self.db.log_transaction(self.current_user["id"], "User Login")
                self.show_dashboard_frame()
            else:
                messagebox.showerror("Error", "Invalid username or password.")

        ttk.Button(frame, text="Login", command=login).grid(row=3, column=0, columnspan=2, pady=15)

    # --- DASHBOARD LAYOUT ---
    def show_dashboard_frame(self):
        self.clear_container()

        # Sidebar navigation
        sidebar = tk.Frame(self.container, bg="#181825", width=220)
        sidebar.pack(side="left", fill="y")

        ttk.Label(sidebar, text="  Dashboard", style="Header.TLabel", background="#181825").pack(pady=20, fill="x")

        # Workspace panel
        self.main_content = ttk.Frame(self.container)
        self.main_content.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        ttk.Button(sidebar, text=" 📚 Books", style="Nav.TButton", command=self.render_books_view).pack(fill="x", pady=2, padx=5)
        ttk.Button(sidebar, text=" 👥 Customers", style="Nav.TButton", command=self.render_customers_view).pack(fill="x", pady=2, padx=5)
        ttk.Button(sidebar, text=" 🔄 Borrow / Return", style="Nav.TButton", command=self.render_borrow_view).pack(fill="x", pady=2, padx=5)
        ttk.Button(sidebar, text=" 🛒 Sales", style="Nav.TButton", command=self.render_sales_view).pack(fill="x", pady=2, padx=5)
        
        if self.current_user["role"] == "Super Admin":
            ttk.Button(sidebar, text=" ⚙ User Management", style="Nav.TButton", command=self.render_users_view).pack(fill="x", pady=2, padx=5)

        ttk.Button(sidebar, text=" 📜 Transaction Log", style="Nav.TButton", command=self.render_transactions_view).pack(fill="x", pady=2, padx=5)
        ttk.Button(sidebar, text=" 🚪 Logout", style="Nav.TButton", command=self.logout).pack(fill="x", side="bottom", pady=15, padx=5)

        self.render_books_view()

    def logout(self):
        if self.current_user:
            self.db.log_transaction(self.current_user["id"], "User Logout")
        self.current_user = None
        self.show_login_frame()

    # ==========================================
    # 3. MODULE VIEWS
    # ==========================================

    # --- BOOK MANAGEMENT ---
    def render_books_view(self):
        self.clear_content()
        ttk.Label(self.main_content, text="Book Inventory", style="Header.TLabel").pack(anchor="w", pady=5)

        ctrl_frame = ttk.Frame(self.main_content)
        ctrl_frame.pack(fill="x", pady=5)

        search_ent = ttk.Entry(ctrl_frame)
        search_ent.pack(side="left", padx=5)

        def search_books():
            q = search_ent.get()
            self.db.cursor.execute(
                "SELECT id, title, author, isbn, category, quantity, price FROM books WHERE title LIKE ? OR isbn LIKE ?", 
                (f'%{q}%', f'%{q}%')
            )
            update_tree(self.db.cursor.fetchall())

        ttk.Button(ctrl_frame, text="Search", command=search_books).pack(side="left", padx=5)

        columns = ("ID", "Title", "Author", "ISBN", "Category", "Qty", "Price")
        tree = ttk.Treeview(self.main_content, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=110)
        tree.pack(fill="both", expand=True, pady=10)

        def update_tree(rows):
            tree.delete(*tree.get_children())
            for r in rows:
                tree.insert("", "end", values=r)

        def open_add_book():
            top = tk.Toplevel(self)
            top.title("Add Book")
            top.geometry("320x360")
            
            fields = ["Title", "Author", "ISBN", "Category", "Publisher", "Quantity", "Price"]
            entries = {}
            for i, f in enumerate(fields):
                tk.Label(top, text=f).grid(row=i, column=0, padx=10, pady=5, sticky="e")
                ent = tk.Entry(top)
                ent.grid(row=i, column=1, padx=10, pady=5)
                entries[f] = ent

            def save_book():
                try:
                    self.db.cursor.execute(
                        "INSERT INTO books (title, author, isbn, category, publisher, quantity, price) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            entries["Title"].get(), entries["Author"].get(), entries["ISBN"].get(), 
                            entries["Category"].get(), entries["Publisher"].get(), 
                            int(entries["Quantity"].get()), float(entries["Price"].get())
                        )
                    )
                    self.db.conn.commit()
                    self.db.log_transaction(self.current_user["id"], f"Added Book: {entries['Title'].get()}")
                    top.destroy()
                    search_books()
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            tk.Button(top, text="Save", command=save_book).grid(row=len(fields), column=0, columnspan=2, pady=15)

        ttk.Button(ctrl_frame, text="+ Add Book", command=open_add_book).pack(side="right", padx=5)
        search_books()

    # --- CUSTOMERS MODULE ---
    def render_customers_view(self):
        self.clear_content()
        ttk.Label(self.main_content, text="Customer Management", style="Header.TLabel").pack(anchor="w", pady=5)

        ctrl_frame = ttk.Frame(self.main_content)
        ctrl_frame.pack(fill="x", pady=5)

        columns = ("ID", "Name", "Email", "Phone")
        tree = ttk.Treeview(self.main_content, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(fill="both", expand=True, pady=10)

        def load_customers():
            tree.delete(*tree.get_children())
            self.db.cursor.execute("SELECT * FROM customers")
            for r in self.db.cursor.fetchall():
                tree.insert("", "end", values=r)

        def open_add_cust():
            top = tk.Toplevel(self)
            top.title("Add Customer")
            top.geometry("280x220")

            tk.Label(top, text="Name").pack(pady=(10, 0))
            e_name = tk.Entry(top); e_name.pack()
            tk.Label(top, text="Email").pack(pady=(5, 0))
            e_email = tk.Entry(top); e_email.pack()
            tk.Label(top, text="Phone").pack(pady=(5, 0))
            e_phone = tk.Entry(top); e_phone.pack()

            def save():
                self.db.cursor.execute("INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)", (e_name.get(), e_email.get(), e_phone.get()))
                self.db.conn.commit()
                self.db.log_transaction(self.current_user["id"], f"Added Customer: {e_name.get()}")
                top.destroy()
                load_customers()

            tk.Button(top, text="Save", command=save).pack(pady=15)

        ttk.Button(ctrl_frame, text="+ Add Customer", command=open_add_cust).pack(side="right", padx=5)
        load_customers()

    # --- BORROW / RETURN MODULE ---
    def render_borrow_view(self):
        self.clear_content()
        ttk.Label(self.main_content, text="Borrow & Return Management", style="Header.TLabel").pack(anchor="w", pady=5)

        frame = ttk.Frame(self.main_content)
        frame.pack(fill="x", pady=10)

        ttk.Label(frame, text="Book ID:").grid(row=0, column=0, padx=5)
        e_book = ttk.Entry(frame, width=10); e_book.grid(row=0, column=1, padx=5)

        ttk.Label(frame, text="Customer ID:").grid(row=0, column=2, padx=5)
        e_cust = ttk.Entry(frame, width=10); e_cust.grid(row=0, column=3, padx=5)

        def borrow_book():
            b_id, c_id = e_book.get(), e_cust.get()
            self.db.cursor.execute("SELECT quantity FROM books WHERE id=?", (b_id,))
            book = self.db.cursor.fetchone()
            if book and book[0] > 0:
                b_date = datetime.date.today().strftime("%Y-%m-%d")
                d_date = (datetime.date.today() + datetime.timedelta(days=14)).strftime("%Y-%m-%d")
                
                self.db.cursor.execute("INSERT INTO borrow (book_id, customer_id, borrow_date, due_date) VALUES (?, ?, ?, ?)", (b_id, c_id, b_date, d_date))
                self.db.cursor.execute("UPDATE books SET quantity = quantity - 1 WHERE id=?", (b_id,))
                self.db.conn.commit()
                self.db.log_transaction(self.current_user["id"], f"Borrowed Book ID: {b_id} to Cust ID: {c_id}")
                messagebox.showinfo("Success", "Book issued successfully!")
                load_borrowed()
            else:
                messagebox.showerror("Error", "Book unavailable or out of stock.")

        ttk.Button(frame, text="Issue Book", command=borrow_book).grid(row=0, column=4, padx=15)

        columns = ("Record ID", "Book ID", "Cust ID", "Borrow Date", "Due Date", "Returned")
        tree = ttk.Treeview(self.main_content, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(fill="both", expand=True, pady=10)

        def load_borrowed():
            tree.delete(*tree.get_children())
            self.db.cursor.execute("SELECT id, book_id, customer_id, borrow_date, due_date, return_date FROM borrow")
            for r in self.db.cursor.fetchall():
                tree.insert("", "end", values=r)

        load_borrowed()

    # --- SALES MODULE ---
    def render_sales_view(self):
        self.clear_content()
        ttk.Label(self.main_content, text="Point of Sale (POS)", style="Header.TLabel").pack(anchor="w", pady=5)

        frame = ttk.Frame(self.main_content)
        frame.pack(fill="x", pady=10)

        ttk.Label(frame, text="Book ID:").grid(row=0, column=0, padx=5)
        e_book = ttk.Entry(frame, width=10); e_book.grid(row=0, column=1, padx=5)

        ttk.Label(frame, text="Qty:").grid(row=0, column=2, padx=5)
        e_qty = ttk.Entry(frame, width=10); e_qty.grid(row=0, column=3, padx=5)

        def make_sale():
            b_id = e_book.get()
            qty = int(e_qty.get() or 1)
            self.db.cursor.execute("SELECT quantity, price FROM books WHERE id=?", (b_id,))
            book = self.db.cursor.fetchone()

            if book and book[0] >= qty:
                total = book[1] * qty
                inv = f"INV-{int(datetime.datetime.now().timestamp())}"
                s_date = datetime.date.today().strftime("%Y-%m-%d")

                self.db.cursor.execute(
                    "INSERT INTO sales (invoice_no, book_id, quantity, total_price, sale_date) VALUES (?, ?, ?, ?, ?)",
                    (inv, b_id, qty, total, s_date)
                )
                self.db.cursor.execute("UPDATE books SET quantity = quantity - ? WHERE id=?", (qty, b_id))
                self.db.conn.commit()
                self.db.log_transaction(self.current_user["id"], f"Sale completed: Invoice {inv}, Total: ${total:.2f}")
                messagebox.showinfo("Success", f"Sale Complete!\nInvoice: {inv}\nTotal: ${total:.2f}")
                load_sales()
            else:
                messagebox.showerror("Error", "Insufficient Stock!")

        ttk.Button(frame, text="Process Sale", command=make_sale).grid(row=0, column=4, padx=15)

        columns = ("Invoice No", "Book ID", "Qty", "Total Price", "Date")
        tree = ttk.Treeview(self.main_content, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(fill="both", expand=True, pady=10)

        def load_sales():
            tree.delete(*tree.get_children())
            self.db.cursor.execute("SELECT invoice_no, book_id, quantity, total_price, sale_date FROM sales")
            for r in self.db.cursor.fetchall():
                tree.insert("", "end", values=r)

        load_sales()

    # --- USER MANAGEMENT ---
    def render_users_view(self):
        self.clear_content()
        ttk.Label(self.main_content, text="User Management (Super Admin)", style="Header.TLabel").pack(anchor="w", pady=5)

        columns = ("ID", "Username", "Role", "Status")
        tree = ttk.Treeview(self.main_content, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(fill="both", expand=True, pady=10)

        def load_users():
            tree.delete(*tree.get_children())
            self.db.cursor.execute("SELECT id, username, role, status FROM users")
            for r in self.db.cursor.fetchall():
                tree.insert("", "end", values=r)

        load_users()

    # --- AUDIT / TRANSACTIONS LOG ---
    def render_transactions_view(self):
        self.clear_content()
        ttk.Label(self.main_content, text="System Audit Logs", style="Header.TLabel").pack(anchor="w", pady=5)

        columns = ("ID", "User ID", "Action", "Timestamp")
        tree = ttk.Treeview(self.main_content, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150 if col != "Action" else 300)
        tree.pack(fill="both", expand=True, pady=10)

        self.db.cursor.execute("SELECT * FROM transactions ORDER BY id DESC")
        for r in self.db.cursor.fetchall():
            tree.insert("", "end", values=r)


# ==========================================
# 4. ENTRY POINT
# ==========================================
if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()