import streamlit as st
import math

st.set_page_config(layout="wide")

# Set Times New Roman for textarea
st.markdown(
    """
    <style>
    textarea {
        font-family: "Times New Roman", Times, serif !important;
        font-size: 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Configuration ---
ac_fuel_constants = {
    "C560": 300,
    "C5EP": 300,
    "NJP3": 450,
    "C5XL": 300,
    "C5XS": 600,
    "C680": 600,
    "CITL": 650,
    "NJCL": 700,
    "CL35": 750,
    "C605": 750,
    "GL55": 1100,
    "GL5T": 1250,
    "GL6T": 1250,
    "GL75": 1250
}

# Full list of Union airports based on the ReFuelEU scope (2025)
union_airports = {
    "LOWG", "LOWI", "LOWS", "LOWW", "EBBR", "EBCI", "EBLG", "LBBG", "LBSF", "LBWN", "LCLK", "LCPH",
    "LKPR", "EDJA", "EDDB", "EDDW", "EDDK", "EDLW", "EDDC", "EDDL", "EDDF", "EDFH", "EDDH", "EDDV",
    "EDSB", "EDDP", "EDDM", "EDDG", "EDLP", "EDLV", "EDDN", "EDDS", "EKYT", "EKBI", "EKCH", "EETN",
    "LGAV", "LGSA", "LGIR", "LGKF", "LGKR", "LGKO", "LGMK", "LGPZ", "LGRP", "LGSR", "LGTS", "LGZA",
    "LEAL", "LEAM", "LEAS", "LEBL", "LEBB", "LEGE", "LEGR", "LEIB", "LEJR", "LECO", "LEMD", "LEMG",
    "LEMH", "LEMI", "LEPA", "LERS", "LEXJ", "LEST", "LEZL", "LEVC", "LEVX", "LEZG", "EFHK", "EFRO",
    "LFKJ", "LFSB", "LFKB", "LFOB", "LFRB", "LFBZ", "LFBD", "LFKF", "LFQQ", "LFLL", "LFML", "LFMT",
    "LFRS", "LFMN", "LFPO", "LFPB", "LFPG", "LFST", "LFBO", "LDDU", "LDSP", "LDZD", "LDZA", "LHBP",
    "EICK", "EIDW", "EIKN", "EINN", "LIEA", "LIBD", "LIME", "LIPE", "LIBR", "LIEE", "LICC", "LIRQ",
    "LIMJ", "LICA", "LIML", "LIMC", "LIRN", "LIEO", "LICJ", "LIBP", "LIRP", "LIRA", "LIRF", "LIMF",
    "LICT", "LIPH", "LIPQ", "LIPZ", "LIPX", "EYKA", "EYVI", "ELLX", "EVRA", "LMML", "EHAM", "EHEH",
    "EHRD", "EPGD", "EPKT", "EPKK", "EPWA", "EPPO", "EPRZ", "EPMO", "EPWR", "LPFR", "LPPT", "LPPR",
    "LROP", "LRCL", "LRIA", "LRTR", "ESGG", "ESPA", "ESMS", "ESSA", "ESSB", "LJLJ", "LZIB"
}

# --- Title & Sidebar ---
st.title("Fuel Policy Calculator (Flight Plan Parsing)")

st.sidebar.title("Fuel Policy Descriptions")

st.sidebar.markdown("""
## ✈️ RefuelEU Aviation Regulation

### Applicability
- Applies if **either the departure or arrival airport** is located in the Union.

### Calculation
- **RefuelEU Uplift = 0.9 × (Fuel for Destination + Taxi Fuel)**
- If this is **less than the FOM minimum**, then uplift must meet **FOM minimum**
- **Total Fuel Required = max(FOB + Uplift, MIN + TXO + FOM - FOB)** → rounded to the nearest hundred

### Purpose
- Prevent tankering
- Promote sustainable uplift practices from Union airports

---

## 📘 Flight Operations Manual 2.4.7 – Minimum Takeoff Fuel Requirements

### Applicability
- Applies regardless of airports, it's NetJets Fuel Policy.

### Calculation
- **FOM Uplift = max(10% of Fuel for Destination, 30-Minute Fuel Constant)**
- **Total Fuel Required = MIN + TXO + FOM - FOB** → rounded to the nearest hundred

### Purpose
- Prevent overfueling into Union airports
- Ensure minimum fuel reserves are loaded when RefuelEU is not applicable
""")

# --- Column Layout ---
col1, col2 = st.columns([1, 1.3])

with col1:
    fuel_onboard = st.number_input("Fuel On Board (FOB) in lbs", min_value=0, value=2500, step=100)
    flight_plan = st.text_area("Flight Plan Input", height=800)

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # This adds vertical space
    if st.button("Calculate Fuel Requirements"):
        st.markdown("<br>", unsafe_allow_html=True)  # This adds vertical space
        def parse_flight_plan(text):
            result = {}
            lines = text.strip().splitlines()
            for line in lines:
                if "PLAN" in line:
                    tokens = line.split()
                    if len(tokens) >= 7:
                        result["dep_icao"] = tokens[3].upper()
                        result["arr_icao"] = tokens[5].upper()
                        result["ac_type"] = tokens[6].upper()
                    break
            for line in lines:
                if line.startswith("POA"):
                    try:
                        result["fuel_dest"] = int(line.split()[2])
                    except: result["fuel_dest"] = 0
                if line.startswith("TXO"):
                    try:
                        result["taxi_fuel"] = int(line.split()[1])
                    except: result["taxi_fuel"] = 0
                if line.startswith("MIN"):
                    try:
                        result["min_fuel"] = int(line.split()[1])
                    except: result["min_fuel"] = 0
            return result

        parsed = parse_flight_plan(flight_plan)
        ac_type = parsed.get("ac_type", "")
        extra_30min = ac_fuel_constants.get(ac_type, 300)

        if parsed:
            st.write("**Departure ICAO:**", parsed.get("dep_icao", "N/A"), "-", "Union" if parsed.get("dep_icao", "") in union_airports else "Not Union")
            st.write("**Arrival ICAO:**", parsed.get("arr_icao", "N/A"), "-", "Union" if parsed.get("arr_icao", "") in union_airports else "Not Union")
            st.write("**Aircraft ICAO Type:**", parsed.get("ac_type", "N/A"))
            st.write("**Fuel for Destination:**", parsed.get("fuel_dest", 0), "lbs")
            st.write("**Taxi Fuel:**", parsed.get("taxi_fuel", 0), "lbs")
            st.write("**MIN Fuel (from Flight Plan):**", parsed.get("min_fuel", 0), "lbs")

        dep = parsed.get("dep_icao", "").upper()
        arr = parsed.get("arr_icao", "").upper()
        dest = parsed.get("fuel_dest", 0)
        taxi = parsed.get("taxi_fuel", 0)
        min_fuel = parsed.get("min_fuel", 0)

        fom = max(0.1 * dest, extra_30min)
        refueleu = 0.9 * (dest + taxi)
        refueleu_applies = dep in union_airports or arr in union_airports

        st.subheader("Calculation Results")

        if refueleu_applies:
            final_uplift = max(refueleu, fom)
            total_required = max(fuel_onboard + final_uplift, min_fuel + taxi + fom - fuel_onboard)
            total_required_rounded = int(math.ceil(total_required / 100.0)) * 100
            flight_plan_TOT = fuel_onboard + total_required_rounded
            fom247 = min_fuel + taxi + fom
            fom247 = int(math.ceil(fom247 / 100.0)) * 100
            st.write(f"**RefuelEU Value:** 90% × ({dest} + {taxi}) = {refueleu:.0f} lbs")
            st.write(f"**FOM Value:** max(10% of {dest}, 30' {ac_type} {extra_30min}) = {fom:.0f} lbs")
            st.write(f"**FOB:** {fuel_onboard} lbs")
            st.write(f"**Total Fuel Required for compliance Max(FOB+RefuelEU Fuel,MIN + TXO + FOM - FOB)**")
            st.write(f"**Total Fuel Required for compliance** Max({fuel_onboard} + {final_uplift:.0f}, {min_fuel} + {taxi} + {fom:.0f} - {fuel_onboard}) = {total_required_rounded} lbs")
            st.write(f"**Flight Plan TOT:** {total_required_rounded} lbs")
            st.success("**Policy Used:** RefuelEU (adjusted to meet FOM 2.4.7)")
            if dep in union_airports:
                st.warning(f"**If not able to refuel min {refueleu:.0f} lbs (TOT {flight_plan_TOT} lbs), add note on Flight Plan: Unable to comply with RefuelEU due to XXXX**")
            st.warning(f"**If not able to comply with {fom:.0f} lbs XTR (TOT {fom247:.0f} lbs), add Enroute Alternate and Flight Plan note: Enroute alternate due to FOM 2.4.7 .**")

        else:
            required_total = min_fuel + taxi + fom - fuel_onboard
            required_total_rounded = int(math.ceil(required_total / 100.0)) * 100
            flight_plan_TOT = fuel_onboard + required_total_rounded
            st.write(f"**FOM Value:** max(10% of {dest}, 30' {ac_type} {extra_30min}) = {fom:.0f} lbs")
            st.warning("**Flight is not eligible for RefuelEU.**")
            st.write(f"**FOB:** {fuel_onboard} lbs")
            st.write(f"**Total Fuel Required for compliance(MIN + TXO + FOM - FOB):** {min_fuel} + {taxi} + {fom:.0f} - {fuel_onboard} = {required_total_rounded} lbs")
            st.write(f"**Flight Plan TOT:** {fuel_onboard} + {required_total_rounded} =  {flight_plan_TOT} lbs")
            st.success("**Policy Used:** FOM 2.4.7")
            st.warning(f"**If not able to comply with {fom:.0f} lbs XTR (TOT {flight_plan_TOT} lbs ), add Enroute Alternate and Flight Plan note: Enroute alternate due to FOM 2.4.7 .**")
