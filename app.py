import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)

# قائمة المؤشرات القيادية
GLOBAL_INDICES = {
    "تاسي": "^TASI",
    "مؤشر الخوف (VIX)": "^VIX",
    "الذهب": "GC=F",
    "الفضة": "SI=F",
    "خام برنت": "BZ=F",
    "النفط الخام": "CL=F"
}

# عينة من الأسهم (يمكنك وضع قائمة بـ 200 رمز هنا)
SAUDI_STOCKS = ["6040", "2222", "1120", "1150", "2010", "2280", "4030", "7010", "1180"]

def calculate_wavetrend(df, n1=10, n2=21):
    if len(df) < n2: return pd.Series(), pd.Series()
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d)
    wt1 = ci.ewm(span=n2, adjust=False).mean()
    wt2 = wt1.rolling(window=4).mean()
    return wt1, wt2

def get_market_status(symbols, period, interval):
    positives = []
    negatives = []
    
    for sym in symbols:
        try:
            ticker = f"{sym}.SR"
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            if df.empty or len(df) < 10: continue
            
            wt1, wt2 = calculate_wavetrend(df)
            last_wt1 = wt1.iloc[-1]
            last_wt2 = wt2.iloc[-1]
            prev_wt1 = wt1.iloc[-2]
            prev_wt2 = wt2.iloc[-2]
            
            # تقاطع إيجابي (صعود)
            is_bullish = (prev_wt1 < prev_wt2) and (last_wt1 > last_wt2)
            # تقاطع سلبي (هبوط)
            is_bearish = (prev_wt1 > prev_wt2) and (last_wt1 < last_wt2)
            
            stock_data = {
                "symbol": sym,
                "price": round(df['Close'].iloc[-1], 2),
                "wt1": round(last_wt1, 2),
                "trend": "صاعد" if last_wt1 > last_wt2 else "هابط"
            }
            
            if is_bullish or (last_wt1 < -50):
                positives.append(stock_data)
            elif is_bearish or (last_wt1 > 50):
                negatives.append(stock_data)
        except: continue
    return positives, negatives

@app.route('/')
def index():
    # جلب فريم الوقت من الرابط (الافتراضي يومي)
    interval = request.args.get('interval', '1d')
    period = "max"
    if interval == "4h": 
        interval = "1h" # yfinance لا يدعم 4h مباشرة بسهولة، نستخدم 1h كبديل دقيق
        period = "2y"
        
    # 1. جلب بيانات المؤشرات العالمية
    global_data = {}
    for name, sym in GLOBAL_INDICES.items():
        try:
            d = yf.Ticker(sym).history(period="1d")
            global_data[name] = round(d['Close'].iloc[-1], 2) if not d.empty else "N/A"
        except: global_data[name] = "Error"
        
    # 2. تحليل الأسهم وفصلها
    pos, neg = get_market_status(SAUDI_STOCKS, period, interval)
    
    return render_template('index.html', 
                           global_indices=global_data, 
                           positives=pos, 
                           negatives=neg, 
                           current_interval=interval)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
