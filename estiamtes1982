import streamlit as st
import pandas as pd
from dateutil import parser
from collections import defaultdict

# Initialize session state variables before any widget is created
if "widget_key" not in st.session_state:
    st.session_state.widget_key = 0
if "explanation_text" not in st.session_state:
    st.session_state.explanation_text = ""
if "ai_text" not in st.session_state:
    st.session_state.ai_text = ""
if "table_df" not in st.session_state:
    st.session_state.table_df = None

# Set page configuration (must be the first Streamlit command)
st.set_page_config(layout="wide", page_title="Estimates Table Planning Processor")

# Inject custom CSS for sidebar and main content
st.markdown(
    """
    <style>
    /* Sidebar font size */
    [data-testid="stSidebar"] * {
        font-size: 10px !important;
    }
    /* Input text areas */
    .stTextArea > div > textarea {
        font-size: 6px !important;
        line-height: 1.1 !important;
    }
    /* DataFrame table font size */
    .stDataFrame table, .stDataFrame th, .stDataFrame td {
        font-size: 8px !important;
    }
    /* Row details table with larger text */
    .row-details-table table, .row-details-table th, .row-details-table td {
         font-size: 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Sidebar Instructions and Reference Information
# ----------------------------
st.sidebar.header("Instructions")
st.sidebar.write(
    """
    **Overview:**

    This tool (Estimates Table Planning Processor) processes ferry waiver reservation data.
    Paste your tab-separated table data into the **Input Table Data** field below.
    
    **How It Works:**
    - The tool auto-detects and skips the header row.
    - It reads the PROGRAM and PRODUCT values from the input if provided; otherwise, they default to **NetJets U.S.** and an empty product.
    - It calculates ferry waiver flags based on airport regions and aircraft groups.
    - It applies discount rules only for reservations on the NetJets U.S. program and only if the requested aircraft type matches the contracted aircraft type.
      *If the types differ, no discount is applied – please check the interchange rate in IJet.*
    - The row details table shows wrapped text in the REASON column for full visibility.
    - An aggregated reservation explanation and an AI conclusion are generated.
    
    **How to Use:**
    1. Paste your table data into **Input Table Data**.
    2. (Optional) Paste discount rule examples into **Discount Definitions**.
    3. Click **Process Table**.
    4. Use **Reset** to clear all inputs.

    **Note on Estimates:**
    - If the reservation is eligible for an upcharge, you can generate two estimates:
       1. One with the upcharge (to meet the 3‑hour daily minimum).
       2. One using standard ferry fees.
    - If it’s not eligible, only the ferry fees estimate applies.
    """
)

st.sidebar.subheader("Region Mapping - NetJets U.S.")
st.sidebar.markdown(
    """
    | **Group** | **ICAO Prefixes**                                                     |
    |-----------|-----------------------------------------------------------------------|
    | CSA       | K                                                                     |
    | Group I   | C, MM, MY, MB, MK, TN, TB, TJ, TI, TQ, TR, TT, TU, TV, MT, MU, MW, MZ, MG, MH, MP, MR, MS, PA |
    | Group II  | PH                                                                    |
    | Group III | BG, BI, EH, EI, EK, EB, ED, EE, EF, EG, EL, EN, EP, ES, EV, EY, LF, LG, LH, LI, LJ, LK, LL, LM, LO, LP, LQ, LR, LS, LT, LU, LW, LY, LZ, GM |
    | Group IV  | SA, SB, SC, SE, SG, SK, SL, SM, SO, SP, SU, SV, SY, ZB, ZG, ZH, ZL, ZS, ZY, VA, VE, VI, VO |
    """
)

st.sidebar.subheader("Region Mapping - NetJets Europe")
st.sidebar.markdown(
    """
    | **Zone / Group**             | **Applicable Aircraft Types**                                   | **Covered Areas / Countries**                                                                                                                                                                                                                                                                      |
    |------------------------------|-----------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | Collective Service Area (CSA)| All aircraft                                                    | Sector A: Austria, Belgium, Czech Republic, Croatia, Denmark, Finland, France, Germany, Greece (excluding Greek Islands), Hungary, Ireland, Italy, Luxembourg, Malta, Netherlands, Norway, Poland, Portugal (excluding Azores & Madeira), Slovakia, Slovenia, Spain (excluding Canary & Balearic Islands), Sweden, Switzerland, United Kingdom<br>Sector B: Albania, Bosnia & Herzegovina, Bulgaria, Cyprus, Estonia, Faroe Islands, Greek Islands only, Iceland, Kosovo, Latvia, Lithuania, Macedonia, Moldova, Montenegro, Morocco, Portugal (Azores & Madeira only), Russia (restricted cities), Romania, Serbia, Spain (Canary & Balearic Islands only), Israel (Tel Aviv only), Libya (Tripoli only), Tunisia (Tunis & Monastir only), Turkey, Ukraine |
    | Ferry Waiver Zone 1          | Citation Latitude, Challenger 350, Falcon 2000EX, Challenger 650, Global 5500, Global 6000 | Destinations outside the CSA covering parts of the Middle East and Eastern Europe – e.g., Armenia, Azerbaijan, Egypt (Cairo, Hurghada, Sharm El-Sheikh), Georgia, and areas in Russia west of 62°50’ (excluding Kaliningrad, Moscow & St. Petersburg)                                       |
    | Ferry Waiver Zone 2          | Challenger 350, Falcon 2000EX, Challenger 650, Global 5500, Global 6000 | Destinations in the Gulf region – e.g., Bahrain, Kazakhstan (e.g., Almaty, Astana), Kuwait, Oman, Qatar, Saudi Arabia, United Arab Emirates                                                                                                                       |
    | Ferry Waiver Long Haul Zone 1A | Challenger 650, Global 5500, Global 6000                         | Long-haul routes from the CSA to North America – e.g., flights to/from Canada (Montreal, Toronto) and U.S. Eastern states (e.g., New Jersey, Rhode Island, Connecticut, Massachusetts, New Hampshire, New York, Vermont, Maine)                                                       |
    | Ferry Waiver Long Haul Zone 1B | Global 5500, Global 6000                                          | Long-haul routes from the CSA to Continental U.S., Canada, Mexico, Bermuda, and the Caribbean Islands                                                                                                                                    |
    | Ferry Waiver Long Haul Zone 2 | Global 6000                                                       | Routes to/from U.S. Alaska and Hawaii, as well as South American destinations (e.g., Brazil, Argentina, Bolivia, Chile, Colombia, Ecuador, French Guiana, Guyana, Paraguay, Peru, Suriname, Uruguay)                                                              |
    """
)

st.sidebar.subheader("Product Details")
product_table_md = """
| **New Name**   | **Old Product Names**                  | **Program** | **Product(s)**                            | **No-Fly Days** | **Characteristics**                                                                                          |
|----------------|----------------------------------------|-------------|-------------------------------------------|-----------------|--------------------------------------------------------------------------------------------------------------|
| Share365       | Share                                  | Share       | None                                      | 0               | NJ Owner contract. Eligible for ferry waiver for FWG 1; standard PPD premium applies.                       |
| Share365e      | QS Executive Share                     | Share       | QS Executive (e)                          | 0               | NJ Owner contract with QS Executive discount terms.                                                        |
| Share365i      | Interim Lease                          | Share       | Interim (i)                               | 0               | NJ Interim Lease contract. Similar to NJ Owner, but with interim lease terms.                              |
| Share365ei     | QS Executive Interim Lease             | Share       | QS Executive (e) + Interim (i)              | 0               | NJ Interim Lease with QS Executive terms.                                                                    |
| Share365l      | Standard / Long-Term Lease             | Share       | Lease (l)                                 | 10              | NJ Lease / Pre-paid Lease. Hourly rate includes OHR and Fuel; additional fees may apply.                     |
| Share365el     | QS Executive Standard / Long-Term Lease  | Share       | QS Executive (e) + Lease (l)                | 10              | NJ Lease with QS Executive discount.                                                                         |
| Share355l      | 25-Hour Lease                          | Share       | Lease (l)                                 | 10              | Standard 25-hr Lease with PPD restrictions; pays a 1.25 PPD premium.                                         |
| Share355lx     | 25-Hour Cross-Country Lease            | Share       | Lease (l) + Cross-Country (x)               | 10              | 25-Hour Cross-Country Lease.                                                                                   |
| Share355e      | QS Executive 25-Hour Lease             | Share       | QS Executive (e) + Lease (l)                | 10              | QS Executive terms on a 25-Hour Lease.                                                                         |
| Share355el     | QS Executive 25-Hour Cross-Country Lease| Share       | QS Executive (e) + Lease (l) + Cross-Country (x)| 10            | QS Executive terms on a 25-Hour Cross-Country Lease.                                                           |
| Card365        | Promo Card                             | Card        | None                                      | 0               | Promo Card for special cases.                                                                                  |
| Card355i       | Interim Card                           | Card        | Interim (i)                               | 10              | Interim Card for owners awaiting lease activation.                                                           |
| Card355ci      | Interim Combo Card                     | Card        | Combo (c) + Interim (i)                     | 10              | Interim Combo Card offering multiple benefits.                                                                 |
| Card355ix      | Interim Cross-Country Card             | Card        | Interim (i) + Cross-Country (x)             | 10              | Interim Cross-Country Card.                                                                                    |
| Card320        | Standard Card                          | Card        | None                                      | 45              | Standard Card with basic access.                                                                             |
| Card320c       | Combo Card                             | Card        | Combo (c)                                 | 45              | Combo Card combining features.                                                                               |
| Card320e       | QS Executive Card                      | Card        | QS Executive (e)                          | 45              | QS Executive Card with enhanced benefits.                                                                    |
| Card320x       | Cross-Country Card                     | Card        | Cross-Country (x)                         | 45              | Cross-Country Card for long-haul flights.                                                                      |
| Card320ex      | Cross-Country QS Executive Card        | Card        | QS Executive (e) + Cross-Country (x)        | 45              | QS Executive benefits on a Cross-Country Card.                                                                 |
| Card275        | One Card                               | Card        | None                                      | 90              | One Card for single-use scenarios.                                                                             |
| Card275x       | Cross-Country One Card                 | Card        | Cross-Country (x)                         | 90              | Cross-Country One Card for extended trips.                                                                     |
"""
st.sidebar.markdown(product_table_md)

st.sidebar.subheader("Ferry Waiver Rules")
st.sidebar.markdown(
    """
    **Ferry Waiver Program Rules:**

    - **Positioning Fees:** When operating under Ferry Waiver, the Owner does not pay ferry hours, fuel, or flat fees on the positioning leg.
      *Note: The tool estimates positioning time at a country level by examining the furthest airport in each country from the CSA. For a more precise estimate, use the F5 function on the timeline in IJet and override the time if needed.*
    
    - **Global Service Area Zone (GL7500 Owners):**
      - All Bombardier Global 7500 Owners and Leases qualify for the Global Service Area.
      - Defined as the contiguous U.S., select cities in Canada, and all locations in Group III (excluding Group I/II countries).
      - Travel within this area is always ferry‑free.
      - For flights outside the area, the flight is ferry‑free if the single flight begins and/or ends in the Global Service Area; or, for multi‑segment trips, if the entire trip meets the criteria (same aircraft, continuous itinerary, averaging at least 3 occupied hours per day).
    
    - **NJA Ferry Waiver Zones (excluding GL7500 Owners):**
      - Refer to the Ferry Waiver Program Maps for detailed zone information.
      - *Note:* For non‑GL7500 Owners requesting the GL7500, executive leadership approval is required. The GL7500 falls under its own group (Group 5) covering global operations.
    
    - **NJE Ferry Waiver Zones:**
      - See the Ferry Waiver Program Brochure for details.
    
    - **3 Hours per Day Rule:**
      - The reservation must be a continuous trip (all airport codes align, the same requested aircraft type is used, and the same program applies).
      - The average flight time per day (calculated from the local ETD date of the first leg to that of the final leg) must be at least 3 hours.
      - If the average is below 3 hours, an additional upcharge is required.
    
    - **High Efficiency Discount:**
      - For Signature Series A/C (or upgrades to G-450/G-IV), the base discount is:
         - 20% off for flight times between 2.5 and 3.4 hrs.
         - 30% off for flight times between 3.5 and 4.4 hrs.
         - 40% off for flight times greater than 4.5 hrs.
      - **Double Discount:** If the discount definitions text (entered in Discount Definitions) includes the word “doubled” (case‑insensitive) and both the first leg departs from and the last leg arrives at a designated High Efficiency Airport (KTEB, KHPN, KIAD, KPBI, KMDW, KDAL, KVNY, KSJC, KLAS, KSFO, KBOS, KAPF, KSDL, KPDK) within the same calendar day, then the discount percentage is doubled.
      - **Important:** If the double discount condition is not met (or “doubled” is not present), then only the base discount applies.
    
    - **Exceptions & Leadership Approval:**
      - Tech stops within the CSA may allow the waiver to still apply.
      - Passenger drop‑offs/pick‑ups under 60 minutes are generally waived.
      - Any exceptions to these rules require leadership approval.
    """
)

# Define High Efficiency Airports for discount doubling
HE_AIRPORTS = {"KTEB", "KHPN", "KIAD", "KPBI", "KMDW", "KDAL", "KVNY", "KSJC", "KLAS", "KSFO", "KBOS", "KAPF", "KSDL", "KPDK"}

# ----------------------------
# Aircraft Mapping (common) - already defined above (repeated for clarity)
# ----------------------------
aircraft_mapping = {
    "BE-400A": "Beechcraft Beechjet 400A",
    "CE-560": "Cessna Citation V",
    "CE-560E": "Cessna Citation Ultra",
    "CE-560EP": "Cessna Citation Encore",
    "EMB-505S": "Embraer Phenom 300S",
    "EMB-505E": "Embraer Phenom 300E",
    "CE-560XL": "Cessna Citation Excel",
    "CE-560XLS": "Cessna Citation XLS",
    "CE-560XLSA": "Cessna Citation XLS+",
    "HS-125-750": "Hawker 750",
    "HS-125-800XPC": "Hawker 800XPC",
    "HS-125-900XP": "Hawker 900XP",
    "CE-680": "Cessna Citation Sovereign",
    "CE-680AS": "Cessna Citation Sovereign+",
    "EMB-545-MOD": "Embraer Praetor 500",
    "CE-700": "Cessna Citation Longitude",
    "CL3500": "Bombardier Challenger 3500",
    "CL-350S": "Bombardier Challenger 350",
    "DA-2000": "Dassault Falcon 2000",
    "DA-2EASY": "Dassault Falcon 2000S",
    "CL-650S": "Bombardier Challenger 650",
    "GIV-SP": "Gulfstream IV-SP",
    "G-450": "Gulfstream G450",
    "GV": "Gulfstream V",
    "GL5500": "Bombardier Global 5500",
    "GL5000S": "Bombardier Global 5000",
    "GL6000S": "Bombardier Global 6000",
    "GL7500": "Bombardier Global 7500",
    "GL8000": "Bombardier Global 8000"
}

# ----------------------------
# U.S. Region Mapping
# ----------------------------
CSA_AIRPORTS = {
    "CYHM", "CYOO", "CYSA", "CYYZ", "CYGK", "CYOW", "CYSN", "CYZD",
    "CYHU", "CYPQ", "CYTZ", "CYZR", "CYKF", "CYQA", "CYUL", "CZBB",
    "CYKZ", "CYQG", "CYVR", "CYMX", "CYQS", "CYXU"
}
region_mapping_us = {
    "C": "Group I", "K": "CSA", "MM": "Group I", "MY": "Group I", "MB": "Group I",
    "MK": "Group I", "TN": "Group I", "TB": "Group I", "TJ": "Group I", "TI": "Group I",
    "TQ": "Group I", "TR": "Group I", "TT": "Group I", "TU": "Group I", "TV": "Group I",
    "MT": "Group I", "MU": "Group I", "MW": "Group I", "MZ": "Group I", "MG": "Group I",
    "MH": "Group I", "MP": "Group I", "MR": "Group I", "MS": "Group I", "PA": "Group I",
    "PH": "Group II",
    "BG": "Group III", "BI": "Group III", "EH": "Group III", "EI": "Group III", "EK": "Group III",
    "EB": "Group III", "ED": "Group III", "EE": "Group III", "EF": "Group III", "EG": "Group III",
    "EL": "Group III", "EN": "Group III", "EP": "Group III", "ES": "Group III", "EV": "Group III",
    "EY": "Group III", "LF": "Group III", "LG": "Group III", "LH": "Group III", "LI": "Group III",
    "LJ": "Group III", "LK": "Group III", "LL": "Group III", "LM": "Group III", "LO": "Group III",
    "LP": "Group III", "LQ": "Group III", "LR": "Group III", "LS": "Group III", "LT": "Group III",
    "LU": "Group III", "LW": "Group III", "LY": "Group III", "LZ": "Group III", "GM": "Group III",
    "SA": "Group IV", "SB": "Group IV", "SC": "Group IV", "SE": "Group IV", "SG": "Group IV",
    "SK": "Group IV", "SL": "Group IV", "SM": "Group IV", "SO": "Group IV", "SP": "Group IV",
    "SU": "Group IV", "SV": "Group IV", "SY": "Group IV", "ZB": "Group IV", "ZG": "Group IV",
    "ZH": "Group IV", "ZL": "Group IV", "ZS": "Group IV", "ZY": "Group IV", "VA": "Group IV",
    "VE": "Group IV", "VI": "Group IV", "VO": "Group IV"
}

# ----------------------------
# NetJets Europe Region Mapping Function
# ----------------------------
def get_region_eu(icao):
    icao = icao.strip().upper()
    for prefix in ["HE", "HU", "HR"]:
        if icao.startswith(prefix):
            return "Group I"
    for prefix in ["UG", "UY", "UU"]:
        if icao.startswith(prefix):
            return "Group II"
    for prefix in ["PA", "PH", "SB"]:
        if icao.startswith(prefix):
            return "Group IV"
    if icao.startswith("K") or icao.startswith("C"):
        return "Group III"
    if icao.startswith("E") or icao.startswith("L"):
        return "CSA"
    return "NO GROUP"

# ----------------------------
# Aircraft Groups Mapping (common to both)
# ----------------------------
aircraft_groups = {
    "BE-400A": "Group I",
    "CE-560": "Group I",
    "CE-560E": "Group I",
    "CE-560EP": "Group I",
    "EMB-505S": "Group I",
    "EMB-505E": "Group I",
    "CE-560XL": "Group I",
    "CE-560XLS": "Group I",
    "CE-560XLSA": "Group I",
    "HS-125-750": "Group I",
    "HS-125-800XPC": "Group I",
    "HS-125-900XP": "Group I",
    "CE-680": "Group I",
    "CE-680AS": "Group I",
    "CL-350S": "Group II",
    "CL3500": "Group II",
    "CE-700": "Group III",
    "CL-650S": "Group III",
    "DA-2000": "Group III",
    "DA-2EASY": "Group III",
    "EMB-545-MOD": "Group III",
    "GIV-SP": "Group III",
    "G-450": "Group III",
    "GL5500": "Group IV",
    "GL5000S": "Group IV",
    "GL6000S": "Group IV",
    "GL7500": "Group IV",
    "GL8000": "Group IV",
    "GV": "Group IV"
}

# ----------------------------
# Product Mapping Dictionary
# ----------------------------
product_mapping = {
    "Share365": "NJ Owner contract. Eligible for ferry waiver for FWG 1; standard PPD premium applies.",
    "Share365i": "NJ Interim Lease contract. Similar to NJ Owner, but with interim lease terms.",
    "Share365l": "NJ Lease / Pre-paid Lease. Hourly rate includes OHR and Fuel; additional fees may apply.",
    "Share355l": "Standard 25-hr Lease with PPD restrictions; pays a 1.25 PPD premium.",
    "NJ X-Country": "30% discount on Challenger 350 for 3.5+ hrs; tech stops combine time.",
    "NJ Transatlantic": "40% discount on Global 5000S/6000S/7500 for 5+ hrs; tech stops combine time.",
    "High Efficiency": "Requires at least 1 pax; first/last flight in NJA CSA; must use contracted aircraft type.",
    "Expanded High Efficiency": "Restricted to flights in NJUS CSA.",
    "Limited High Efficiency": "Capped: 20% for 2.5-3.4 hrs, 30% for 3.5-4.4 hrs, 40% for 4.5+ hrs."
}

# ----------------------------
# Calculate Discount Function
# ----------------------------
def calculate_discount(row):
    prog = row.get("program", "").strip().lower()
    if prog != "netjets u.s.":
        return "0%"
    if row.get("contracted_ac"):
        req_ac = row["req_ac"].strip().upper()
        cont_ac = row["contracted_ac"].strip().upper()
        if req_ac != cont_ac:
            return "0%"
    try:
        bt = float(row["bt"])
    except:
        bt = 0.0
    dep = row["dep"].strip().upper()
    arr = row["arr"].strip().upper()
    dep_region = "CSA" if (dep in CSA_AIRPORTS or dep.startswith("K")) else region_mapping_us.get(dep[:2], "NO GROUP")
    arr_region = "CSA" if (arr in CSA_AIRPORTS or arr.startswith("K")) else region_mapping_us.get(arr[:2], "NO GROUP")
    if dep_region != "CSA" and arr_region != "CSA":
        return "0%"
    prod = row["product"].strip().lower()
    if "high efficiency" in prod:
        if bt < 2.5:
            return "0%"
        elif bt < 3.5:
            return "20%"
        elif bt < 4.5:
            return "30%"
        else:
            return "40%"
    if row["req_ac"].strip().upper() in ["CL-350S", "CL3500"]:
        if bt >= 3.5:
            return "30%"
    return "0%"

# ----------------------------
# Process Table Function
# ----------------------------
def process_table(input_data: str, discount_def: str, default_program="NetJets U.S."):
    lines = input_data.splitlines()
    if not lines:
        return "", "", "", []
    # Remove header row if present.
    if lines[0].strip().upper().startswith("REQUEST NUMBER"):
        header = lines.pop(0)
    else:
        header = ""
    first_row_parts = lines[0].split("\t")
    program_index = None
    if len(first_row_parts) >= 11 and "PROGRAM" in first_row_parts:
        program_index = first_row_parts.index("PROGRAM")
    elif len(first_row_parts) >= 18:
        program_index = 17
    rows = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) < 10:
            continue
        row_data = {
            "req_number": parts[0],
            "date": parts[1],
            "dep": parts[3],
            "arr": parts[4],
            "etd": parts[6],
            "eta": parts[7],
            "req_ac": parts[8],
            "bt": parts[9]
        }
        # CONTRACTED A/C assumed at index 11
        if len(parts) > 11:
            row_data["contracted_ac"] = parts[11].strip()
        else:
            row_data["contracted_ac"] = row_data["req_ac"]
        # PRODUCT assumed at index 13
        if len(parts) > 13:
            row_data["product"] = parts[13].strip()
        else:
            row_data["product"] = ""
        # "PROGRAM" column if exists.
        if program_index is not None and len(parts) > program_index:
            row_data["program"] = parts[program_index].strip()
        else:
            row_data["program"] = default_program
        # Read "Cont Hrs" (Contract Hours) from index 29 if available, else default to "0"
        if len(parts) > 29:
            row_data["cont_hrs"] = parts[29].strip()
        else:
            row_data["cont_hrs"] = "0"
        rows.append(row_data)
    processed = []
    for row in rows:
        dep = row["dep"]
        arr = row["arr"]
        ac = row["req_ac"]
        prog = row.get("program", default_program).lower()
        if "europe" in prog:
            dep_region = get_region_eu(dep)
            arr_region = get_region_eu(arr)
        else:
            dep_region = ("CSA" if dep in CSA_AIRPORTS or dep.startswith("K")
                          else region_mapping_us.get(dep[:2], region_mapping_us.get(dep[0], "NO GROUP")))
            arr_region = ("CSA" if arr in CSA_AIRPORTS or arr.startswith("K")
                          else region_mapping_us.get(arr[:2], region_mapping_us.get(arr[0], "NO GROUP")))
        ac_group = aircraft_groups.get(ac, "NO GROUP")
        waiver = {"ferry_in": "N", "ferry_out": "N"}
        if dep_region == "CSA" or arr_region == "CSA":
            waiver = {"ferry_in": "Y", "ferry_out": "Y"}
            if dep_region == "CSA" and arr_region == "CSA":
                basic_reason = "because both airports are in CSA"
            elif dep_region == "CSA" and arr_region == "NO GROUP":
                basic_reason = "because the departure is in CSA, but the arrival is not in any FWG"
            elif arr_region == "CSA" and dep_region == "NO GROUP":
                basic_reason = "because the arrival is in CSA, but the departure is not in any FWG"
            elif dep_region == "CSA":
                basic_reason = "because the departure is in CSA and the arrival is in the applicable FWG"
            elif arr_region == "CSA":
                basic_reason = "because the arrival is in CSA and the departure is in the applicable FWG"
            else:
                basic_reason = "because both airports are in CSA"
        elif dep_region == "Group I" and arr_region == "Group I":
            waiver = {"ferry_in": "Y", "ferry_out": "Y"}
            basic_reason = "because both airports are in Group I (intra Group I flight)"
        elif ((dep_region == "Group I" and arr_region == "Group III") or 
              (dep_region == "Group III" and arr_region == "Group I")) and ac_group in ["Group III", "Group IV"]:
            waiver = {"ferry_in": "Y", "ferry_out": "Y"}
            basic_reason = "because the flight is between Group I and Group III and the aircraft is in Group III/IV"
        else:
            waiver = {"ferry_in": "N", "ferry_out": "N"}
            basic_reason = "no applicable waiver rule applies"
        if dep_region == "NO GROUP":
            waiver["ferry_in"] = "N"
            basic_reason += " (departure airport not in any FWG)"
        if arr_region == "NO GROUP":
            waiver["ferry_out"] = "N"
            basic_reason += " (arrival airport not in any FWG)"
        if "europe" in prog and "CSA" in basic_reason and "FWG" in basic_reason:
            basic_reason += " (Europe)"
        discount = calculate_discount(row)
        if row.get("contracted_ac") and row["req_ac"].strip().upper() != row["contracted_ac"].strip().upper():
            discount = "0%"
            basic_reason += " (Discount not applicable because requested AC type does not match contracted AC type. Please check the interchange rate in IJet.)"
        row["discount"] = discount
        row["dep_region"] = dep_region
        row["arr_region"] = arr_region
        row["ac_group"] = ac_group
        row["waiver"] = waiver
        row["basic_reason"] = basic_reason
        row["product_desc"] = product_mapping.get(row["product"], "No product info available")
        processed.append(row)
    groups = defaultdict(list)
    for row in processed:
        base = row["req_number"].split("-")[0]
        prog = row["program"].strip().lower()
        groups[(base, prog)].append(row)
    # Do not re-sort; preserve input order.
    final_processed = []
    for key in groups.keys():
        final_processed.extend(groups[key])
    
    # Determine if double discount should be applied.
    apply_double_discount = "doubled" in discount_def.lower() if discount_def.strip() else False
    if apply_double_discount:
        for key, legs in groups.items():
            if legs:
                first_leg = legs[0]
                last_leg = legs[-1]
                if (first_leg["dep"].strip().upper() in HE_AIRPORTS and
                    last_leg["arr"].strip().upper() in HE_AIRPORTS):
                    for row in legs:
                        if "high efficiency" in row.get("product", "").strip().lower() and row["discount"] != "0%":
                            base_disc = int(row["discount"].replace("%", ""))
                            doubled = base_disc * 2
                            row["discount"] = f"{doubled}%"
                            row["basic_reason"] += f" (Discount doubled to {doubled}% as first leg departs and last leg arrives at a High Efficiency Airport)"
                            row["doubled"] = True
    table_data = []
    for row in final_processed:
        discount_desc = f"Discount: {row['discount']}."
        table_data.append({
            "REQUEST NUMBER": row["req_number"],
            "DATE": row["date"],
            "PROGRAM": row["program"],
            "DEP": row["dep"],
            "ARR": row["arr"],
            "REQ A/C": aircraft_mapping.get(row["req_ac"], row["req_ac"]),
            "PRODUCT": row["product"],
            "PRODUCT DESC": row["product_desc"],
            "BT": row["bt"],
            "A/C GROUP": row["ac_group"],
            "WAIVER IN": row["waiver"]["ferry_in"],
            "WAIVER OUT": row["waiver"]["ferry_out"],
            "DISCOUNT": row["discount"],
            "REASON": row["basic_reason"] + " " + discount_desc
        })
    
    if final_processed:
        total_flight_time = sum(float(row["bt"]) for row in final_processed if row["bt"])
        total_contract_hours = sum(float(row["cont_hrs"]) for row in final_processed if row.get("cont_hrs") and row["cont_hrs"].replace('.','',1).isdigit())
        dates = [parser.parse(row["date"]) for row in final_processed]
        first_date = min(dates)
        last_date = max(dates)
        days = (last_date - first_date).days + 1
        avg_ft = total_flight_time / days if days > 0 else total_flight_time
        reservation_summary = (
            f"Reservation spans from {first_date.strftime('%m/%d/%Y')} to {last_date.strftime('%m/%d/%Y')} "
            f"({days} days), with a total flight time of {total_flight_time} hrs, averaging {avg_ft:.2f} hrs per day.\n"
        )
        product_info = {}
        for row in final_processed:
            prod = row.get("product", "")
            desc = row.get("product_desc", "")
            if prod:
                product_info[prod] = desc
        if product_info:
            product_summary = "Reservation Product Summary:" + "".join(f"\n- {p}: {d}" for p, d in product_info.items())
        else:
            product_summary = "Reservation Product Summary: None"
        
        # Check continuity: same arrival/departure and same requested AC type.
        is_continuous = all(
            final_processed[i-1]["arr"].strip().upper() == final_processed[i]["dep"].strip().upper() and 
            final_processed[i-1]["req_ac"].strip().upper() == final_processed[i]["req_ac"].strip().upper()
            for i in range(1, len(final_processed))
        )
        
        # Check if every leg is fully ferry waived.
        fully_waived = all(row["waiver"]["ferry_in"] == "Y" and row["waiver"]["ferry_out"] == "Y" for row in final_processed)
        
        # Build detailed discount explanation.
        discount_explanation = []
        for row in final_processed:
            if row["discount"] != "0%":
                try:
                    bt = float(row["bt"])
                except:
                    bt = 0.0
                if "high efficiency" in row.get("product", "").strip().lower():
                    if bt < 3.5:
                        tier_explanation = "a 20% discount" 
                    elif bt < 4.5:
                        tier_explanation = "a 30% discount" 
                    else:
                        tier_explanation = "a 40% discount" 
                    if row.get("doubled", False):
                        tier_explanation += " (discount doubled)"
                else:
                    tier_explanation = f"a {row['discount']} discount based on flight time criteria"
                discount_explanation.append(
                    f"Leg {row['req_number']} received {tier_explanation} for a High Efficiency product operating within the CSA."
                )
        if discount_explanation:
            discount_summary = "Discount Details: " + " ".join(discount_explanation)
        else:
            discount_summary = "No discount was applied on any leg."
        
        # Check if any leg has a requested AC type different from contracted AC type.
        mismatch_found = any(
            row["req_ac"].strip().upper() != row["contracted_ac"].strip().upper() 
            for row in final_processed
        )
        mismatch_note = ""
        if mismatch_found:
            mismatch_note = " Additionally, one or more legs have a mismatch between the requested and contracted aircraft type. Please verify that the interchange rate is applied correctly."
        
        # Build AI Conclusion with detailed explanation.
        if not is_continuous:
            reasons = []
            for i in range(1, len(final_processed)):
                prev = final_processed[i-1]
                curr = final_processed[i]
                if prev["arr"].strip().upper() != curr["dep"].strip().upper():
                    reasons.append(f"Leg {prev['req_number']} arrival ({prev['arr']}) does not match leg {curr['req_number']} departure ({curr['dep']}).")
                if prev["req_ac"].strip().upper() != curr["req_ac"].strip().upper():
                    reasons.append(f"Leg {prev['req_number']} requested AC ({prev['req_ac']}) differs from leg {curr['req_number']} requested AC ({curr['req_ac']}).")
            reason_str = " ".join(reasons) if reasons else "Continuity requirements are not met."
            ai_conclusion = (
                "Conclusion: The reservation does not meet the continuity requirements: " +
                reason_str +
                " Therefore, only standard ferry fees are applicable. Please submit an estimate based solely on these fees."
            )
        elif fully_waived:
            ai_conclusion = (
                "Conclusion: The reservation is continuous and fully qualifies for a ferry waiver on all legs. No additional upcharge is required. "
                + discount_summary
            )
        elif avg_ft < 3:
            upcharge = (3 * days) - total_flight_time
            if upcharge > 10:
                ai_conclusion = (
                    f"Conclusion: The reservation is continuous but averages only {avg_ft:.2f} hrs per day, which is below the required 3 hrs per day. "
                    f"An additional {upcharge:.2f} hrs is needed to meet the minimum flight time requirement. This additional charge is significant and may not be cost effective; please review the available contract hours and consider using standard ferry fees instead. "
                    + discount_summary
                )
            else:
                ai_conclusion = (
                    f"Conclusion: The reservation is continuous but averages only {avg_ft:.2f} hrs per day, which is below the required minimum of 3 hrs per day. "
                    f"An additional {upcharge:.2f} hrs is needed to meet the requirement. Please prepare two estimates: one based solely on standard ferry fees, and a second incorporating the additional upcharge. Also, ensure that the contract has sufficient hours to cover the extra time. "
                    + discount_summary
                )
        else:
            ai_conclusion = (
                "Conclusion: The reservation is continuous and meets the minimum daily flight time requirement of 3 hours. No additional upcharge is necessary. "
                + discount_summary
            )
        
        # Always add the total contract hours available and mismatch note if applicable.
        ai_conclusion += f" Total Contract Hours available: {total_contract_hours:.2f} hrs.{mismatch_note}"
        
        explanation = (
            "Detailed Reservation Explanation:\n" +
            reservation_summary +
            "\n" +
            product_summary +
            "\n" +
            ("Note: No discount is applicable to any leg not operated on the NetJets U.S. program."
             if not all(row["program"].strip().lower() == "netjets u.s." for row in final_processed)
             else "Note: Discount is applicable to this reservation.")
        )
    else:
        reservation_summary = "No valid rows processed."
        explanation = ""
        ai_conclusion = ""
    final_summary = explanation
    return final_summary, ai_conclusion, table_data

# ----------------------------
# Streamlit App
# ----------------------------
def main():
    st.title("Estimates Table Planning Processor")
    st.write(
        "Paste your table data (tab-separated) below and click **Process Table**. "
        "The header row is auto-detected and skipped. Each row's PROGRAM and PRODUCT values are read from the input if provided; "
        "otherwise, they default to NetJets U.S. and an empty product respectively."
    )
    
    # Use widget_key in keys for both discount and input text areas to clear on reset.
    discount_text = st.text_area("Discount Definitions", height=170, key=f"discount_input_{st.session_state.widget_key}",
                                  help="Enter discount rule examples (free text) as provided in IJet.")
    
    input_text = st.text_area("Input Table Data", height=160, key=f"input_text_{st.session_state.widget_key}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Process Table"):
            if input_text:
                expl, ai_conclusion, table_data = process_table(input_text, discount_text, default_program="NetJets U.S.")
                if discount_text.strip():
                    expl += "\n\nDiscount Rules:\n" + discount_text
                st.session_state.explanation_text = expl
                st.session_state.ai_text = ai_conclusion
                df = pd.DataFrame(table_data)
                # Use styled DataFrame for better text wrapping on the REASON column.
                styled_df = df.style.set_properties(subset=["REASON"], **{'white-space': 'pre-wrap'})
                st.session_state.table_df = styled_df
            else:
                st.warning("Please enter your input data.")
    with col2:
        if st.button("Reset"):
            st.session_state.widget_key += 1
            st.session_state.explanation_text = ""
            st.session_state.ai_text = ""
            st.session_state.table_df = None
            try:
                st.experimental_rerun()
            except Exception as e:
                st.write("Please refresh the page to clear the inputs.")

    
    if st.session_state.table_df is not None:
        st.write("Row Details Table:")
        st.markdown(
            f'<div class="row-details-table">{st.session_state.table_df.to_html(escape=False)}</div>',
            unsafe_allow_html=True
        )
    
    st.markdown("### Detailed Reservation Explanation:")
    st.text_area("Explanation", value=st.session_state.explanation_text, height=300)
    st.markdown("### AI Conclusion:")
    st.text_area("Conclusion", value=st.session_state.ai_text, height=200)

if __name__ == "__main__":
    main()
