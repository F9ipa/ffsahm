import os
from flask import Flask, render_template
import yfinance as yf
import pandas_ta as ta
import pandas as pd

app = Flask(__name__)

# دالة لقراءة الأسهم من ملف stocks.txt
def load_symbols():
    symbols = []
    if os.path.exists('stocks.txt'):
        with open('stocks.txt', 'r') as f:
            # قراءة الأسطر وإزالة المسافات والأسطر الفارغة
            symbols = [line.strip() for line in f if line.strip()]
    # إذا كان الملف فارغاً، نضع عينة افتراضية لتجنب الخطأ
    return symbols if symbols else ["2222.SR", "1120.SR", "AAPL"]

def get_wavetrend_signals(symbol, interval):
    try:
        # جلب البيانات (سنتين للشهري وسنة للأسبوعي)
        period = "2y" if interval == "1mo" else "1y"
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        
        if df.empty or len(df) < 30:
            return False, 0
        
        # --- حساب معادلة WaveTrend (LazyBear) ---
        # ap = hlc3
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        
        # esa = ema(ap, n1=10)
        esa = ta.ema(ap, length=10)
        
        # d = ema(abs(ap - esa), n1=10)
        d = ta.ema(abs(ap - esa), length=10)
        
        # ci = (ap - esa) / (0.015 * d)
        ci = (ap - esa) / (0.015 * d)
        
        # wt1 = tci = ema(ci, n2=21)
        wt1 = ta.ema(ci, length=21)
        
        # wt2 = sma(wt1, 4)
        wt2 = ta.sma(wt1, length=4)
        
        last_wt1 = wt1.iloc[-1]
        last_wt2 = wt2.iloc[-1]
        
        # الشرط: أن يكون الخط الأخضر (wt1) فوق الأحمر (wt2)
        # يمكنك إضافة شرط (last_wt1 < -53) إذا أردت فقط مناطق الارتداد
        is_bullish = last_wt1 > last_wt2
        
        return is_bullish, round(float(df['Close'].iloc[-1]), 2)
    except Exception as e:
        print(f"Error scanning {symbol}: {e}")
        return False, 0

@app.route('/')
def index():
    symbols = load_symbols()
    positive_stocks = []
    
    # فحص القائمة (سيتم فحص أول 50 سهم لتجنب بطء Render في الخطة المجانية)
    # يمكنك إزالة [0:50] إذا كانت السيرفرات سريعة
    for sym in symbols[:50]:
        w_status, price = get_wavetrend_signals(sym, "1wk")
        m_status, _ = get_wavetrend_signals(sym, "1mo")
        
        if w_status or m_status:
            positive_stocks.append({
                "symbol": sym,
                "price": price,
                "weekly": "إيجابي ✅" if w_status else "انتظار",
                "monthly": "إيجابي ✅" if m_status else "انتظار"
            })
            
    return render_template('index.html', stocks=positive_stocks)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
