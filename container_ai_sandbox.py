import streamlit as st
import requests
import os
import time
from google import genai

# ==========================================
# 1. PAGE CONFIGURATION & CONSTANTS
# ==========================================
st.set_page_config(
    page_title="Container Load Planner",
    page_icon="📦",
    layout="wide"
)

# Custom compact styling to eliminate dead space
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        div[data-baseweb="input"] > div {
            min-height: 32px;
        }
        .stTextInput input {
            padding: 4px 8px;
        }
        hr {
            margin: 1rem 0px;
        }
    </style>
""", unsafe_allow_html=True)

DEFAULT_API_KEY = "AQ.Ab8RN6Iw9bXWfgtaetzZ8g_yC1QRFLXqV-Nl6mmRefYDxn-8HA"

CONTAINER_SPECS = {
    "40' High Cube (40'HC)": {"length": 473.0, "height": 101.0, "width": 92.0},
    "45' High Cube (45'HC)": {"length": 533.0, "height": 101.0, "width": 92.0}
}

MAX_TOP_TIER_HEIGHT = 66.0    
MAX_4CAR_HEIGHT_SUM = 255.0   

# ==========================================
# 2. MASTER VEHICLE DATABASE
# ==========================================
EXACT_SPECS_DB = {
    ("tesla", "model y"): (187.0, 64.0, 75.6),
    ("tesla", "model 3"): (184.8, 56.8, 72.8),
    ("tesla", "model x"): (198.3, 66.1, 78.7),
    ("tesla", "model s"): (196.0, 56.9, 77.3),
    ("kia", "forte"): (182.7, 56.5, 70.9),
    ("kia", "k5"): (193.1, 56.9, 73.2),
    ("kia", "k4"): (185.4, 55.9, 72.8),
    ("kia", "seltos"): (172.0, 63.6, 70.9),
    ("kia", "sportage"): (183.5, 65.4, 73.4),
    ("kia", "soul"): (165.2, 63.0, 70.9),
    ("kia", "niro"): (174.0, 60.8, 71.9),
    ("kia", "sorento"): (181.7, 66.7, 74.8),
    ("kia", "ev6"): (184.3, 60.8, 74.4),
    ("kia", "stinger"): (190.2, 55.1, 73.6),
    ("kia", "sedona"): (201.4, 68.5, 78.1),
    ("kia", "optima"): (191.1, 57.7, 73.2),
    ("kia", "rio"): (172.6, 57.1, 67.9),
    ("hyundai", "elantra"): (184.1, 55.7, 71.9),
    ("hyundai", "kona"): (171.3, 61.6, 70.9),
    ("hyundai", "santa cruz"): (195.7, 66.7, 75.0),
    ("hyundai", "santa fe"): (188.4, 67.7, 74.8),
    ("hyundai", "sonata"): (193.3, 56.9, 73.2),
    ("hyundai", "tucson"): (182.3, 65.6, 73.4),
    ("hyundai", "venue"): (158.9, 61.6, 69.7),
    ("hyundai", "palisade"): (196.7, 68.9, 77.8),
    ("hyundai", "ioniq"): (176.0, 57.1, 71.7),
    ("chevrolet", "volt"): (180.4, 56.4, 71.2),
    ("chevrolet", "blazer"): (191.8, 67.0, 76.7),
    ("chevrolet", "malibu"): (194.2, 57.9, 73.0),
    ("chevrolet", "equinox"): (183.1, 65.4, 72.6),
    ("chevrolet", "trax"): (178.6, 61.4, 70.7),
    ("chevrolet", "trailblazer"): (173.5, 65.2, 70.8),
    ("chevrolet", "colorado"): (213.0, 78.8, 74.3),
    ("chevrolet", "bolt"): (163.2, 62.8, 69.5),
    ("toyota", "camry"): (192.1, 56.9, 72.4),
    ("toyota", "corolla"): (182.3, 56.5, 70.1),
    ("toyota", "rav4"): (181.1, 67.0, 73.0),
    ("toyota", "bz4x"): (184.6, 65.0, 73.2),
    ("toyota", "c-hr"): (171.7, 61.6, 70.7),
    ("toyota", "4runner"): (190.2, 71.5, 75.8),
    ("toyota", "highlander"): (194.9, 68.1, 76.0),
    ("toyota", "venza"): (186.6, 65.9, 72.8),
    ("toyota", "tacoma"): (212.3, 70.6, 74.4),
    ("nissan", "rogue"): (183.0, 66.5, 72.4),
    ("nissan", "sentra"): (182.7, 57.0, 71.5),
    ("nissan", "versa"): (177.0, 57.7, 68.5),
    ("nissan", "kicks"): (169.1, 63.3, 69.3),
    ("nissan", "altima"): (192.9, 56.7, 72.9),
    ("nissan", "nv200"): (186.2, 73.7, 68.1),
    ("nissan", "titan"): (228.1, 75.4, 79.5),
    ("nissan", "armada"): (208.9, 75.8, 79.9),
    ("nissan", "murano"): (192.4, 67.8, 75.4),
    ("jeep", "cherokee"): (183.1, 66.2, 73.2),
    ("jeep", "grand cherokee"): (193.5, 70.8, 77.5),
    ("jeep", "compass"): (173.4, 64.6, 73.8),
    ("jeep", "wrangler"): (188.4, 73.6, 73.8),
    ("jeep", "renegade"): (166.6, 66.5, 73.2),
    ("jeep", "gladiator"): (218.0, 75.0, 73.8),
    ("ford", "transit connect"): (190.0, 72.0, 72.2),
    ("ford", "transit"): (219.9, 82.2, 81.3),
    ("ford", "fusion"): (191.8, 58.2, 72.9),
    ("ford", "escape"): (180.1, 66.1, 74.1),
    ("ford", "explorer"): (198.8, 70.2, 78.9),
    ("ford", "mustang"): (188.3, 54.4, 75.4),
    ("ford", "mustang mach-e"): (186.0, 64.0, 74.1),
    ("ford", "f-150"): (231.7, 77.2, 79.9),
    ("ford", "ecosport"): (161.3, 64.8, 69.5),
    ("ford", "ranger"): (210.8, 71.1, 73.3),
    ("ford", "maverick"): (199.7, 68.7, 72.6),
    ("ford", "edge"): (188.8, 68.3, 75.9),
    ("dodge", "journey"): (192.4, 66.6, 72.2),
    ("dodge", "challenger"): (197.9, 57.5, 75.7),
    ("dodge", "hornet"): (178.0, 63.8, 72.5),
    ("dodge", "sprinter"): (232.5, 96.0, 79.7),
    ("ram", "promaster"): (213.1, 93.0, 81.0),
    ("ram", "promaster city"): (187.5, 74.0, 72.1),
    ("ram", "1500"): (232.9, 77.6, 82.1),
    ("honda", "prologue"): (192.0, 64.7, 78.3),
    ("honda", "civic"): (184.8, 55.7, 70.9),
    ("honda", "accord"): (195.7, 57.1, 73.3),
    ("honda", "cr-v"): (184.8, 66.2, 73.2),
    ("honda", "hr-v"): (179.8, 63.4, 74.0),
    ("honda", "pilot"): (199.9, 71.0, 78.5),
    ("bmw", "3 series"): (185.7, 56.8, 71.9),
    ("bmw", "5 series"): (199.2, 59.6, 74.8),
    ("bmw", "4 series"): (187.9, 54.6, 72.9),
    ("bmw", "2 series"): (178.5, 55.1, 72.4),
    ("bmw", "x1"): (177.2, 64.6, 72.6),
    ("bmw", "x2"): (179.4, 62.6, 72.6),
    ("bmw", "x3"): (185.4, 66.0, 74.4),
    ("bmw", "x5"): (194.2, 68.7, 78.9),
    ("bmw", "x7"): (203.3, 71.1, 78.7),
    ("bmw", "i4"): (188.3, 57.0, 72.9),
    ("bmw", "i5"): (199.2, 59.6, 74.8),
    ("bmw", "i7"): (216.2, 60.8, 76.8),
    ("bmw", "ix"): (195.0, 66.7, 77.4),
    ("mercedes-benz", "cla"): (184.6, 56.7, 72.0),
    ("mercedes-benz", "c-class"): (187.0, 56.6, 71.7),
    ("mercedes-benz", "e-class"): (194.9, 58.3, 74.0),
    ("mercedes-benz", "s-class"): (208.2, 59.2, 75.5),
    ("mercedes-benz", "a-class"): (179.1, 56.9, 70.7),
    ("mercedes-benz", "cls"): (196.4, 56.3, 74.4),
    ("mercedes-benz", "glc"): (185.7, 64.6, 74.4),
    ("mercedes-benz", "gle"): (194.3, 70.7, 76.7),
    ("mercedes-benz", "gls"): (205.0, 71.8, 77.0),
    ("mercedes-benz", "g-class"): (190.0, 77.4, 76.0),
    ("mercedes-benz", "eqb"): (184.4, 65.6, 72.2),
    ("mercedes-benz", "eqe"): (195.0, 59.5, 75.0),
    ("mercedes-benz", "metris"): (202.4, 75.2, 75.9),
    ("mercedes-benz", "sprinter"): (233.5, 96.3, 79.7),
    ("volkswagen", "id.4"): (180.5, 64.5, 72.9),
    ("volkswagen", "passat"): (193.6, 58.2, 72.2),
    ("volkswagen", "jetta"): (186.5, 57.7, 70.8),
    ("volkswagen", "tiguan"): (186.1, 66.4, 72.4),
    ("volkswagen", "taos"): (175.8, 64.4, 72.5),
    ("audi", "q3"): (176.6, 62.9, 72.8),
    ("audi", "q4"): (180.6, 64.2, 73.4),
    ("audi", "q6"): (187.8, 64.9, 76.3),
    ("audi", "q7"): (199.3, 68.5, 77.6),
    ("lexus", "rz"): (189.2, 64.4, 74.6),
    ("lexus", "rx"): (192.5, 66.7, 75.6),
    ("lexus", "nx"): (183.5, 65.6, 73.4),
    ("lexus", "ux"): (176.9, 60.6, 72.4),
    ("lexus", "gx"): (197.0, 75.4, 78.0),
    ("lexus", "es"): (195.9, 56.9, 73.4),
    ("lexus", "is"): (185.4, 56.5, 72.4),
    ("mazda", "3"): (175.6, 56.7, 70.7),
    ("mazda", "6"): (191.5, 57.1, 72.4),
    ("mazda", "cx-30"): (173.0, 60.6, 70.7),
    ("mazda", "cx-9"): (199.4, 67.6, 77.2),
    ("mazda", "cx-90"): (201.6, 68.2, 78.5),
    ("subaru", "impreza"): (176.2, 58.3, 70.1),
    ("subaru", "legacy"): (191.1, 59.1, 72.4),
    ("subaru", "crosstrek"): (176.4, 63.0, 70.9),
    ("subaru", "outback"): (191.1, 66.1, 73.8),
    ("subaru", "wrx"): (183.8, 57.8, 71.9),
    ("porsche", "cayenne"): (193.6, 66.8, 78.1),
    ("porsche", "panamera"): (198.8, 56.0, 76.3),
    ("porsche", "taycan"): (195.4, 54.3, 77.4),
    ("porsche", "911"): (178.4, 51.1, 72.9),
    ("land rover", "range rover"): (199.0, 73.6, 80.6),
    ("land rover", "range rover sport"): (194.7, 71.7, 80.6),
    ("land rover", "range rover velar"): (188.9, 65.6, 76.0),
    ("vinfast", "vf8"): (187.0, 65.6, 76.1),
    ("cadillac", "lyriq"): (196.7, 63.9, 77.8),
    ("cadillac", "elr"): (186.0, 55.9, 73.0),
    ("lincoln", "nautilus"): (193.2, 66.2, 76.1),
    ("lincoln", "mkz"): (194.1, 58.1, 73.4),
    ("lincoln", "aviator"): (199.3, 69.6, 79.8),
    ("buick", "encore"): (171.4, 64.0, 70.1),
    ("acura", "zdx"): (197.6, 64.4, 77.0),
    ("alfa romeo", "tonale"): (178.4, 63.0, 72.4),
    ("infiniti", "qx50"): (184.7, 66.0, 74.9),
    ("infiniti", "qx60"): (198.2, 69.7, 78.0),
    ("genesis", "gv60"): (177.8, 62.4, 74.4),
    ("maserati", "levante"): (197.0, 66.1, 77.5),
    ("mini", "countryman"): (174.4, 64.3, 72.0),
    ("mini", "cooper"): (152.5, 55.7, 68.0),
    ("mini", "hardtop"): (152.2, 55.7, 68.0),
    ("gmc", "acadia"): (193.4, 66.7, 75.4),
    ("gmc", "sierra"): (231.7, 78.3, 81.2),
    ("gmc", "terrain"): (182.3, 65.4, 72.4),
    ("mitsubishi", "outlander"): (185.4, 68.7, 73.3),
    ("can-am", "ryker"): (92.6, 41.8, 59.4),
    ("harley-davidson", "motorcycle"): (95.0, 55.0, 38.0),
    ("ski-doo", "snowmobile"): (122.0, 47.0, 48.0),
    ("bobcat", "skid steer"): (130.0, 77.8, 67.0),
}

# ==========================================
# 3. VIN DECODER HELPER
# ==========================================
def decode_vin_and_get_specs(vin):
    if len(vin) != 17:
        return None
    url = "https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/" + str(vin) + "?format=json"
    try:
        res = requests.get(url, timeout=5).json()
        results = {item['Variable']: item['Value'] for item in res.get('Results', [])}
        
        make = results.get("Make", "").strip()
        model = results.get("Model", "").strip()
        year = results.get("Model Year", "").strip()
        body = results.get("Body Class", "").strip()
        
        if not make:
            return None

        make_key = make.lower()
        model_key = model.lower()
        
        found_specs = None
        for (db_make, db_model), specs in EXACT_SPECS_DB.items():
            if db_make in make_key and db_model in model_key:
                found_specs = specs
                break

        if found_specs:
            return {
                "name": (year + " " + make + " " + model).strip(),
                "body": body,
                "length": found_specs[0],
                "height": found_specs[1],
                "width": found_specs[2],
                "source": "Exact Database Spec"
            }
        else:
            return {
                "name": (year + " " + make + " " + model).strip(),
                "body": body,
                "length": 0.0,
                "height": 0.0,
                "width": 0.0,
                "source": "Manual Entry Needed"
            }
    except Exception:
        return None

# ==========================================
# LINE 1: COMPACT BULK VIN & RESULTS (TOP)
# ==========================================
st.markdown("### ⚡ Bulk VIN Paste & Results")

r1_col_input, r1_col_results = st.columns([1, 1.2])

with r1_col_input:
    selected_container = st.selectbox(
        "Container Type:",
        options=list(CONTAINER_SPECS.keys()),
        index=0,
        label_visibility="collapsed"
    )
    active_container_specs = CONTAINER_SPECS[selected_container]
    CONTAINER_MAX_LEN = active_container_specs["length"]

    bulk_vins_input = st.text_area(
        "Bulk VINs:",
        placeholder="Paste up to 4 VINs here (one per line)...",
        height=75,
        key="bulk_vin_area",
        label_visibility="collapsed"
    )
    
    col_b1, col_b2, col_b3 = st.columns([2, 2, 1.5])
    
    def process_vins():
        if bulk_vins_input:
            cleaned_vins = [v.strip().upper() for v in bulk_vins_input.replace(",", "\n").split("\n") if v.strip()]
            for idx, v_item in enumerate(cleaned_vins[:4]):
                st.session_state["vin_" + str(idx+1)] = v_item
                info = decode_vin_and_get_specs(v_item)
                if info and info["length"] > 0:
                    st.session_state["label_" + str(idx+1)] = info["name"]
                    st.session_state["len_" + str(idx+1)] = float(info["length"])
                    st.session_state["hgt_" + str(idx+1)] = float(info["height"])
                    st.session_state["wid_" + str(idx+1)] = float(info["width"])
                    
                    if info["height"] <= MAX_TOP_TIER_HEIGHT and idx < 2:
                        st.session_state["pos_" + str(idx+1)] = "Elevated / Ramped (Top Tier)"
                    else:
                        st.session_state["pos_" + str(idx+1)] = "Ground Floor"

    if col_b1.button("🚀 Load VINs", type="primary", use_container_width=True):
        process_vins()
        st.rerun()

    if col_b2.button("🧹 Clear", use_container_width=True):
        for i in range(1, 5):
            st.session_state["vin_" + str(i)] = ""
            st.session_state["label_" + str(i)] = ""
            st.session_state["len_" + str(i)] = 0.0
            st.session_state["hgt_" + str(i)] = 0.0
            st.session_state["wid_" + str(i)] = 0.0
        st.rerun()
        
    col_b3.metric("Limit", f"{CONTAINER_MAX_LEN}\"", label_visibility="collapsed")

# Gather vehicles to calculate results immediately at the top
vehicles = []
for i in range(1, 5):
    v_len = st.session_state.get(f"len_{i}", 0.0)
    v_hgt = st.session_state.get(f"hgt_{i}", 0.0)
    v_wid = st.session_state.get(f"wid_{i}", 0.0)
    v_pos = st.session_state.get(f"pos_{i}", "Ground Floor")
    v_lab = st.session_state.get(f"label_{i}", f"Car {i}")
    
    if v_len > 0:
        vehicles.append({
            "label": v_lab if v_lab else f"Car {i}",
            "length": v_len,
            "height": v_hgt,
            "width": v_wid,
            "is_top_tier": "Top Tier" in v_pos
        })

with r1_col_results:
    if vehicles:
        invalid_ramped_suvs = [v for v in vehicles if v["is_top_tier"] and v["height"] > MAX_TOP_TIER_HEIGHT]
        total_height_sum = sum(v["height"] for v in vehicles)
        ground_vehicles = [v for v in vehicles if not v["is_top_tier"]]
        top_vehicles = [v for v in vehicles if v["is_top_tier"]]
        total_effective_length = sum(v["length"] for v in ground_vehicles) + (len(top_vehicles) * 35.0)
        remaining_space = CONTAINER_MAX_LEN - total_effective_length

        if invalid_ramped_suvs:
            st.error(f"❌ **FAIL: Ramped height > {MAX_TOP_TIER_HEIGHT}\"**")
        elif len(vehicles) == 4 and total_height_sum > MAX_4CAR_HEIGHT_SUM:
            st.error(f"❌ **FAIL: Roof height sum > {MAX_4CAR_HEIGHT_SUM}\"**")
        elif total_effective_length > CONTAINER_MAX_LEN:
            st.error(f"❌ **FAIL: Length exceeded ({round(total_effective_length, 1)}\" / {CONTAINER_MAX_LEN}\")**")
        else:
            st.success(f"✅ **PASS! Buffer space remaining: {round(remaining_space, 1)}\"**")
    else:
        st.info("ℹ️ Paste VINs above to see load calculation results here.")

st.markdown("---")

# ==========================================
# LINE 2: COMPACT VEHICLE SPECIFICATIONS
# ==========================================
st.markdown("### 🚘 Vehicle Specifications & Positions")

v_cols = st.columns(4)

for i in range(1, 5):
    with v_cols[i-1]:
        st.markdown(f"**Vehicle #{i}**")
        
        vin = st.text_input(f"VIN #{i}", key=f"vin_{i}", label_visibility="collapsed", placeholder=f"VIN #{i}").strip().upper()
        
        prev_vin_key = f"prev_vin_{i}"
        if prev_vin_key not in st.session_state:
            st.session_state[prev_vin_key] = ""
            
        if vin != st.session_state[prev_vin_key]:
            st.session_state[prev_vin_key] = vin
            if vin and len(vin) == 17:
                info = decode_vin_and_get_specs(vin)
                if info:
                    st.session_state[f"label_{i}"] = info["name"]
                    st.session_state[f"len_{i}"] = float(info["length"])
                    st.session_state[f"hgt_{i}"] = float(info["height"])
                    st.session_state[f"wid_{i}"] = float(info["width"])

        position = st.selectbox(
            f"Pos #{i}",
            options=["Elevated / Ramped (Top Tier)", "Ground Floor"],
            index=0 if i <= 2 else 1,
            key=f"pos_{i}",
            label_visibility="collapsed"
        )

        label = st.text_input(f"Label #{i}", key=f"label_{i}", label_visibility="collapsed", placeholder="Label / Name")
        
        d_col1, d_col2, d_col3 = st.columns(3)
        with d_col1:
            length = st.number_input(f"L{i}", min_value=0.0, max_value=260.0, step=0.1, key=f"len_{i}", label_visibility="collapsed")
        with d_col2:
            height = st.number_input(f"H{i}", min_value=0.0, max_value=120.0, step=0.1, key=f"hgt_{i}", label_visibility="collapsed")
        with d_col3:
            width = st.number_input(f"W{i}", min_value=0.0, max_value=100.0, step=0.1, key=f"wid_{i}", label_visibility="collapsed")

st.markdown("---")

# ==========================================
# LINE 3: DETAILED TABLE & AI CONSOLE (BOTTOM)
# ==========================================
if vehicles:
    st.markdown("### 📊 Detailed Breakdown")
    table_data = []
    for v in vehicles:
        table_data.append({
            "Vehicle": v["label"],
            "Dimensions (L x H x W)": f"{round(v['length'], 1)}\" x {round(v['height'], 1)}\" x {round(v['width'], 1)}\"",
            "Position": "Top Tier" if v["is_top_tier"] else "Ground Floor",
            "Footprint": "+35.0\" (Ramped)" if v["is_top_tier"] else f"{round(v['length'], 1)}\""
        })
    st.table(table_data)

# AI Developer Console at the very bottom
with st.expander("⚙️ AI Developer & Code Editor Console", expanded=False):
    st.caption("Execute instructions to append logic (`#`) or modify existing code (`!`).")
    gemini_api_key = st.text_input("Gemini API Key", value=DEFAULT_API_KEY, type="password")
    
    prompt_command = st.text_area(
        "Instruction:",
        placeholder="e.g. # Add an export button..."
    )
    
    if st.button("Execute Code Modification"):
        if not prompt_command.strip():
            st.warning("Please type an instruction command.")
        else:
            prefix = prompt_command.strip()[0]
            actual_instruction = prompt_command.strip()[1:].strip()
            
            if prefix not in ['#', '!']:
                st.error("❌ Invalid format! Prompt must start with **#** or **!**.")
            else:
                api_key_to_use = gemini_api_key.strip() if gemini_api_key.strip() else os.environ.get("GEMINI_API_KEY", DEFAULT_API_KEY)
                
                with st.spinner("🤖 Modifying application code..."):
                    try:
                        client = genai.Client(api_key=api_key_to_use)
                        
                        script_path = __file__
                        with open(script_path, "r", encoding="utf-8") as f:
                            current_code = f.read()
                            
                        cmd_type = "APPEND NEW CODE SECTION" if prefix == "#" else "MODIFY/REWRITE EXISTING CODE LOGIC"
                        
                        bt = chr(96) * 3
                        coding_prompt = (
                            "You are an expert Python software engineer modifying a Streamlit script file.\n\n"
                            "Current Source Code:\n" + bt + "python\n" + current_code + "\n" + bt + "\n\n"
                            "User Command Type: " + cmd_type + "\n"
                            "User Instruction: " + actual_instruction + "\n\n"
                            "CRITICAL FORMATTING INSTRUCTIONS:\n"
                            "1. Return ONLY valid Python code inside standard triple backticks.\n"
                            "2. NEVER output raw multiline f-strings containing curly braces.\n"
                            "3. PRESERVE the EXACT_SPECS_DB dictionary and all vehicle specs intact."
                        )
                        
                        models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro']
                        response = None
                        success = False
                        
                        for model_name in models_to_try:
                            if success:
                                break
                            max_retries = 4
                            delay = 2
                            for attempt in range(max_retries):
                                try:
                                    response = client.models.generate_content(
                                        model=model_name,
                                        contents=coding_prompt,
                                    )
                                    if response and response.text:
                                        success = True
                                        break
                                except Exception as err:
                                    err_str = str(err).lower()
                                    if any(code in err_str for code in ["503", "429", "unavailable", "quota", "overload"]):
                                        time.sleep(delay)
                                        delay *= 2
                                    else:
                                        break
                        
                        if success and response and response.text:
                            raw_text = response.text
                            BT = chr(96) * 3
                            if (BT + "python") in raw_text:
                                updated_code = raw_text.split(BT + "python")[1].split(BT)[0].strip()
                            elif BT in raw_text:
                                updated_code = raw_text.split(BT)[1].split(BT)[0].strip()
                            else:
                                updated_code = raw_text.strip()
                                
                            with open(script_path, "w", encoding="utf-8") as f:
                                f.write(updated_code)
                                
                            st.success("✨ **Code updated!** Reloading application...")
                            st.rerun()
                        else:
                            st.error("❌ Server busy. Please try again.")
                        
                    except Exception as e:
                        st.error("Failed to update source code: " + str(e))
