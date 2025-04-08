import streamlit as st
import pandas as pd
from dateutil import parser
from collections import defaultdict
import datetime
import requests
import traceback
from st_aggrid import AgGrid, GridOptionsBuilder

def rewrite_text(text):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        # IMPORTANT: Store your API key securely (e.g., in an environment variable or st.secrets)
        "Authorization": "Bearer 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"
    }
    #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
    
    # Detailed system prompt providing context and decision-making logic.
    system_prompt = (
        "You are an expert in aviation reservations and cost calculations. "
        "Your task is to rewrite the following explanation text so that it is clear, detailed, and friendly for a non-technical audience. "
        "The explanation must cover the following decision-making steps:\n\n"
        "1. Endpoint Evaluation:\n"
        "- For NetJets U.S. reservations, an airport qualifies if it is in the CSA (defined as airports with ICAO codes starting with 'K' or from a designated list of Canadian CSA airports) or if it qualifies based on acceptable aircraft groups.\n"
        "- For NetJets Europe reservations, both departure and arrival endpoints must fall within the CSA as defined by our EU mapping.\n\n"
        "2. Tech Stops:\n"
        "- Tech stops are not included in the overall average block time calculation.\n\n"
        "3. Discount Application:\n"
        "- Discounts based on block time (OHF/trip time) are applied only for specific products (High Efficiency, Limited High Efficiency, Expanded High Efficiency, NJ Transatlantic, and NJ X-Country). \n"
        "- For other products, different discount rules apply that are not tied to block time thresholds. \n"
        "- For NetJets Europe reservations, no discount based on block time is applicable.\n\n"
        "4. Overall Waiver Decision:\n"
        "- The overall waiver decision is determined by evaluating whether the endpoints qualify (using CSA or additional criteria) and applying special rules for certain aircraft types (for example, Global 7500 has its own waiver logic).\n\n"
        "You dont have to do this by bullet points, make it a understandble text that shows that you are an expert explaining the mental process of the overall Estimates process."
        "DOnt summize when you have multiple legs."
        "Please rewrite the following explanation text in a clear, step-by-step manner that would help educate a team member about how the calculation works."
    )
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    response = requests.post(url, headers=headers, json=data, verify=False)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return f"Error rewriting text: {response.text}"


# -----------------------------------------------------------
# Function: load_reservations_from_upload
# Purpose: Load reservations from an uploaded Excel file into a DataFrame
# -----------------------------------------------------------
def load_reservations_from_upload(uploaded_file) -> pd.DataFrame:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()  # Clean column names
        st.write("Loaded Excel file successfully. Total rows:", len(df))
        return df
    except Exception as e:
        tb = traceback.format_exc()
        st.error(f"Error reading Excel file: {e}\n\n{tb}")
        return pd.DataFrame()

# -----------------------------------------------------------
# Function: load_reservation
# Purpose: Filter reservations DataFrame by a given reservation number and map to expected format
# -----------------------------------------------------------
def load_reservation(res_number: str, df: pd.DataFrame) -> pd.DataFrame:
    st.write("Preview of filtered rows:", 
             df[df["Reservation ID"].astype(str).str.contains(res_number, case=False, na=False)].head(5))
    filtered_df = df[df["Reservation ID"].astype(str).str.contains(res_number, case=False, na=False)]
    
    mapped = pd.DataFrame({
        "req_number": filtered_df.get("Request ID-Leg Order Nbr", pd.Series(["0"] * len(filtered_df))),
        "date": filtered_df.get("EDT Date L", pd.Series(["0"] * len(filtered_df))),
        "dep": filtered_df.get("DEP", pd.Series(["0"] * len(filtered_df))),
        "arr": filtered_df.get("ARR", pd.Series(["0"] * len(filtered_df))),
        "etd": filtered_df.get("ETD L", pd.Series(["0"] * len(filtered_df))),
        "eta": filtered_df.get("ETA L", pd.Series(["0"] * len(filtered_df))),
        "req_ac": filtered_df.get("REQ A/C", pd.Series(["0"] * len(filtered_df))),
        "bt": filtered_df.get("BT", pd.Series(["0"] * len(filtered_df))),
        "contracted_ac": filtered_df.get("GUARANTEED A/C", 
                                          filtered_df.get("REQ A/C", pd.Series(["0"] * len(filtered_df)))),
        "product": filtered_df.get("Contract Product Name", pd.Series(["0"] * len(filtered_df))),
        "program": filtered_df.get("Request Program", pd.Series(["NetJets U.S."] * len(filtered_df))),
        "cont_hrs": filtered_df.get("Overridden Trip Time", pd.Series(["0"] * len(filtered_df)))
    })
    return mapped

# -----------------------------------------------------------
# Session State Initialization and Page Configuration
# -----------------------------------------------------------
if "widget_key" not in st.session_state:
    st.session_state.widget_key = 0
if "explanation_text" not in st.session_state:
    st.session_state.explanation_text = ""
if "ai_text" not in st.session_state:
    st.session_state.ai_text = ""
if "table_df" not in st.session_state:
    st.session_state.table_df = None
if "upcharge_df" not in st.session_state:
    st.session_state.upcharge_df = None
if "reservation_df" not in st.session_state:
    st.session_state.reservation_df = None
if "all_reservations_df" not in st.session_state:
    st.session_state.all_reservations_df = pd.DataFrame()
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

st.set_page_config(layout="wide", page_title="Estimates Table Planning Processor")

# -----------------------------------------------------------
# Custom CSS Injection
# -----------------------------------------------------------
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] * { font-size: 14px !important; }

    /* Applies to all text areas */
    textarea[data-testid="stTextArea"] {
        font-size: 12px !important;
        
    }

    /* Applies to tables shown with st.dataframe */
    .stDataFrame table, .stDataFrame th, .stDataFrame td {
        font-size: 12px !important;
    }

    /* Applies to tables inside a div with class .row-details-table */
    .row-details-table table, .row-details-table th, .row-details-table td {
        font-size: 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# -----------------------------------------------------------
# Sidebar: Instructions and Product Explanations
# -----------------------------------------------------------
st.sidebar.header("Instructions")
st.sidebar.write(
    """
    **Overview:**
    
    This tool processes ferry waiver reservation data by applying six rules and product-specific discount logic.
    
    **File Upload & Filter:**
      1. Upload your reservations Excel file.
      2. View all reservations.
      3. Filter the reservations by a Reservation Number.
      4. Then load the filtered data into the Input Table Data area for quote processing.
    
    ## Global Service Area Zone – All Bombardier Global 7500 Owners and Leases

    - **Global Service Area Definition:**
      - Regardless of the requested and scheduled aircraft, qualify for a Global Service Area that is defined as the contiguous U.S., select cities in Canada, and all locations identified in Group III. *(This does not include countries listed in Group I or Group II.)*
      
    - **Ferry‑Free Travel:**
      - Travel between and within the Global Service Area is always ferry‑free.
      - Additionally, flights anywhere in the world are ferry‑free provided they meet the following requirements:  
        - Single flight begins and/or ends in the Global Service Area; or  
        - Multiple flights within one continuous trip itinerary meet the following requirements:  
          - Departure or final arrival location meets the requirements of a single flight *(flight begins or ends in the Global Service Area)*  
          - Entire trip is requested on the same aircraft  
          - Itinerary averages three or more occupied hours per day for the duration of the trip  
            - *Example: KTEB‑NTAA‑NFFN // both flights are over a 4‑day period, minimum of 12 hrs flight time required // Total estimated flight time: 16.6 hrs // Flight would be considered ferry‑free.*
      
    - **Note on NJE:**
      - When requesting NJE, the GSA no longer applies as this is now a cross‑program flight. Standard NJE ferry waiver rules apply. In many cases it is better for the Owner to stay with the GL7500 throughout, unless cabotage rules dictate otherwise, so be sure to look at both options when possible and offer the better of the two.

    ## NJA Ferry Waiver Zones (excluding GL7500 Owners)
    - See Ferry Waiver Program Maps below for details.
    - *Note: For non‑GL7500 Owners that request the GL7500, REQUIRES EXECUTIVE LEADERSHIP APPROVAL. Upgrade requests to the GL7500 should receive the same ferry waiver based on the GSA, but must be on the GL7500.*

    ## NJE Ferry Waiver Zones
    - See Ferry Waiver Program Brochure for details.

    ## 3 Hours per day rules
    - Must be one continuous trip. All airport codes must align throughout the legs so that one aircraft could do the entire trip without repositioning. Any break in airport codes breaks the continuous requirement.
    - All legs must be on the same requested aircraft type. Different contracts may be used throughout the trip; this does not impact this requirement—it is solely based on the requested aircraft type remaining the same.
    - All legs must be on the same operator. If one leg is required to be on a different operator due to regulatory requirements, this breaks the continuity requirement.
    - The minimum time of 3 hrs per day average is determined by counting days from the local ETD date of the first leg to the final leg’s local ETD date. This calculation is based solely on the local ETD date, regardless of time zone changes or crossing the International Date Line.

    ## Ferry Waiver Rules
    - **Within the CSA:**
      - Travel within the Collective Service Area (contiguous U.S. and select Canadian cities) is always ferry‑free.
    - **Between the CSA and Ferry Waiver Zones:**
      - To fly ferry‑free, your flight must be between the Collective Service Area and the ferry waiver zone that pertains to the aircraft you’ve requested and are scheduled on.
    - **Tech Stops:**
      - When tech stops are necessary, the ferry waiver is determined by the Owner‑requested origin and destination.
        - *Example: LDSP‑SUMU, with a required tech stop in TXKF. A Group III to Group I ferry waiver does not apply. The Owner would be required to pay positioning fees from CSA‑LDSP and from SUMU‑CSA.*
        - *Exception: If the tech stop is in the CSA, the ferry waiver can be applied. Example: GL6000, EGGW‑KEWR‑PHOG; tech stop is KEWR. In this case, because the tech stop is in the CSA, the ferry waiver would apply for both EGGW and PHOG, even though the flight was requested as being operated outside of the CSA. This same logic can be applied to flights on NJE if the tech stop is in the POA.*
    - **Passenger Drop‑Off/Pick‑Up Stops:**
      - For stops added solely for scheduled drop‑off or pick‑up (lasting less than 60 minutes), any potential positioning fees that might apply due to the stop may be waived.
    - **Multi‑Leg Reservations:**
      - A multi‑leg reservation may be eligible for ferry waiver provided the flight originates and terminates in the CSA (e.g., KBFI‑RJTT‑ZBAA‑RPLL‑PGUM‑KSFO).  
        - Travel to any location, regardless of zone; once the flight has left the CSA, international-to-international legs are permitted provided the reservation remains as one continuous trip and the average flight time of 3.0 hrs/day (or higher) is met. Tech stops that create domestic legs should also be included.
        - The required 3‑hour average is determined by counting the number of days from the local departure date (ETD) of the first leg to the local departure date of the final leg.
      - A multi‑leg reservation that "starts OR ends in the CSA" AND then "starts OR ends in the ferry waiver zone of the aircraft" (e.g., KLAX‑RJAA‑SAEZ‑MWCR‑MYNN or SAEZ‑MWCR‑RJAA‑KLAX) must remain as one continuous trip and meet the 3‑hour per day average.
    - **Revenue Flights Outside the CSA (Exceptions):**
      - For a single‑segment flight operating solely within Group 1 that does not meet the minimum 3.0 hrs of block time, positioning or upcharges are required. (Tech stops and passenger drop‑off/pick‑up stops of an hour or less can be combined to meet the 3‑hr minimum.) If the block time is less than 3 hrs, then the following must be presented to the Owner:
        - The Owner pays positioning fees to the non‑CSA location and then from the other non‑CSA location, provided both are in Group 1.
        - The Owner is up‑charged to meet the 3‑hour flight segment minimum, which applies to each qualifying leg.
      - For multiple‑segment flights, the Intra Group 1 options may be applicable, but it may be more cost‑effective to consider the STANDARD 3‑hr per day rules option versus the above intra Group 1 options; Standard meaning where positioning is to the initial location and from the final location, plus any upcharge to meet the 3 hrs per day.
        - **Exception:** For flights operating over several days (e.g., initial flight departs 14 Mar and the return flight departs 17 Mar, 4 days), the quote needs to be run two ways and the cheapest one is provided to the owner.
          1. First: With ferry fees.
          2. Second: If the total flight time between the flights averages out to 3 hrs/day, then ferry fees are waived (e.g., 4 days equals 12 hrs). If not, it may still be cheaper to charge for the additional hours to meet the 3 hrs/day versus the actual ferry costs.
          3. Depending on the situation, it is possible to use a combination of ferry fees and Time Below Minimums (particularly when the flight is operating completely outside of the CSA).
      - If ferry charges do apply, the ferry is planned to/from the closest CSA US Port of Entry.
    - **Demo Flights:**
      - Positioning fees are charged regardless of destination and aircraft type. (Hourly rate and fuel)
      - Ferry fees apply to/from the continental U.S.; CSA does not apply.
      - May be waived by Sales or OS.
    
    **Discounts & Upcharge:**
      1. Discounts are applied based on product type.
      2. Upcharge: If overall flight time is below 3 hrs/day, extra hours (if ≤ 10) are added.
    
    **Processing Table Data:**
      1. Paste your table data (tab-separated) for quote processing.
    """
)

product_explanations = {
    "Elite Card": "Includes flight hours, fuel, and FET; Standard PPD Ferry Rules apply; Eligible for travel on NJE.",
    "Expanded High Efficiency": (
        "Restricted to flights that depart/arrive in the NJUS CSA.\n"
        "Tech stops within NJA CSA count; flights entirely outside NJA CSA are not eligible.\n"
        "Discount tiers: 20% for 2.5-3.4 hrs, 30% for 3.5-4.4 hrs, 40% for 4.5+ hrs.\n"
        "Airport Pricing: if daily flight time begins AND ends at specific airports (KTEB, KHPN, KIAD, KPBI, KMDW, KDAL, KVNY, KSJC, KLAS, KSFO, KBOS, KAPF, KSDL, KPDK), discounts are 40%/60%/80%.\n"
        "Signature Series aircraft: EMB505S, CE680AS, EMB545MOD, CE-700, CL350S, CL650S, G450, GL5000S, GL5500, GL6000S, GL7500."
    ),
    "25-hr Lease (Premium Access)": "PPD restrictions; pays 1.25 PPD premium; eligible for ferry waiver to/from Group 1; not eligible for Group 2-4 (except G450).",
    "25-hr Specialty Lease (Premium Access)": "Same as above with specialty conditions.",
    "Limited High Efficiency": (
        "Discount applies with specified hours and aircraft type; first/last flight must start/end in NJUS CSA; at least 1 pax required.\n"
        "Discount tiers: 20% for 2.5-3.4 hrs, 30% for 3.5-4.4 hrs, 40% for 4.5+ hrs."
    ),
    "High Efficiency": (
        "Discount applies when flight is between NJA CSA and NJE CSA; at least 1 pax required; requested AC must match contracted AC.\n"
        "Tech stops within NJA CSA qualify; tech stops outside disqualify the leg.\n"
        "Global 6000: 40% discount for 5+ hr transatlantic flights between NJA CSA and NJE CSA A/B.\n"
        "Global 5000: 40% discount for 5+ hr transatlantic flights between NJA CSA and NJE CSA A/B.\n"
        "Longitude: 20% discount for 2.5-3.4 hrs, 30% for 3.5+ hrs (depart/arrive in NJA CSA).\n"
        "Challenger 350: 30% discount for 3.5+ hrs (depart/arrive in NJA CSA)."
    ),
    "Promo": "Promo details...",
    "Specialty": "Includes flight hours, fuel, and FET; Standard PPD Ferry Rules apply.",
    "Restricted Lease": "PPD restrictions; pays 1.25 PPD premium; eligible for ferry waiver to/from Group 1; not eligible for Group 2-4 (except G450).",
    "Interim Card": "Card hours for owners who have paid deposit on future share; same access as 25-hr lease; interim solution until lease/share is active.",
    "One Card": "Can only request up to CL650S; available on NJE up to a CL650S; Standard PPD Ferry Rules apply.",
    "NJ X-Country": "30% discount to OHF on Challenger 350 flights 3.5+ hrs requested, departing/arriving at NJA CSA.",
    "Interim Specialty Card": "Details for Interim Specialty Card...",
    "25-hr Specialty Lease": "OHF does not include fuel. Restrictions for flights with 3.5-hour minimum segment and specific aircraft requirements.",
    "Restricted Specialty Lease": "OHF does not include fuel. Restrictions for flights with 3.5-hour minimum segment and specific aircraft requirements.",
    "QS Executive": "Guaranteed upgrade to largest aircraft type owned by Corporate Account at interchange rate.",
    "100-Hour Card": "Includes flight hours, fuel, and FET; Do NOT charge PPD premium; Standard PPD Ferry Rules apply; PPD G450 Cards eligible for ferry waiver.",
    "NJ Transatlantic": "40% discount on Global 5000S/GL5500/6000S/7500 for 5+ hrs, departing/arriving at NJA CSA and NJE CSA A/B.",
    "50 Hour": "Same rules as the Standard Card; MUST check if fuel was prepaid; Standard PPD Ferry Rules apply.",
    "Classic": "Includes flight hours, fuel, and FET; International fees still apply; Standard PPD Ferry Rules apply.",
    "Restricted Specialty QC Executive Lease": "OHF does not include fuel. Restrictions for 3.5-hour minimum flight segments and specific aircraft requirements."
}

selected_product = st.sidebar.selectbox("Select a Product", list(product_explanations.keys()), key="unique_product_select")
exp = product_explanations[selected_product]
bullet_lines = "\n".join([f"- {line}" for line in exp.splitlines() if line.strip() != ""])
st.sidebar.markdown("**Product Explanation:**\n" + bullet_lines)

# -----------------------------------------------------------
# Region and Aircraft Mappings
# -----------------------------------------------------------
# EU Region Mapping (raw values)
region_mapping_eu = {
    "LO": "CSA", "EB": "CSA", "LK": "CSA", "LD": "CSA", "EK": "CSA", "EF": "CSA", "LF": "CSA", "ED": "CSA",
    "LG": "CSA", "LH": "CSA", "EI": "CSA", "LI": "CSA", "EL": "CSA", "LM": "CSA", "EH": "CSA", "EN": "CSA",
    "EP": "CSA", "LP": "CSA", "LZ": "CSA", "LJ": "CSA", "LE": "CSA", "ES": "CSA", "LS": "CSA", "EG": "CSA",
    "LA": "CSA", "LQ": "CSA", "LB": "CSA", "LC": "CSA", "EE": "CSA", "BI": "CSA", "BK": "CSA", "EV": "CSA",
    "EY": "CSA", "LW": "CSA", "LU": "CSA", "LY": "CSA", "GM": "CSA", "UU": "CSA", "LR": "CSA", "LL": "CSA",
    "HL": "CSA", "DT": "CSA", "LT": "CSA", "UK": "CSA",
    "UD": "FWZ1", "UB": "FWZ1", "HE": "FWZ1", "UG": "FWZ1",
    "OB": "FWZ2", "UA": "FWZ2", "OK": "FWZ2", "OO": "FWZ2", "OT": "FWZ2", "OE": "FWZ2", "OM": "FWZ2",
    "CY": "FWLH1A", "K": "FWLH1A",
    "MM": "FWLH1B", "TX": "FWLH1B", "CI": "FWLH1B",
    "PA": "FWLH2", "PH": "FWLH2", "SB": "FWLH2", "SA": "FWLH2", "SL": "FWLH2", "SC": "FWLH2",
    "SK": "FWLH2", "SE": "FWLH2", "SG": "FWLH2", "SO": "FWLH2", "SY": "FWLH2", "SP": "FWLH2",
    "SM": "FWLH2", "SU": "FWLH2"
}

# US Region Mapping
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
    "EY": "Group III", "LF": "Group III", "LG": "Group III", "LH": "Group III", "LI": "Group III","LE": "Group III",
    "LJ": "Group III", "LK": "Group III", "LL": "Group III", "LM": "Group III", "LO": "Group III",
    "LP": "Group III", "LQ": "Group III", "LR": "Group III", "LS": "Group III", "LT": "Group III",
    "LU": "Group III", "LW": "Group III", "LY": "Group III", "LZ": "Group III", "GM": "Group III",
    "SA": "Group IV", "SB": "Group IV", "SC": "Group IV", "SE": "Group IV", "SG": "Group IV",
    "SK": "Group IV", "SL": "Group IV", "SM": "Group IV", "SO": "Group IV", "SP": "Group IV",
    "SU": "Group IV", "SV": "Group IV", "SY": "Group IV", "ZB": "Group IV", "ZG": "Group IV",
    "ZH": "Group IV", "ZL": "Group IV", "ZS": "Group IV", "ZY": "Group IV", "VA": "Group IV",
    "VE": "Group IV", "VI": "Group IV", "VO": "Group IV"
}

# Aircraft Mapping
aircraft_mapping = {
    "EMB-505S": "Embraer Phenom 300S",
    "EMB-505E": "Embraer Phenom 300E",
    "CE-560XLS": "Cessna Citation XLS",
    "CE-560XLSA": "Cessna Citation XLS+",
    "CE-680": "Cessna Citation Sovereign",
    "CE-680AS": "Cessna Citation Latitude",
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
# Create a reverse mapping (full name -> code)
reverse_aircraft_mapping = {v.upper(): k for k, v in aircraft_mapping.items()}

# -----------------------------------------------------------
# Helper Functions for Region and Discount Eligibility
# -----------------------------------------------------------
def is_csa(icao: str) -> bool:
    """
    U.S. CSA check: determines if an airport is in the U.S. CSA based on ICAO code.
    """
    icao = icao.strip().upper()
    canadian_csa = {"CYHM", "CYOO", "CYSA", "CYYZ", "CYGK", "CYOW", "CYSN", "CYZD",
                    "CYHU", "CYPQ", "CYTZ", "CYZR", "CYKF", "CYQA", "CYUL", "CZBB",
                    "CYKZ", "CYQG", "CYVR", "CYMX", "CYQS", "CYXU"}
    return icao.startswith("K") or icao in canadian_csa

def is_csa_program(icao: str, program: str) -> bool:
    """
    Program-aware CSA check:
    - For NetJets Europe, use the EU mapping (via get_region).
    - For others, use the U.S.-based is_csa.
    """
    if program.strip().lower() == "netjets europe":
        return get_region(icao, program) == "CSA"
    else:
        return is_csa(icao)

def convert_eu_region(region: str) -> str:
    """
    Convert EU region raw codes to standardized group codes.
    """
    if region == "CSA":
        return "CSA"
    mapping = {
        "FWZ1": "Group I", 
        "FWZ2": "Group II", 
        "FWLH1A": "Group III", 
        "FWLH1B": "Group IV", 
        "FWLH2": "Group IV"
    }
    return mapping.get(region, region)

def get_region(icao: str, program: str) -> str:
    """
    Get the region for an airport based on its ICAO code and reservation program.
    Uses EU mapping if program is "NetJets Europe", else US mapping.
    """
    icao = icao.strip().upper()
    prefix = icao[:2]
    if program.strip().lower() == "netjets europe":
        region_raw = region_mapping_eu.get(prefix, "NO GROUP")
        return convert_eu_region(region_raw)
    else:
        return region_mapping_us.get(prefix, "NO GROUP")

def get_acceptable_region_groups(requested_ac: str) -> set:
    """
    Return a set of acceptable region groups for a given requested aircraft.
    """
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
        "GL5000S": "Group III",
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
        return {"Group I", "Group II", "Group III", "Group IV"}
    elif group == "GSA":
        return {"Group III"}
    return set()

def qualifies_for_fw(icao: str, requested_ac: str, program: str) -> bool:
    """
    Determine if an endpoint qualifies for a ferry waiver based on:
    - CSA membership (for both NJUS and NJE)
    - Group eligibility strictly tied to aircraft group
    """
    icao = icao.strip().upper()
    # First check if it qualifies as CSA (U.S. or EU)
    if is_csa_program(icao, program):
        return True

    # Get the region for the airport
    region = get_region(icao, program)

    # Hard fail if region is unknown
    if region == "NO GROUP":
        return False

    # Determine allowed ferry zones per aircraft group
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
        "GL5000S": "Group III",
        "GL5500": "Group III",
        "GL6000S": "Group IV",
        "GL6000": "Group IV",
        "GL7500": "GSA"
    }

    group = requested_ac_group.get(requested_ac, None)
    if group is None:
        return False  # Unknown aircraft group

    # Now match aircraft group to allowed zones
    if group == "Group I":
        return region == "Group I"
    elif group == "Group II":
        return region in {"Group I", "Group II"}
    elif group == "Group III":
        return region in {"Group I", "Group II", "Group III"}
    elif group == "Group IV":
        return region in {"Group I", "Group II", "Group III", "Group IV"}
        #return False
    elif group == "GSA":
        return region == "Group III"  # Applies to GL7500

    return False


def is_gsa(icao: str) -> bool:
    """
    Check if the airport qualifies as GSA (or is in the CSA).
    """
    icao = icao.strip().upper()
    if is_csa(icao):
        return True
    prefix = icao[:2]
    return region_mapping_us.get(prefix, "NO GROUP") == "Group III"

def is_nje_csa(icao: str) -> bool:
    """
    Check if an airport is within the NJE CSA.
    """
    icao = icao.strip().upper()
    prefix = icao[:2]
    return region_mapping_eu.get(prefix, "") == "CSA"

# -----------------------------------------------------------
# Discount Calculation and Explanation Functions
# -----------------------------------------------------------
def calculate_discount(row):
    """
    Calculate the discount for a reservation row based on product, aircraft, block time, and other rules.
    Only applicable for NetJets U.S. reservations.
    
    Steps:
      1. If the reservation is not NetJets U.S., return "0%".
      2. Normalize the requested aircraft code using a reverse mapping if needed.
      3. Extract product name (in lowercase) and block time (bt).
      4. Apply discount rules based on the product:
         - For "expanded high efficiency", check for pax count, valid aircraft type,
           and require that at least one endpoint is in CSA. Then, if the flight qualifies for
           airport pricing (both endpoints at certain airports), use one set of thresholds; otherwise, use another.
         - For "limited high efficiency" and "high efficiency", similar logic applies with different thresholds.
         - For NJ Transatlantic and NJ X-Country, check that the requested aircraft is in a set of valid types,
           validate endpoints using additional criteria, and then apply a fixed discount if the block time meets a threshold.
    """
    # Only U.S. reservations are eligible for these block time discounts.
    if row.get("program", "").strip().lower() != "netjets u.s.":
        return "0%"
    
    # Normalize the requested aircraft code.
    req_ac = row.get("req_ac", "").strip().upper()
    if req_ac not in aircraft_mapping and req_ac in reverse_aircraft_mapping:
        req_ac = reverse_aircraft_mapping[req_ac]
    
    product = row.get("product", "").strip().lower()
    contracted_ac = row.get("contracted_ac", "").strip().upper()
    
    # Parse block time; if parsing fails, use 0.
    try:
        bt = float(row.get("bt", "0"))
    except:
        bt = 0.0

    # For 25-hr Lease (Premium Access) there is no discount.
    if product == "25-hr lease (premium access)":
        return "0%"
    
  # Expanded High Efficiency:
    elif product == "expanded high efficiency":
        # Must have at least one pax.
        if "pax" in row and int(row["pax"]) < 1:
            return "0%"
        # Only eligible if the requested aircraft is in the signature series.
        signature_series = {"EMB-505S", "CE-680AS", "EMB545MOD", "CE-700", 
                            "CL-350S", "CL3500", "CL-650S", "G450", 
                            "GL5000S", "GL5500", "GL6000S", "GL7500"}
        if req_ac not in signature_series:
            return "0%"
        # At least one endpoint must qualify as CSA.
        if not (is_csa_program(row.get("dep", ""), row.get("program", "")) or 
                is_csa_program(row.get("arr", ""), row.get("program", ""))):
            return "0%"
        # Check if both endpoints are in the premium airport pricing list.
        airport_pricing_airports = {"KTEB", "KHPN", "KIAD", "KPBI", "KMDW", "KDAL",
                                    "KVNY", "KSJC", "KLAS", "KSFO", "KBOS", "KAPF",
                                    "KSDL", "KPDK"}
        dep = row.get("dep", "").strip().upper()
        arr = row.get("arr", "").strip().upper()
        airport_pricing = (dep in airport_pricing_airports and arr in airport_pricing_airports)
        # Apply discount thresholds based on the aggregated daily block time.
        if bt < 2.5:
            return "0%"
        elif 2.5 <= bt < 3.5:
            return "40%" if airport_pricing else "20%"
        elif 3.5 <= bt < 4.5:
            return "60%" if airport_pricing else "30%"
        elif bt >= 4.5:
            return "80%" if airport_pricing else "40%"
        else:
            return "0%"
    
    # --- Limited High Efficiency Rules ---
    elif product == "limited high efficiency":
        # The requested aircraft must match the contracted aircraft.
        if req_ac != contracted_ac:
            return "0%"
        if "pax" in row and int(row["pax"]) < 1:
            return "0%"
        signature_series = {"EMB-505S", "CE-680AS", "EMB545MOD", "CE-700",
                            "CL-350S", "CL3500", "CL-650S", "G450",
                            "GL5000S", "GL5500", "GL6000S", "GL7500"}
        if req_ac not in signature_series:
            return "0%"
        if bt < 2.5:
            return "0%"
        elif 2.5 <= bt < 3.5:
            return "20%"
        elif 3.5 <= bt < 4.5:
            return "30%"
        elif bt >= 4.5:
            return "40%"
        else:
            return "0%"
    
    # --- High Efficiency Rules ---
    elif product == "high efficiency":
        if req_ac != contracted_ac:
            return "0%"
        if "pax" in row and int(row["pax"]) < 1:
            return "0%"
        # Different aircraft types use different thresholds.
        if req_ac in {"GL6000S", "GL6000", "GL5000S", "GL5500"}:
            return "40%" if bt >= 5.0 else "0%"
        elif req_ac == "CE-700":
            if bt < 2.5:
                return "0%"
            elif 2.5 <= bt < 3.5:
                return "20%"
            elif bt >= 3.5:
                return "30%"
            else:
                return "0%"
        elif req_ac in {"CL-350S", "CL3500"}:
            return "30%" if bt >= 3.5 else "0%"
        else:
            return "0%"
    
    # --- NJ Transatlantic Rules ---
    elif product == "nj transatlantic":
        valid_types = {"GL5000S", "GL5500", "GL6000S", "GL7500"}
        if req_ac not in valid_types:
            return "0%"
        dep = row.get("dep", "").strip().upper()
        arr = row.get("arr", "").strip().upper()
        # Check endpoints using additional criteria.
        if not ((is_csa_program(dep, row.get("program", "")) and is_nje_csa(arr)) or 
                (is_csa_program(arr, row.get("program", "")) and is_nje_csa(dep))):
            return "0%"
        return "40%" if bt >= 5.0 else "0%"
    
    # --- NJ X-Country Rules ---
    elif product == "nj x-country":
        valid_types = {"CL-350S", "CL3500"}
        if req_ac not in valid_types:
            return "0%"
        dep = row.get("dep", "").strip().upper()
        arr = row.get("arr", "").strip().upper()
        if not (is_csa_program(dep, row.get("program", "")) and is_csa_program(arr, row.get("program", ""))):
            return "0%"
        return "30%" if bt >= 3.5 else "0%"
    
    # Default case: no discount
    return "0%"



def build_explanation(row, overall_message, overall_waiver_decision, req_ac, is_tech_stop=False):
    """
    Build a detailed explanation string for a flight leg.
    """
    program = row.get("program", "")
    dep = row["dep"].strip().upper()
    arr = row["arr"].strip().upper()
    dep_qual = "CSA" if is_csa_program(dep, program) else get_region(dep, program)
    arr_qual = "CSA" if is_csa_program(arr, program) else get_region(arr, program)
    bt_str = row.get("bt", "N/A")
    try:
        bt = float(bt_str)
    except:
        bt = 0.0
    product = row.get("product", "").strip()
    prod_desc = product_explanations.get(product, "No product info available")
    discount = row.get("discount", "0%")
    
    # Define products for which discount is based on block time
    discount_products = {"high efficiency", "limited high efficiency", "expanded high efficiency", "nj transatlantic", "nj x-country"}
    
    if discount != "0%":
        # Existing discount logic...
        if product.lower() == "limited high efficiency":
            if bt >= 4.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs exceeds the threshold of 4.5 hrs."
            elif 3.5 <= bt < 4.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs is more than 3.5 hrs but less than 4.5 hrs."
            elif 2.5 <= bt < 3.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs is more than 2.5 hrs but less than 3.5 hrs."
            else:
                discount_msg = ""
        elif product.lower() == "high efficiency":
            if req_ac in {"GL6000S", "GL6000", "GL5000S", "GL5500"} and bt >= 5.0:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs exceeds the threshold of 5.0 hrs."
            elif req_ac == "CE-700":
                if bt >= 3.5:
                    discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs exceeds the threshold of 3.5 hrs."
                elif 2.5 <= bt < 3.5:
                    discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs is more than 2.5 hrs but less than 3.5 hrs."
                else:
                    discount_msg = ""
            elif req_ac in {"CL-350S", "CL3500"} and bt >= 3.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs exceeds the threshold of 3.5 hrs."
            else:
                discount_msg = ""
        elif product.lower() == "expanded high efficiency":
            if bt >= 4.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs exceeds the threshold of 4.5 hrs."
            elif 3.5 <= bt < 4.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs is more than 3.5 hrs but less than 4.5 hrs."
            elif 2.5 <= bt < 3.5:
                discount_msg = f"A discount of {discount} was applied because the block time of {bt} hrs is more than 2.5 hrs but less than 3.5 hrs."
            else:
                discount_msg = ""
        elif product.lower() in {"nj transatlantic", "nj x-country"}:
            # You can similarly add conditions for these products if needed.
            discount_msg = ""
        else:
            discount_msg = ""
    else:
        # When discount is "0%", if the product is one of the discountable ones, mention threshold;
        # otherwise, simply note that no discount applies.
        if row.get("program", "").strip().lower() != "netjets u.s.":
            discount_msg = f"No discount is applicable for the {row.get('program')} program."
        elif product.lower() in discount_products:
            discount_msg = "No discount was applied because the block time did not meet the required threshold."
        else:
            discount_msg = "No discount is applicable for this product."
    
    tech_stop_note = "Note: This is a tech stop and is not included in the overall average block time calculation." if is_tech_stop else ""
    
    explanation = (
        f"Requested program: {program}. {overall_message} "
        f"(Overall waiver: {overall_waiver_decision}{', Ferry Fees are applicable' if overall_waiver_decision == 'N' else ''}). "
        f"Flight {row['req_number']}: Departure {dep} qualifies as {dep_qual}; Arrival {arr} qualifies as {arr_qual}. "
        f"Block time: {bt_str} hrs. Aircraft: {req_ac}. Product: {product}. "
        f"{tech_stop_note} {discount_msg}"
    ).strip()
    
    return explanation

# -----------------------------------------------------------
# Reservation Eligibility Rules Functions
# -----------------------------------------------------------
def rule_n4_eligible(legs, requested_ac: str):
    """
    Rule N4: Evaluate reservations originating and terminating in CSA.
    """
    sorted_legs = legs
    first_leg = sorted_legs[0]
    last_leg = sorted_legs[-1]
    if is_csa_program(first_leg["dep"], first_leg["program"]) and is_csa_program(last_leg["arr"], last_leg["program"]):
        return (True, "Reservation originates and terminates in CSA.")
    exit_date = None
    for leg in sorted_legs:
        if not is_csa_program(leg["dep"], leg["program"]):
            exit_date = parser.parse(leg["date"])
            break
    if exit_date is None:
        return (True, "Reservation remains in CSA.")
    return_date = None
    for leg in sorted_legs:
        leg_date = parser.parse(leg["date"])
        if leg_date > exit_date and is_csa_program(leg["dep"], leg["program"]):
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
    """
    Rule N5: Evaluate reservations with one endpoint in CSA.
    """
    program = legs[0].get("program", "NetJets U.S.")
    sorted_legs = legs
    first_leg = sorted_legs[0]
    last_leg = sorted_legs[-1]
    dep_ok = is_csa_program(first_leg["dep"], program) or qualifies_for_fw(first_leg["dep"], requested_ac, program)
    arr_ok = is_csa_program(last_leg["arr"], program) or qualifies_for_fw(last_leg["arr"], requested_ac, program)
    if not (is_csa_program(first_leg["dep"], program) or is_csa_program(last_leg["arr"], program)):
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
            "GL5000S": "Group III",
            "GL5500": "Group III",
            "GL6000S": "Group IV",
            "GL6000": "Group IV",
            "GL7500": "GSA"
        }
        req_group = requested_ac_group.get(requested_ac, None)
        reasons = []
        if not dep_ok:
            reasons.append(f"Departure endpoint does not qualify for the {requested_ac} Ferry Waiver Zone - Aircraft type {req_group}.")
        if not arr_ok:
            reasons.append(f"Arrival endpoint does not qualify for the {requested_ac} Ferry Waiver Zone - Aircraft type {req_group}.")
        return (False, " ".join(reasons))

def rule_n6_eligible(legs, requested_ac: str):
    """
    Rule N6: Evaluate reservations with both endpoints outside CSA.
    """
    program = legs[0].get("program", "NetJets U.S.")
    sorted_legs = legs
    first_leg = sorted_legs[0]
    last_leg = sorted_legs[-1]
    dep = first_leg["dep"].strip().upper()
    arr = last_leg["arr"].strip().upper()
    dep_region = get_region(dep, program)
    arr_region = get_region(arr, program)
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
            return (True, f"Reservation qualifies for Group I with {avg_bt:.2f} hrs/day over {num_days} days.") if avg_bt >= 3.0 else (False, f"Average block time {avg_bt:.2f} hrs/day is below 3 hrs for Group I flight.")
        else:
            return (False, "Endpoints are not both in Group I for a Group I flight.")
    elif req_group in {"Group III", "Group IV"}:
        if (dep_region in {"Group I", "Group III"}) and (arr_region in {"Group I", "Group III"}):
            return (True, f"Reservation qualifies for {req_group} with {avg_bt:.2f} hrs/day over {num_days} days.") if avg_bt >= 3.0 else (False, f"Average block time {avg_bt:.2f} hrs/day is below 3 hrs for {req_group} flight.")
        else:
            return (False, f"Endpoints do not meet required regions for {req_group} flight.")
    else:
        return (False, "Requested aircraft group not recognized for Rule n6.")

def determine_reservation_waiver(legs, requested_ac: str):
    """
    Determine overall waiver eligibility for a reservation based on its legs.
    Applies different logic for NetJets Europe versus U.S.
    """
    sorted_legs = legs
    first_leg = sorted_legs[0]
    last_leg = sorted_legs[-1]
    program = first_leg.get("program", "NetJets U.S.").strip().lower()
    
    if program == "netjets europe":
        # EU-specific logic: both endpoints must qualify as CSA via EU mapping.
        dep_region = get_region(first_leg["dep"], "NetJets Europe")
        arr_region = get_region(last_leg["arr"], "NetJets Europe")
        if dep_region == "CSA" and arr_region == "CSA":
            return ("Y", "Reservation qualifies for EU waiver (both endpoints in EU CSA).")
        else:
            return ("N", "Endpoints do not meet EU waiver criteria.")
    
    # U.S. logic:
    if requested_ac == "GL7500":
        dep_ok = is_gsa(first_leg["dep"]) or is_csa_program(first_leg["dep"], first_leg["program"])
        arr_ok = is_gsa(last_leg["arr"]) or is_csa_program(last_leg["arr"], last_leg["program"])
        if dep_ok or arr_ok:
            return ("Y", "Reservation qualifies for Global 7500 waiver (at least one endpoint in GSA).")
        else:
            return ("N", "Neither endpoint qualifies for Global 7500 GSA waiver.")
    else:
        dep_in = is_csa_program(first_leg["dep"], first_leg["program"])
        arr_in = is_csa_program(last_leg["arr"], last_leg["program"])
        if dep_in and arr_in:
            return ("Y", "Reservation is entirely domestic (both endpoints in CSA).")
        if dep_in != arr_in:
            eligible, message = rule_n5_eligible(sorted_legs, requested_ac)
            return ("Y" if eligible else "N", message)
        if not dep_in and not arr_in:
            eligible, message = rule_n6_eligible(sorted_legs, requested_ac)
            return ("Y" if eligible else "N", message)
    return ("N", "Unable to determine waiver eligibility.")

# -----------------------------------------------------------
# New Helper: Determine Continuity for Discount Calculation
# -----------------------------------------------------------

def is_continuous_for_discount(legs):
    if len(legs) <= 1:
        return True
    for idx in range(1, len(legs) - 1):
        tech_stop = legs[idx]
        if not (is_csa_program(tech_stop["dep"], tech_stop["program"]) and is_csa_program(tech_stop["arr"], tech_stop["program"])):
            return False
    return True

def is_continuous_reservation(legs):
    """
    Determines if a reservation is continuous based on sequential legs.
    A reservation is continuous if each leg's departure matches the previous leg's arrival.
    """
    if len(legs) <= 1:
        return True

    for i in range(1, len(legs)):
        prev_arr = legs[i - 1]["arr"].strip().upper()
        curr_dep = legs[i]["dep"].strip().upper()
        if prev_arr != curr_dep:
            return False
    return True

# -----------------------------------------------------------
# Main Processing Function: process_reservations
# Purpose: Process input reservation data and generate outputs
# -----------------------------------------------------------
def process_reservations(input_data: str, discount_def: str, default_program="NetJets U.S."):
    lines = input_data.splitlines()
    if not lines:
        return "", "", [], []
    if lines[0].strip().upper().startswith("REQUEST NUMBER"):
        lines.pop(0)

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
            "bt": parts[9],
            "contracted_ac": parts[11].strip() if len(parts) > 11 else parts[8],
            "product": parts[13].strip() if len(parts) > 13 else "",
            "program": parts[17].strip() if len(parts) > 17 else default_program,
            "cont_hrs": parts[29].strip() if len(parts) > 29 else "0"
        }
        rows.append(row_data)

    first_departure = parser.parse(rows[0]["date"])
    last_row = rows[-1]
    last_arrival = parser.parse(last_row["date"])
    total_duration_days = (last_arrival.date() - first_departure.date()).days + 1

#    total_duration_days = (last_arrival - first_departure).total_seconds() / 86400
    total_bt = sum(float(row["bt"]) for row in rows)
    avg_bt = total_bt / total_duration_days if total_duration_days > 0 else total_bt

    all_same_ac = all(row["req_ac"].upper() == rows[0]["req_ac"].upper() for row in rows)
    all_same_program = all(row["program"] == rows[0]["program"] for row in rows)
    continuous = is_continuous_reservation(rows)

    first_dep = rows[0]["dep"].strip().upper()
    last_arr = rows[-1]["arr"].strip().upper()
    first_dep_group = get_region(first_dep, rows[0]["program"])
    last_arr_group = get_region(last_arr, rows[0]["program"])
    zone_ok = (
        is_csa_program(first_dep, rows[0]["program"]) or is_csa_program(last_arr, rows[0]["program"])
        or (first_dep_group == "Group I" and last_arr_group == "Group I")
    )

    overall_eligible = avg_bt >= 3 and all_same_ac and all_same_program and continuous and zone_ok

    groups = {}
    for row in rows:
        base_req = row["req_number"].split("-")[0]
        groups.setdefault(base_req, []).append(row)

    final_processed = []

    for base_req, legs in groups.items():
        sorted_legs = legs

        for idx, row in enumerate(sorted_legs):
            req_ac = row["req_ac"].strip().upper()
            program = row["program"]

            suffix = row["req_number"].split("-")[-1]
            is_tech_stop = len(sorted_legs) > 1 and suffix.isdigit() and int(suffix) > 1

            dep = row["dep"].strip().upper()
            arr = row["arr"].strip().upper()
            dep_csa = is_csa_program(dep, program)
            arr_csa = is_csa_program(arr, program)
            dep_ok = qualifies_for_fw(dep, req_ac, program)
            arr_ok = qualifies_for_fw(arr, req_ac, program)

            if overall_eligible:
                st.toast("3Hrs Rule Compliant!", icon="✅")
                row["waiver"] = {"ferry_in": "Y", "ferry_out": "Y"}
                waiver_message = "✅ Reservation meets 3hrs compliance: average BT is above 3hrs/day, same aircraft type, same program, and continuous."
                waiver_decision = "Y"
            elif is_tech_stop:
                st.toast("Tech Stop!", icon="✅")
                prev_leg = sorted_legs[idx - 1] if idx > 0 else row
                next_leg = sorted_legs[idx + 1] if idx + 1 < len(sorted_legs) else row
                next_dep_ok = qualifies_for_fw(next_leg["dep"].strip().upper(), req_ac, program)

                row["waiver"] = {"ferry_in": "Y", "ferry_out": "Y" if next_dep_ok or arr_csa else "N"}
                prev_leg["waiver"] = prev_leg.get("waiver", {})
                prev_leg["waiver"]["ferry_out"] = "Y"

                waiver_message = "✅ Tech stop detected: Waiver IN forced to Y; OUT based on next leg's departure. Previous leg's OUT forced to Y."
                waiver_decision = "Y" if row["waiver"]["ferry_out"] == "Y" else "N"
            else:
                ferry_in = "Y" if dep_csa else ("Y" if dep_ok and arr_csa else "N")
                ferry_out = "Y" if arr_csa else ("Y" if arr_ok and dep_csa else "N")
                row["waiver"] = {"ferry_in": ferry_in, "ferry_out": ferry_out}
                st.toast("Not compliant with the 3Hrs Rule", icon="❌")
                waiver_message = "❌ Reservation does not meet 3hrs Rule compliance; waiver eligibility for multi-leg requests is determined by overall endpoints and ferry zone."
                waiver_decision = "N"

            discount = calculate_discount(row) if is_continuous_for_discount else "0%"
            row["discount"] = discount
            
            #flag_icon = "\U0001F1FA\U0001F1F8" if program.lower() == "netjets u.s." else "\U0001F1EA\U0001F1FA"
            bullet_reason = "\n".join([
                f"* 🗺️ Requested program: {program}.",
                f"* {waiver_message} (Overall waiver: {waiver_decision}).",
                f"* 📍Flight {row['req_number']}: Departure {dep} qualifies as {'CSA' if dep_csa else get_region(dep, program)}; Arrival {arr} qualifies as {'CSA' if arr_csa else get_region(arr, program)}.",
                f"* ⏱️Block time: {row['bt']} hrs.", 
                f"* ✈️Aircraft: {req_ac}.",
                f"* 📋Product: {row['product']}.",
            ])
            if discount != "0%":
                bullet_reason += f"💸 A discount of {discount} was applied because the block time of {row['bt']} hrs exceeds the threshold."

            row["basic_reason"] = bullet_reason
            row["product_desc"] = product_explanations.get(row["product"], "❌ No product info available")
            final_processed.append(row)

    table_data = []
    for row in final_processed:
        table_data.append({
            "REQUEST NUMBER": row["req_number"],
            "DATE": row["date"],
            "PROGRAM": row["program"],
            "DEP": row["dep"],
            "ARR": row["arr"],
            "REQUESTED A/C": aircraft_mapping.get(row["req_ac"], row["req_ac"]),
            "CONTRACT A/C": aircraft_mapping.get(row["contracted_ac"], row["contracted_ac"]),
            "PRODUCT": row["product"],
            "PRODUCT DESC": row["product_desc"],
            "BT": row["bt"],
            "WAIVER IN": row["waiver"]["ferry_in"],
            "WAIVER OUT": row["waiver"]["ferry_out"],
            "DISCOUNT": row["discount"],
            "REASON": row["basic_reason"],
        })

    upcharge_table = []
    if len(rows) > 1 and avg_bt < 3:
        required_total = 3 * total_duration_days
        missing = required_total - total_bt
        if 0 < missing <= 30:
            st.toast("Upcharge Needed!", icon="❌")
            upcharge_row = {
                "req_number": "Upcharge",
                "date": f"{first_departure.strftime('%m/%d/%Y %H:%M')} - {last_arrival.strftime('%m/%d/%Y %H:%M')}",
                "program": rows[0]["program"],
                "dep": first_dep,
                "arr": last_arr,
                "req_ac": rows[0]["req_ac"],
                "product": "Upcharge Option",
                "product_desc": "Upcharge option: Add extra hours to meet the minimum overall average of 3 hrs/day.",
                "bt": f"{total_bt:.1f}",
                "cont_hrs": "",
                "waiver": {"ferry_in": "Y", "ferry_out": "Y"},
                "discount": f"Upcharge (Add {missing:.1f} hrs)",
                "basic_reason": (
                    f"Upcharge Option: Overall flight time is {total_bt:.1f} hrs over {total_duration_days:.2f} days "
                    f"(avg {avg_bt:.2f} hrs/day). Add {missing:.1f} hrs to meet the 3 hrs/day minimum."
                )
            }
            upcharge_table.append({
                "REQUEST NUMBER": upcharge_row["req_number"],
                "DATE": upcharge_row["date"],
                "PROGRAM": upcharge_row["program"],
                "DEP": upcharge_row["dep"],
                "ARR": upcharge_row["arr"],
                "REQ A/C": aircraft_mapping.get(upcharge_row["req_ac"], upcharge_row["req_ac"]),
                "PRODUCT": upcharge_row["product"],
                "PRODUCT DESC": upcharge_row["product_desc"],
                "BT": upcharge_row["bt"],
                "WAIVER IN": upcharge_row["waiver"]["ferry_in"],
                "WAIVER OUT": upcharge_row["waiver"]["ferry_out"],
                "DISCOUNT": upcharge_row["discount"],
                "REASON": upcharge_row["basic_reason"] + f" Discount: {upcharge_row['discount']}."
            })
            st.toast("Upcharge Option Table Added!", icon="✅")

    detailed_logic = "\n".join([f"{r['basic_reason']}" for r in final_processed])
    note = "\n**Note:** Tech stops are not included in the overall average block time calculation." if any("tech stop" in r["basic_reason"].lower() for r in final_processed) else ""
    reservation_summary = f"Detailed Flight Evaluation:\n{detailed_logic}{note}\n"

    ai_rewrite = rewrite_text(reservation_summary)
    total_contract_hours = sum(float(row["cont_hrs"]) for row in final_processed if row.get("cont_hrs") and row["cont_hrs"].replace('.', '', 1).isdigit())
    ai_conclusion = ai_rewrite + f"\nTotal Contract Hours available: {total_contract_hours:.2f} hrs."
    explanation = reservation_summary + "\n" + ai_conclusion

    return explanation, ai_conclusion, table_data, upcharge_table

# --- Main Application Function: main ---
# Purpose: Set up UI sections for file upload, filtering, processing, and display of results
def main():
    st.title("Estimates Table Planning Processor")
    st.write(
        "Paste your table data (tab-separated) below and click **Process Table**. "
        "The header row is auto-detected. PROGRAM and PRODUCT default to **NetJets U.S.** if not provided."
    )

    # --- File Upload Section ---
    # --- File Upload Section ---
    st.markdown("## Upload Reservations Excel File")
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        df_all = load_reservations_from_upload(uploaded_file)
        st.session_state.all_reservations_df = df_all
        st.markdown("### All Reservations")

        # --- AgGrid Table Setup ---
        # Create AgGrid options
        gb = GridOptionsBuilder.from_dataframe(df_all)
        gb.configure_selection("single", use_checkbox=True)  # Allow selecting rows
        grid_options = gb.build()

        # Display the table with row selection
        response = AgGrid(df_all, gridOptions=grid_options, height=400)

        # --- Check if a row is selected and auto-paste reservation number ---
        selected_rows = response['selected_rows']  # Get the selected rows

        # Check if selected_rows is not None and not empty
        if selected_rows is not None and not selected_rows.empty:  # Use .empty to check if the DataFrame is empty
            selected_reservation = selected_rows.iloc[0].get('Reservation ID', '')  # Adjust this according to your column name
            st.session_state.selected_reservation_number = selected_reservation  # Save the selected reservation number

            # Auto-paste selected reservation number into the text input
            st.text_input("Selected Reservation Number", value=selected_reservation, disabled=True)
        else:
            st.warning("No reservation selected!")

    else:
        st.info("Awaiting file upload.")


    # --- Reservation Filter Section ---
    if "all_reservations_df" in st.session_state and not st.session_state.all_reservations_df.empty:
        st.markdown("## Filter Reservations by Reservation Number")
        res_number = st.text_input("Enter Reservation Number to Filter", value=st.session_state.selected_reservation_number if "selected_reservation_number" in st.session_state else "")
        
    if st.button("Filter Reservations", key="filter_reservations_button"):
        filtered_df = load_reservation(res_number, st.session_state.all_reservations_df)
        if filtered_df.empty:
            st.warning("No reservations found with that number.")
        else:
            # Save filtered data
            st.session_state.reservation_df = filtered_df

            # Step 1: Prepare the input table text
            temp = filtered_df.copy()
            final_df = pd.DataFrame({
                "REQUEST NUMBER": temp["req_number"],
                "DATE": temp["date"],
                "FERRY WAIVER IN": "",
                "DEP": temp["dep"],
                "ARR": temp["arr"],
                "FERRY WAIVER OUT": "",
                "ETD": temp["etd"],
                "ETA": temp["eta"],
                "REQ A/C": temp["req_ac"],
                "BT": temp["bt"],
                "BBT": "",
                "CONTRACTED A/C": temp["contracted_ac"],
                "CONTRACT": "",
                "PRODUCT": temp["product"],
                "FUEL PREPAID": "",
                "FLIGHT TYPE": "",
                "FLIGHT RULE": "",
                "PROGRAM": temp["program"],
                "PAX NBR": "",
                "I/C Rate": "",
                "NJE": "",
                "PPD": "",
                "PPD Ind": "",
                "Final Rate": "",
                "Initial Hrs": "",
                "Time Below": "",
                "Contract TB": "",
                "Excess Time 1": "",
                "Excess Time 2": "",
                "Cont Hrs": temp["cont_hrs"],
                "Total Hrs": "",
                "Hourly Rate": "",
                "Discount Rate": ""
            })
            table_text = final_df.to_csv(sep='\t', index=False)
            st.session_state.input_text = table_text

            # Step 2: Process the table
            #discount_text = ""
            discount_text = st.session_state.get("discount_input_" + str(st.session_state.widget_key), "")
            expl, ai_conclusion, table_data, upcharge_table = process_reservations(table_text, discount_text, default_program="NetJets U.S.")
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

            st.success("Reservation filtered, loaded, and processed!")


    # --- Load Filtered Data as Input ---
    #if st.session_state.get("reservation_df") is not None and not st.session_state.reservation_df.empty:
        #if st.button("Load Filtered Data as Input", key="load_filtered_data_button"):
        #    temp = st.session_state.reservation_df.copy()
        #    final_df = pd.DataFrame({
        #        "REQUEST NUMBER": temp["req_number"],
        #        "DATE": temp["date"],
        #        "FERRY WAIVER IN": "",
        #        "DEP": temp["dep"],
        #        "ARR": temp["arr"],
        #        "FERRY WAIVER OUT": "",
        #        "ETD": temp["etd"],
        #        "ETA": temp["eta"],
        #        "REQ A/C": temp["req_ac"],
        #        "BT": temp["bt"],
        #        "BBT": "",
        #        "CONTRACTED A/C": temp["contracted_ac"],
        #        "CONTRACT": "",
        #        "PRODUCT": temp["product"],
        #        "FUEL PREPAID": "",
        #        "FLIGHT TYPE": "",
        #        "FLIGHT RULE": "",
        #        "PROGRAM": temp["program"],
        #        "PAX NBR": "",
        #        "I/C Rate": "",
        #        "NJE": "",
        #        "PPD": "",
        #        "PPD Ind": "",
        #        "Final Rate": "",
        #        "Initial Hrs": "",
        #        "Time Below": "",
        #        "Contract TB": "",
        #        "Excess Time 1": "",
        #        "Excess Time 2": "",
        #        "Cont Hrs": temp["cont_hrs"],
        #        "Total Hrs": "",
        #        "Hourly Rate": "",
        #        "Discount Rate": ""
        #    })
        #    table_text = final_df.to_csv(sep='\t', index=False)
        #    st.session_state.input_text = table_text
        #    st.success("Filtered data loaded into Input Table Data.")
        #    try:
        #        st.experimental_rerun()
        #    except AttributeError:
        #        st.warning("Your Streamlit version does not support experimental_rerun. Please refresh manually.")


    # --- Input Areas for Table Processing ---
    discount_text = ""
    #discount_text = st.text_area("Discount Definitions(Can be pasted from Ijet)", height=100, key=f"discount_input_{st.session_state.widget_key}",
    #                            help="Enter discount rule examples (free text) as provided in IJet.")
    input_text = st.text_area(
        "Input Table Data (Can be pasted from The Excel Estimates Tool)",
        value=st.session_state.input_text,
        height=250,
        key=f"input_text_{st.session_state.widget_key}"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Process Table", key="process_table_button"):
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
        if st.button("Reset", key="reset_button"):
            st.session_state.widget_key += 1
            st.session_state.input_text = ""          # Clear the input table data
            st.session_state.explanation_text = ""     # Clear the explanation text
            st.session_state.ai_text = ""              # Clear the AI conclusion text
            st.session_state.table_df = None           # Clear the computed table
            st.session_state.upcharge_df = None        # Clear the upcharge table
            st.write("Input table data and computed results have been cleared.")

    
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
    #st.text_area("Explanation", value=st.session_state.explanation_text, height=70)
    #st.markdown("### AI Conclusion:")
    st.text_area("Conclusion", value=st.session_state.ai_text, height=800)

if __name__ == "__main__":
    main()