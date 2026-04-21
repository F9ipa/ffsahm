import yfinance as yf
import pandas as pd
import pandas_ta as ta
from flask import Flask, render_template, request
import os

app = Flask(__name__)

def calculate_wavetrend(df):
    if len(df) < 40: return pd.Series(), pd.Series()
    # معادلة LazyBear
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ta.ema(ap, length=10)
    d = ta.ema(abs(ap - esa), length=10)
    ci = (ap - esa) / (0.015 * d)
    wt1 = ta.ema(ci, length=21)
    wt2 = ta.sma(wt1, length=4)
    return wt1, wt2

def get_signals(interval):
    # قراءة الرموز من الملف
    try:
        with open('stocks.txt', 'r') as f:
            tickers = [line.strip() for line in f if line.strip()]
    except:
        tickers = ["2222.SR"] # احتياطي

    pos_signals = []
    neg_signals = []
    
    for t in tickers:
        try:
            # جلب البيانات (أقصى مدة ممكنة لكل فاصل)
            period = "2y" if interval in ['1d', '1wk', '1mo'] else "1mo"
            data = yf.download(t, period=period, interval=interval, progress=False)
            
            if data.empty: continue
            
            wt1, wt2 = calculate_wavetrend(data)
            
            # فحص آخر شمعتين للتقاطع
            w1_now, w2_now = wt1.iloc[-1], wt2.iloc[-1]
            w1_prev, w2_prev = wt1.iloc[-2], wt2.iloc[-2]
            
            if w1_prev <= w2_prev and w1_now > w2_now:
                pos_signals.append(t.split('.')[0])
            elif w1_prev >= w2_prev and w1_now < w2_now:
                neg_signals.append(t.split('.')[0])
        except Exception as e:
            print(f"Error scanning {t}: {e}")
            continue
            
    return pos_signals, neg_signals

@app.route('/')
def index():
    # الفواصل المتاحة: 1mo, 1wk, 1d, 90m (بديل لـ 4 ساعات لأن ياهو لا يدعمها مباشرة مجاناً)
    interval = request.args.get('interval', '1d')
    pos, neg = get_signals(interval)
    return render_template('index.html', pos=pos, neg=neg, interval=interval)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
