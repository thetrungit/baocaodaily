import json, os
creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Kết nối Google Sheets
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    return gspread.authorize(creds)

gc = get_gspread_client()
sheet_id = "1kJc1rpJ0xdVBEdAQBzYOJYb5Gi9B2fyy"
spreadsheet = gc.open_by_key(sheet_id)

# Trang chính
st.title("📋 Hệ thống Quản lý Báo cáo Y tế")

menu = st.sidebar.radio("Chức năng", ["Nhập liệu", "Xem báo cáo"])

sheet_names = [ws.title for ws in spreadsheet.worksheets()]

if menu == "Nhập liệu":
    st.header("➕ Nhập dữ liệu")

    selected_sheet = st.selectbox("Chọn Khoa (sheet)", sheet_names)
    ws = spreadsheet.worksheet(selected_sheet)

    # Nhập liệu
    hoten = st.text_input("Họ và tên")
    ngay = st.date_input("Ngày")
    ghichu = st.text_input("Ghi chú")

    # Xử lý nút
    if st.button("➕ Thêm"):
        ws.append_row([hoten, ngay.strftime("%Y-%m-%d"), ghichu])
        st.success("Đã thêm dòng mới!")

    # Xem bảng hiện tại để sửa/xoá
    df = pd.DataFrame(ws.get_all_records())
    st.write("📄 Dữ liệu hiện có", df)

    selected_index = st.number_input("Chọn dòng để sửa/xoá (bắt đầu từ 1)", min_value=1, max_value=len(df), step=1)

    if st.button("✏️ Sửa"):
        ws.update(f"A{selected_index+1}", [[hoten, ngay.strftime("%Y-%m-%d"), ghichu]])
        st.success("Đã sửa!")

    if st.button("❌ Xoá"):
        ws.delete_rows(selected_index + 1)
        st.success("Đã xoá!")

elif menu == "Xem báo cáo":
    st.header("📊 Báo cáo theo thời gian")

    selected_sheet = st.selectbox("Chọn Khoa (sheet)", sheet_names)
    ws = spreadsheet.worksheet(selected_sheet)
    df = pd.DataFrame(ws.get_all_records())

    if "Ngày" not in df.columns:
        st.warning("Không có cột 'Ngày' trong sheet.")
    else:
        df["Ngày"] = pd.to_datetime(df["Ngày"], errors='coerce')

        from_date = st.date_input("Từ ngày", value=datetime(2024, 1, 1))
        to_date = st.date_input("Đến ngày", value=datetime.today())

        mask = (df["Ngày"] >= pd.to_datetime(from_date)) & (df["Ngày"] <= pd.to_datetime(to_date))
        filtered_df = df.loc[mask]

        st.success(f"📆 Tổng số dòng: {len(filtered_df)}")
        st.dataframe(filtered_df)

