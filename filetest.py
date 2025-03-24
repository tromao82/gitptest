import os
import streamlit as st

def main():
    # Replace with the correct UNC path. For example, if G: maps to \\cmhfps03\Reports, update accordingly:
    unc_path = r"\\cmhfps03\DATA\FLIGHT CENTER\International Planning\Intl Estimates\Estimates Tool\Data\QUOTES_Workflow_Report.xlsx"
    st.write("Checking UNC file path:", unc_path)
    exists = os.path.exists(unc_path)
    st.write("Does the file exist?", exists)
    if not exists:
        st.error("File not found using UNC path! Please verify that the UNC path is correct and accessible.")
    else:
        st.success("File found using UNC path!")
    
if __name__ == "__main__":
    main()
