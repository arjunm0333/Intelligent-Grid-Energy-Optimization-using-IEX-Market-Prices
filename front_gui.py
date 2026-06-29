# front.py (refreshed UI)
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from datetime import datetime, timedelta
import sqlite3
import os
from scraper_iex_mcp import mcp  # expects mcp() function inside this module
from scraper_iex_mcp import rec

DB_NAME = "appliance_schedule.db"
TIME_FORMAT = "%H:%M"

def generate_time_slots():
    slots = []
    current = datetime.strptime("00:00", TIME_FORMAT)
    for _ in range(96):
        start = current.strftime(TIME_FORMAT)
        end = (current + timedelta(minutes=15)).strftime(TIME_FORMAT)
        slots.append(f"{start} - {end}")
        current += timedelta(minutes=15)
    return slots

time_slots = generate_time_slots()

power_ratings = {
    "Refrigerator": 250, "Chimney": 250, "Laptop": 200, "Television": 200,
    "Fan": 100, "camera dvr": 60, "Water Purifier": 60, "Fluorescent lamp": 40,
    "Ceiling lamp": 30, "LED Bulbs": 20, "cctv camera": 7, "Mobile charging": 6,
    "Night lamp": 3, "Washing machine": 2300, "Air conditioner": 3500,
    "Water Heater": 2000, "Electric kettle": 2000, "Pumping machine": 1500,
    "Bore pump": 1400, "Vacuum cleaner": 1200, "Home theatre": 1000,
    "Electric Cooker": 1000, "Mixie": 1000, "Iron": 1000, "Microwave oven": 900
}
appliances = list(power_ratings.keys())

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    columns_str = ", ".join([f'"{slot}" TEXT' for slot in time_slots])

    c.execute(f'''
        CREATE TABLE IF NOT EXISTS schedule_2 (
            appliance TEXT PRIMARY KEY,
            is_247_on INTEGER DEFAULT 0,
            {columns_str}
        )
    ''')
    conn.commit()

    # Ensure column exists (backwards compatibility)
    c.execute("PRAGMA table_info(schedule_2)")
    columns_info = c.fetchall()
    column_names = [col[1] for col in columns_info]
    if 'is_247_on' not in column_names:
        c.execute("ALTER TABLE schedule_2 ADD COLUMN is_247_on INTEGER DEFAULT 0")
        conn.commit()

    for appliance in appliances:
        c.execute("INSERT OR IGNORE INTO schedule_2 (appliance) VALUES (?)", (appliance,))
    conn.commit()
    conn.close()

# Run MCP scraping (keeps your existing behavior)
print("Using DB at:", os.path.abspath(DB_NAME))
mcp_data.mcp()
init_db()

# quick MCP validation
conn_mcp_validation = sqlite3.connect("iex_market_snapshot.db")
c_mcp_validation = conn_mcp_validation.cursor()
c_mcp_validation.execute("SELECT COUNT(*) FROM dam_price WHERE date_captured = ?", (datetime.now().strftime("%Y-%m-%d"),))
mcp_count = c_mcp_validation.fetchone()[0]
conn_mcp_validation.close()

if mcp_count != 96:
    print("⚠️ Warning: MCP data is missing or incomplete for today!")

# --- GUI ---
root = tk.Tk()
root.title("Appliance Scheduler — Optimized")
root.geometry("1400x780")
root.minsize(1000, 600)

# ---------- Styling ----------
style = ttk.Style(root)
style.theme_use("clam")  # clam is neutral and supports customizations

# fonts
TITLE_FONT = tkfont.Font(family="Inter", size=18, weight="bold")
LABEL_FONT = tkfont.Font(family="Inter", size=11)
SMALL_FONT = tkfont.Font(family="Inter", size=10)

style.configure("TFrame", background="#f5f6fa")
style.configure("Card.TFrame", background="#ffffff", relief="flat")
style.configure("Header.TLabel", font=TITLE_FONT, background="#f5f6fa")
style.configure("TLabel", background="#f5f6fa", font=LABEL_FONT)
style.configure("Small.TLabel", background="#f5f6fa", font=SMALL_FONT)
style.configure("TButton", font=LABEL_FONT, padding=6)
style.configure("Primary.TButton", background="#2b6cb0", foreground="#ffffff")
style.map("Primary.TButton",
          background=[("active", "#255a97"), ("disabled", "#a6c0df")])

# Treeview custom
style.configure("Treeview",
                background="#ffffff",
                foreground="#111827",
                fieldbackground="#ffffff",
                rowheight=28,
                font=("Inter", 10))
style.configure("Treeview.Heading", font=("Inter", 10, "bold"))
style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])  # full area

# alternating row colors
style.map("Treeview", background=[('selected', '#cfe8ff')])
ALT1 = "#ffffff"
ALT2 = "#f3f6fb"

# ---------- Layout ----------
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Outer container
outer = ttk.Frame(root, padding=(12, 12, 12, 12), style="TFrame")
outer.grid(row=0, column=0, sticky="nsew")

# Top header
header = ttk.Frame(outer, style="TFrame")
header.pack(fill="x", pady=(0, 10))
ttk.Label(header, text="Appliance Scheduler", style="Header.TLabel").pack(side="left")
mcp_status = ttk.Label(header, text=f"MCP blocks today: {mcp_count}/96", style="Small.TLabel")
mcp_status.pack(side="right")

# Main split: left controls, right table
main_panes = ttk.Frame(outer, style="TFrame")
main_panes.pack(fill="both", expand=True)

main_panes.grid_rowconfigure(0, weight=1)
main_panes.grid_columnconfigure(1, weight=1)

# ---------- Left: Controls card ----------
control_card = ttk.Frame(main_panes, style="Card.TFrame", padding=(12,12,12,12))
control_card.grid(row=0, column=0, sticky="nsw", padx=(0,12), pady=(0,6))
control_card.grid_propagate(False)
control_card.configure(width=360)

ttk.Label(control_card, text="Configure Appliance", font=("Inter", 14, "bold"), background="#ffffff").pack(anchor="w", pady=(0,8))

# form elements
form = ttk.Frame(control_card, style="Card.TFrame")
form.pack(fill="x")

ttk.Label(form, text="Select Appliance:").pack(anchor="w", pady=(6,2))
appliance_var = tk.StringVar()
appliance_combo = ttk.Combobox(form, textvariable=appliance_var, values=appliances, state="readonly", width=30)
appliance_combo.pack(fill="x")

ttk.Label(form, text="Select Time Slot:").pack(anchor="w", pady=(8,2))
time_var = tk.StringVar()
time_dropdown = ttk.Combobox(form, textvariable=time_var, values=time_slots, state="readonly", width=30)
time_dropdown.pack(fill="x")

ttk.Label(form, text="Number of Appliances (1–10):").pack(anchor="w", pady=(8,2))
quantity_var = tk.StringVar()
quantity_combo = ttk.Combobox(form, textvariable=quantity_var, values=[str(i) for i in range(1, 11)], state="readonly", width=30)
quantity_combo.pack(fill="x")

# 24/7 toggle with nice label
always_on_var = tk.BooleanVar()
def toggle_time_dropdown():
    time_dropdown.configure(state="disabled" if always_on_var.get() else "readonly")

toggle_frame = ttk.Frame(form, style="Card.TFrame")
toggle_frame.pack(fill="x", pady=(10,2))
always_check = ttk.Checkbutton(toggle_frame, text="24/7 ON (set appliance always on)", variable=always_on_var, command=toggle_time_dropdown)
always_check.pack(anchor="w")

result_label = ttk.Label(control_card, text="", style="Small.TLabel")
result_label.pack(anchor="w", pady=(8,2))

# Buttons
btn_frame = ttk.Frame(control_card, style="Card.TFrame")
btn_frame.pack(fill="x", pady=(12,0))
submit_btn = ttk.Button(btn_frame, text="Submit", command=lambda: submit(), style="TButton")
submit_btn.pack(side="left", expand=True, fill="x", padx=(0,6))
clear_btn = ttk.Button(btn_frame, text="Clear All", command=lambda: clear_all(), style="TButton")
clear_btn.pack(side="left", expand=True, fill="x", padx=(6,6))
rec_btn = ttk.Button(btn_frame, text="Show Recommendation", command=lambda: [rec(result_tab), tab_control.select(result_tab)], style="Primary.TButton")
rec_btn.pack(side="left", expand=True, fill="x", padx=(6,0))

# Helpful hints
hint = ttk.Label(control_card, text="Hint: Select appliance and time slot, choose quantity. Use 24/7 toggle for always-on devices.", style="Small.TLabel", wraplength=320)
hint.pack(anchor="w", pady=(10,0))

# ---------- Right: Tabs & Table ----------
tab_control = ttk.Notebook(main_panes)
tab_control.grid(row=0, column=1, sticky="nsew")

main_tab = ttk.Frame(tab_control, style="TFrame")
result_tab = ttk.Frame(tab_control, style="TFrame")
tab_control.add(main_tab, text="Main")
tab_control.add(result_tab, text="Recommendation")

# Table area inside main_tab
table_outer = ttk.Frame(main_tab, style="TFrame")
table_outer.pack(fill="both", expand=True, padx=(6,0), pady=(0,6))

# canvas + frame to allow full-size treeview with scrollbars
tree_frame = ttk.Frame(table_outer)
tree_frame.pack(fill="both", expand=True)

# Treeview and scrollbars
columns = ["appliance", "is_247_on"] + time_slots
tree_container = ttk.Frame(tree_frame)
tree_container.pack(fill="both", expand=True)

v_scroll = ttk.Scrollbar(tree_container, orient="vertical")
h_scroll = ttk.Scrollbar(table_outer, orient="horizontal")

tree = ttk.Treeview(tree_container, columns=columns, show="headings", yscrollcommand=v_scroll.set)
v_scroll.config(command=tree.yview)
h_scroll.config(command=tree.xview)
tree.configure(xscrollcommand=h_scroll.set)

# Headings & column sizing
tree.heading("appliance", text="Appliance")
tree.column("appliance", width=180, anchor="w", stretch=False)
tree.heading("is_247_on", text="24/7")
tree.column("is_247_on", width=70, anchor="center", stretch=False)

for col in time_slots:
    tree.heading(col, text=col)
    tree.column(col, width=90, anchor="center")  # narrow columns for many time blocks

tree.pack(side="left", fill="both", expand=True)
v_scroll.pack(side="right", fill="y")
h_scroll.pack(side="bottom", fill="x")

# alternate row coloring helper
def colorize_rows():
    for i, iid in enumerate(tree.get_children()):
        tree.item(iid, tags=('odd' if i%2 else 'even',))
    tree.tag_configure('even', background=ALT1)
    tree.tag_configure('odd', background=ALT2)

# ---------- Functions ----------
def refresh_table():
    for row in tree.get_children():
        tree.delete(row)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    select_cols = ["appliance", "is_247_on"] + [f'"{slot}"' for slot in time_slots]
    c.execute(f"SELECT {', '.join(select_cols)} FROM schedule_2")
    for row in c.fetchall():
        display_row = list(row)
        display_row[1] = "Yes" if display_row[1] == 1 else "No"
        tree.insert("", "end", values=display_row)
    conn.close()
    colorize_rows()

def submit():
    appliance = appliance_var.get()
    time_slot = time_var.get()
    quantity = quantity_var.get()
    is_247 = always_on_var.get()

    if not appliance or not quantity or (not time_slot and not is_247):
        result_label.config(text="Please fill all fields correctly.", foreground="#b02a37")
        return

    try:
        total_power = power_ratings.get(appliance, 0) * int(quantity)
    except Exception as e:
        result_label.config(text="Invalid quantity.", foreground="#b02a37")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if is_247:
        c.execute('UPDATE schedule_2 SET is_247_on = ? WHERE appliance = ?', (1, appliance))
        for slot in time_slots:
            c.execute(f'UPDATE schedule_2 SET "{slot}" = ? WHERE appliance = ?', (total_power, appliance))
    else:
        c.execute('UPDATE schedule_2 SET is_247_on = ? WHERE appliance = ?', (0, appliance))
        c.execute(f'UPDATE schedule_2 SET "{time_slot}" = ? WHERE appliance = ?', (total_power, appliance))

    conn.commit()
    conn.close()
    result_label.config(text="Updated successfully.", foreground="#006b2c")
    refresh_table()

def clear_all():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    for slot in time_slots:
        c.execute(f'UPDATE schedule_2 SET "{slot}" = NULL')
    c.execute('UPDATE schedule_2 SET is_247_on = 0')
    conn.commit()
    conn.close()
    result_label.config(text="Cleared.", foreground="#0b6a9a")
    refresh_table()

# ---------- Bottom sticky bar ----------
status_bar = ttk.Frame(outer, padding=(8,6), style="TFrame")
status_bar.pack(fill="x", side="bottom", pady=(8,0))
status_text = tk.StringVar()
status_text.set("Ready")
status_label = ttk.Label(status_bar, textvariable=status_text, style="Small.TLabel")
status_label.pack(side="left")

def update_status(msg, duration=4000):
    status_text.set(msg)
    root.after(duration, lambda: status_text.set("Ready"))

# Hook into buttons to update status
orig_submit = submit
def submit_with_status():
    orig_submit()
    update_status("Schedule updated.")
submit_btn.configure(command=submit_with_status)
rec_btn.configure(command=lambda: [rec(result_tab), tab_control.select(result_tab), update_status("Recommendations generated.")])

# Finalize table contents and start
refresh_table()

# Keyboard shortcuts
def on_escape(event=None):
    root.quit()
root.bind("<Escape>", on_escape)

root.mainloop()