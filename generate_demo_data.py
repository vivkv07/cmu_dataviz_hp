import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import json
import os # Import os to handle file paths

# --- Configuration ---
NUM_PRINTERS = 10000 # Already > 100
NUM_DAYS = 18 * 30 # Simulate data for approx 18 months (540 days)
START_DATE = datetime.now() - timedelta(days=NUM_DAYS)

# --- MODIFICATION START: Added Envy Photo and Tango models ---
PRINTER_MODELS = {
    "OfficeJet Pro": {"segment": ["SMB", "Enterprise"], "avg_monthly_pages": (300, 1500), "color_ratio": 0.4, "error_rate_monthly": 0.03, "inks": ["Black", "Cyan", "Magenta", "Yellow"]},
    "Envy Inspire": {"segment": ["Home", "SMB"], "avg_monthly_pages": (50, 400), "color_ratio": 0.6, "error_rate_monthly": 0.02, "inks": ["Black", "Tri-color"]},
    "DeskJet": {"segment": ["Home"], "avg_monthly_pages": (20, 150), "color_ratio": 0.5, "error_rate_monthly": 0.04, "inks": ["Black", "Tri-color"]},
    "Smart Tank": {"segment": ["Home", "SMB"], "avg_monthly_pages": (100, 600), "color_ratio": 0.55, "error_rate_monthly": 0.015, "inks": ["Black", "Cyan", "Magenta", "Yellow"]}, # Tank printers
    "Envy Photo": {"segment": ["Home"], "avg_monthly_pages": (40, 250), "color_ratio": 0.7, "error_rate_monthly": 0.025, "inks": ["Black", "Tri-color", "Photo Black"]}, # Added Model
    "Tango": {"segment": ["Home"], "avg_monthly_pages": (30, 120), "color_ratio": 0.6, "error_rate_monthly": 0.03, "inks": ["Black", "Tri-color"]} # Added Model
}
# --- MODIFICATION END ---

REGIONS = ["NA", "EU", "APAC", "LATAM"]
CUSTOMER_SEGMENTS = ["Home", "SMB", "Enterprise"]
ERROR_CODES = ["E01", "E04", "P11", "C02", "M05", "J10", "F03"]
FIRMWARE_VERSIONS = ["FW1.0", "FW1.1", "FW1.2", "FW2.0", "FW2.1"]
AVG_DAYS_PER_MONTH = 30.437 # More precise average

# --- Generate Printer Inventory ---
printers_data = []
print(f"Generating inventory for {NUM_PRINTERS} printers (Expanded Ink Models)...")
for i in range(NUM_PRINTERS):
    # Ensure a model is chosen only from the updated list
    model_name = random.choice(list(PRINTER_MODELS.keys()))
    model_info = PRINTER_MODELS[model_name]
    # Ensure segment is valid for the chosen model
    segment = random.choice(model_info["segment"])
    region = random.choice(REGIONS)
    firmware = random.choice(FIRMWARE_VERSIONS)
    # Generate unique printer ID based on model name
    printer_id = f"{model_name.split()[0][:3].upper()}{random.randint(1000, 9999)}{chr(65+(i//100)%26)}{chr(65+i%26)}"

    # Calculate base daily pages and daily error rate
    base_monthly_pages = random.uniform(*model_info["avg_monthly_pages"])
    base_daily_pages = base_monthly_pages / AVG_DAYS_PER_MONTH
    daily_error_rate = (model_info["error_rate_monthly"] * random.uniform(0.7, 1.3)) / AVG_DAYS_PER_MONTH

    printers_data.append({
        "printer_id": printer_id,
        "model": model_name,
        "customer_segment": segment,
        "region": region,
        "firmware_version": firmware,
        "base_daily_pages": base_daily_pages, # Store base daily rate
        "color_ratio": model_info["color_ratio"] * random.uniform(0.8, 1.2),
        "daily_error_rate": daily_error_rate, # Store daily error rate
        "ink_types": model_info["inks"] # Store ink types for this model
    })

printers_df = pd.DataFrame(printers_data)
# Create a mapping from printer_id to ink_types for easier lookup later
# Handle cases where a printer_id might somehow not be in the map (though unlikely here)
printer_ink_map = printers_df.set_index('printer_id')['ink_types'].to_dict()
print("Printer inventory generated.")

# --- Generate Daily Usage Data (Long Format) ---
usage_data = []
error_data_flat = [] # Store flattened error info directly

# Track cumulative pages and ink levels per printer
printer_state = {}
for pid in printers_df['printer_id']:
    # Safely get ink types from map, provide default if missing
    ink_types_for_printer = printer_ink_map.get(pid, ['Unknown'])
    printer_state[pid] = {
        'cumulative_pages': 0,
        'pages_at_last_event': 0,
        # Initialize ink levels (simplified)
        'ink_levels': {ink: random.randint(80, 100) for ink in ink_types_for_printer}
    }

# Estimate pages per cartridge (highly simplified)
# These are rough estimates for simulation purposes
PAGES_PER_MONO_CARTRIDGE = 300
PAGES_PER_COLOR_CARTRIDGE = 200 # Per color/tri-color
PAGES_PER_PHOTO_BLACK = 250 # Estimate for photo black

print(f"Generating daily usage data for {NUM_DAYS} days...")
current_date = START_DATE
for day_num in range(NUM_DAYS):
    date_stamp = current_date.strftime('%Y-%m-%d')
    if day_num % 30 == 0: # Print progress update monthly
        print(f"  Processing data for {date_stamp}...")

    for index, printer in printers_df.iterrows():
        printer_id = printer['printer_id']
        # Ensure state exists for the printer_id
        if printer_id not in printer_state:
            print(f"Warning: Skipping printer {printer_id} - not found in state dictionary.")
            continue
        state = printer_state[printer_id]

        # Simulate usage trend (seasonality, slight growth)
        seasonality = 1.0
        if printer['customer_segment'] == 'Home':
            month = current_date.month
            if month in [11, 12, 1]: seasonality = random.uniform(1.1, 1.4)
            elif month in [6, 7, 8]: seasonality = random.uniform(0.8, 0.95)

        time_trend_factor = 1 + (day_num / NUM_DAYS) * 0.1
        daily_pages = max(0, int(printer['base_daily_pages'] * seasonality * time_trend_factor * random.uniform(0.6, 1.4)))

        # Simulate connectivity probes (Array Example)
        num_probes = random.randint(0, 5)
        daily_connectivity_probes = []
        if num_probes > 0:
            for _ in range(num_probes):
                probe_time = current_date + timedelta(hours=random.uniform(0, 23.99))
                daily_connectivity_probes.append(probe_time.isoformat() + "Z")
            daily_connectivity_probes.sort() # Sort timestamps


        # Only record usage row if pages > 0 OR probes happened
        if daily_pages > 0 or num_probes > 0:
            color_pages = int(daily_pages * printer['color_ratio'])
            mono_pages = daily_pages - color_pages

            # Simulate ink consumption and update levels
            ink_consumed_mono = mono_pages / PAGES_PER_MONO_CARTRIDGE
            # Color consumption depends on color pages
            ink_consumed_color = color_pages / PAGES_PER_COLOR_CARTRIDGE
            # Photo black consumption (simplified: assume proportional to color pages for photo models)
            ink_consumed_photo_black = 0
            if 'Photo Black' in state['ink_levels']:
                 ink_consumed_photo_black = color_pages / PAGES_PER_PHOTO_BLACK


            current_ink_levels = state['ink_levels']
            # Decrement ink levels based on usage (simplified)
            for ink, level in current_ink_levels.items():
                decrement = 0
                if 'Black' in ink and 'Photo' not in ink: # Standard Black
                    decrement = (ink_consumed_mono * 100)
                elif 'Photo Black' in ink:
                    decrement = (ink_consumed_photo_black * 100)
                elif 'Tri-color' in ink:
                    # Assume tri-color depletes based on total color pages
                    decrement = (ink_consumed_color * 100)
                else: # Individual colors (Cyan, Magenta, Yellow)
                    # Distribute color usage among individual color cartridges
                    num_color_inks = sum(1 for i in current_ink_levels if i in ['Cyan', 'Magenta', 'Yellow'])
                    if num_color_inks > 0:
                         decrement = (ink_consumed_color * 100) / num_color_inks
                    # If no individual colors, decrement remains 0 (should be handled by Tri-color case)

                current_ink_levels[ink] = max(0, level - decrement * random.uniform(0.8, 1.2)) # Add noise


            # Update cumulative pages for low ink event simulation
            state['cumulative_pages'] += daily_pages
            low_ink_event_today = False

            # Check if ANY ink level is below threshold (e.g., 20%)
            if any(level < 20 for level in current_ink_levels.values()):
                 pages_since_last_event = state['cumulative_pages'] - state['pages_at_last_event']
                 if pages_since_last_event > 50 and random.random() < 0.2: # Higher chance once low
                     low_ink_event_today = True
                     state['pages_at_last_event'] = state['cumulative_pages'] # Reset page counter


            # Create Ink Levels Snapshot (Nested Example - JSON String)
            ink_levels_list = [{"cartridge": ink, "level_percent": round(level, 1)} for ink, level in current_ink_levels.items()]
            ink_levels_snapshot_json = json.dumps(ink_levels_list)


            usage_data.append({
                "printer_id": printer_id,
                "usage_date": date_stamp,
                "total_pages": daily_pages,
                "color_pages": color_pages,
                "mono_pages": mono_pages,
                "ink_consumed_mono_units": round(ink_consumed_mono, 4),
                "ink_consumed_color_units": round(ink_consumed_color, 4), # Note: This is a simplified general color metric
                "low_ink_event_occurred": low_ink_event_today,
                "daily_connectivity_probes": daily_connectivity_probes, # Array (List)
                "ink_levels_snapshot": ink_levels_snapshot_json # Nested (JSON String)
            })

            # Simulate errors
            error_chance = printer['daily_error_rate'] * (1 + daily_pages / (printer['base_daily_pages'] * 5 + 1))
            if random.random() < error_chance:
                 error_time = current_date + timedelta(hours=random.uniform(0, 23.99))
                 error_data_flat.append({
                     "printer_id": printer_id,
                     "error_timestamp": error_time.isoformat() + "Z",
                     "error_code": random.choice(ERROR_CODES),
                     "error_severity": random.choice(["Low", "Medium", "High"])
                 })

    current_date += timedelta(days=1) # Move to next day

print("Daily usage data generation complete.")

usage_df = pd.DataFrame(usage_data)
errors_flat_df = pd.DataFrame(error_data_flat)

# --- Generate Market Share/Revenue Data (Recalculate based on expanded models) ---
print("Generating revenue share data (Expanded Ink Models)...")
revenue_data = []
# Use printers_df which only contains ink models now
model_groups = printers_df.groupby('model')['printer_id'].count()
total_printers = len(printers_df) # Total is now only ink printers

for model, count in model_groups.items():
    market_share_units = count / total_printers if total_printers > 0 else 0
    # Simulate revenue share based on market share and perceived model value
    revenue_share = market_share_units * random.uniform(0.8, 1.5)
    revenue_data.append({
        "model_line": model, # This now includes the added ink models
        "market_share_percent": round(market_share_units * 100, 2),
        "estimated_revenue_share": revenue_share
    })

revenue_df = pd.DataFrame(revenue_data)

# Normalize revenue share to sum to 100%
total_share = revenue_df['estimated_revenue_share'].sum()
if total_share > 0:
    revenue_df['revenue_contribution_percent'] = round((revenue_df['estimated_revenue_share'] / total_share) * 100, 2)
else:
    revenue_df['revenue_contribution_percent'] = 0
revenue_df = revenue_df.drop(columns=['estimated_revenue_share'])
print("Revenue share data generated.")

# --- Define output directory ---
output_dir = "sample_data" # New directory name
os.makedirs(output_dir, exist_ok=True)

# --- Save DataFrames to CSV ---
printers_csv_path = os.path.join(output_dir, "printers.csv")
usage_csv_path = os.path.join(output_dir, "daily_usage.csv") # Main file with new cols
errors_csv_path = os.path.join(output_dir, "printer_errors.csv")
revenue_csv_path = os.path.join(output_dir, "revenue_share.csv") # Updated revenue share

print("Saving CSV files...")
try:
    # Save printers_df (now expanded ink models)
    printers_df_to_save = printers_df.drop(columns=['ink_types']) # Option 1: Drop list col
    printers_df_to_save.to_csv(printers_csv_path, index=False, encoding='utf-8')
    print(f"Successfully saved printers data to {printers_csv_path}")

    usage_df.to_csv(usage_csv_path, index=False, encoding='utf-8', date_format='%Y-%m-%d')
    print(f"Successfully saved daily usage data (with nested/array cols) to {usage_csv_path}")

    if not errors_flat_df.empty:
        errors_flat_df.to_csv(errors_csv_path, index=False, encoding='utf-8')
        print(f"Successfully saved flattened error data to {errors_csv_path}")
    else:
        print("No error data to save.")

    # Save the updated revenue_df (now expanded ink models)
    revenue_df.to_csv(revenue_csv_path, index=False, encoding='utf-8')
    print(f"Successfully saved revenue share data to {revenue_csv_path}")

    print(f"\n--- Data Summary ---")
    print(f"Printers: {len(printers_df)}")
    print(f"Daily Usage Records: {len(usage_df)}")
    print(f"Error Records: {len(errors_flat_df)}")
    print(f"Revenue Records: {len(revenue_df)}")
    print(f"\nFiles saved in directory: '{output_dir}'")
    print(f"\nNOTE: Data now contains expanded Inkjet models including Envy Photo and Tango.")


except Exception as e:
    print(f"An error occurred while saving CSV files: {e}")

