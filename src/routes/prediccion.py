from flask import Blueprint, request, jsonify, session
import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

prediccion_bp = Blueprint('prediccion', __name__)

def require_login(f):
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Debe iniciar sesión'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@prediccion_bp.route('/prediccion-lstm')
@require_login
def prediccion_lstm():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Predicción de Precios con LSTM</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.plot.ly/plotly-2.27.1.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .header { background-color: #007bff; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .content { background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }
            .prediction-form { margin-bottom: 20px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
            .form-input { padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            .btn { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background-color: #0056b3; }
            .btn:disabled { background-color: #6c757d; cursor: not-allowed; }
            .prediction-summary { background-color: #e9ecef; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .prediction-result { background-color: #d4edda; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #28a745; }
            .chart-container { margin-top: 20px; }
            .loading { color: #6c757d; text-align: center; padding: 20px; }
            .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
            .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
            .metric-label { font-size: 14px; color: #6c757d; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 Predicción de Precios con LSTM</h1>
            <a href="/dashboard" style="color: white; text-decoration: none;">← Volver al Dashboard</a>
        </div>
        
        <div class="content">
            <div class="prediction-form">
                <input type="text" id="stockSymbol" class="form-input" placeholder="Símbolo (ej: AAPL)" value="AAPL" style="width: 150px;">
                <select id="predictionDays" class="form-input">
                    <option value="7">7 días</option>
                    <option value="15">15 días</option>
                    <option value="30" selected>30 días</option>
                </select>
                <select id="trainingPeriod" class="form-input">
                    <option value="1y">1 año</option>
                    <option value="2y" selected>2 años</option>
                    <option value="5y">5 años</option>
                </select>
                <button onclick="predictPrices()" class="btn" id="predictBtn">Generar Predicción</button>
            </div>
            
            <div id="predictionSummary" class="prediction-summary" style="display: none;">
                <h3>Resumen de la Predicción</h3>
                <div id="summaryContent"></div>
            </div>
            
            <div id="predictionResult" class="prediction-result" style="display: none;">
                <h3>Resultado de la Predicción</h3>
                <div id="resultContent"></div>
            </div>
            
            <div id="metricsContainer" class="metrics" style="display: none;"></div>
            
            <div id="chartContainer" class="chart-container"></div>
            <div id="loading" class="loading" style="display: none;">Entrenando modelo LSTM y generando predicciones...</div>
            <div id="error" style="color: red; display: none;"></div>
        </div>
        
        <script>
            async function predictPrices() {
                const symbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
                const predictionDays = parseInt(document.getElementById('predictionDays').value);
                const trainingPeriod = document.getElementById('trainingPeriod').value;
                
                if (!symbol) {
                    alert('Por favor ingrese un símbolo');
                    return;
                }
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('predictionSummary').style.display = 'none';
                document.getElementById('predictionResult').style.display = 'none';
                document.getElementById('metricsContainer').style.display = 'none';
                document.getElementById('chartContainer').innerHTML = '';
                document.getElementById('error').style.display = 'none';
                document.getElementById('predictBtn').disabled = true;
                
                try {
                    const response = await fetch('/api/predict-lstm', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ 
                            symbol: symbol,
                            prediction_days: predictionDays,
                            training_period: trainingPeriod
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        displayPredictionResults(data.data);
                    } else {
                        document.getElementById('error').textContent = data.message;
                        document.getElementById('error').style.display = 'block';
                    }
                } catch (error) {
                    document.getElementById('error').textContent = 'Error de conexión';
                    document.getElementById('error').style.display = 'block';
                } finally {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('predictBtn').disabled = false;
                }
            }
            
            function displayPredictionResults(data) {
                // Mostrar resumen
                const summaryContent = document.getElementById('summaryContent');
                summaryContent.innerHTML = 
                    '<strong>Empresa:</strong> ' + data.company_name + ' (' + data.symbol + ')<br>' +
                    '<strong>Período de entrenamiento:</strong> ' + data.training_period + '<br>' +
                    '<strong>Días de predicción:</strong> ' + data.prediction_days + '<br>' +
                    '<strong>Precio actual:</strong> $' + data.current_price.toFixed(2);
                
                document.getElementById('predictionSummary').style.display = 'block';
                
                // Mostrar resultado de predicción
                const resultContent = document.getElementById('resultContent');
                const priceChange = data.predicted_price - data.current_price;
                const changePercent = (priceChange / data.current_price) * 100;
                const trend = changePercent > 0 ? 'ALCISTA' : changePercent < 0 ? 'BAJISTA' : 'NEUTRAL';
                const trendColor = changePercent > 0 ? '#28a745' : changePercent < 0 ? '#dc3545' : '#6c757d';
                
                resultContent.innerHTML = 
                    '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">' +
                    '<div style="text-align: center;">' +
                    '<div style="font-size: 24px; font-weight: bold; color: ' + trendColor + ';">$' + data.predicted_price.toFixed(2) + '</div>' +
                    '<div style="font-size: 14px; color: #6c757d;">Precio Predicho</div>' +
                    '</div>' +
                    '<div style="text-align: center;">' +
                    '<div style="font-size: 24px; font-weight: bold; color: ' + trendColor + ';">' + 
                    (priceChange >= 0 ? '+' : '') + priceChange.toFixed(2) + '</div>' +
                    '<div style="font-size: 14px; color: #6c757d;">Cambio ($)</div>' +
                    '</div>' +
                    '<div style="text-align: center;">' +
                    '<div style="font-size: 24px; font-weight: bold; color: ' + trendColor + ';">' + 
                    (changePercent >= 0 ? '+' : '') + changePercent.toFixed(2) + '%</div>' +
                    '<div style="font-size: 14px; color: #6c757d;">Cambio (%)</div>' +
                    '</div>' +
                    '<div style="text-align: center;">' +
                    '<div style="font-size: 24px; font-weight: bold; color: ' + trendColor + ';">' + trend + '</div>' +
                    '<div style="font-size: 14px; color: #6c757d;">Tendencia</div>' +
                    '</div>' +
                    '</div>' +
                    '<div style="margin-top: 15px; padding: 10px; background-color: #f8f9fa; border-radius: 4px;">' +
                    '<strong>Confianza del modelo:</strong> ' + (data.model_confidence * 100).toFixed(1) + '%<br>' +
                    '<strong>Recomendación:</strong> ' + data.recommendation +
                    '</div>';
                
                document.getElementById('predictionResult').style.display = 'block';
                
                // Mostrar métricas del modelo
                const metricsContainer = document.getElementById('metricsContainer');
                metricsContainer.innerHTML = 
                    '<div class="metric-card">' +
                    '<div class="metric-value">' + data.model_metrics.mse.toFixed(4) + '</div>' +
                    '<div class="metric-label">MSE</div>' +
                    '</div>' +
                    '<div class="metric-card">' +
                    '<div class="metric-value">' + data.model_metrics.rmse.toFixed(4) + '</div>' +
                    '<div class="metric-label">RMSE</div>' +
                    '</div>' +
                    '<div class="metric-card">' +
                    '<div class="metric-value">' + (data.model_metrics.accuracy * 100).toFixed(1) + '%</div>' +
                    '<div class="metric-label">Precisión</div>' +
                    '</div>';
                
                document.getElementById('metricsContainer').style.display = 'grid';
                
                // Crear gráfico
                createPredictionChart(data);
            }
            
            function createPredictionChart(data) {
                const historicalTrace = {
                    x: data.historical_dates,
                    y: data.historical_prices,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Precio Histórico',
                    line: { color: '#007bff', width: 2 }
                };
                
                const predictionTrace = {
                    x: data.prediction_dates,
                    y: data.predicted_prices,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Predicción LSTM',
                    line: { color: '#dc3545', width: 2, dash: 'dash' },
                    marker: { size: 6 }
                };
                
                const layout = {
                    title: 'Predicción de Precios con LSTM - ' + data.symbol,
                    xaxis: { title: 'Fecha' },
                    yaxis: { title: 'Precio ($)' },
                    hovermode: 'x unified',
                    showlegend: true,
                    height: 500
                };
                
                Plotly.newPlot('chartContainer', [historicalTrace, predictionTrace], layout);
            }
            
            // Cargar predicción inicial
            predictPrices();
        </script>
    </body>
    </html>
    '''

@prediccion_bp.route('/api/predict-lstm', methods=['POST'])
@require_login
def api_predict_lstm():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        prediction_days = data.get('prediction_days', 30)
        training_period = data.get('training_period', '1y')
        
        if not symbol:
            return jsonify({'success': False, 'message': 'Símbolo requerido'})
        
        # Obtener datos históricos
        ticker = yf.Ticker(symbol)
        info = ticker.info
        company_name = info.get('longName', symbol)
        
        # Obtener datos históricos para entrenamiento
        hist_data = ticker.history(period=training_period)
        
        if hist_data.empty:
            return jsonify({'success': False, 'message': 'No se pudieron obtener datos históricos'})
        
        # Preparar datos para LSTM
        prices = hist_data['Close'].values.reshape(-1, 1)
        
        # Normalizar datos
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(prices)
        
        # Crear secuencias para LSTM
        sequence_length = 60  # Usar 60 días para predecir el siguiente
        X, y = create_sequences(scaled_data, sequence_length)
        
        if len(X) == 0:
            return jsonify({'success': False, 'message': 'Datos insuficientes para entrenamiento'})
        
        # Dividir datos en entrenamiento y prueba
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        # Crear y entrenar modelo LSTM
        model = create_lstm_model((sequence_length, 1))
        model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=0, validation_split=0.1)
        
        # Evaluar modelo
        train_predictions = model.predict(X_train)
        test_predictions = model.predict(X_test)
        
        # Calcular métricas
        train_mse = mean_squared_error(y_train, train_predictions)
        test_mse = mean_squared_error(y_test, test_predictions)
        rmse = np.sqrt(test_mse)
        
        # Calcular precisión (porcentaje de predicciones dentro del 5% del valor real)
        test_predictions_scaled = scaler.inverse_transform(test_predictions)
        y_test_scaled = scaler.inverse_transform(y_test.reshape(-1, 1))
        accuracy = np.mean(np.abs((test_predictions_scaled - y_test_scaled) / y_test_scaled) < 0.05)
        
        # Generar predicciones futuras
        last_sequence = scaled_data[-sequence_length:].reshape(1, sequence_length, 1) # Asegurarse de que sea 3D para la primera predicción
        future_predictions = []

        # Generar predicciones futuras
        # Asegurarse de que last_sequence sea 3D para la primera predicción
        # last_sequence debe ser (1, sequence_length, 1) para el modelo
        last_sequence = scaled_data[-sequence_length:].reshape(1, sequence_length, 1)
        future_predictions = []

        for _ in range(prediction_days):
            # Realizar la predicción
            next_pred = model.predict(last_sequence)
            
            # La predicción es un array 2D, por ejemplo [[valor]], necesitamos solo el valor
            predicted_value = next_pred[0, 0]
            future_predictions.append(predicted_value)

            # Actualizar la secuencia: quitar el primer elemento y añadir la nueva predicción
            # 1. Quitar el primer elemento de la secuencia (desplazar la ventana)
            # Esto toma todos los elementos excepto el primero a lo largo de la dimensión de la secuencia
            # El resultado sigue siendo 3D: (1, sequence_length - 1, 1)
            updated_sequence_part = last_sequence[:, 1:, :] 
            
            # 2. Reformar el valor predicho para que sea compatible con la concatenación (3D)
            # Debe tener la forma (1, 1, 1)
            new_input_value = np.array([[[predicted_value]]], dtype=np.float32) # Aseguramos que sea 3D y float32

            # 3. Concatenar la secuencia desplazada con el nuevo valor predicho
            # Concatenamos a lo largo del eje de los timesteps (axis=1)
            last_sequence = np.concatenate((updated_sequence_part, new_input_value), axis=1)

        # ... (resto del código)
        # Desnormalizar predicciones
        future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))
        
        # Preparar datos para respuesta
        current_price = float(hist_data['Close'].iloc[-1])
        predicted_price = float(future_predictions[-1][0])
        
        # Generar fechas para predicciones
        last_date = hist_data.index[-1]
        prediction_dates = [last_date + timedelta(days=i+1) for i in range(prediction_days)]
        
        # Calcular confianza del modelo
        model_confidence = max(0.5, min(0.95, accuracy))
        
        # Generar recomendación
        price_change_percent = (predicted_price - current_price) / current_price * 100
        if price_change_percent > 5:
            recommendation = "Considerar comprar o mantener posiciones existentes"
        elif price_change_percent < -5:
            recommendation = "Considerar vender o evitar nuevas posiciones"
        else:
            recommendation = "Mantener posiciones actuales, tendencia neutral"
        
        result = {
            'symbol': symbol,
            'company_name': company_name,
            'current_price': current_price,
            'predicted_price': predicted_price,
            'prediction_days': prediction_days,
            'training_period': training_period,
            'model_confidence': model_confidence,
            'recommendation': recommendation,
            'model_metrics': {
                'mse': float(test_mse),
                'rmse': float(rmse),
                'accuracy': float(accuracy)
            },
            'historical_dates': [date.strftime('%Y-%m-%d') for date in hist_data.index[-100:]],
            'historical_prices': hist_data['Close'].iloc[-100:].tolist(),
            'prediction_dates': [date.strftime('%Y-%m-%d') for date in prediction_dates],
            'predicted_prices': [float(pred[0]) for pred in future_predictions],
            'analysis_date': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

def create_sequences(data, sequence_length):
    """Crear secuencias para entrenamiento LSTM"""
    X, y = [], []
    for i in range(sequence_length, len(data)):
        X.append(data[i-sequence_length:i, 0])
        y.append(data[i, 0])
    return np.array(X), np.array(y)

def create_lstm_model(input_shape):
    """Crear modelo LSTM"""
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(50, return_sequences=True),
        Dropout(0.2),
        LSTM(50),
        Dropout(0.2),
        Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

    