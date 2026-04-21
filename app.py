from flask import Flask, render_template, request
import yfinance as yf

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    stock_data = None
    symbol = "2222"  # الافتراضي سهم أرامكو
    
    if request.method == 'POST':
        symbol = request.form.get('symbol')
    
    # جلب البيانات من ياهو فاينانس
    ticker = yf.Ticker(f"{symbol}.SR")
    df = ticker.history(period="1d")
    
    if not df.empty:
        stock_data = {
            "symbol": symbol,
            "price": round(df['Close'].iloc[-1], 2),
            "high": round(df['High'].iloc[-1], 2),
            "low": round(df['Low'].iloc[-1], 2)
        }

    return render_template('index.html', data=stock_data)

if __name__ == '__main__':
    app.run(debug=True)
