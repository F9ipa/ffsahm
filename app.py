import streamlit as st
import requests
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="رادار تاسي الاحترافي", layout="wide")

st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 رادار السوق السعودي الذكي")
st.write("يتم سحب البيانات الآن مباشرة من TradingView لجميع أسهم السوق")

def get_all_tasi_data():
    # هذا الرابط يجلب كل أسهم السوق السعودي المتاحة في السكرينر
    url = "https://scanner.tradingview.com/saudi/scan"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # طلب كافة الأسهم مع الفلاتر الفنية
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}
        ],
        "options": {"lang": "ar"},
        "markets": ["saudi"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name", 
            "description", 
            "close", 
            "change", 
            "RSI", 
            "EMA20", 
            "EMA50",
            "volume"
        ],
        "sort": {"sortBy": "change", "sortOrder": "desc"},
        "range": [0, 300] # جلب أول 300 شركة (تغطي كامل السوق)
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        rows = []
        for item in data['data']:
            d = item['d']
            rows.append({
                "الرمز": item['s'].split(':')[1],
                "الشركة": d[1],
                "السعر": d[2],
                "التغيير %": round(d[3], 2),
                "RSI": round(d[4], 2) if d[4] else 0,
                "EMA20": round(d[5], 2) if d[5] else 0,
                "EMA50": round(d[6], 2) if d[6] else 0,
                "الفوليوم": d[7]
            })
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return pd.DataFrame()

# زر التحديث
if st.sidebar.button('تحديث الرادار 🔄'):
    df = get_all_tasi_data()
    
    if not df.empty:
        # استراتيجية الفلترة: الأسهم التي فوق متوسط 20 (إيجابية مضاربية)
        st.subheader("🚀 الأسهم في مسار صاعد (فوق EMA20)")
        positive_df = df[df['السعر'] > df['EMA20']]
        
        # عرض الجدول
        st.dataframe(positive_df, use_container_width=True)
        
        # إحصائيات سريعة
        col1, col2 = st.columns(2)
        col1.metric("عدد الشركات المحللة", len(df))
        col2.metric("شركات إيجابية", len(positive_df))
    else:
        st.write("انقر على الزر لتحديث البيانات")
