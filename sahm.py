from flask import Flask, render_template
import yfinance as yf

app = Flask(__name__)

def get_stock_data(symbol="^TASI"):
    # جلب بيانات المؤشر العام أو أي شركة سعودية
    stock = yf.Ticker(symbol)
    df = stock.history(period="1d")
    if not df.empty:
        return {
            "name": symbol,
            "price": round(df['Close'].iloc[-1], 2),
            "change": round(df['Close'].iloc[-1] - df['Open'].iloc[-1], 2)
        }
    return None

@app.route('/')
def index():
    data = get_stock_data() # يمكنك تغيير الرمز هنا لشركة محددة
    return render_template('index.html', data=data)

if __name__ == "__main__":
    app.run(debug=True)