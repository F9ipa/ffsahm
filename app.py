import pandas as pd
import numpy as np
import yfinance as yf
from flask import Flask, render_template
import os

app = Flask(__name__)

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

def calculate_wavetrend(df, n1=10, n2=21):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d)
    wt1 = ci.ewm(span=n2, adjust=False).mean()
    wt2 = wt1.rolling(window=4).mean()
    return wt1, wt2

def get_signals():
    # قائمة أسهم افتراضية قوية لضمان العمل
    symbols = ["^TASI", "6040.SR", "1120.SR", "2222.SR"]
    
    if os.path.exists('symbols.txt'):
        with open('symbols.txt', 'r') as f:
            user_symbols = [line.strip() for line in f.readlines() if line.strip()]
            if user_symbols: symbols = user_symbols
    
    results = []
    errors = []

    for symbol in symbols:
        try:
            # جلب البيانات بفاصل شهري
            data = yf.download(symbol, period="max", interval="1mo", progress=False)
            
            if data.empty or len(data) < 10:
                errors.append(f"لا توجد بيانات كافية للسهم: {symbol}")
                continue

            ha_data = get_heikin_ashi(data)
            wt1, wt2 = calculate_wavetrend(ha_data)
            
            curr_wt1 = float(wt1.iloc[-1])
            curr_wt2 = float(wt2.iloc[-1])
            prev_wt1 = float(wt1.iloc[-2])
            prev_wt2 = float(wt2.iloc[-2])

            signal = "انتظار"
            color = "#95a5a6"
            
            if prev_wt1 <= prev_wt2 and curr_wt1 > curr_wt2:
                signal = "إيجابي (قيد التشكل)"
                color = "#2ecc71"
            elif prev_wt1 >= prev_wt2 and curr_wt1 < curr_wt2:
                signal = "سلبي (قيد التشكل)"
                color = "#e74c3c"

            results.append({
                'symbol': symbol,
                'wt1': round(curr_wt1, 2),
                'wt2': round(curr_wt2, 2),
                'signal': signal,
                'color': color
            })
        except Exception as e:
            errors.append(f"خطأ في {symbol}: {str(e)}")
            
    return results, errors

@app.route('/')
def index():
    stocks, errors = get_signals()
    return render_template('index.html', stocks=stocks, errors=errors)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
