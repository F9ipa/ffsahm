from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)

# قائمة الأسهم للمسح (يمكنك إضافة أي رمز سهم سعودي هنا)
WATCHLIST = ["6040", "2222", "1120", "1150", "2010", "2280", "4030"]

def calculate_wavetrend(df, n1=10, n2=21):
    # معادلة FARES_vip (WaveTrend)
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d)
    wt1 = ci.ewm(span=n2, adjust=False).mean()
    wt2 = wt1.rolling(window=4).mean()
    return wt1, wt2

def analyze_market():
    results = []
    for symbol in WATCHLIST:
        ticker = f"{symbol}.SR"
        # جلب بيانات كافية لحساب المؤشرات (آخر 60 يوم)
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        
        if df.empty or len(df) < 30: continue

        # حساب WaveTrend (مؤشرك الخاص)
        wt1_series, wt2_series = calculate_wavetrend(df)
        
        last_wt1 = round(wt1_series.iloc[-1], 2)
        last_wt2 = round(wt2_series.iloc[-1], 2)
        prev_wt1 = wt1_series.iloc[-2]
        prev_wt2 = wt2_series.iloc[-2]

        # فحص التقاطع (Cross)
        bullish_cross = (prev_wt1 < prev_wt2) and (last_wt1 > last_wt2)
        bearish_cross = (prev_wt1 > prev_wt2) and (last_wt1 < last_wt2)

        # منطق اتخاذ القرار الاحترافي
        decision = "انتظار"
        color = "secondary"
        logic = "لا توجد إشارة واضحة"

        if bullish_cross and last_wt1 < -53:
            decision = "دخول ذهبي"
            color = "success"
            logic = f"تقاطع إيجابي في قاع ({last_wt1})"
        elif last_wt1 < -60:
            decision = "مراقبة لصيقة"
            color = "info"
            logic = "منطقة تشبع بيعي حاد"
        elif bearish_cross and last_wt1 > 53:
            decision = "خروج / جني ربح"
            color = "danger"
            logic = f"تقاطع سلبي في قمة ({last_wt1})"
        elif last_wt1 > 60:
            decision = "تضخم عالي"
            color = "warning"
            logic = "منطقة تشبع شرائي (خطر)"

        results.append({
            "symbol": symbol,
            "price": round(df['Close'].iloc[-1], 2),
            "wt1": last_wt1,
            "wt2": last_wt2,
            "decision": decision,
            "color": color,
            "logic": logic
        })
    return results

@app.route('/')
def index():
    # جلب مؤشرات عالمية سريعة
    try:
        commodities = {
            "برنت": round(yf.Ticker("BZ=F").history(period="1d")['Close'].iloc[-1], 2),
            "الذهب": round(yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1], 2),
            "تاسي": round(yf.Ticker("^TASI").history(period="1d")['Close'].iloc[-1], 2)
        }
    except:
        commodities = {"برنت": "00", "الذهب": "00", "تاسي": "00"}
        
    market_data = analyze_market()
    return render_template('index.html', results=market_data, commodities=commodities)

if __name__ == '__main__':
    app.run(debug=True)
