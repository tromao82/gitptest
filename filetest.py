import streamlit as st
import pandas as pd

def main():
    st.title("Excel File Uploader and Viewer")
    st.write("Please upload your Excel file.")

    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("File successfully loaded!")
            st.write("Total rows:", len(df))
            st.write("Columns:", df.columns.tolist())
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")
    else:
        st.info("Awaiting file upload.")

if __name__ == "__main__":
    main()
