import os
from flask import Flask, render_template
import yfinance as yf

app = Flask(__name__)

def load_symbols():
    try:
        # التأكد من مسار الملف الصحيح على سيرفر Render
        file_path = os.path.join(os.path.dirname(__file__), 'tasi.txt')
        with open(file_path, 'r') as f:
            # تنظيف الرموز وإضافة .SR
            return [f"{line.strip()}.SR" for line in f if line.strip()]
    except Exception as e:
        print(f"Error loading file: {e}")
        return ["2222.SR", "1120.SR"]

@app.route('/')
def index():
    symbols = load_symbols()
    stocks_list = []
    
    try:
        # جلب البيانات لجميع الرموز (269 شركة) بطلب واحد فقط!
        # هذه الطريقة تمنع الحظر وتضمن ظهور الكل
        data = yf.download(' '.join(symbols), period="1d", group_by='ticker', threads=True)
        
        for symbol in symbols:
            try:
                # استخراج البيانات لكل سهم من الطلب الجماعي
                ticker_data = data[symbol]
                if not ticker_data.empty:
                    # نأخذ آخر سعر إغلاق وأول سعر افتتاح لليوم
                    current_price = ticker_data['Close'].iloc[-1]
                    prev_close = ticker_data['Open'].iloc[0] # أو سعر إغلاق الأمس
                    
                    change = current_price - prev_close
                    pct_change = (change / prev_close) * 100
                    
                    stocks_list.append({
                        'symbol': symbol.replace('.SR', ''),
                        'lNameAr': f"شركة {symbol.replace('.SR', '')}",
                        'lastTradePrice': round(float(current_price), 2),
                        'change': round(float(change), 2),
                        'pctChange': round(float(pct_change), 2)
                    })
            except:
                continue
    except Exception as e:
        print(f"Major Error: {e}")

    # ترتيب الشركات من الأكثر صعوداً للأقل
    stocks_list = sorted(stocks_list, key=lambda x: x['pctChange'], reverse=True)
    
    return render_template('index.html', stocks=stocks_list)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
