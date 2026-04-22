import pandas as pd
import numpy as np
import yfinance as yf
from flask import Flask, render_template
import os

app = Flask(__name__)

# دالة تحويل الشموع العادية إلى هايكن آشي (Heikin-Ashi) لفلترة الضجيج
def get_heikin_ashi(df):
    try:
        ha_df = df.copy()
        ha_df['Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
        ha_open = np.zeros(len(df))
        ha_open[0] = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
        for i in range(1, len(df)):
            ha_open[i] = (ha_open[i-1] + ha_df['Close'].iloc[i-1]) / 2
        ha_df['Open'] = ha_open
        ha_df['High'] = ha_df[['High', 'Open', 'Close']].max(axis=1)
        ha_df['Low'] = ha_df[['Low', 'Open', 'Close']].min(axis=1)
        return ha_df
    except:
        return df

# دالة حساب مؤشر WaveTrend (نفس إعدادات تريدنج فيو الأصلية 10, 21)
def calculate_wavetrend(df, n1=10, n2=21):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d)
    wt1 = ci.ewm(span=n2, adjust=False).mean()
    wt2 = wt1.rolling(window=4).mean()
    return wt1, wt2

def get_signals():
    # 1. القائمة الاحتياطية (في حال لم يقرأ الملف)
    symbols = ["^TASI", "6040.SR", "2222.SR", "1120.SR"]
    
    # 2. محاولة قراءة الأسهم من ملف symbols.txt بمسار مطلق
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_path, 'symbols.txt')
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                file_symbols = [line.strip() for line in f.readlines() if line.strip()]
                if file_symbols:
                    symbols = file_symbols
    except Exception as e:
        print(f"خطأ في قراءة ملف الأسهم: {e}")

    results = []
    # 3. جلب ومعالجة البيانات لكل سهم
    for symbol in symbols:
        try:
            # جلب بيانات سنتين بفاصل أسبوعي لضمان سرعة الاستجابة
            data = yf.download(symbol, period="2y", interval="1wk", progress=False, timeout=10)
            
            if data is None or data.empty or len(data) < 25:
                continue

            # حساب الهايكن آشي والمؤشرات
            ha_data = get_heikin_ashi(data)
            wt1, wt2 = calculate_wavetrend(ha_data)
            
            # الحصول على آخر قيمتين للمقارنة (تحديد التقاطع)
            c_wt1, c_wt2 = float(wt1.iloc[-1]), float(wt2.iloc[-1])
            p_wt1, p_wt2 = float(wt1.iloc[-2]), float(wt2.iloc[-2])

            # منطق الإشارات
            if p_wt1 <= p_wt2 and c_wt1 > c_wt2:
                signal, color = "إيجابي (تقاطع)", "#089981" # أخضر
            elif p_wt1 >= p_wt2 and c_wt1 < c_wt2:
                signal, color = "سلبي (تقاطع)", "#f23645" # أحمر
            else:
                signal, color = "انتظار", "#787b86" # رمادي

            results.append({
                'symbol': symbol,
                'wt1': round(c_wt1, 2),
                'wt2': round(c_wt2, 2),
                'signal': signal,
                'color': color
            })
        except:
            continue
            
    return results

@app.route('/')
def index():
    stocks = get_signals()
    # يتم تمرير النتائج لملف index.html المنسق بـ Dark Mode
    return render_template('index.html', stocks=stocks)

if __name__ == "__main__":
    # تشغيل التطبيق على المنفذ المخصص من Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
