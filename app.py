import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="رادار تاسي الذكي", layout="wide")

# تصميم الواجهة لتناسب الجوال (RTL)
st.markdown("""<style> .main { text-align: right; direction: rtl; } </style>""", unsafe_allow_html=True)

st.title("📈 رادار السوق السعودي")

def fetch_data_with_progress():
    url = "https://scanner.tradingview.com/saudi/scan"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "markets": ["saudi"],
        "columns": ["name", "description", "close", "change", "RSI", "EMA20"],
        "range": [0, 100] # سنجلب 100 شركة كمثال للسرعة
    }

    # إعداد شريط التقدم والوقت
    progress_bar = st.progress(0)
    status_text = st.empty()
    start_time = time.time()

    # محاكاة العداد (لأن طلب الـ API يأتي دفعة واحدة، سنقسم العرض ليعطي شعور العداد)
    for i in range(1, 101):
        # في المنتصف نقوم بطلب البيانات الفعلي
        if i == 50:
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                raw_data = response.json()
            except:
                st.error("خطأ في الاتصال بالسيرفر")
                return None

        # حساب الوقت
        current_time = time.time()
        elapsed_time = current_time - start_time
        # تقدير الوقت المتبقي (بناءً على سرعة العداد)
        remaining_time = (elapsed_time / i) * (100 - i) if i > 0 else 0
        
        # تحديث شريط التقدم
        progress_bar.progress(i)
        status_text.text(f"جاري التحميل: {i}% | المستغرق: {elapsed_time:.1f}ث | المتبقي: {remaining_time:.1f}ث")
        
        # سرعة العداد (يمكنك تقليلها ليصبح العداد أسرع)
        time.sleep(0.02)

    return raw_data

if st.button('بدء عملية الفحص الفني 🔍'):
    data = fetch_data_with_progress()
    
    if data and 'data' in data:
        rows = []
        for item in data['data']:
            d = item['d']
            rows.append({
                "الرمز": item['s'].split(':')[1],
                "الشركة": d[1],
                "السعر": d[2],
                "RSI": round(d[4], 2) if d[4] else 0,
                "الحالة": "✅ صاعد" if d[2] > d[5] else "⚠️ هابط"
            })
        
        df = pd.DataFrame(rows)
        st.success("✅ اكتمل التحليل")
        st.table(df) # استخدام table بدلاً من dataframe لضمان الثبات في الخلفية
