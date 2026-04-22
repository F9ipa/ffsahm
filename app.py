import pandas as pd
import yfinance as yf
from flask import Flask, render_template
import os

app = Flask(__name__)

# دالة حساب مؤشر WaveTrend يدوياً لضمان التوافق مع Render
def calculate_wavetrend(df, n1=10, n2=21):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d)
    wt1 = ci.ewm(span=n2, adjust=False).mean()
    wt2 = wt1.rolling(window=4).mean()
    return wt1, wt2

def get_signals():
    # قائمة الأسهم الافتراضية (تاسي، تبوك، الراجحي، أرامكو)
    default_symbols = ["^TASI", "6040.SR", "1120.SR", "2222.SR"]
    
    symbols = []
    if os.path.exists('symbols.txt'):
        with open('symbols.txt', 'r') as f:
            symbols = [line.strip() for line in f.readlines() if line.strip()]
    
    if not symbols:
        symbols = default_symbols
    
    results = []
    for symbol in symbols:
        try:
            # جلب بيانات شهرية لمدة 5 سنوات لضمان دقة المؤشر
            data = yf.download(symbol, period="5y", interval="1mo", progress=False)
            
            if data.empty or len(data) < 30:
                continue

            wt1, wt2 = calculate_wavetrend(data)
            
            # جلب آخر 3 قيم (الحالية - السابقة - ما قبل السابقة)
            curr_wt1 = float(wt1.iloc[-1])   # شمعة الشهر الحالي (متحركة)
            curr_wt2 = float(wt2.iloc[-1])
            
            prev_wt1 = float(wt1.iloc[-2])   # شمعة الشهر الماضي (مغلقة)
            prev_wt2 = float(wt2.iloc[-2])
            
            p_prev_wt1 = float(wt1.iloc[-3]) # شمعة ما قبل الماضي
            p_prev_wt2 = float(wt2.iloc[-3])

            signal = "انتظار"
            color = "gray"
            
            # منطق الإشارة الاستباقية (قبل إغلاق الشمعة)
            if prev_wt1 <= prev_wt2 and curr_wt1 > curr_wt2:
                signal = "إيجابي (قيد التشكل)"
                color = "#2ecc71" # أخضر فاتح
            
            # منطق تأكيد الإشارة (إذا كانت الشمعة السابقة أغلقت على تقاطع)
            elif p_prev_wt1 <= p_prev_wt2 and prev_wt1 > prev_wt2:
                signal = "إيجابي مؤكد (شمعة سابقة)"
                color = "#27ae60" # أخضر غامق
                
            # منطق الإشارة السلبية
            elif prev_wt1 >= prev_wt2 and curr_wt1 < curr_wt2:
                signal = "سلبي (قيد التشكل)"
                color = "#e74c3c" # أحمر

            results.append({
                'symbol': symbol,
                'wt1': round(curr_wt1, 2),
                'wt2': round(curr_wt2, 2),
                'signal': signal,
                'color': color
            })
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            
    return results

@app.route('/')
def index():
    stocks_data = get_signals()
    return render_template('index.html', stocks=stocks_data)

if __name__ == "__main__":
    # تشغيل التطبيق على المنفذ المخصص من Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
