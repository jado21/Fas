from flask import Blueprint, request, jsonify, session
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

recomendaciones_bp = Blueprint('recomendaciones', __name__)

def require_login(f):
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Debe iniciar sesión'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@recomendaciones_bp.route('/recomendaciones')
@require_login
def recomendaciones():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Recomendaciones de Compra/Venta</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .header { background-color: #007bff; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .content { background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }
            .analysis-form { margin-bottom: 20px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
            .form-input { padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            .btn { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background-color: #0056b3; }
            .recommendation-card { background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #007bff; }
            .recommendation-strong { background-color: #d4edda; border-left-color: #28a745; }
            .recommendation-moderate { background-color: #fff3cd; border-left-color: #ffc107; }
            .recommendation-weak { background-color: #f8d7da; border-left-color: #dc3545; }
            .recommendation-title { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
            .recommendation-score { font-size: 18px; margin-bottom: 15px; }
            .indicators-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 20px; }
            .indicator-card { background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; }
            .indicator-title { font-weight: bold; margin-bottom: 10px; color: #333; }
            .indicator-value { font-size: 18px; font-weight: bold; }
            .indicator-signal { padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; margin-top: 5px; display: inline-block; }
            .signal-buy { background-color: #d4edda; color: #155724; }
            .signal-sell { background-color: #f8d7da; color: #721c24; }
            .signal-hold { background-color: #d1ecf1; color: #0c5460; }
            .loading { color: #6c757d; text-align: center; padding: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>💡 Recomendaciones de Compra/Venta</h1>
            <a href="/dashboard" style="color: white; text-decoration: none;">← Volver al Dashboard</a>
        </div>
        
        <div class="content">
            <div class="analysis-form">
                <input type="text" id="stockSymbol" class="form-input" placeholder="Símbolo (ej: AAPL)" value="AAPL" style="width: 150px;">
                <select id="analysisType" class="form-input">
                    <option value="comprehensive">Análisis Completo</option>
                    <option value="technical">Solo Técnico</option>
                    <option value="fundamental">Solo Fundamental</option>
                </select>
                <select id="timeframe" class="form-input">
                    <option value="short">Corto Plazo (1-3 meses)</option>
                    <option value="medium" selected>Mediano Plazo (3-12 meses)</option>
                    <option value="long">Largo Plazo (1+ años)</option>
                </select>
                <button onclick="generateRecommendation()" class="btn">Generar Recomendación</button>
            </div>
            
            <div id="recommendationCard" class="recommendation-card" style="display: none;">
                <div id="recommendationTitle" class="recommendation-title"></div>
                <div id="recommendationScore" class="recommendation-score"></div>
                <div id="recommendationDescription"></div>
            </div>
            
            <div id="indicatorsContainer" class="indicators-grid" style="display: none;"></div>
            
            <div id="loading" class="loading" style="display: none;">Analizando indicadores y generando recomendación...</div>
            <div id="error" style="color: red; display: none;"></div>
        </div>
        
        <script>
            async function generateRecommendation() {
                const symbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
                const analysisType = document.getElementById('analysisType').value;
                const timeframe = document.getElementById('timeframe').value;
                
                if (!symbol) {
                    alert('Por favor ingrese un símbolo');
                    return;
                }
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('recommendationCard').style.display = 'none';
                document.getElementById('indicatorsContainer').style.display = 'none';
                document.getElementById('error').style.display = 'none';
                
                try {
                    const response = await fetch('/api/generate-recommendation', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ 
                            symbol: symbol,
                            analysis_type: analysisType,
                            timeframe: timeframe
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        displayRecommendation(data.data);
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
            
            function displayRecommendation(data) {
                // Mostrar recomendación principal
                const card = document.getElementById('recommendationCard');
                const title = document.getElementById('recommendationTitle');
                const score = document.getElementById('recommendationScore');
                const description = document.getElementById('recommendationDescription');
                
                // Determinar clase CSS basada en la recomendación
                card.className = 'recommendation-card';
                if (data.recommendation.action === 'COMPRAR') {
                    card.classList.add('recommendation-strong');
                } else if (data.recommendation.action === 'MANTENER') {
                    card.classList.add('recommendation-moderate');
                } else {
                    card.classList.add('recommendation-weak');
                }
                
                title.textContent = data.recommendation.action + ' - ' + data.company_name + ' (' + data.symbol + ')';
                score.textContent = 'Puntuación: ' + data.recommendation.score.toFixed(1) + '/10 (' + data.recommendation.confidence + ')';
                description.innerHTML = 
                    '<strong>Razón:</strong> ' + data.recommendation.reason + '<br><br>' +
                    '<strong>Precio objetivo:</strong> $' + data.recommendation.target_price.toFixed(2) + '<br>' +
                    '<strong>Stop loss sugerido:</strong> $' + data.recommendation.stop_loss.toFixed(2) + '<br>' +
                    '<strong>Horizonte temporal:</strong> ' + data.timeframe;
                
                card.style.display = 'block';
                
                // Mostrar indicadores
                const container = document.getElementById('indicatorsContainer');
                container.innerHTML = '';
                
                data.indicators.forEach(indicator => {
                    const indicatorCard = document.createElement('div');
                    indicatorCard.className = 'indicator-card';
                    
                    let signalClass = 'signal-hold';
                    if (indicator.signal === 'COMPRAR') signalClass = 'signal-buy';
                    else if (indicator.signal === 'VENDER') signalClass = 'signal-sell';
                    
                    indicatorCard.innerHTML = 
                        '<div class="indicator-title">' + indicator.name + '</div>' +
                        '<div class="indicator-value">' + indicator.value + '</div>' +
                        '<span class="indicator-signal ' + signalClass + '">' + indicator.signal + '</span>' +
                        '<div style="margin-top: 10px; font-size: 14px; color: #6c757d;">' + indicator.description + '</div>';
                    
                    container.appendChild(indicatorCard);
                });
                
                container.style.display = 'grid';
            }
            
            // Cargar recomendación inicial
            generateRecommendation();
        </script>
    </body>
    </html>
    '''

@recomendaciones_bp.route('/api/generate-recommendation', methods=['POST'])
@require_login
def api_generate_recommendation():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        analysis_type = data.get('analysis_type', 'comprehensive')
        timeframe = data.get('timeframe', 'medium')
        
        if not symbol:
            return jsonify({'success': False, 'message': 'Símbolo requerido'})
        
        # Obtener datos de la empresa
        ticker = yf.Ticker(symbol)
        info = ticker.info
        company_name = info.get('longName', symbol)
        
        # Obtener datos históricos
        hist_data = ticker.history(period="1y")
        
        if hist_data.empty:
            return jsonify({'success': False, 'message': 'No se pudieron obtener datos históricos'})
        
        # Calcular indicadores técnicos
        indicators = []
        
        if analysis_type in ['comprehensive', 'technical']:
            indicators.extend(calculate_technical_indicators(hist_data))
        
        if analysis_type in ['comprehensive', 'fundamental']:
            indicators.extend(calculate_fundamental_indicators(info, hist_data))
        
        # Generar recomendación basada en indicadores
        recommendation = generate_recommendation_from_indicators(indicators, hist_data, timeframe)
        
        result = {
            'symbol': symbol,
            'company_name': company_name,
            'analysis_type': analysis_type,
            'timeframe': timeframe,
            'recommendation': recommendation,
            'indicators': indicators,
            'analysis_date': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

def calculate_technical_indicators(hist_data):
    """Calcular indicadores técnicos"""
    indicators = []
    
    # Precios
    close_prices = hist_data['Close'].values
    high_prices = hist_data['High'].values
    low_prices = hist_data['Low'].values
    volume = hist_data['Volume'].values
    
    # RSI
    try:
        rsi = calculate_rsi(close_prices, 14)
        current_rsi = rsi[-1]
        
        if current_rsi < 30:
            rsi_signal = 'COMPRAR'
        elif current_rsi > 70:
            rsi_signal = 'VENDER'
        else:
            rsi_signal = 'MANTENER'
        
        indicators.append({
            'name': 'RSI (14)',
            'value': f'{current_rsi:.2f}',
            'signal': rsi_signal,
            'description': 'Índice de Fuerza Relativa. Valores < 30 indican sobreventa, > 70 sobrecompra.'
        })
    except:
        pass
    
    # MACD
    try:
        macd_line, macd_signal, macd_histogram = calculate_macd(close_prices)
        
        if macd_line[-1] > macd_signal[-1] and macd_line[-2] <= macd_signal[-2]:
            macd_signal_action = 'COMPRAR'
        elif macd_line[-1] < macd_signal[-1] and macd_line[-2] >= macd_signal[-2]:
            macd_signal_action = 'VENDER'
        else:
            macd_signal_action = 'MANTENER'
        
        indicators.append({
            'name': 'MACD',
            'value': f'{macd_line[-1]:.4f}',
            'signal': macd_signal_action,
            'description': 'Convergencia/Divergencia de Medias Móviles. Cruces indican cambios de tendencia.'
        })
    except:
        pass
    
    # Medias Móviles
    try:
        sma_20 = np.mean(close_prices[-20:])
        sma_50 = np.mean(close_prices[-50:])
        current_price = close_prices[-1]
        
        if current_price > sma_20 > sma_50:
            ma_signal = 'COMPRAR'
        elif current_price < sma_20 < sma_50:
            ma_signal = 'VENDER'
        else:
            ma_signal = 'MANTENER'
        
        indicators.append({
            'name': 'Medias Móviles',
            'value': f'SMA20: ${sma_20:.2f}',
            'signal': ma_signal,
            'description': 'Comparación entre precio actual y medias móviles de 20 y 50 días.'
        })
    except:
        pass
    
    # Bandas de Bollinger
    try:
        sma_20 = np.mean(close_prices[-20:])
        std_20 = np.std(close_prices[-20:])
        upper_band = sma_20 + (2 * std_20)
        lower_band = sma_20 - (2 * std_20)
        current_price = close_prices[-1]
        
        if current_price <= lower_band:
            bb_signal = 'COMPRAR'
        elif current_price >= upper_band:
            bb_signal = 'VENDER'
        else:
            bb_signal = 'MANTENER'
        
        indicators.append({
            'name': 'Bandas de Bollinger',
            'value': f'${current_price:.2f} ({lower_band:.2f}-{upper_band:.2f})',
            'signal': bb_signal,
            'description': 'Precio cerca de banda inferior sugiere compra, cerca de superior sugiere venta.'
        })
    except:
        pass
    
    return indicators

def calculate_fundamental_indicators(info, hist_data):
    """Calcular indicadores fundamentales"""
    indicators = []
    
    # P/E Ratio
    pe_ratio = info.get('trailingPE')
    if pe_ratio:
        if pe_ratio < 15:
            pe_signal = 'COMPRAR'
        elif pe_ratio > 25:
            pe_signal = 'VENDER'
        else:
            pe_signal = 'MANTENER'
        
        indicators.append({
            'name': 'P/E Ratio',
            'value': f'{pe_ratio:.2f}',
            'signal': pe_signal,
            'description': 'Relación precio/ganancias. Valores bajos pueden indicar infravaloración.'
        })
    
    # Dividend Yield
    dividend_yield = info.get('dividendYield')
    if dividend_yield:
        dividend_yield_percent = dividend_yield * 100
        
        if dividend_yield_percent > 4:
            div_signal = 'COMPRAR'
        elif dividend_yield_percent < 1:
            div_signal = 'MANTENER'
        else:
            div_signal = 'MANTENER'
        
        indicators.append({
            'name': 'Rendimiento por Dividendo',
            'value': f'{dividend_yield_percent:.2f}%',
            'signal': div_signal,
            'description': 'Porcentaje de dividendos respecto al precio. Valores altos pueden ser atractivos.'
        })
    
    # Market Cap
    market_cap = info.get('marketCap')
    if market_cap:
        market_cap_b = market_cap / 1e9
        
        if market_cap_b > 200:
            cap_signal = 'MANTENER'
            cap_desc = 'Gran capitalización - Estabilidad'
        elif market_cap_b > 10:
            cap_signal = 'MANTENER'
            cap_desc = 'Mediana capitalización - Balance riesgo/retorno'
        else:
            cap_signal = 'COMPRAR'
            cap_desc = 'Pequeña capitalización - Mayor potencial de crecimiento'
        
        indicators.append({
            'name': 'Capitalización de Mercado',
            'value': f'${market_cap_b:.1f}B',
            'signal': cap_signal,
            'description': cap_desc
        })
    
    # Price to Book
    price_to_book = info.get('priceToBook')
    if price_to_book:
        if price_to_book < 1:
            pb_signal = 'COMPRAR'
        elif price_to_book > 3:
            pb_signal = 'VENDER'
        else:
            pb_signal = 'MANTENER'
        
        indicators.append({
            'name': 'Precio/Valor en Libros',
            'value': f'{price_to_book:.2f}',
            'signal': pb_signal,
            'description': 'Relación entre precio y valor contable. Valores < 1 pueden indicar infravaloración.'
        })
    
    return indicators

def generate_recommendation_from_indicators(indicators, hist_data, timeframe):
    """Generar recomendación basada en indicadores"""
    
    # Contar señales
    buy_signals = sum(1 for ind in indicators if ind['signal'] == 'COMPRAR')
    sell_signals = sum(1 for ind in indicators if ind['signal'] == 'VENDER')
    hold_signals = sum(1 for ind in indicators if ind['signal'] == 'MANTENER')
    
    total_signals = len(indicators)
    
    if total_signals == 0:
        return {
            'action': 'MANTENER',
            'score': 5.0,
            'confidence': 'Baja',
            'reason': 'Datos insuficientes para análisis',
            'target_price': hist_data['Close'].iloc[-1],
            'stop_loss': hist_data['Close'].iloc[-1] * 0.9
        }
    
    # Calcular puntuación
    buy_ratio = buy_signals / total_signals
    sell_ratio = sell_signals / total_signals
    
    current_price = hist_data['Close'].iloc[-1]
    
    if buy_ratio >= 0.6:
        action = 'COMPRAR'
        score = 7 + (buy_ratio - 0.6) * 7.5
        confidence = 'Alta' if buy_ratio >= 0.8 else 'Media'
        reason = f'{buy_signals} de {total_signals} indicadores sugieren compra'
        target_price = current_price * 1.15  # 15% objetivo
        stop_loss = current_price * 0.92     # 8% stop loss
    elif sell_ratio >= 0.6:
        action = 'VENDER'
        score = 3 - (sell_ratio - 0.6) * 7.5
        confidence = 'Alta' if sell_ratio >= 0.8 else 'Media'
        reason = f'{sell_signals} de {total_signals} indicadores sugieren venta'
        target_price = current_price * 0.85  # 15% objetivo a la baja
        stop_loss = current_price * 1.08     # 8% stop loss
    else:
        action = 'MANTENER'
        score = 5.0
        confidence = 'Media'
        reason = 'Señales mixtas, se recomienda mantener posición actual'
        target_price = current_price
        stop_loss = current_price * 0.95     # 5% stop loss
    
    # Ajustar por horizonte temporal
    if timeframe == 'short':
        target_price = current_price + (target_price - current_price) * 0.5
    elif timeframe == 'long':
        target_price = current_price + (target_price - current_price) * 1.5
    
    return {
        'action': action,
        'score': max(0, min(10, score)),
        'confidence': confidence,
        'reason': reason,
        'target_price': target_price,
        'stop_loss': stop_loss
    }

def calculate_rsi(prices, period=14):
    """Calcular RSI"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gains = np.convolve(gains, np.ones(period)/period, mode='valid')
    avg_losses = np.convolve(losses, np.ones(period)/period, mode='valid')
    
    rs = avg_gains / (avg_losses + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calcular MACD"""
    ema_fast = pd.Series(prices).ewm(span=fast).mean()
    ema_slow = pd.Series(prices).ewm(span=slow).mean()
    
    macd_line = ema_fast - ema_slow
    macd_signal = macd_line.ewm(span=signal).mean()
    macd_histogram = macd_line - macd_signal
    
    return macd_line.values, macd_signal.values, macd_histogram.values

