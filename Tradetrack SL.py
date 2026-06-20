# TradeTrack SL - Sales & Inventory Tracker 
# Aligned with SDG 8: Decent Work and Economic Growth

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import json
import os

# CONSTANTS
APP_TITLE = "TradeTrack SL - Sales & Inventory Tracker"
LOW_STOCK_THRESHOLD = 5
CURRENCY = "NLe"

# DATA STORAGE
inventory = {} # { name: {"price": float, "quantity": int, "category": str} }
sales_log = [] # [ {"product", "qty", "unit_price", "total", "date", "category"} ]

# DATA FILE
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tradetrack_data.json")


# DATA PERSISTENCE FUNCTIONS

def save_data():
    """Save inventory and sales log to a JSON file."""
    try:
        data = {"inventory": inventory, "sales_log": sales_log}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Warning: Could not save data — {e}")


def load_data():
    """Load inventory and sales log from JSON file if it exists."""
    global inventory, sales_log
    if not os.path.exists(DATA_FILE):
        return  # No saved data yet — start fresh
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        inventory = data.get("inventory", {})
        sales_log = data.get("sales_log", [])
    except Exception as e:
        print(f"Warning: Could not load data — {e}")


# CORE LOGIC FUNCTIONS

def add_product(name, price, quantity, category="General"):
    """Add a new product or restock an existing one."""
    name = name.strip().title()
    if not name:
        return False, "Product name cannot be empty."
    try:
        price = float(price)
        quantity = int(quantity)
    except ValueError:
        return False, "Price and quantity must be valid numbers."
    if price <= 0 or quantity < 0:
        return False, "Price must be > 0 and quantity cannot be negative."
    if name in inventory:
        inventory[name]["price"]     = price
        inventory[name]["quantity"] += quantity
        inventory[name]["category"]  = category
        save_data()
        return True, f"'{name}' updated. New stock: {inventory[name]['quantity']}"
    inventory[name] = {"price": price, "quantity": quantity, "category": category}
    save_data()
    return True, f"'{name}' added to inventory."


def edit_product(old_name, new_name, new_price, new_qty, new_category):
    """Edit an existing product's details."""
    old_name = old_name.strip().title()
    new_name = new_name.strip().title()
    if old_name not in inventory:
        return False, f"Product '{old_name}' not found."
    try:
        new_price = float(new_price)
        new_qty   = int(new_qty)
    except ValueError:
        return False, "Price and quantity must be valid numbers."
    if new_price <= 0 or new_qty < 0:
        return False, "Price must be > 0 and quantity cannot be negative."
    if new_name != old_name:
        inventory[new_name] = inventory.pop(old_name)
    inventory[new_name]["price"]    = new_price
    inventory[new_name]["quantity"] = new_qty
    inventory[new_name]["category"] = new_category
    save_data()
    return True, f"'{old_name}' updated successfully."


def delete_product(name):
    """Remove a product from inventory."""
    name = name.strip().title()
    if name not in inventory:
        return False, f"Product '{name}' not found."
    del inventory[name]
    save_data()
    return True, f"'{name}' deleted from inventory."


def record_sale(product_name, quantity_sold):
    """Record a sale and update stock."""
    product_name = product_name.strip().title()
    if product_name not in inventory:
        return False, f"Product '{product_name}' not found in inventory."
    try:
        quantity_sold = int(quantity_sold)
    except ValueError:
        return False, "Quantity sold must be a whole number."
    if quantity_sold <= 0:
        return False, "Quantity sold must be greater than zero."
    if inventory[product_name]["quantity"] < quantity_sold:
        return False, f"Insufficient stock. Only {inventory[product_name]['quantity']} unit(s) available."
    total = inventory[product_name]["price"] * quantity_sold
    inventory[product_name]["quantity"] -= quantity_sold
    sales_log.append({
        "product": product_name,
        "qty": quantity_sold,
        "unit_price": inventory[product_name]["price"],
        "total": total,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "category": inventory[product_name].get("category", "General")
    })
    msg = f"Sale recorded! {quantity_sold} x {product_name} = {CURRENCY} {total:,.2f}"
    if inventory[product_name]["quantity"] <= LOW_STOCK_THRESHOLD:
        msg += f"\n⚠️ LOW STOCK: Only {inventory[product_name]['quantity']} unit(s) left!"
    save_data()
    return True, msg


def search_inventory(keyword):
    """Search inventory by keyword."""
    keyword = keyword.strip().lower()
    return {k: v for k, v in inventory.items() if keyword in k.lower()}


def filter_by_category(category):
    """Filter inventory by category."""
    if category == "All":
        return inventory
    return {k: v for k, v in inventory.items() if v.get("category") == category}


def get_low_stock_items():
    """Return products at or below the low stock threshold."""
    return [(n, d["quantity"]) for n, d in inventory.items() if d["quantity"] <= LOW_STOCK_THRESHOLD]


def get_top_selling_products(n=5):
    """Return the top N best-selling products by quantity sold."""
    totals = {}
    for s in sales_log:
        totals[s["product"]] = totals.get(s["product"], 0) + s["qty"]
    sorted_items = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    return sorted_items[:n]


def get_category_revenue():
    """Return total revenue per product category."""
    cat_rev = {}
    for s in sales_log:
        cat = s.get("category", "General")
        cat_rev[cat] = cat_rev.get(cat, 0) + s["total"]
    return cat_rev


def generate_receipt(sale):
    """Generate a receipt string for a single sale."""
    lines = [
        "=" * 38,
        "TRADETRACK SL",
        "Sales Receipt | Sierra Leone",
        "=" * 38,
        f" Date: {sale['date']}",
        f" Product: {sale['product']}",
        f" Category: {sale.get('category', 'General')}",
        f" Unit Price: {CURRENCY} {sale['unit_price']:,.2f}",
        f" Quantity: {sale['qty']}",
        "-" * 38,
        f"  TOTAL: {CURRENCY} {sale['total']:,.2f}",
        "=" * 38,
        "  Thank you for your business!",
        "  Powered by TradeTrack SL",
        "=" * 38,
    ]
    return "\n".join(lines)


def generate_summary():
    """Generate a full business summary report."""
    if not sales_log and not inventory:
        return "No data available. Add products and record sales first."
    total_revenue = sum(s["total"] for s in sales_log)
    total_transactions = len(sales_log)
    top_sellers = get_top_selling_products(5)
    cat_revenue        = get_category_revenue()

    lines = [
        "=" * 54,
        "TRADETRACK SL — BUSINESS SUMMARY REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 54,
        f"\n Total Transactions: {total_transactions}",
        f"Total Revenue: {CURRENCY} {total_revenue:,.2f}",
        f" Products in Stock: {len(inventory)}",
        f"\n  REVENUE BY CATEGORY:",
        "  " + "-" * 50,
    ]
    for cat, rev in cat_revenue.items():
        lines.append(f"  {cat:<25} {CURRENCY} {rev:,.2f}")

    lines += [
        f"\n  TOP {len(top_sellers)} BEST-SELLING PRODUCTS:",
        "  " + "-" * 50,
    ]
    for i, (name, qty) in enumerate(top_sellers, 1):
        lines.append(f"  {i}. {name:<22} {qty} unit(s) sold")

    lines += [
        f"\n  FULL INVENTORY ({len(inventory)} product(s)):",
        "  " + "-" * 50,
        f" {'Product':<20} {'Category':<12} {'Price':>8} {'Stock':>6}",
        "  " + "-" * 50,
    ]
    for name, data in inventory.items():
        flag = " ⚠️" if data["quantity"] <= LOW_STOCK_THRESHOLD else ""
        lines.append(f"  {name:<20} {data.get('category','General'):<12} {CURRENCY} {data['price']:>6,.2f} {data['quantity']:>5}{flag}")

    lines.append("\n  RECENT SALES (Last 10):")
    lines.append("  " + "-" * 50)
    for s in reversed(sales_log[-10:]):
        lines.append(f"  {s['date']}  {s['product'][:14]:<14} x{s['qty']}  {CURRENCY} {s['total']:,.2f}")

    low = get_low_stock_items()
    if low:
        lines.append("\n  ⚠️  LOW STOCK ALERTS:")
        for n, q in low:
            lines.append(f"     - {n}: {q} unit(s) remaining")
    lines.append("\n" + "=" * 54)
    return "\n".join(lines)


def export_summary_to_file(filepath):
    """Export the summary report to a text file."""
    report = generate_summary()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    return True, "Report exported successfully."


def export_inventory_to_csv(filepath):
    """Export inventory to a CSV file."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("Product Name,Category,Unit Price (NLe),Stock Quantity,Status\n")
        for name, data in inventory.items():
            status = "Low Stock" if data["quantity"] <= LOW_STOCK_THRESHOLD else "In Stock"
            f.write(f"{name},{data.get('category','General')},{data['price']:.2f},{data['quantity']},{status}\n")
    return True, "Inventory exported to CSV."

# GUI APPLICATION

CATEGORIES = ["General", "Food & Beverages", "Household", "Electronics", "Clothing", "Stationery", "Health & Beauty"]

class TradeTrackApp:
    """Main GUI application class for TradeTrack SL."""

    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("920x700")
        self.root.resizable(True, True)
        self.root.configure(bg="#1B4F72")
        self._build_header()
        self._build_notebook()
        self._build_status_bar()

    # HEADER 
    def _build_header(self):
        f = tk.Frame(self.root, bg="#1B4F72", pady=8)
        f.pack(fill="x")
        tk.Label(f, text="🛒 TradeTrack SL", font=("Tahoma", 20, "bold"),
                 bg="#1B4F72", fg="#F9E79F").pack()
        tk.Label(f, text="Sales & Inventory Tracker v2.0  |  SDG 8: Decent Work & Economic Growth",
                 font=("Tahoma", 9), bg="#1B4F72", fg="#AED6F1").pack()

    # NOTEBOOK
    def _build_notebook(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#1B4F72", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Tahoma", 9, "bold"),
                        padding=[10, 5], background="#2E86C1", foreground="white")
        style.map("TNotebook.Tab", background=[("selected", "#F9E79F")],
                  foreground=[("selected", "#1B4F72")])
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        self._build_inventory_tab()
        self._build_sales_tab()
        self._build_view_tab()
        self._build_edit_tab()
        self._build_search_tab()
        self._build_receipt_tab()
        self._build_dashboard_tab()
        self._build_summary_tab()
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # TAB BUILDER HELPER
    def _tab_frame(self, title_text):
        tab = tk.Frame(self.notebook, bg="#EBF5FB")
        tk.Label(tab, text=title_text, font=("Tahoma", 13, "bold"),
                 bg="#EBF5FB", fg="#1B4F72").pack(pady=(12, 4))
        return tab

    def _form_frame(self, parent):
        f = tk.Frame(parent, bg="#EBF5FB")
        f.pack(pady=4)
        return f

    def _result_label(self, parent):
        lbl = tk.Label(parent, text="", font=("Tahoma", 10, "italic"),
                       bg="#EBF5FB", fg="#1D8348", wraplength=550, justify="center")
        lbl.pack(pady=6)
        return lbl

    def _entry_row(self, form, label, row, width=24):
        tk.Label(form, text=label, font=("Tahoma", 10), bg="#EBF5FB",
                 anchor="w", width=22).grid(row=row, column=0, padx=10, pady=6, sticky="w")
        e = tk.Entry(form, font=("Tahoma", 10), width=width, relief="solid", bd=1)
        e.grid(row=row, column=1, padx=10, pady=6)
        return e

    def _combo_row(self, form, label, row, values, var, width=22):
        tk.Label(form, text=label, font=("Tahoma", 10), bg="#EBF5FB",
                 anchor="w", width=22).grid(row=row, column=0, padx=10, pady=6, sticky="w")
        cb = ttk.Combobox(form, textvariable=var, values=values,
                          font=("Tahoma", 10), width=width, state="readonly")
        cb.grid(row=row, column=1, padx=10, pady=6)
        return cb

    def _btn_row(self, parent, buttons):
        f = tk.Frame(parent, bg="#EBF5FB")
        f.pack(pady=8)
        for text, color, cmd in buttons:
            tk.Button(f, text=text, font=("Tahoma", 10, "bold"),
                      bg=color, fg="white", relief="flat", padx=12, pady=5,
                      cursor="hand2", command=cmd).pack(side="left", padx=5)
        return f

    def _treeview(self, parent, cols, widths, height=12):
        frame = tk.Frame(parent, bg="#EBF5FB")
        frame.pack(fill="both", expand=True, padx=10, pady=4)
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=height)
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        tree.tag_configure("low", background="#FADBD8")
        tree.tag_configure("ok",  background="#D5F5E3")
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        return tree

    # TAB 1: ADD PRODUCT
    def _build_inventory_tab(self):
        tab = self._tab_frame("Add / Restock Product")
        tk.Label(tab, text="Enter product details below. Existing products will be restocked.",
                 font=("Tahoma", 9), bg="#EBF5FB", fg="#555").pack()
        form = self._form_frame(tab)
        self.inv_name_e  = self._entry_row(form, "Product Name:", 0)
        self.inv_price_e = self._entry_row(form, f"Unit Price ({CURRENCY}):", 1)
        self.inv_qty_e   = self._entry_row(form, "Quantity:", 2)
        self.inv_cat_var = tk.StringVar(value="General")
        self._combo_row(form, "Category:", 3, CATEGORIES, self.inv_cat_var)
        self.inv_entries = [self.inv_name_e, self.inv_price_e, self.inv_qty_e]
        self._btn_row(tab, [
            ("✅ Add / Restock", "#1A5276", self._handle_add_product),
            ("🔄 Clear",         "#7F8C8D", lambda: self._clear_entries(self.inv_entries)),
        ])
        self.inv_result = self._result_label(tab)
        self.notebook.add(tab, text="📦 Add Product")

    # TAB 2: RECORD SALE
    def _build_sales_tab(self):
        tab = self._tab_frame("Record a Sale")
        tk.Label(tab, text="Select a product and enter the quantity sold.",
                 font=("Tahoma", 9), bg="#EBF5FB", fg="#555").pack()
        form = self._form_frame(tab)
        self.sale_product_var = tk.StringVar()
        self.sale_dropdown = self._combo_row(form, "Product Name:", 0, [], self.sale_product_var)
        self.sale_dropdown.bind("<<ComboboxSelected>>", self._show_product_price)
        self.sale_price_lbl = tk.Label(form, text="", font=("Tahoma", 10, "italic"),
                                       bg="#EBF5FB", fg="#2E86C1")
        self.sale_price_lbl.grid(row=1, column=1, sticky="w", padx=10)
        self.sale_qty_entry = self._entry_row(form, "Quantity Sold:", 2)
        self._btn_row(tab, [
            ("💳 Record Sale",    "#1D8348", self._handle_record_sale),
            ("🔄 Refresh List",   "#7F8C8D", self._refresh_dropdown),
        ])
        self.sale_result = self._result_label(tab)
        self.notebook.add(tab, text="💰 Record Sale")

    # TAB 3: VIEW INVENTORY
    def _build_view_tab(self):
        tab = self._tab_frame("Current Inventory")
        cols   = ("Product", "Category", f"Price ({CURRENCY})", "Stock", "Status")
        widths = [180, 130, 120, 80, 110]
        self.tree = self._treeview(tab, cols, widths)
        self._btn_row(tab, [
            ("🔃 Refresh",              "#2E86C1", self._refresh_inventory_view),
            ("📤 Export to CSV",        "#6C3483", self._handle_export_csv),
        ])
        self.notebook.add(tab, text="📋 View Inventory")

    # TAB 4: EDIT / DELETE
    def _build_edit_tab(self):
        tab = self._tab_frame("Edit / Delete Product")
        tk.Label(tab, text="Select a product to edit its details or delete it from inventory.",
                 font=("Tahoma", 9), bg="#EBF5FB", fg="#555").pack()
        form = self._form_frame(tab)
        self.edit_product_var = tk.StringVar()
        self.edit_dropdown = self._combo_row(form, "Select Product:", 0, [], self.edit_product_var)
        self.edit_dropdown.bind("<<ComboboxSelected>>", self._load_product_for_edit)
        self.edit_name_e  = self._entry_row(form, "New Name:", 1)
        self.edit_price_e = self._entry_row(form, f"New Price ({CURRENCY}):", 2)
        self.edit_qty_e   = self._entry_row(form, "New Quantity:", 3)
        self.edit_cat_var = tk.StringVar(value="General")
        self._combo_row(form, "Category:", 4, CATEGORIES, self.edit_cat_var)
        self.edit_entries = [self.edit_name_e, self.edit_price_e, self.edit_qty_e]
        self._btn_row(tab, [
            ("✏️ Save Changes",  "#E67E22", self._handle_edit_product),
            ("🗑️ Delete Product","#C0392B", self._handle_delete_product),
        ])
        self.edit_result = self._result_label(tab)
        self.notebook.add(tab, text="✏️ Edit / Delete")

    # TAB 5: SEARCH & FILTER
    def _build_search_tab(self):
        tab = self._tab_frame("Search & Filter Inventory")
        sf = tk.Frame(tab, bg="#EBF5FB")
        sf.pack(pady=4)
        tk.Label(sf, text="Search:", font=("Tahoma", 10), bg="#EBF5FB").grid(row=0, column=0, padx=6)
        self.search_entry = tk.Entry(sf, font=("Tahoma", 10), width=20, relief="solid", bd=1)
        self.search_entry.grid(row=0, column=1, padx=6)
        tk.Label(sf, text="Category:", font=("Tahoma", 10), bg="#EBF5FB").grid(row=0, column=2, padx=6)
        self.filter_cat_var = tk.StringVar(value="All")
        cat_opts = ["All"] + CATEGORIES
        ttk.Combobox(sf, textvariable=self.filter_cat_var, values=cat_opts,
                     font=("Tahoma", 10), width=16, state="readonly").grid(row=0, column=3, padx=6)
        self._btn_row(tab, [
            ("🔍 Search",    "#1A5276", self._handle_search),
            ("🔄 Clear",     "#7F8C8D", self._clear_search),
        ])
        cols   = ("Product", "Category", f"Price ({CURRENCY})", "Stock", "Status")
        widths = [180, 130, 120, 80, 110]
        self.search_tree = self._treeview(tab, cols, widths, height=10)
        self.notebook.add(tab, text="🔍 Search")

    # TAB 6: RECEIPT
    def _build_receipt_tab(self):
        tab = self._tab_frame("Sales Receipt Generator")
        tk.Label(tab, text="Select a recent sale to generate and save its receipt.",
                 font=("Tahoma", 9), bg="#EBF5FB", fg="#555").pack()
        rf = tk.Frame(tab, bg="#EBF5FB"); rf.pack(pady=6)
        tk.Label(rf, text="Select Sale:", font=("Tahoma", 10), bg="#EBF5FB").pack(side="left", padx=6)
        self.receipt_dropdown = ttk.Combobox(rf, font=("Tahoma", 10), width=45, state="readonly")
        self.receipt_dropdown.pack(side="left", padx=6)
        self._btn_row(tab, [
            ("🧾 View Receipt",  "#1A5276", self._handle_view_receipt),
            ("💾 Save Receipt",  "#1D8348", self._handle_save_receipt),
        ])
        self.receipt_text = tk.Text(tab, font=("Courier", 11), bg="#FDFEFE",
                                    relief="solid", bd=1, state="disabled",
                                    width=44, height=16)
        self.receipt_text.pack(pady=4)
        self.notebook.add(tab, text="🧾 Receipt")

    # TAB 7: DASHBOARD
    def _build_dashboard_tab(self):
        tab = self._tab_frame("Business Dashboard")
        tk.Label(tab, text="A quick overview of your business performance.",
                 font=("Tahoma", 9), bg="#EBF5FB", fg="#555").pack()

        # Stats row
        self.dash_stats_frame = tk.Frame(tab, bg="#EBF5FB")
        self.dash_stats_frame.pack(fill="x", padx=20, pady=10)

        self.dash_cards = {}
        card_data = [
            ("total_products", "📦 Products",      "#2E86C1"),
            ("total_sales",    "💰 Sales Made",     "#1D8348"),
            ("total_revenue",  "💵 Total Revenue",  "#6C3483"),
            ("low_stock",      "⚠️ Low Stock",      "#C0392B"),
        ]
        for key, label, color in card_data:
            card = tk.Frame(self.dash_stats_frame, bg=color, padx=14, pady=10, relief="flat")
            card.pack(side="left", expand=True, fill="both", padx=6)
            tk.Label(card, text=label, font=("Tahoma", 9, "bold"),
                     bg=color, fg="white").pack()
            val_lbl = tk.Label(card, text="—", font=("Tahoma", 16, "bold"),
                               bg=color, fg="white")
            val_lbl.pack()
            self.dash_cards[key] = val_lbl

        # Top sellers
        tk.Label(tab, text="🏆 Top 5 Best-Selling Products",
                 font=("Tahoma", 11, "bold"), bg="#EBF5FB", fg="#1B4F72").pack(pady=(8, 2))
        cols   = ("Rank", "Product", "Units Sold", "Revenue (NLe)")
        widths = [60, 220, 120, 160]
        self.dash_tree = self._treeview(tab, cols, widths, height=6)
        self._btn_row(tab, [
            ("🔃 Refresh Dashboard", "#1B4F72", self._refresh_dashboard),
        ])
        self.notebook.add(tab, text="📈 Dashboard")

    # TAB 8: SUMMARY
    def _build_summary_tab(self):
        tab = self._tab_frame("Business Summary Report")
        self.summary_text = tk.Text(tab, font=("Courier", 10), bg="#FDFEFE",
                                    relief="solid", bd=1, state="disabled",
                                    wrap="none", height=22)
        hs = ttk.Scrollbar(tab, orient="horizontal", command=self.summary_text.xview)
        vs = ttk.Scrollbar(tab, orient="vertical",   command=self.summary_text.yview)
        self.summary_text.configure(xscrollcommand=hs.set, yscrollcommand=vs.set)
        self.summary_text.pack(fill="both", expand=True, padx=10)
        hs.pack(fill="x", padx=10)
        self._btn_row(tab, [
            ("📊 Generate Report",    "#6C3483", self._handle_summary),
            ("📤 Export to File",     "#1D8348", self._handle_export),
        ])
        self.notebook.add(tab, text="📊 Summary")

    # STATUS BAR
    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Welcome to TradeTrack SL v2.0 | Sierra Leone")
        tk.Label(self.root, textvariable=self.status_var, font=("Tahoma", 9),
                 bg="#1B4F72", fg="#AED6F1", anchor="w", padx=10, pady=3).pack(fill="x", side="bottom")


    # EVENT HANDLERS

    def _handle_add_product(self):
        name  = self.inv_name_e.get()
        price = self.inv_price_e.get()
        qty   = self.inv_qty_e.get()
        cat   = self.inv_cat_var.get()
        success, msg = add_product(name, price, qty, cat)
        self.inv_result.config(text=msg, fg="#1D8348" if success else "#C0392B")
        if success:
            self._clear_entries(self.inv_entries)
            self._set_status(f"'{name.strip().title()}' added/updated.")

    def _handle_record_sale(self):
        product = self.sale_product_var.get()
        qty     = self.sale_qty_entry.get()
        success, msg = record_sale(product, qty)
        self.sale_result.config(text=msg, fg="#1D8348" if success else "#C0392B")
        if success:
            self.sale_qty_entry.delete(0, tk.END)
            self.sale_price_lbl.config(text="")
            self._set_status(f"Sale recorded for '{product}'.")

    def _handle_edit_product(self):
        old  = self.edit_product_var.get()
        name = self.edit_name_e.get()
        price= self.edit_price_e.get()
        qty  = self.edit_qty_e.get()
        cat  = self.edit_cat_var.get()
        success, msg = edit_product(old, name, price, qty, cat)
        self.edit_result.config(text=msg, fg="#1D8348" if success else "#C0392B")
        if success:
            self._refresh_edit_dropdown()
            self._set_status(msg)

    def _handle_delete_product(self):
        name = self.edit_product_var.get()
        if not name:
            self.edit_result.config(text="Please select a product first.", fg="#C0392B")
            return
        if messagebox.askyesno("Confirm Delete", f"Delete '{name}'? This cannot be undone."):
            success, msg = delete_product(name)
            self.edit_result.config(text=msg, fg="#1D8348" if success else "#C0392B")
            if success:
                self._clear_entries(self.edit_entries)
                self.edit_product_var.set("")
                self._refresh_edit_dropdown()
                self._set_status(msg)

    def _handle_search(self):
        keyword = self.search_entry.get()
        cat     = self.filter_cat_var.get()
        results = search_inventory(keyword) if keyword else filter_by_category(cat)
        if keyword and cat != "All":
            results = {k: v for k, v in results.items() if v.get("category") == cat}
        for row in self.search_tree.get_children():
            self.search_tree.delete(row)
        for name, data in results.items():
            status = "⚠️ Low Stock" if data["quantity"] <= LOW_STOCK_THRESHOLD else "✅ In Stock"
            tag    = "low" if data["quantity"] <= LOW_STOCK_THRESHOLD else "ok"
            self.search_tree.insert("", tk.END,
                values=(name, data.get("category","General"),
                        f"{CURRENCY} {data['price']:,.2f}", data["quantity"], status), tags=(tag,))
        self._set_status(f"Search: {len(results)} result(s) found.")

    def _handle_view_receipt(self):
        idx = self.receipt_dropdown.current()
        if idx < 0 or not sales_log:
            return
        receipt = generate_receipt(sales_log[-(idx + 1)])
        self.receipt_text.config(state="normal")
        self.receipt_text.delete("1.0", tk.END)
        self.receipt_text.insert(tk.END, receipt)
        self.receipt_text.config(state="disabled")
        self._set_status("Receipt generated.")

    def _handle_save_receipt(self):
        idx = self.receipt_dropdown.current()
        if idx < 0 or not sales_log:
            messagebox.showwarning("No Receipt", "Please select a sale first.")
            return
        sale    = sales_log[-(idx + 1)]
        receipt = generate_receipt(sale)
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text Files", "*.txt")],
            initialfile=f"Receipt_{sale['product']}_{sale['date'].replace(':', '-').replace(' ', '_')}.txt")
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(receipt)
            messagebox.showinfo("Saved", f"Receipt saved:\n{filepath}")
            self._set_status("Receipt saved.")

    def _handle_summary(self):
        report = generate_summary()
        self.summary_text.config(state="normal")
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, report)
        self.summary_text.config(state="disabled")
        self._set_status("Summary report generated.")

    def _handle_export(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text Files", "*.txt")],
            initialfile=f"TradeTrack_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt")
        if filepath:
            export_summary_to_file(filepath)
            messagebox.showinfo("Exported", f"Report saved:\n{filepath}")
            self._set_status("Report exported.")

    def _handle_export_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV Files", "*.csv")],
            initialfile=f"TradeTrack_Inventory_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
        if filepath:
            export_inventory_to_csv(filepath)
            messagebox.showinfo("Exported", f"Inventory exported:\n{filepath}")
            self._set_status("Inventory exported to CSV.")

    def _refresh_dashboard(self):
        total_rev = sum(s["total"] for s in sales_log)
        self.dash_cards["total_products"].config(text=str(len(inventory)))
        self.dash_cards["total_sales"].config(text=str(len(sales_log)))
        self.dash_cards["total_revenue"].config(text=f"{CURRENCY} {total_rev:,.2f}")
        self.dash_cards["low_stock"].config(text=str(len(get_low_stock_items())))
        for row in self.dash_tree.get_children():
            self.dash_tree.delete(row)
        for i, (name, qty) in enumerate(get_top_selling_products(5), 1):
            rev = sum(s["total"] for s in sales_log if s["product"] == name)
            self.dash_tree.insert("", tk.END, values=(i, name, qty, f"{rev:,.2f}"))
        self._set_status("Dashboard refreshed.")

    # HELPERS

    def _show_product_price(self, event=None):
        name = self.sale_product_var.get()
        if name in inventory:
            p = inventory[name]["price"]
            q = inventory[name]["quantity"]
            self.sale_price_lbl.config(text=f"Price: {CURRENCY} {p:,.2f}  |  In Stock: {q}")

    def _refresh_dropdown(self):
        products = list(inventory.keys())
        self.sale_dropdown["values"] = products
        self.sale_result.config(text=f"{len(products)} product(s) available.", fg="#2E86C1")

    def _refresh_edit_dropdown(self):
        self.edit_dropdown["values"] = list(inventory.keys())

    def _load_product_for_edit(self, event=None):
        name = self.edit_product_var.get()
        if name in inventory:
            self.edit_name_e.delete(0, tk.END);  self.edit_name_e.insert(0, name)
            self.edit_price_e.delete(0, tk.END); self.edit_price_e.insert(0, f"{inventory[name]['price']:.2f}")
            self.edit_qty_e.delete(0, tk.END);   self.edit_qty_e.insert(0, str(inventory[name]["quantity"]))
            self.edit_cat_var.set(inventory[name].get("category", "General"))

    def _refresh_inventory_view(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for name, data in inventory.items():
            status = "⚠️ Low Stock" if data["quantity"] <= LOW_STOCK_THRESHOLD else "✅ In Stock"
            tag    = "low" if data["quantity"] <= LOW_STOCK_THRESHOLD else "ok"
            self.tree.insert("", tk.END,
                values=(name, data.get("category","General"),
                        f"{CURRENCY} {data['price']:,.2f}", data["quantity"], status), tags=(tag,))
        self._set_status(f"Inventory refreshed. {len(inventory)} product(s).")

    def _refresh_receipt_dropdown(self):
        self.receipt_dropdown["values"] = [
            f"{s['date']}  —  {s['product']}  x{s['qty']}  ({CURRENCY} {s['total']:,.2f})"
            for s in reversed(sales_log)
        ]

    def _on_tab_changed(self, event):
        idx = self.notebook.index(self.notebook.select())
        actions = {
            1: lambda: (self._refresh_dropdown(), self.sale_result.config(text="")),
            2: self._refresh_inventory_view,
            3: self._refresh_edit_dropdown,
            4: self._handle_search,
            5: self._refresh_receipt_dropdown,
            6: self._refresh_dashboard,
        }
        if idx in actions:
            actions[idx]()

    def _clear_entries(self, entries):
        for e in entries:
            e.delete(0, tk.END)

    def _clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.filter_cat_var.set("All")
        self._handle_search()

    def _set_status(self, message):
        self.status_var.set(f"[{datetime.now().strftime('%H:%M:%S')}]  {message}")


# MAIN ENTRY POINT

def main():
    """Launch TradeTrack SL."""
    load_data()   # Load saved data before launching the GUI
    root = tk.Tk()
    app = TradeTrackApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (save_data(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()