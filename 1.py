import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import urllib.parse
import webbrowser

# Set page config for dark theme
st.set_page_config(
    page_title="فرسانا يامحمد",
    page_icon="😁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply dark theme and mobile optimization
st.markdown("""
    <style>
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        .stButton>button {
            background-color: #262730;
            color: #FAFAFA;
            width: 100%;
            padding: 1rem;
            font-size: 1.2rem;
        }
        .stDateInput>div>div {
            background-color: #262730;
            color: #FAFAFA;
        }
        /* Mobile optimization */
        @media (max-width: 768px) {
            .stApp {
                padding: 1rem 0.5rem;
            }
            .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Constants
SHEET_ID = '1fnqyVMhbiAyG7d2lU4ewJtmGjzqSdEg_9ysvK9-AkKE'

@st.cache_data(ttl=300)
def load_data():
    try:
        url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'
        df = pd.read_csv(url)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def format_message(filtered_df):
    # Separate invoices and collections
    invoices = filtered_df[filtered_df['رقم الفاتورة'].notna()]
    collections = filtered_df[filtered_df['رقم السند '].notna()]
    
    # Calculate totals
    total_invoices = invoices['مبلغ الفاتورة'].sum()
    total_collections = collections['مبلغ الفاتورة'].sum()
    
    # Format the message
    message = "تقرير اليوم:\n\n"
    
    # Add transactions
    for _, row in filtered_df.iterrows():
        message += f"كود العميل: {row['كود العميل']}\n"
        if pd.notna(row['رقم الفاتورة']):
            message += f"رقم الفاتورة: {row['رقم الفاتورة']}\n"
        if pd.notna(row['رقم السند ']):
            message += f"رقم التحصيل: {row['رقم السند ']}\n"
        message += f"تاريخ الفاتورة: {row['تاريخ الفاتورة']}\n"
        message += f"المبلغ: {row['مبلغ الفاتورة']}\n"
        if pd.notna(row['نوع التحصيل ']):
            message += f"نوع التحصيل: {row['نوع التحصيل ']}\n"
        message += "-------------------\n"
    
    # Add totals
    message += f"\nإجمالي الفواتير: {total_invoices:.2f}\n"
    message += f"إجمالي التحصيل: {total_collections:.2f}\n"
    
    return message

def main():
    st.title("")
    
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Date selector with larger touch target
    selected_date = st.date_input(
        "اختر التاريخ",
        datetime.now(pytz.timezone('Asia/Riyadh')).date(),
        key="date_picker"
    )
    
    # Filter data for selected date
    filtered_df = df[df['Timestamp'].dt.date == selected_date]
    
    if not filtered_df.empty:
        # Calculate totals based on invoice/collection numbers
        invoices = filtered_df[filtered_df['رقم الفاتورة'].notna()]
        collections = filtered_df[filtered_df['رقم السند '].notna()]
        
        total_invoices = invoices['مبلغ الفاتورة'].sum()
        total_collections = collections['مبلغ الفاتورة'].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("إجمالي الفواتير", f"{total_invoices:.2f}")
        with col2:
            st.metric("إجمالي التحصيل", f"{total_collections:.2f}")
        
        # WhatsApp sharing button
        if st.button("مشاركة عبر واتساب"):
            message = format_message(filtered_df)
            whatsapp_url = f"whatsapp://send?text={urllib.parse.quote(message)}"
            try:
                webbrowser.open(whatsapp_url)
                st.success("جاري الفتح في واتساب...")
            except Exception as e:
                st.error("حدث خطأ في فتح واتساب. يرجى المحاولة مرة أخرى.")
    else:
        st.info("لا توجد عمليات في التاريخ المحدد")

if __name__ == "__main__":
    main()