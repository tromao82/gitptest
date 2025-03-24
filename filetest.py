import os
import streamlit as st

def main():
    # Check the UNC directory first
    dir_path = r"\\cmhfps03\DATA"
    st.write("Checking if UNC directory exists:", dir_path)
    dir_exists = os.path.exists(dir_path)
    st.write("Directory exists?", dir_exists)
    
    # Now check the full file path using UNC format (with backslashes)
    file_path = r"\\cmhfps03\DATA\FLIGHT CENTER\International Planning\Intl Estimates\Estimates Tool\Data\QUOTES_Workflow_Report.xlsx"
    st.write("Checking UNC file path (backslashes):", file_path)
    file_exists = os.path.exists(file_path)
    st.write("File exists?", file_exists)
    
    if not file_exists:
        st.error("File not found using UNC path! Please verify the UNC path and that you have permissions to access it.")
    else:
        st.success("File found using UNC path!")
    
if __name__ == "__main__":
    main()
