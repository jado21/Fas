from flask import Blueprint, request, jsonify, session
import yfinance as yf
import json
from datetime import datetime

precios_bp = Blueprint('precios', __name__)

def require_login(f):
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Debe iniciar sesión'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@precios_bp.route('/precios-tiempo-real')
@require_login
def precios_tiempo_real():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Precios en Tiempo Real</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .header { background-color: #007bff; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .content { background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }
            .stock-form { margin-bottom: 20px; }
            .stock-input { padding: 10px; margin-right: 10px; border: 1px solid #ddd; border-radius: 4px; }
            .btn { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background-color: #0056b3; }
            .stock-info { margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 8px; }
            .price { font-size: 24px; font-weight: bold; color: #28a745; }
            .change { font-size: 18px; margin-top: 5px; }
            .positive { color: #28a745; }
            .negative { color: #dc3545; }
            .loading { color: #6c757d; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📈 Precios en Tiempo Real</h1>
            <a href="/dashboard" style="color: white; text-decoration: none;">← Volver al Dashboard</a>
        </div>
        
        <div class="content">
            <div class="stock-form">
                <input type="text" id="stockSymbol" class="stock-input" placeholder="Símbolo (ej: AAPL, GOOGL, TSLA)" value="AAPL">
                <button onclick="getStockPrice()" class="btn">Obtener Precio</button>
                <button onclick="startAutoUpdate()" class="btn" id="autoBtn">Auto-actualizar</button>
            </div>
            
            <div id="stockInfo" class="stock-info" style="display: none;">
                <h3 id="stockName"></h3>
                <div id="stockPrice" class="price"></div>
                <div id="stockChange" class="change"></div>
                <div id="stockDetails"></div>
            </div>
            
            <div id="loading" class="loading" style="display: none;">Cargando...</div>
            <div id="error" style="color: red; display: none;"></div>
        </div>
        
        <script>
            let autoUpdateInterval = null;
            
            async function getStockPrice() {
                const symbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
                if (!symbol) {
                    alert('Por favor ingrese un símbolo');
                    return;
                }
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('stockInfo').style.display = 'none';
                document.getElementById('error').style.display = 'none';
                
                try {
                    const response = await fetch('/api/stock-price', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ symbol: symbol })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        displayStockInfo(data.data);
                    } else {
                        document.getElementById('error').textContent = data.message;
                        document.getElementById('error').style.display = 'block';
                    }
                } catch (error) {
                    document.getElementById('error').textContent = 'Error de conexión';
                    document.getElementById('error').style.display = 'block';
                } finally {
                    document.getElementById('loading').style.display = 'none';
                }
            }
            
            function displayStockInfo(data) {
                document.getElementById('stockName').textContent = data.name + ' (' + data.symbol + ')';
                document.getElementById('stockPrice').textContent = '$' + data.price.toFixed(2);
                
                const change = data.change;
                const changePercent = data.changePercent;
                const changeElement = document.getElementById('stockChange');
                
                if (change >= 0) {
                    changeElement.className = 'change positive';
                    changeElement.textContent = '+$' + change.toFixed(2) + ' (+' + changePercent.toFixed(2) + '%)';
                } else {
                    changeElement.className = 'change negative';
                    changeElement.textContent = '-$' + Math.abs(change).toFixed(2) + ' (' + changePercent.toFixed(2) + '%)';
                }
                
                document.getElementById('stockDetails').innerHTML = 
                    '<strong>Volumen:</strong> ' + data.volume.toLocaleString() + '<br>' +
                    '<strong>Máximo del día:</strong> $' + data.dayHigh.toFixed(2) + '<br>' +
                    '<strong>Mínimo del día:</strong> $' + data.dayLow.toFixed(2) + '<br>' +
                    '<strong>Última actualización:</strong> ' + new Date().toLocaleTimeString();
                
                document.getElementById('stockInfo').style.display = 'block';
            }
            
            function startAutoUpdate() {
                const btn = document.getElementById('autoBtn');
                
                if (autoUpdateInterval) {
                    clearInterval(autoUpdateInterval);
                    autoUpdateInterval = null;
                    btn.textContent = 'Auto-actualizar';
                    btn.style.backgroundColor = '#007bff';
                } else {
                    autoUpdateInterval = setInterval(getStockPrice, 10000); // Cada 10 segundos
                    btn.textContent = 'Detener auto-actualización';
                    btn.style.backgroundColor = '#dc3545';
                }
            }
            
            // Cargar precio inicial
            getStockPrice();
        </script>
    </body>
    </html>
    '''

@precios_bp.route('/api/stock-price', methods=['POST'])
@require_login
def api_stock_price():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        
        if not symbol:
            return jsonify({'success': False, 'message': 'Símbolo requerido'})
        
        # Obtener datos de yfinance
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="2d")
        
        if hist.empty:
            return jsonify({'success': False, 'message': 'Símbolo no encontrado'})
        
        current_price = hist['Close'].iloc[-1]
        previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        
        change = current_price - previous_price
        change_percent = (change / previous_price) * 100 if previous_price != 0 else 0
        
        stock_data = {
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'price': float(current_price),
            'change': float(change),
            'changePercent': float(change_percent),
            'volume': int(hist['Volume'].iloc[-1]),
            'dayHigh': float(hist['High'].iloc[-1]),
            'dayLow': float(hist['Low'].iloc[-1]),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'data': stock_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

