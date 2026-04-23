import streamlit as st
import requests
import pandas as pd
import os

# إعداد واجهة الصفحة
st.set_page_config(page_title="رادار الأسهم السعودية", layout="wide")
st.title("📊 رادار السوق السعودي - TradingView")

def get_tv_data(symbols):
    url = "https://scanner.tradingview.com/saudi/scan"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {
        "symbols": {"tickers": [f"TADAWUL:{s}" for s in symbols]},
        "columns": ["name", "close", "change", "RSI", "EMA20", "EMA50"]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        rows = []
        for item in data['data']:
            rows.append({
                "الرمز": item['s'].split(':')[1],
                "السعر": item['d'][1],
                "التغيير %": round(item['d'][2], 2),
                "RSI": round(item['d'][3], 2) if item['d'][3] else 0,
                "EMA20": item['d'][4],
                "EMA50": item['d'][5]
            })
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

# قراءة الملف
if os.path.exists('tasi.txt'):
    with open('tasi.txt', 'r') as f:
        my_symbols = [line.strip() for line in f if line.strip().isdigit()]
    
    if st.button('تحديث البيانات الآن 🔄'):
        df = get_tv_data(my_symbols)
        
        if not df.empty:
            # إضافة منطق الفلترة (مثال: الأسهم الإيجابية فقط)
            df['الحالة'] = df.apply(lambda x: "✅ إيجابي" if x['السعر'] > x['EMA20'] else "⚠️ سلبي", axis=1)
            
            # عرض البيانات في جدول تفاعلي
            st.dataframe(df.style.highlight_max(axis=0, subset=['RSI']), use_container_width=True)
            
            st.success(f"تم تحديث {len(df)} سهم بنجاح.")
        else:
            st.error("فشل في جلب البيانات من TradingView.")
else:
    st.warning("ملف tasi.txt غير موجود في المستودع!")
