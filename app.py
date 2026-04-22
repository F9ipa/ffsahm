import os
from flask import Flask, render_template
import yfinance as yf
import pandas as pd

app = Flask(__name__)

def get_tasi_data_from_yahoo():
    # قائمة ببعض الرموز كمثال، يمكنك إضافة كل الرموز الـ 269 لاحقاً
    # أو قراءتها من ملف tasi.txt إذا رفعته مع المشروع
    sample_symbols = ["2222.SR", "1120.SR", "1180.SR", "2010.SR", "7010.SR"] 
    
    # لجلب الـ 269 شركة، يفضل جلبها على دفعات
    try:
        # جلب البيانات لعدة رموز مرة واحدة لتسريع العملية
        tickers = yf.Tickers(' '.join(sample_symbols))
        stocks_list = []
        
        for symbol in sample_symbols:
            info = tickers.tickers[symbol].fast_info
            # استخراج اسم الشركة (اختياري، ياهو يوفر الاسماء بالانجليزي غالباً)
            stocks_list.append({
                'symbol': symbol.replace('.SR', ''),
                'lNameAr': f"شركة {symbol.replace('.SR', '')}", # يمكنك ربطها بقاموس أسماء عربية
                'lastTradePrice': round(info['last_price'], 2),
                'change': round(info['last_price'] - info['previous_close'], 2),
                'pctChange': round(((info['last_price'] - info['previous_close']) / info['previous_close']) * 100, 2)
            })
        return stocks_list
    except Exception as e:
        print(f"Yahoo Error: {e}")
        return []

@app.route('/')
def index():
    stocks = get_tasi_data_from_yahoo()
    return render_template('index.html', stocks=stocks)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
