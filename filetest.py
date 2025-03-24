import os
import streamlit as st

def main():
    file_path = r"G:\Product Delivery\GITP\Reports\New\QUOTES_Workflow_Report.xlsx"
    st.write("Checking file path:", file_path)
    exists = os.path.exists(file_path)
    st.write("Does the file exist?", exists)
    if not exists:
        st.error("File not found! Please verify that the path is correct and accessible.")
    else:
        st.success("File found!")

if __name__ == "__main__":
    main()
