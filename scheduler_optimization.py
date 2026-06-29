import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import sqlite3
import logging

# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# --- Database paths ---
MCP_DB = "iex_market_snapshot.db"
POWER_DB = "appliance_schedule.db"
MCP_TABLE = "dam_price"
POWER_TABLE = "schedule_2"

# --- Global Power Ratings (to ensure consistent values) ---
POWER_RATINGS_STATIC = {
    "Refrigerator": 250, "Chimney": 250, "Laptop": 200, "Television": 200,
    "Fan": 100, "camera dvr": 60, "Water Purifier": 60, "Fluorescent lamp": 40,
    "Ceiling lamp": 30, "LED Bulbs": 20, "cctv camera": 7, "Mobile charging": 6,
    "Night lamp": 3, "Washing machine": 2300, "Air conditioner": 3500,
    "Water Heater": 2000, "Electric kettle": 2000, "Pumping machine": 1500,
    "Bore pump": 1400, "Vacuum cleaner": 1200, "Home theatre": 1000,
    "Electric Cooker": 1000, "Mixie": 1000, "Iron": 1000, "Microwave oven": 900
}

# --- FIXED: Enhanced Appliance "Personalities" Constraint Dictionary ---
APPLIANCE_CONSTRAINTS = {
    "Refrigerator":     {"type": "curtailable"},
    
    # Fully Shiftable (can run anytime - typically appliances that don't disturb users)
    "Washing machine":  {"type": "fully_shiftable"},
    "Pumping machine":  {"type": "fully_shiftable"},
    "Bore pump":        {"type": "fully_shiftable"},
    "Fan":              {"type": "fully_shiftable"},
    "Laptop":           {"type": "fully_shiftable"},
    "Chimney":          {"type": "fully_shiftable"},
    "camera dvr":       {"type": "fully_shiftable"},
    "cctv camera":      {"type": "fully_shiftable"},
    "Water Purifier":   {"type": "fully_shiftable"},

    # --- Non-contiguous (individual 15-min blocks within window) ---
    "LED Bulbs":        {"type": "preferred_window_noncontiguous", "window": (72, 92)}, # 18:00 - 23:00
    "Mixie":            {"type": "preferred_window_noncontiguous", "window": (24, 40)}, # 06:00 - 10:00
    "Mobile charging":  {"type": "preferred_window_noncontiguous", "window": (72, 92)}, # Evening charging
    "Electric kettle":  {"type": "preferred_window_noncontiguous", "window": (24, 84)}, # 06:00 - 21:00
    "Night lamp":       {"type": "preferred_window_noncontiguous", "window": (84, 96)}, # 21:00 - 00:00
    "Fluorescent lamp": {"type": "preferred_window_noncontiguous", "window": (72, 92)}, # 18:00 - 23:00
    "Ceiling lamp":     {"type": "preferred_window_noncontiguous", "window": (72, 92)}, # 18:00 - 23:00

    # --- Contiguous (single continuous block within window) ---
    "Iron":             {"type": "preferred_window_contiguous", "window": (28, 72)}, # 07:00 - 18:00
    "Microwave oven":   {"type": "preferred_window_contiguous", "window": (28, 88)}, # 07:00 - 22:00
    "Television":       {"type": "preferred_window_contiguous", "window": (68, 92)}, # 17:00 - 23:00
    "Electric Cooker":  {"type": "preferred_window_contiguous", "window": (28, 84)}, # 07:00 - 21:00
    "Water Heater":     {"type": "preferred_window_contiguous", "window": (40, 84)}, # 10:00 - 21:00
    "Vacuum cleaner":   {"type": "preferred_window_contiguous", "window": (28, 84)}, # 07:00 - 21:00
    "Home theatre":     {"type": "preferred_window_contiguous", "window": (68, 92)}, # 17:00 - 23:00
    "Air conditioner":  {"type": "preferred_window_contiguous", "window": (40, 92)}, # 10:00 - 23:00

    # --- Default for any remaining appliances ---
    "default":          {"type": "fully_shiftable"}
}


# --- Utility Functions ---
def block_to_time_range(block_index):
    start = datetime.strptime("00:00", "%H:%M") + timedelta(minutes=15 * block_index)
    end = start + timedelta(minutes=15)
    return f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"

def format_slot_list(blocks):
    blocks = sorted(list(set(blocks)))
    if not blocks:
        return "N/A"
    
    if len(blocks) == 96 and blocks[0] == 0 and blocks[-1] == 95 and all(blocks[i] == blocks[i-1] + 1 for i in range(1, 96)):
        return "00:00–00:00" 

    ranges = []
    current_range_start_block = blocks[0]
    current_range_end_block = blocks[0]

    for i in range(1, len(blocks)):
        if blocks[i] == current_range_end_block + 1:
            current_range_end_block = blocks[i]
        else:
            ranges.append(f"{block_to_time_range(current_range_start_block).split('–')[0]}–{block_to_time_range(current_range_end_block).split('–')[1]}")
            current_range_start_block = blocks[i]
            current_range_end_block = blocks[i]
    
    ranges.append(f"{block_to_time_range(current_range_start_block).split('–')[0]}–{block_to_time_range(current_range_end_block).split('–')[1]}")
    
    return ', '.join(ranges)


# --- Recommendation Logic ---
def rec(result_tab):
    def clean_nulls_in_db():
        conn = sqlite3.connect(POWER_DB)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({POWER_TABLE})")
        
        columns_to_update = []
        for col_info in cursor.fetchall():
            col_name = col_info[1]
            if " - " in col_name and ":" in col_name:
                columns_to_update.append(f'"{col_name}"')
        
        if columns_to_update:
            set_clause = ", ".join([f'{col} = COALESCE({col}, 0)' for col in columns_to_update])
            cursor.execute(f'UPDATE {POWER_TABLE} SET {set_clause};')
            conn.commit()
        conn.close()

    def get_mcp_values(date_str):
        conn = sqlite3.connect(MCP_DB)
        cursor = conn.cursor()
        cursor.execute(f"SELECT mcp_value FROM {MCP_TABLE} WHERE date_captured = ? ORDER BY time_block ASC", (date_str,))
        values = [row[0] for row in cursor.fetchall()]
        conn.close()
        if len(values) != 96:
            logging.warning(f"Expected 96 MCP values for {date_str}, but got {len(values)}. Using dummy MCP data.")
            return [1.0] * 96 
        return values

    def load_appliances_from_db():
        conn = sqlite3.connect(POWER_DB)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {POWER_TABLE}")
        rows = cursor.fetchall()
        
        cursor.execute(f"PRAGMA table_info({POWER_TABLE})")
        column_names = [col[1] for col in cursor.fetchall()]
        conn.close() 

        appliance_info = []
        for row_data in rows:
            name = row_data[column_names.index('appliance')]
            is_247_on = row_data[column_names.index('is_247_on')] if 'is_247_on' in column_names else 0

            time_slot_values = []
            for i in range(len(column_names)):
                if column_names[i] not in ['appliance', 'is_247_on']:
                    time_slot_values.append(float(row_data[i]) if row_data[i] is not None else 0.0)

            if is_247_on == 1:
                original_blocks = list(range(96))
                avg_power_watt = POWER_RATINGS_STATIC.get(name, 0)
            else:
                original_blocks = [i for i, v in enumerate(time_slot_values) if v > 0]
                if not original_blocks:
                    continue 
                avg_power_watt = sum(time_slot_values) / len(original_blocks) if original_blocks else 0

            constraints = APPLIANCE_CONSTRAINTS.get(name, APPLIANCE_CONSTRAINTS["default"])

            power_mw = avg_power_watt / 1_000_000
            appliance_info.append({
                "name": name,
                "power_mw": power_mw,
                "duration": len(original_blocks),
                "original_blocks": original_blocks, 
                "is_247_on": is_247_on,
                "constraints": constraints
            })
        return appliance_info

    # --- FIXED: Enhanced recommendation logic ---
    def recommend_schedule(mcp_values, appliance_info):
        schedule = [[0.0] * 96 for _ in appliance_info]
        occupied_blocks = [False] * 96 
        
        # Separate refrigerator handling
        refrigerator_index = -1
        for i, app in enumerate(appliance_info):
            if app["name"] == "Refrigerator" and app["is_247_on"] == 1:
                refrigerator_index = i
                break

        # Handle refrigerator first
        if refrigerator_index != -1:
            appliance = appliance_info[refrigerator_index]
            power = appliance["power_mw"]
            
            # Find cheapest 8 blocks to turn off (during low usage hours)
            inactive_blocks_candidate = list(range(80, 96)) + list(range(0, 24))
            inactive_blocks = [b for b in inactive_blocks_candidate if 0 <= b < 96]
            
            inactive_block_costs = [(mcp_values[b], b) for b in inactive_blocks]
            inactive_block_costs.sort(key=lambda x: x[0], reverse=True) 

            blocks_to_turn_off_count = 8 
            blocks_to_turn_off = []
            
            for _, block_idx in inactive_block_costs:
                if len(blocks_to_turn_off) < blocks_to_turn_off_count:
                    blocks_to_turn_off.append(block_idx)
                else:
                    break
            
            blocks_to_turn_off.sort()
            refrigerator_on_blocks = sorted(list(set(range(96)) - set(blocks_to_turn_off)))
            
            appliance_info[refrigerator_index]["recommended_blocks"] = refrigerator_on_blocks
            appliance_info[refrigerator_index]["turned_off_blocks"] = blocks_to_turn_off 
            appliance_info[refrigerator_index]["duration"] = len(refrigerator_on_blocks)

            for t in refrigerator_on_blocks:
                schedule[refrigerator_index][t] = power
                occupied_blocks[t] = True

        # Process other appliances by priority (shorter durations first)
        sorted_appliances = sorted(
            [i for i in range(len(appliance_info)) if i != refrigerator_index or appliance_info[i]["is_247_on"] != 1],
            key=lambda i: appliance_info[i]["duration"]
        )

        for i in sorted_appliances:
            appliance = appliance_info[i]
            power = appliance["power_mw"]
            duration = appliance["duration"]
            constraints = appliance["constraints"]
            
            if duration == 0:
                appliance_info[i]["recommended_blocks"] = []
                continue

            appliance_type = constraints.get("type", "fully_shiftable")
            recommended_blocks = []
            
            # Handle different constraint types properly
            
            if appliance_type == "preferred_window_noncontiguous":
                # Find cheapest individual blocks within preferred window
                window_start = constraints["window"][0]
                window_end = constraints["window"][1]
                
                # Get available blocks in window sorted by cost
                available_blocks = []
                for t in range(window_start, window_end + 1):
                    if 0 <= t < 96 and not occupied_blocks[t]:
                        available_blocks.append((mcp_values[t], t))
                
                # Sort by cost (cheapest first)
                available_blocks.sort(key=lambda x: x[0])
                
                # Take the required number of cheapest blocks
                for _, block_idx in available_blocks[:duration]:
                    recommended_blocks.append(block_idx)
                    occupied_blocks[block_idx] = True

            elif appliance_type == "preferred_window_contiguous":
                # Find single continuous block within preferred window
                window_start = constraints["window"][0]
                window_end = constraints["window"][1]
                
                best_start = -1
                min_cost = float('inf')
                
                # Search for contiguous block within window
                for start in range(window_start, window_end - duration + 2):
                    end = start + duration
                    if end > 96:
                        continue
                    
                    # Check if all blocks are available
                    conflict = False
                    total_cost = 0
                    for t in range(start, end):
                        if occupied_blocks[t]:
                            conflict = True
                            break
                        total_cost += mcp_values[t]
                    
                    if not conflict and total_cost < min_cost:
                        min_cost = total_cost
                        best_start = start
                
                if best_start != -1:
                    recommended_blocks = list(range(best_start, best_start + duration))
                    for t in recommended_blocks:
                        occupied_blocks[t] = True

            else:  # fully_shiftable
                # Find cheapest contiguous block anywhere
                best_start = -1
                min_cost = float('inf')
                
                for start in range(0, 96 - duration + 1):
                    end = start + duration
                    
                    # Check if all blocks are available
                    conflict = False
                    total_cost = 0
                    for t in range(start, end):
                        if occupied_blocks[t]:
                            conflict = True
                            break
                        total_cost += mcp_values[t]
                    
                    if not conflict and total_cost < min_cost:
                        min_cost = total_cost
                        best_start = start
                
                if best_start != -1:
                    recommended_blocks = list(range(best_start, best_start + duration))
                    for t in recommended_blocks:
                        occupied_blocks[t] = True

            # Fallback: use original blocks if no suitable slot found
            if not recommended_blocks:
                recommended_blocks = appliance["original_blocks"]
                # Try to occupy as many original blocks as possible
                for t in recommended_blocks:
                    if 0 <= t < 96 and not occupied_blocks[t]:
                        occupied_blocks[t] = True
            
            appliance_info[i]["recommended_blocks"] = sorted(recommended_blocks)
            for t in recommended_blocks:
                if 0 <= t < 96:
                    schedule[i][t] = power
        
        return schedule

    def compute_total_cost(mcp_values, schedule):
        total_cost = 0.0
        for appliance_schedule in schedule:
            for t in range(96):
                power_mw = appliance_schedule[t]
                total_cost += power_mw * mcp_values[t] * 0.25 
        return total_cost

    def compute_original_cost(mcp_values, original_rows):
        total_cost = 0.0
        conn = sqlite3.connect(POWER_DB)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({POWER_TABLE})")
        column_names = [col[1] for col in cursor.fetchall()]
        conn.close()

        for row_data in original_rows:
            name = row_data[column_names.index('appliance')]
            is_247_on = row_data[column_names.index('is_247_on')] if 'is_247_on' in column_names else 0
            
            appliance_power_watt = POWER_RATINGS_STATIC.get(name, 0)

            if is_247_on == 1:
                power_mw = appliance_power_watt / 1_000_000
                for i in range(96):
                    total_cost += power_mw * mcp_values[i] * 0.25
            else:
                time_slot_values = []
                for i in range(len(column_names)):
                    if column_names[i] not in ['appliance', 'is_247_on']:
                        time_slot_values.append(float(row_data[i]) if row_data[i] is not None else 0.0)

                for i in range(96):
                    power_mw = time_slot_values[i] / 1_000_000
                    total_cost += power_mw * mcp_values[i] * 0.25
        return total_cost

    def display_results(result_tab, appliances, schedule, original_rows, cost_original, cost_optimized):
        for widget in result_tab.winfo_children():
            widget.destroy()

        outer_frame = tk.Frame(result_tab)
        outer_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer_frame)
        v_scroll = tk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        h_scroll = tk.Scrollbar(outer_frame, orient="horizontal", command=canvas.xview)

        scrollable_frame = tk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")

        tk.Label(scrollable_frame, text="Recommended Schedule", font=("Arial", 16, "bold")).pack(pady=10)

        for appliance in appliances: 
            name = appliance['name']
            original_blocks = appliance.get("original_blocks", [])
            recommended_blocks = appliance.get("recommended_blocks", [])
            turned_off_blocks = appliance.get("turned_off_blocks", []) 

            frame = tk.Frame(scrollable_frame, bd=1, relief="solid", padx=10, pady=5, bg="#f6f6f6")
            frame.pack(fill="x", padx=20, pady=6)

            tk.Label(frame, text=name, font=("Arial", 14, "bold"), bg="#f6f6f6").pack(anchor="w")
            
            original_str = format_slot_list(original_blocks)
            recommended_str = format_slot_list(recommended_blocks)
            
            tk.Label(frame, text=f"🕓 Original:     {original_str}", anchor="w", font=("Consolas", 10), bg="#f6f6f6").pack(anchor="w")
            tk.Label(frame, text=f"✅ Recommended: {recommended_str}", anchor="w", font=("Consolas", 10), bg="#f6f6f6").pack(anchor="w")

            if name == "Refrigerator" and turned_off_blocks:
                turned_off_str = format_slot_list(turned_off_blocks)
                tk.Label(frame, text=f"💡 Suggestion: Turned OFF for 2 hours during: {turned_off_str} to save energy.",
                         fg="red", font=("Consolas", 10, "italic"), bg="#f6f6f6").pack(anchor="w")

        # --- Sticky Bottom Summary ---
        sticky_bar = tk.Frame(result_tab, bg="#ffffff", bd=2, relief="raised")
        sticky_bar.pack(side="bottom", fill="x")

        savings = cost_original - cost_optimized
        tk.Label(sticky_bar, text=f"🕓 Original Cost: ₹{cost_original:.2f}", font=("Arial", 12, "bold"), bg="#ffffff").pack(side="left", padx=20, pady=10)
        tk.Label(sticky_bar, text=f"✅ Optimized Cost: ₹{cost_optimized:.2f}", font=("Arial", 12, "bold"), bg="#ffffff").pack(side="left", padx=20, pady=10)
        tk.Label(sticky_bar, text=f"💸 Savings: ₹{savings:.2f}", font=("Arial", 12, "bold"), fg="green", bg="#ffffff").pack(side="left", padx=20, pady=10)

    # --- Run Optimization ---
    clean_nulls_in_db()
    date_today = datetime.now().strftime("%Y-%m-%d")
    mcp = get_mcp_values(date_today)

    conn = sqlite3.connect(POWER_DB)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {POWER_TABLE}")
    original_rows = cursor.fetchall()
    conn.close()

    appliances = load_appliances_from_db()
    schedule = recommend_schedule(mcp, appliances)
    cost_original = compute_original_cost(mcp, original_rows)
    cost_optimized = compute_total_cost(mcp, schedule)

    display_results(result_tab, appliances, schedule, original_rows, cost_original, cost_optimized)