import os
import streamlit as st

def main():
    # Using backslashes in a raw string
    file_path_back = r"\\cmhfps03\DATA\FLIGHT CENTER\International Planning\Intl Estimates\Estimates Tool\Data\QUOTES_Workflow_Report.xlsx"
    # Using forward slashes
    file_path_forward = "//cmhfps03/DATA/FLIGHT CENTER/International Planning/Intl Estimates/Estimates Tool/Data/QUOTES_Workflow_Report.xlsx"
    
    st.write("Checking UNC file path (backslashes):", file_path_back)
    exists_back = os.path.exists(file_path_back)
    st.write("Exists (backslashes):", exists_back)
    
    st.write("Checking UNC file path (forward slashes):", file_path_forward)
    exists_forward = os.path.exists(file_path_forward)
    st.write("Exists (forward slashes):", exists_forward)
    
    if not exists_back and not exists_forward:
        st.error("File not found using either UNC format. Please verify the UNC path and permissions.")
    else:
        st.success("File found using UNC format!")

if __name__ == "__main__":
    main()
