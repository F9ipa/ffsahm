import streamlit as st
import requests
import pandas as pd
import time

# إعدادات واجهة المستخدم
st.set_page_config(page_title="رادار تاسي اليومي", layout="wide")

# تنسيق النصوص لتظهر من اليمين لليسار (اللغة العربية)
st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stMetricValue"] { text-align: right; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 رادار السوق السعودي (الفاصل اليومي)")
st.info("هذا الرادار يقوم بمسح كامل السوق السعودي بناءً على بيانات TradingView اللحظية للفريم اليومي.")

def fetch_data():
    url = "https://scanner.tradingview.com/saudi/scan"
    
    # متصفح وهمي لضمان قبول الطلب من سيرفرات Render
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # جلب البيانات على الفاصل اليومي (الافتراضي في السكرينر)
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "markets": ["saudi"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": ["name", "description", "close", "change", "RSI", "EMA20", "EMA50", "volume"],
        "sort": {"sortBy": "change", "sortOrder": "desc"},
        "range": [0, 250] # تغطية كامل أسهم السوق السعودي
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=25)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"خطأ في السيرفر: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"عذراً، فشل الاتصال: {e}")
        return None

# زر التشغيل مع العداد
if st.button('تحديث مسح السوق 🔄'):
    progress_bar = st.progress(0)
    status_text = st.empty()
    start_time = time.time()

    # عداد تجميلي لتوضيح حالة التقدم
    for i in range(1, 101):
        if i == 40: # سحب البيانات الفعلي في منتصف العداد
            raw_data = fetch_data()
        
        elapsed = time.time() - start_time
        remaining = (elapsed / i) * (100 - i) if i > 0 else 0
        
        progress_bar.progress(i)
        status_text.text(f"جاري المسح: {i}% | المستغرق: {elapsed:.1f}ث | المتبقي: {remaining:.1f}ث")
        time.sleep(0.01)

    if raw_data and 'data' in raw_data:
        rows = []
        for item in raw_data['data']:
            d = item['d']
            rows.append({
                "الرمز": item['s'].split(':')[1],
                "الشركة": d[1],
                "السعر": d[2],
                "التغيير %": round(d[3], 2),
                "RSI": round(d[4], 2) if d[4] else 0,
                "الترند (EMA20)": "📈 صاعد" if d[2] > d[5] else "📉 هابط",
                "السيولة": d[7]
            })
        
        df = pd.DataFrame(rows)
        
        # عرض إحصائيات سريعة
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي الشركات", len(df))
        c2.metric("أعلى تغيير", f"{df['التغيير %'].max()}%")
        c3.metric("متوسط RSI", round(df['RSI'].mean(), 1))

        # عرض الجدول النهائي
        st.success("اكتمل المسح اليومي بنجاح")
        st.dataframe(df, use_container_width=True)
