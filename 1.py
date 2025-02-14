import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import urllib.parse
import numpy as np

# Set page config for dark theme
st.set_page_config(
    page_title="",
    page_icon="",
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
        /* Hide streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Constants
SHEET_ID = '1fnqyVMhbiAyG7d2lU4ewJtmGjzqSdEg_9ysvK9-AkKE'
TIMEZONE = pytz.timezone('Asia/Riyadh')

def safe_int_convert(value):
    try:
        if pd.isna(value):
            return "غير متوفر"
        return str(int(float(value)))
    except (ValueError, TypeError):
        return str(value)

@st.cache_data(ttl=300)
def load_data():
    try:
        url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'
        df = pd.read_csv(url)
        
        # Convert Timestamp to datetime and normalize timezone
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Timestamp'] = df['Timestamp'].dt.tz_localize('UTC').dt.tz_convert('Asia/Riyadh')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def get_date_range(selected_date):
    start_of_day = datetime.combine(selected_date, datetime.min.time())
    end_of_day = datetime.combine(selected_date, datetime.max.time())
    
    start_of_day = TIMEZONE.localize(start_of_day)
    end_of_day = TIMEZONE.localize(end_of_day)
    
    return start_of_day, end_of_day

def format_message(filtered_df, selected_date, selected_types):
    # Format the selected date in Arabic style
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # Filter by selected types
    filtered_df = filtered_df[filtered_df['نوع العملية'].isin(selected_types)]
    
    # Separate invoices and collections
    invoices = filtered_df[filtered_df['نوع العملية'] == 'فاتورة']
    collections = filtered_df[filtered_df['نوع العملية'] == 'تحصيل']
    
    # Calculate totals
    total_invoices = invoices['مبلغ الفاتورة'].sum() if 'فاتورة' in selected_types else 0
    total_collections = collections['مبلغ الفاتورة'].sum() if 'تحصيل' in selected_types else 0
    
    # Format the message with the selected date
    message = f"تقرير يوم {date_str}:\n\n"
    
    # Add transactions
    for _, row in filtered_df.iterrows():
        message += f"كود العميل: {row['كود العميل']}\n"
        if row['نوع العملية'] == 'فاتورة':
            message += f"رقم الفاتورة: {safe_int_convert(row['رقم الفاتورة'])}\n"
            message += f"تاريخ الفاتورة: {row['تاريخ الفاتورة']}\n"
        elif row['نوع العملية'] == 'تحصيل':
            # For collections, use رقم السند if available, otherwise use رقم الفاتورة
            receipt_num = row['رقم السند '] if pd.notna(row['رقم السند ']) else row['رقم الفاتورة']
            message += f"رقم التحصيل: {safe_int_convert(receipt_num)}\n"
            message += f"تاريخ التحصيل: {row['Timestamp'].strftime('%d-%m-%Y')}\n"
        message += f"المبلغ: {row['مبلغ الفاتورة']}\n"
        if pd.notna(row['نوع التحصيل ']):
            message += f"نوع التحصيل: {row['نوع التحصيل ']}\n"
        message += "-------------------\n"
    
    # Add totals based on selected types
    if 'فاتورة' in selected_types:
        message += f"\nإجمالي الفواتير: {total_invoices:.2f}\n"
    if 'تحصيل' in selected_types:
        message += f"إجمالي التحصيل: {total_collections:.2f}\n"
    
    return message

def main():
    st.title("")
    
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Get current date in Saudi Arabia timezone
    now = datetime.now(TIMEZONE)
    
    # Create two columns for date and type selection
    col1, col2 = st.columns([2, 2])
    
    with col1:
        # Date selector with larger touch target
        selected_date = st.date_input(
            "اختر التاريخ",
            now.date(),
            key="date_picker"
        )
    
    with col2:
        # Multi-selector for transaction types
        selected_types = st.multiselect(
            "نوع العملية",
            options=['تحصيل', 'فاتورة'],
            default=['تحصيل'],
            key="type_selector"
        )
    
    # Get date range in Saudi timezone
    start_of_day, end_of_day = get_date_range(selected_date)
    
    # Filter data by Timestamp within the selected date in Saudi timezone
    filtered_df = df[
        (df['Timestamp'] >= start_of_day) & 
        (df['Timestamp'] <= end_of_day)
    ].copy()
    
    if not filtered_df.empty and selected_types:
        # Filter by selected types for totals
        type_filtered_df = filtered_df[filtered_df['نوع العملية'].isin(selected_types)]
        
        # Calculate totals for visible types only
        invoices = type_filtered_df[type_filtered_df['نوع العملية'] == 'فاتورة']
        collections = type_filtered_df[type_filtered_df['نوع العملية'] == 'تحصيل']
        
        total_invoices = invoices['مبلغ الفاتورة'].sum() if 'فاتورة' in selected_types else 0
        total_collections = collections['مبلغ الفاتورة'].sum() if 'تحصيل' in selected_types else 0
        
        col1, col2 = st.columns(2)
        if 'فاتورة' in selected_types:
            with col1:
                st.metric("إجمالي الفواتير", f"{total_invoices:.2f}")
        if 'تحصيل' in selected_types:
            with col2:
                st.metric("إجمالي التحصيل", f"{total_collections:.2f}")
        
        # Generate message with selected date and types
        message = format_message(filtered_df, selected_date, selected_types)
        
        # Create WhatsApp share link
        whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(message)}"
        
        # Create a clickable link that opens WhatsApp
        st.markdown(
            f'<a href="{whatsapp_url}" target="_blank" style="text-decoration: none; width: 100%;">'
            '<button style="background-color: #25D366; color: white; padding: 15px; '
            'border: none; border-radius: 8px; cursor: pointer; width: 100%; '
            'font-size: 18px; margin: 10px 0;">'
            '📱 مشاركة عبر واتساب</button></a>',
            unsafe_allow_html=True
        )
        
    else:
        if not selected_types:
            st.info("الرجاء اختيار نوع العملية")
        else:
            st.info("لا توجد عمليات في التاريخ المحدد")

if __name__ == "__main__":
    main()
