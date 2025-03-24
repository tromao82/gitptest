import streamlit as st
import pandas as pd
from dateutil import parser
from collections import defaultdict
import datetime
import requests

# ----------------------------
# Cache the entire Excel file so it's loaded only once
# ----------------------------
@st.cache_data
def load_all_reservations() -> pd.DataFrame:
    file_path = r"G:\Product Delivery\GITP\Reports\New\QUOTES_Workflow_Report.xlsx"
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return pd.DataFrame()
    # Strip extra whitespace from column names
    df.columns = df.columns.str.strip()
    return df

# ----------------------------
# New Module: Load Reservation with Debugging
# ----------------------------
def load_reservation(res_number: str) -> pd.DataFrame:
    st.write("Debug: Entered load_reservation()")
    df = load_all_reservations()
    st.write("Debug: Loaded file from cache. Total rows:", len(df))
    st.write("Debug: Available columns:", df.columns.tolist())
    
    if "Reservation ID" not in df.columns:
        st.error("Column 'Reservation ID' not found in the file!")
        return pd.DataFrame()
    
    filtered_df = df[df["Reservation ID"].astype(str).str.contains(res_number, case=False, na=False)]
    st.write(f"Debug: Found {len(filtered_df)} rows matching reservation number '{res_number}'.")
    st.write("Debug: Preview of filtered rows:", filtered_df.head(5))
    
    mapped = pd.DataFrame({
        "req_number": filtered_df.get("Request ID-Leg Order Nbr", pd.Series(["0"] * len(filtered_df))),
        "date": filtered_df.get("EDT Date L", pd.Series(["0"] * len(filtered_df))),
        "dep": filtered_df.get("DEP", pd.Series(["0"] * len(filtered_df))),
        "arr": filtered_df.get("ARR", pd.Series(["0"] * len(filtered_df))),
        "etd": filtered_df.get("ETD L", pd.Series(["0"] * len(filtered_df))),
        "eta": filtered_df.get("ETA L", pd.Series(["0"] * len(filtered_df))),
        "req_ac": filtered_df.get("REQ A/C", pd.Series(["0"] * len(filtered_df))),
        "bt": filtered_df.get("BT", pd.Series(["0"] * len(filtered_df))),
        "contracted_ac": filtered_df.get("GUARANTEED A/C", filtered_df.get("REQ A/C", pd.Series(["0"] * len(filtered_df)))),
        "product": filtered_df.get("Contract Product Name", pd.Series(["0"] * len(filtered_df))),
        "program": filtered_df.get("Request Program", pd.Series(["NetJets U.S."] * len(filtered_df))),
        "cont_hrs": filtered_df.get("Overridden Trip Time", pd.Series(["0"] * len(filtered_df)))
    })
    st.write("Debug: Mapping complete. Preview of mapped DataFrame:", mapped.head(5))
    return mapped

# ----------------------------
# Function to call OpenAI API to rewrite AI Conclusion text
# ----------------------------
def rewrite_text(text):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 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"
    }
    data = {
         "model": "gpt-4o-mini",
         "messages": [      
             {
                "role": "system",
                "content": (
                    "Rewrite the following text in a clear, detailed, and friendly manner for a non-technical audience. "
                    "Explain step-by-step how the departure and arrival endpoints are evaluated, how tech stops are handled "
                    "(tech stops are not included in the overall average), the role of block time, and how the overall waiver decision, discounts, or upcharge option are determined."
                )
             },
             {"role": "user", "content": text}
         ],
         "temperature": 0.7,
         "max_tokens": 350
    }
    response = requests.post(url, headers=headers, json=data, verify=False)
    if response.status_code == 200:
         return response.json()["choices"][0]["message"]["content"].strip()
    else:
         return f"Error rewriting text: {response.text}"

# ----------------------------
# Helper Functions and Mappings
# ----------------------------
CANADIAN_CSA = {
    "CYHM", "CYOO", "CYSA", "CYYZ", "CYGK", "CYOW", "CYSN", "CYZD",
    "CYHU", "CYPQ", "CYTZ", "CYZR", "CYKF", "CYQA", "CYUL", "CZBB",
    "CYKZ", "CYQG", "CYVR", "CYMX", "CYQS", "CYXU"
}

def is_csa(icao: str) -> bool:
    icao = icao.strip().upper()
    return icao.startswith("K") or icao in CANADIAN_CSA

region_mapping_us = {
    "CY": "Group I",
    "C": "Group I", 
    "MM": "Group I", "MY": "Group I", "MB": "Group I",
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

def get_acceptable_region_groups(requested_ac: str) -> set:
    requested_ac_group = {
        "EMB-505S": "Group I",
        "EMB-505E": "Group I",
        "CE-560XLS": "Group I",
        "CE-560XLSA": "Group I",
        "CE-680": "Group I",
        "CE-680AS": "Group I",
        "CL-350S": "Group II",
        "CL3500": "Group II",
        "CE-700": "Group III",
        "CL-650S": "Group III",
        "GL5500": "Group III",
        "GL6000S": "Group IV",
        "GL6000": "Group IV",
        "GL7500": "GSA"
    }
    group = requested_ac_group.get(requested_ac, None)
    if group is None:
        return set()
    if group == "Group I":
        return {"Group I"}
    elif group == "Group II":
        return {"Group I", "Group II"}
    elif group == "Group III":
        return {"Group I", "Group II", "Group III"}
    elif group == "Group IV":
        return {"Group I", "Group II", "Group III"}
    elif group == "GSA":
        return {"Group III"}
    return set()

def qualifies_for_fw(icao: str, requested_ac: str) -> bool:
    icao = icao.strip().upper()
    if is_csa(icao):
        return True
    acceptable = get_acceptable_region_groups(requested_ac)
    prefix = icao[:2]
    region = region_mapping_us.get(prefix, "NO GROUP")
    return region in acceptable

def is_gsa(icao: str) -> bool:
    icao = icao.strip().upper()
    if is_csa(icao):
        return True
    prefix = icao[:2]
    return region_mapping_us.get(prefix, "NO GROUP") == "Group III"

def is_nje_csa(icao: str) -> bool:
    icao = icao.strip().upper()
    prefix = icao[:2]
    return (region_mapping_us.get(prefix, "NO GROUP") == "Group III") or (prefix == "GM")

# Aircraft Mapping
aircraft_mapping = {
    "EMB-505S": "Embraer Phenom 300S",
    "EMB-505E": "Embraer Phenom 300E",
    "CE-560XLS": "Cessna Citation XLS",
    "CE-560XLSA": "Cessna Citation XLS+",
    "CE-680": "Cessna Citation Sovereign",
    "CE-680AS": "Cessna Citation Sovereign+",
    "CL-350S": "Bombardier Challenger 350",
    "CL3500": "Bombardier Challenger 350",
    "CE-700": "Cessna Citation Longitude",
    "CL-650S": "Bombardier Challenger 650",
    "GL5500": "Bombardier Global 5500",
    "GL5000S": "Bombardier Global 5000",
    "GL6000S": "Bombardier Global 6000",
    "GL7500": "Bombardier Global 7500",
    "GL8000": "Bombardier Global 8000"
}

# Product Mapping
product_mapping = {
    "Share365": "NJ Owner contract. Eligible for ferry waiver for FWG 1; standard PPD premium applies.",
    "Share365i": "NJ Interim Lease contract. Similar to NJ Owner, but with interim lease terms.",
    "Share365l": "NJ Lease / Pre-paid Lease. Hourly rate includes OHR and Fuel; additional fees may apply.",
    "Share355l": "Standard 25-hr Lease with PPD restrictions; pays a 1.25 PPD premium.",
    "NJ X-Country": "30% discount on Challenger 350 for 3.5+ hrs; tech stops combine time.",
    "NJ Transatlantic": "40% discount on Global 5000S/6000S/7500 for 5+ hrs; tech stops combine time.",
    "High Efficiency": "High Efficiency discount as per defined rules.",
    "Expanded High Efficiency": "Expanded High Efficiency discount as per defined rules.",
    "Limited High Efficiency": "Limited High Efficiency discount as per defined rules."
}

def calculate_discount(row):
    prog = row.get("program", "").strip().lower()
    if prog != "netjets u.s.":
        return "0%"
    try:
        req_ac = row["req_ac"].strip().upper()
        cont_ac = row["contracted_ac"].strip().upper()
    except KeyError:
        return "0%"
    prod = row.get("product", "").strip().lower()
    if prod == "high efficiency":
        if req_ac != cont_ac:
            return "0%"
    try:
        bt = float(row["bt"])
    except:
        bt = 0.0
    dep = row["dep"].strip().upper()
    arr = row["arr"].strip().upper()
    if prod == "high efficiency":
        if "pax" in row and int(row["pax"]) < 1:
            return "0%"
        if req_ac in ["GL6000S", "GL6000", "GL5000S", "GL5500"]:
            if ((is_csa(dep) and is_nje_csa(arr)) or (is_csa(arr) and is_nje_csa(dep))):
                if bt >= 5.0:
                    return "40%"
            return "0%"
        elif req_ac == "CE-700":
            if not (is_csa(dep) or is_csa(arr)):
                return "0%"
            if 2.5 <= bt < 3.5:
                return "20%"
            elif bt >= 3.5:
                return "30%"
            else:
                return "0%"
        elif req_ac in ["CL-350S", "CL3500"]:
            if not (is_csa(dep) or is_csa(arr)):
                return "0%"
            if bt >= 3.5:
                return "30%"
            else:
                return "0%"
        else:
            return "0%"
    elif prod == "expanded high efficiency":
        if "pax" in row and int(row["pax"]) < 1:
            return "0%"
        signature_series = {"EMB505S", "CE680AS", "EMB545MOD", "CE700", "CL-350S", "CL3500",
                            "CL650S", "G450", "GL5000S", "GL5500", "GL6000S", "GL7500"}
        if req_ac not in signature_series:
            return "0%"
        if not (is_csa(dep) or is_csa(arr)):
            return "0%"
        airport_pricing_airports = {"KTEB", "KHPN", "KIAD", "KPBI", "KMDW", "KDAL",
                                    "KVNY", "KSJC", "KLAS", "KSFO", "KBOS", "KAPF",
                                    "KSDL", "KPDK"}
        is_airport_pricing = (dep in airport_pricing_airports and arr in airport_pricing_airports)
        if bt < 2.5:
            return "0%"
        if 2.5 <= bt < 3.5:
            return "40%" if is_airport_pricing else "20%"
        elif 3.5 <= bt < 4.5:
            return "60%" if is_airport_pricing else "30%"
        elif bt >= 4.5:
            return "80%" if is_airport_pricing else "40%"
        else:
            return "0%"
    elif prod == "limited high efficiency":
        if "pax" in row and int(row["pax"]) < 1:
            return "0%"
        signature_series = {"EMB505S", "CE680AS", "EMB545MOD", "CE700", "CL-350S", "CL3500",
                            "CL650S", "G450", "GL5000S", "GL5500", "GL6000S", "GL7500"}
        if req_ac not in signature_series:
            return "0%"
        if not (is_csa(dep) or is_csa(arr)):
            return "0%"
        if bt < 2.5:
            return "0%"
        if 2.5 <= bt < 3.5:
            return "20%"
        elif 3.5 <= bt < 4.5:
            return "30%"
        elif bt >= 4.5:
            return "40%"
        else:
            return "0%"
    if req_ac in ["GL6000S", "GL6000"]:
        if not (qualifies_for_fw(dep, req_ac) and qualifies_for_fw(arr, req_ac)):
            return "0%"
    elif req_ac == "GL7500":
        if not ((is_gsa(dep) or is_csa(dep)) or (is_gsa(arr) or is_csa(arr))):
            return "0%"
    else:
        if not (qualifies_for_fw(dep, req_ac) and qualifies_for_fw(arr, req_ac)):
            return "0%"
    if req_ac in ["CL-350S", "CL3500"]:
        if bt >= 3.5:
            return "30%"
    return "0%"

def build_explanation(row, overall_message, overall_waiver_decision, req_ac, is_tech_stop=False):
    dep = row["dep"].strip().upper()
    arr = row["arr"].strip().upper()
    dep_qual = "CSA" if is_csa(dep) else region_mapping_us.get(dep[:2], "NO GROUP")
    arr_qual = "CSA" if is_csa(arr) else region_mapping_us.get(arr[:2], "NO GROUP")
    bt_str = row.get("bt", "N/A")
    try:
        bt = float(bt_str)
    except:
        bt = 0.0
    product = row.get("product", "").strip()
    prod_desc = product_mapping.get(product, "No product info available")
    discount = row.get("discount", "0%")
    discount_msg = ""
    if discount != "0%":
        if product.lower() == "limited high efficiency":
            if bt >= 4.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs exceeds the threshold of 4.5 hrs."
            elif 3.5 <= bt < 4.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs is more than 3.5 hrs but less than 4.5 hrs."
            elif 2.5 <= bt < 3.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs is more than 2.5 hrs but less than 3.5 hrs."
        elif product.lower() == "high efficiency":
            if req_ac in ["GL6000S", "GL6000", "GL5000S", "GL5500"]:
                if bt >= 5.0:
                    discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs exceeds the threshold of 5.0 hrs."
            elif req_ac == "CE-700":
                if bt >= 3.5:
                    discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs exceeds the threshold of 3.5 hrs."
                elif 2.5 <= bt < 3.5:
                    discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs is more than 2.5 hrs but less than 3.5 hrs."
            elif req_ac in ["CL-350S", "CL3500"]:
                if bt >= 3.5:
                    discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs exceeds the threshold of 3.5 hrs."
        elif product.lower() == "expanded high efficiency":
            if bt >= 4.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs exceeds the threshold of 4.5 hrs."
            elif 3.5 <= bt < 4.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs is more than 3.5 hrs but less than 4.5 hrs."
            elif 2.5 <= bt < 3.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs is more than 2.5 hrs but less than 3.5 hrs."
    else:
        discount_msg = "No discount was applied because the block time did not meet the required threshold."
    tech_stop_msg = " This flight is a tech stop and is not included in the overall average calculation." if is_tech_stop else ""
    explanation = (
        f"{overall_message} (Overall waiver: {overall_waiver_decision}). "
        f"Flight {row['req_number']}: Departure {dep} qualifies as {dep_qual}; "
        f"Arrival {arr} qualifies as {arr_qual}. Block time: {bt_str} hrs. "
        f"Aircraft: {req_ac}. Product: {product}. Characteristics: {prod_desc}.{tech_stop_msg} {discount_msg}"
    )
    return explanation

def check_tech_stops(legs) -> bool:
    return True

def rule_n4_eligible(legs, requested_ac: str):
    sorted_legs = sorted(legs, key=lambda r: parser.parse(r["date"]))
    first_leg = sorted_legs[0]
    last_leg = sorted_legs[-1]
    if is_csa(first_leg["dep"]) and is_csa(last_leg["arr"]):
        return (True, "Reservation originates and terminates in CSA.")
    exit_date = None
    return_date = None
    for leg in sorted_legs:
        if not is_csa(leg["dep"]):
            exit_date = parser.parse(leg["date"])
            break
    if exit_date is None:
        return (True, "Reservation remains in CSA.")
    for leg in sorted_legs:
        leg_date = parser.parse(leg["date"])
        if leg_date > exit_date and is_csa(leg["dep"]):
            return_date = leg_date
            break
    if return_date is None:
        return (False, "Reservation leaves CSA and does not return.")
    num_days = (return_date.date() - exit_date.date()).days + 1
    total_bt = sum(float(leg["bt"]) for leg in sorted_legs if exit_date <= parser.parse(leg["date"]) <= return_date)
    avg_bt = total_bt / num_days if num_days > 0 else 0.0
    if avg_bt >= 3.0:
        return (True, f"Reservation qualifies with an average of {avg_bt:.2f} hrs/day over {num_days} days.")
    else:
        return (False, f"Average block time {avg_bt:.2f} hrs/day is below required 3 hrs/day.")

def rule_n5_eligible(legs, requested_ac: str):
    sorted_legs = sorted(legs, key=lambda r: parser.parse(r["date"]))
    first_leg = sorted_legs[0]
    last_leg = sorted_legs[-1]
    dep_ok = is_csa(first_leg["dep"]) or qualifies_for_fw(first_leg["dep"], requested_ac)
    arr_ok = is_csa(last_leg["arr"]) or qualifies_for_fw(last_leg["arr"], requested_ac)
    if not (is_csa(first_leg["dep"]) or is_csa(last_leg["arr"])):
        return (False, "Neither endpoint is in CSA; Rule n5 does not apply.")
    first_date = parser.parse(first_leg["date"])
    last_date = parser.parse(last_leg["date"])
    num_days = (last_date.date() - first_date.date()).days + 1
    total_bt = sum(float(leg["bt"]) for leg in sorted_legs)
    avg_bt = total_bt / num_days if num_days > 0 else total_bt
    if avg_bt < 3.0:
        return (False, f"Average block time {avg_bt:.2f} hrs/day is below 3 hrs/day.")
    if dep_ok and arr_ok:
        return (True, f"Reservation qualifies with average block time of {avg_bt:.2f} hrs/day over {num_days} days.")
    else:
        reasons = []
        if not dep_ok:
            reasons.append("Departure endpoint does not qualify.")
        if not arr_ok:
            reasons.append("Arrival endpoint does not qualify.")
        return (False, " ".join(reasons))

def rule_n6_eligible(legs, requested_ac: str):
    sorted_legs = sorted(legs, key=lambda r: parser.parse(r["date"]))
    first_leg = sorted_legs[0]
    last_leg = sorted_legs[-1]
    dep = first_leg["dep"].strip().upper()
    arr = last_leg["arr"].strip().upper()
    dep_region = region_mapping_us.get(dep[:2], "NO GROUP")
    arr_region = region_mapping_us.get(arr[:2], "NO GROUP")
    first_date = parser.parse(first_leg["date"])
    last_date = parser.parse(last_leg["date"])
    num_days = (last_date.date() - first_date.date()).days + 1
    total_bt = sum(float(leg["bt"]) for leg in sorted_legs)
    avg_bt = total_bt / num_days if num_days > 0 else total_bt
    requested_ac_group = {
        "EMB-505S": "Group I",
        "EMB-505E": "Group I",
        "CE-560XLS": "Group I",
        "CE-560XLSA": "Group I",
        "CE-680": "Group I",
        "CE-680AS": "Group I",
        "CL-350S": "Group II",
        "CL3500": "Group II",
        "CE-700": "Group III",
        "CL-650S": "Group III",
        "GL5500": "Group III",
        "GL6000S": "Group IV",
        "GL6000": "Group IV",
        "GL7500": "GSA"
    }
    req_group = requested_ac_group.get(requested_ac, None)
    if req_group == "Group I":
        if dep_region == "Group I" and arr_region == "Group I":
            if avg_bt >= 3.0:
                return (True, f"Reservation qualifies for Group I with {avg_bt:.2f} hrs/day over {num_days} days.")
            else:
                return (False, f"Average block time {avg_bt:.2f} hrs/day is below 3 hrs for Group I flight.")
        else:
            return (False, "Endpoints are not both in Group I for a Group I flight.")
    elif req_group in {"Group III", "Group IV"}:
        if (dep_region in {"Group I", "Group III"}) and (arr_region in {"Group I", "Group III"}):
            if avg_bt >= 3.0:
                return (True, f"Reservation qualifies for {req_group} with {avg_bt:.2f} hrs/day over {num_days} days.")
            else:
                return (False, f"Average block time {avg_bt:.2f} hrs/day is below 3 hrs for {req_group} flight.")
        else:
            return (False, f"Endpoints do not meet required regions for {req_group} flight.")
    else:
        return (False, "Requested aircraft group not recognized for Rule n6.")

def determine_reservation_waiver(legs, requested_ac: str):
    sorted_legs = sorted(legs, key=lambda r: parser.parse(r["date"]))
    if not check_tech_stops(sorted_legs):
        return ("N", "Tech stop check failed.")
    first_leg = sorted_legs[0]
    last_leg = sorted_legs[-1]
    
    if requested_ac == "GL7500":
        dep_ok = (is_gsa(first_leg["dep"]) or is_csa(first_leg["dep"]))
        arr_ok = (is_gsa(last_leg["arr"]) or is_csa(last_leg["arr"]))
        if dep_ok or arr_ok:
            return ("Y", "Reservation qualifies for Global 7500 waiver (at least one endpoint in GSA).")
        else:
            return ("N", "Neither endpoint qualifies for Global 7500 GSA waiver.")
    else:
        dep_in = is_csa(first_leg["dep"])
        arr_in = is_csa(last_leg["arr"])
        if dep_in and arr_in:
            return ("Y", "Reservation is entirely domestic (both endpoints in CSA).")
        if dep_in != arr_in:
            eligible, message = rule_n5_eligible(sorted_legs, requested_ac)
            return ("Y" if eligible else "N", message)
        if not dep_in and not arr_in:
            eligible, message = rule_n6_eligible(sorted_legs, requested_ac)
            return ("Y" if eligible else "N", message)
    return ("N", "Unable to determine waiver eligibility.")

def process_reservations(input_data: str, discount_def: str, default_program="NetJets U.S."):
    lines = input_data.splitlines()
    if not lines:
        return "", "", [], []
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
        if len(parts) > 11:
            row_data["contracted_ac"] = parts[11].strip()
        else:
            row_data["contracted_ac"] = row_data["req_number"]
        if len(parts) > 13:
            row_data["product"] = parts[13].strip()
        else:
            row_data["product"] = ""
        if program_index is not None and len(parts) > program_index:
            row_data["program"] = parts[program_index].strip()
        else:
            row_data["program"] = default_program
        if len(parts) > 29:
            row_data["cont_hrs"] = parts[29].strip()
        else:
            row_data["cont_hrs"] = "0"
        rows.append(row_data)
    
    groups = defaultdict(list)
    for row in rows:
        base = row["req_number"].split("-")[0]
        groups[base].append(row)
    
    final_processed = []
    group_waiver = {}
    tech_stop_exists = False
    for base, legs in groups.items():
        req_ac = legs[0]["req_ac"].strip().upper()
        waiver_decision, waiver_message = determine_reservation_waiver(legs, req_ac)
        group_waiver[base] = (waiver_decision, waiver_message)
        for idx, row in enumerate(legs):
            is_tech_stop = (len(legs) > 1 and idx not in (0, len(legs)-1))
            if is_tech_stop:
                tech_stop_exists = True
            if len(legs) > 1:
                if idx == 0:
                    if req_ac == "GL7500":
                        row["waiver"] = {"ferry_in": "Y" if (is_gsa(row["dep"]) or is_csa(row["dep"])) else "N", "ferry_out": "Y"}
                    elif req_ac in ["GL6000S", "GL6000"]:
                        row["waiver"] = {"ferry_in": "Y" if qualifies_for_fw(row["dep"], req_ac) else "N", "ferry_out": "Y"}
                    else:
                        row["waiver"] = {"ferry_in": "Y" if qualifies_for_fw(row["dep"], req_ac) else "N", "ferry_out": "Y"}
                elif idx == len(legs) - 1:
                    if req_ac == "GL7500":
                        row["waiver"] = {"ferry_in": "Y", "waiver_out": "Y" if waiver_decision == "Y" else ("Y" if (is_gsa(row["arr"]) or is_csa(row["arr"])) else "N")}
                        row["waiver"] = {"ferry_in": "Y", "ferry_out": "Y" if waiver_decision == "Y" else ("Y" if (is_gsa(row["arr"]) or is_csa(row["arr"])) else "N")}
                    elif req_ac in ["GL6000S", "GL6000"]:
                        row["waiver"] = {"ferry_in": "Y", "ferry_out": "Y" if qualifies_for_fw(row["arr"], req_ac) else "N"}
                    else:
                        row["waiver"] = {"ferry_in": "Y", "ferry_out": "Y" if qualifies_for_fw(row["arr"], req_ac) else "N"}
                else:
                    row["waiver"] = {"ferry_in": "Y", "ferry_out": "Y"}
            else:
                if req_ac == "GL7500":
                    if waiver_decision == "Y":
                        row["waiver"] = {"ferry_in": "Y", "ferry_out": "Y"}
                    else:
                        row["waiver"] = {"ferry_in": "Y" if (is_gsa(row["dep"]) or is_csa(row["dep"])) else "N",
                                         "ferry_out": "Y" if (is_gsa(row["arr"]) or is_csa(row["arr"])) else "N"}
                elif req_ac in ["GL6000S", "GL6000"]:
                    row["waiver"] = {"ferry_in": "Y" if qualifies_for_fw(row["dep"], req_ac) else "N",
                                     "ferry_out": "Y" if qualifies_for_fw(row["arr"], req_ac) else "N"}
                else:
                    row["waiver"] = {"ferry_in": "Y" if qualifies_for_fw(row["dep"], req_ac) else "N",
                                     "ferry_out": "Y" if qualifies_for_fw(row["arr"], req_ac) else "N"}
            if waiver_decision == "Y":
                discount = calculate_discount(row)
            else:
                discount = "0%"
            row["discount"] = discount
            basic_reason = build_explanation(row, waiver_message, waiver_decision, req_ac, is_tech_stop=is_tech_stop)
            if is_tech_stop:
                basic_reason += " (This flight is a tech stop and is not included in the overall average calculation.)"
            row["basic_reason"] = basic_reason
            row["product_desc"] = product_mapping.get(row["product"], "No product info available")
            final_processed.append(row)
    
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
            "A/C GROUP": aircraft_mapping.get(row["req_ac"], "NO GROUP"),
            "WAIVER IN": row["waiver"]["ferry_in"],
            "WAIVER OUT": row["waiver"]["ferry_out"],
            "DISCOUNT": row["discount"],
            "REASON": row["basic_reason"] + " " + discount_desc
        })
    
    upcharge_rows = []
    for base, legs in groups.items():
        if len(legs) <= 1:
            continue
        first_date = min(parser.parse(leg["date"]) for leg in legs)
        last_date = max(parser.parse(leg["date"]) for leg in legs)
        num_days = (last_date.date() - first_date.date()).days + 1
        total_bt = sum(float(leg["bt"]) for leg in legs)
        avg_bt = total_bt / num_days if num_days > 0 else total_bt
        if avg_bt < 3:
            missing = (3 * num_days) - total_bt
            if missing > 0 and missing <= 10:
                new_row = {}
                new_row["req_number"] = base + " Upcharge"
                new_row["date"] = f"{first_date.strftime('%m/%d/%Y')} - {last_date.strftime('%m/%d/%Y')}"
                new_row["program"] = legs[0]["program"]
                new_row["dep"] = legs[0]["dep"]
                new_row["arr"] = legs[-1]["arr"]
                new_row["req_ac"] = legs[0]["req_ac"]
                new_row["product"] = "Upcharge Option"
                new_row["product_desc"] = "Upcharge option: Add extra hours to meet the minimum overall average of 3 hrs/day."
                new_row["bt"] = f"{total_bt:.1f}"
                new_row["cont_hrs"] = ""
                new_row["waiver"] = {"ferry_in": "Y", "ferry_out": "Y"}
                new_row["discount"] = f"Upcharge (Add {missing:.1f} hrs)"
                new_row["basic_reason"] = (
                    f"Upcharge Option: Overall flight time is {total_bt:.1f} hrs over {num_days} days (averaging {avg_bt:.2f} hrs/day). "
                    f"To meet the minimum of 3 hrs/day (total required: {3*num_days:.1f} hrs), an additional {missing:.1f} hrs must be added. "
                    "This option is cost effective."
                )
                upcharge_rows.append(new_row)
    
    upcharge_table = []
    for row in upcharge_rows:
        discount_desc = f"Discount: {row['discount']}."
        upcharge_table.append({
            "REQUEST NUMBER": row["req_number"],
            "DATE": row["date"],
            "PROGRAM": row["program"],
            "DEP": row["dep"],
            "ARR": row["arr"],
            "REQ A/C": aircraft_mapping.get(row["req_ac"], row["req_ac"]),
            "PRODUCT": row["product"],
            "PRODUCT DESC": row["product_desc"],
            "BT": row["bt"],
            "WAIVER IN": row["waiver"]["ferry_in"],
            "WAIVER OUT": row["waiver"]["ferry_out"],
            "DISCOUNT": row["discount"],
            "REASON": row["basic_reason"] + " " + discount_desc
        })
    
    detailed_logic = "\n".join([f"- **{r['req_number']}**: {r['basic_reason']}" for r in final_processed])
    note = "\n**Note:** Tech stops are not included in the overall average block time calculation." if tech_stop_exists else ""
    reservation_summary = f"Detailed Flight Evaluation:\n{detailed_logic}{note}\n"
    
    if final_processed:
        total_flight_time = sum(float(row["bt"]) for row in final_processed if row["bt"])
        total_contract_hours = sum(float(row["cont_hrs"]) for row in final_processed if row.get("cont_hrs") and row["cont_hrs"].replace('.', '', 1).isdigit())
        dates_list = [parser.parse(row["date"]) for row in final_processed]
        first_date = min(dates_list)
        last_date = max(dates_list)
        days = (last_date - first_date).days + 1
        avg_ft = total_flight_time / days if days > 0 else total_flight_time
        summary_text = (
            f"Reservation spans from {first_date.strftime('%m/%d/%Y')} to {last_date.strftime('%m/%d/%Y')} "
            f"({days} days), total flight time: {total_flight_time} hrs, averaging {avg_ft:.2f} hrs per day."
        )
    else:
        summary_text = ""
    
    ai_rewrite = rewrite_text(reservation_summary)
    ai_conclusion = ai_rewrite + f"\nTotal Contract Hours available: {total_contract_hours:.2f} hrs."
    
    explanation = summary_text + "\n" + reservation_summary
    return explanation, ai_conclusion, table_data, upcharge_table

def main():
    st.title("Estimates Table Planning Processor")
    st.write(
        "Paste your table data (tab-separated) below and click **Process Table**. "
        "The header row is auto-detected. PROGRAM and PRODUCT default to **NetJets U.S.** if not provided."
    )
    
    # --- New Section: Show All Reservations ---
    st.markdown("## Show All Reservations")
    if st.button("Show All Reservations"):
        df_all = load_all_reservations()
        if "file_cached" not in st.session_state:
            st.session_state["file_cached"] = True
            st.info("File loaded from disk and cached.")
        else:
            st.info("File already cached.")
        st.write("Total rows loaded:", len(df_all))
        st.write("Column names:", df_all.columns.tolist())
        st.dataframe(df_all, height=500)
    
    # --- New Section: Load Reservation ---
    st.markdown("## Load Reservation")
    reservation_input = st.text_input("Enter Reservation Number", key="reservation_input")
    if st.button("Load Reservation"):
        if reservation_input:
            with st.spinner("Loading reservation..."):
                try:
                    res_df = load_reservation(reservation_input)
                    st.session_state.reservation_df = res_df
                    st.write("Loaded Reservation Data:")
                    st.dataframe(res_df, height=500)
                except Exception as e:
                    st.error(f"Error loading reservation: {e}")
        else:
            st.warning("Please enter a reservation number.")
    
    # --- Existing Input Areas ---
    discount_text = st.text_area("Discount Definitions", height=250, key=f"discount_input_{st.session_state.widget_key}",
                                  help="Enter discount rule examples (free text) as provided in IJet.")
    input_text = st.text_area("Input Table Data", height=250, key=f"input_text_{st.session_state.widget_key}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Process Table"):
            if input_text:
                expl, ai_conclusion, table_data, upcharge_table = process_reservations(input_text, discount_text, default_program="NetJets U.S.")
                if discount_text.strip():
                    expl += "\n\nDiscount Rules:\n" + discount_text
                st.session_state.explanation_text = expl
                st.session_state.ai_text = ai_conclusion
                df = pd.DataFrame(table_data)
                styled_df = df.style.set_properties(subset=["REASON"], **{'white-space': 'pre-wrap'})
                st.session_state.table_df = styled_df
                if upcharge_table:
                    up_df = pd.DataFrame(upcharge_table)
                    styled_up = up_df.style.set_properties(subset=["REASON"], **{'white-space': 'pre-wrap'})
                    st.session_state.upcharge_df = styled_up
                else:
                    st.session_state.upcharge_df = None
            else:
                st.warning("Please enter your input data.")
    with col2:
        if st.button("Reset"):
            st.session_state.widget_key += 1
            st.session_state.explanation_text = ""
            st.session_state.ai_text = ""
            st.session_state.table_df = None
            st.session_state.upcharge_df = None
            st.write("Inputs have been cleared. Please refresh the page if needed.")
    
    if st.session_state.table_df is not None:
        st.write("Row Details Table:")
        st.markdown(
            f'<div class="row-details-table">{st.session_state.table_df.to_html(escape=False)}</div>',
            unsafe_allow_html=True
        )
    if st.session_state.upcharge_df is not None:
        st.write("Upcharge Option Table (Additional Hours Required to Meet 3 hrs/day Rule):")
        st.markdown(
            f'<div class="row-details-table">{st.session_state.upcharge_df.to_html(escape=False)}</div>',
            unsafe_allow_html=True
        )
    
    st.markdown("### Detailed Reservation Explanation:")
    st.text_area("Explanation", value=st.session_state.explanation_text, height=500)
    st.markdown("### AI Conclusion:")
    st.text_area("Conclusion", value=st.session_state.ai_text, height=500)

if __name__ == "__main__":
    main()
