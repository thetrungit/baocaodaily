import os
import json
import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials  

# ✅ Kết nối Google Sheets qua biến môi trường
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

gc = get_gspread_client()
sheet_id = "1NNwDEmiF7wIOLsZVQvL0Ae84lNvsFd5B9uJ0yeD8Hf4"
spreadsheet = gc.open_by_key(sheet_id)

# ✅ Hàm đảm bảo dòng tiêu đề có tồn tại và hợp lệ
def ensure_headers(ws, expected_headers=["Họ và tên", "Ngày", "Ghi chú"]):
    try:
        header = ws.row_values(1)
        if len(header) < len(expected_headers) or all(cell.strip() == "" for cell in header):
            ws.insert_row(expected_headers, index=1)
    except Exception as e:
        st.error(f"Lỗi kiểm tra header: {e}")

# Giao diện chính
st.title("📋 Hệ thống Quản lý Báo cáo Y tế")
menu = st.sidebar.radio("Chức năng", ["Nhập liệu", "Xem báo cáo"])

sheet_names = [ws.title for ws in spreadsheet.worksheets()]

if menu == "Nhập liệu":
    st.header("➕ Nhập dữ liệu")
    selected_sheet = st.selectbox("Chọn Khoa (sheet)", sheet_names)
    ws = spreadsheet.worksheet(selected_sheet)
    ensure_headers(ws)

    # Nhập liệu
    hoten = st.text_input("Họ và tên")
    ngay = st.date_input("Ngày")
    ghichu = st.text_input("Ghi chú")

    if st.button("➕ Thêm"):
        ws.append_row([hoten, ngay.strftime("%Y-%m-%d"), ghichu])
        st.success("✅ Đã thêm dòng mới!")

    df = pd.DataFrame(ws.get_all_records())
    st.write("📄 Dữ liệu hiện có", df)

    if not df.empty:
        selected_index = st.number_input("Chọn dòng để sửa/xoá (bắt đầu từ 1)", min_value=1, max_value=len(df), step=1)

        if st.button("✏️ Sửa"):
            ws.update(f"A{selected_index+1}", [[hoten, ngay.strftime("%Y-%m-%d"), ghichu]])
            st.success("✅ Đã sửa!")

        if st.button("❌ Xoá"):
            ws.delete_rows(selected_index + 1)
            st.success("✅ Đã xoá!")

elif menu == "Xem báo cáo":
    st.header("📊 Báo cáo theo thời gian")
    selected_sheet = st.selectbox("Chọn Khoa (sheet)", sheet_names)
    ws = spreadsheet.worksheet(selected_sheet)
    ensure_headers(ws)

    df = pd.DataFrame(ws.get_all_records())

    if "Ngày" not in df.columns:
        st.warning("⚠️ Sheet không có cột 'Ngày'.")
    else:
        df["Ngày"] = pd.to_datetime(df["Ngày"], errors='coerce')

        from_date = st.date_input("Từ ngày", value=datetime(2024, 1, 1))
        to_date = st.date_input("Đến ngày", value=datetime.today())

        mask = (df["Ngày"] >= from_date) & (df["Ngày"] <= to_date)
        filtered_df = df.loc[mask]

        st.success(f"📆 Tổng số dòng: {len(filtered_df)}")
        st.dataframe(filtered_df)
