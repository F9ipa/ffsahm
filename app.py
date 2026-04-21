import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# --- إعدادات الصفحة لتشبه تصميم الصورة ---
st.set_page_config(page_title="منصة التحليل الذكي", layout="wide")

# تنسيق CSS مخصص للوصول لشكل الصورة (الخلفية الداكنة والخطوط)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #1f2937; color: white; border: 1px solid #374151; }
    .stButton>button:hover { background-color: #3b82f6; border-color: #3b82f6; }
    .status-up { color: #10b981; font-weight: bold; }
    .status-down { color: #ef4444; font-weight: bold; }
    div[data-testid="stExpander"] { background-color: #1f2937; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- دالة حساب مؤشر WaveTrend (FARES_vip) ---
def calculate_wavetrend(df, n1=10, n2=21):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d)
    wt1 = ci.ewm(span=n2, adjust=False).mean()
    wt2 = wt1.rolling(window=4).mean()
    return wt1, wt2

# --- جلب البيانات وفلترتها ---
@st.cache_data(ttl=300) # تحديث كل 5 دقائق
def get_market_data(symbols):
    results = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol + ".SR") # السوق السعودي
            df = ticker.history(period="60d", interval="1d")
            if df.empty: continue
            
            wt1, wt2 = calculate_wavetrend(df)
            
            last_wt1 = wt1.iloc[-1]
            last_wt2 = wt2.iloc[-1]
            prev_wt1 = wt1.iloc[-2]
            prev_wt2 = wt2.iloc[-2]
            
            # تحديد الإشارة
            signal = "انتظار"
            color_class = ""
            if prev_wt1 < prev_wt2 and last_wt1 > last_wt2:
                signal = "دخول (تقاطع صاعد) 🚀"
                color_class = "status-up"
            elif prev_wt1 > prev_wt2 and last_wt1 < last_wt2:
                signal = "خروج (تقاطع هابط) ⚠️"
                color_class = "status-down"
            elif last_wt1 < -53:
                signal = "منطقة تجميع (Oversold)"
            elif last_wt1 > 53:
                signal = "تخفيف حمولة (Overbought)"

            results.append({
                "الرمز": symbol,
                "السعر الحالي": round(df['Close'].iloc[-1], 2),
                "التغير": f"{round(((df['Close'].iloc[-1] / df['Close'].iloc[-2]) - 1) * 100, 2)}%",
                "قيمة WT1": round(last_wt1, 2),
                "قيمة WT2": round(last_wt2, 2),
                "الحالة الإجمالية": signal
            })
        except:
            continue
    return pd.DataFrame(results)

# --- واجهة المستخدم (التصميم العلوي) ---
st.title("📊 منصة التتبع والتحليل الرقمي")

# أزرار الفلترة مثل التي في الصورة
col1, col2, col3 = st.columns(3)
with col1:
    btn_all = st.button("كل الأسهم")
with col2:
    btn_entry = st.button("فرص الدخول")
with col3:
    btn_analysis = st.button("تحليل الاحتياج")

# قائمة الأسهم للمراقبة (يمكنك زيادة الرموز هنا)
symbols_to_track = ['2010', '1120', '2222', '7010', '1180', '4030']

# جلب البيانات
data_df = get_market_data(symbols_to_track)

# منطق الفلترة عند الضغط على الأزرار
if btn_entry:
    data_df = data_df[data_df['الحالة الإجمالية'].str.contains("دخول")]

# عرض البيانات بجدول احترافي
st.markdown("### رحلات الوصول (إشارات السوق)")
st.dataframe(
    data_df,
    column_config={
        "الرمز": "الشركة",
        "الحالة الإجمالية": st.column_config.TextColumn("التوصية اللحظية"),
        "السعر الحالي": st.column_config.NumberColumn(format="%.2f SR"),
    },
    hide_index=True,
    use_container_width=True
)

# --- إضافات احترافية من عندي (بدون شارتات) ---
st.sidebar.header("إعدادات المنصة")
n1_val = st.sidebar.slider("طول القناة (n1)", 5, 20, 10)
n2_val = st.sidebar.slider("طول المتوسط (n2)", 10, 50, 21)

st.sidebar.markdown("---")
st.sidebar.info("هذه المنصة تعمل بالذكاء الاصطناعي وتعتمد على معادلات WaveTrend الخاصة بك.")
