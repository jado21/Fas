from flask import Blueprint, request, jsonify, session
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.utils
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint('dashboard_interactivo', __name__)

def require_login(f):
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Debe iniciar sesión'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@dashboard_bp.route('/dashboard-interactivo')
@require_login
def dashboard_interactivo():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard Interactivo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.plot.ly/plotly-2.27.1.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .header { background-color: #007bff; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .dashboard-controls { background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
            .form-input { padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            .btn { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background-color: #0056b3; }
            .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
            .dashboard-card { background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }
            .card-title { font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
            .metrics-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .metric-item { text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 8px; }
            .metric-value { font-size: 20px; font-weight: bold; color: #007bff; }
            .metric-label { font-size: 12px; color: #6c757d; margin-top: 5px; }
            .metric-change { font-size: 14px; margin-top: 5px; }
            .positive { color: #28a745; }
            .negative { color: #dc3545; }
            .loading { color: #6c757d; text-align: center; padding: 20px; }
            .chart-container { height: 400px; }
            .small-chart { height: 250px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Dashboard Interactivo</h1>
            <a href="/dashboard" style="color: white; text-decoration: none;">← Volver al Dashboard</a>
        </div>
        
        <div class="dashboard-controls">
            <input type="text" id="stockSymbol" class="form-input" placeholder="Símbolo principal" value="AAPL" style="width: 150px;">
            <input type="text" id="compareSymbols" class="form-input" placeholder="Comparar con (ej: GOOGL,MSFT)" value="GOOGL,MSFT" style="width: 200px;">
            <select id="timeRange" class="form-input">
                <option value="1mo">1 Mes</option>
                <option value="3mo">3 Meses</option>
                <option value="6mo" selected>6 Meses</option>
                <option value="1y">1 Año</option>
                <option value="2y">2 Años</option>
            </select>
            <button onclick="loadDashboard()" class="btn">Actualizar Dashboard</button>
            <button onclick="exportData()" class="btn" style="background-color: #28a745;">Exportar Datos</button>
        </div>
        
        <div id="metricsOverview" class="metrics-row"></div>
        
        <div class="dashboard-grid">
            <div class="dashboard-card">
                <div class="card-title">Gráfico de Precios Principal</div>
                <div id="mainChart" class="chart-container"></div>
            </div>
            
            <div class="dashboard-card">
                <div class="card-title">Comparación de Rendimientos</div>
                <div id="comparisonChart" class="chart-container"></div>
            </div>
            
            <div class="dashboard-card">
                <div class="card-title">Volumen de Transacciones</div>
                <div id="volumeChart" class="small-chart"></div>
            </div>
            
            <div class="dashboard-card">
                <div class="card-title">Indicadores Técnicos</div>
                <div id="technicalChart" class="small-chart"></div>
            </div>
            
            <div class="dashboard-card">
                <div class="card-title">Distribución de Retornos</div>
                <div id="returnsChart" class="small-chart"></div>
            </div>
            
            <div class="dashboard-card">
                <div class="card-title">Correlación de Mercado</div>
                <div id="correlationChart" class="small-chart"></div>
            </div>
        </div>
        
        <div id="loading" class="loading" style="display: none;">Cargando dashboard...</div>
        <div id="error" style="color: red; display: none;"></div>
        
        <script>
            async function loadDashboard() {
                const symbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
                const compareSymbols = document.getElementById('compareSymbols').value.trim().toUpperCase();
                const timeRange = document.getElementById('timeRange').value;
                
                if (!symbol) {
                    alert('Por favor ingrese un símbolo principal');
                    return;
                }
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('error').style.display = 'none';
                
                try {
                    const response = await fetch('/api/dashboard-data', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ 
                            symbol: symbol,
                            compare_symbols: compareSymbols,
                            time_range: timeRange
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        displayDashboard(data.data);
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
            
            function displayDashboard(data) {
                // Mostrar métricas generales
                displayMetricsOverview(data.metrics);
                
                // Crear gráficos
                createMainChart(data.main_chart);
                createComparisonChart(data.comparison_chart);
                createVolumeChart(data.volume_chart);
                createTechnicalChart(data.technical_chart);
                createReturnsChart(data.returns_chart);
                createCorrelationChart(data.correlation_chart);
            }
            
            function displayMetricsOverview(metrics) {
                const container = document.getElementById('metricsOverview');
                container.innerHTML = '';
                
                metrics.forEach(metric => {
                    const metricElement = document.createElement('div');
                    metricElement.className = 'metric-item';
                    
                    const changeClass = metric.change >= 0 ? 'positive' : 'negative';
                    const changeSymbol = metric.change >= 0 ? '+' : '';
                    
                    metricElement.innerHTML = 
                        '<div class="metric-value">' + metric.value + '</div>' +
                        '<div class="metric-label">' + metric.label + '</div>' +
                        '<div class="metric-change ' + changeClass + '">' + 
                        changeSymbol + metric.change.toFixed(2) + metric.unit + '</div>';
                    
                    container.appendChild(metricElement);
                });
            }
            
            function createMainChart(chartData) {
                const traces = chartData.traces.map(trace => ({
                    x: trace.x,
                    y: trace.y,
                    type: 'scatter',
                    mode: 'lines',
                    name: trace.name,
                    line: { color: trace.color, width: 2 }
                }));
                
                const layout = {
                    title: chartData.title,
                    xaxis: { title: 'Fecha' },
                    yaxis: { title: 'Precio ($)' },
                    hovermode: 'x unified',
                    showlegend: true,
                    height: 380
                };
                
                Plotly.newPlot('mainChart', traces, layout);
            }
            
            function createComparisonChart(chartData) {
                const traces = chartData.traces.map(trace => ({
                    x: trace.x,
                    y: trace.y,
                    type: 'scatter',
                    mode: 'lines',
                    name: trace.name,
                    line: { color: trace.color, width: 2 }
                }));
                
                const layout = {
                    title: chartData.title,
                    xaxis: { title: 'Fecha' },
                    yaxis: { title: 'Rendimiento (%)' },
                    hovermode: 'x unified',
                    showlegend: true,
                    height: 380
                };
                
                Plotly.newPlot('comparisonChart', traces, layout);
            }
            
            function createVolumeChart(chartData) {
                const trace = {
                    x: chartData.x,
                    y: chartData.y,
                    type: 'bar',
                    name: 'Volumen',
                    marker: { color: '#007bff', opacity: 0.7 }
                };
                
                const layout = {
                    title: chartData.title,
                    xaxis: { title: 'Fecha' },
                    yaxis: { title: 'Volumen' },
                    height: 230
                };
                
                Plotly.newPlot('volumeChart', [trace], layout);
            }
            
            function createTechnicalChart(chartData) {
                const traces = chartData.traces.map(trace => ({
                    x: trace.x,
                    y: trace.y,
                    type: 'scatter',
                    mode: 'lines',
                    name: trace.name,
                    line: { color: trace.color, width: 1 }
                }));
                
                const layout = {
                    title: chartData.title,
                    xaxis: { title: 'Fecha' },
                    yaxis: { title: 'Valor' },
                    showlegend: true,
                    height: 230
                };
                
                Plotly.newPlot('technicalChart', traces, layout);
            }
            
            function createReturnsChart(chartData) {
                const trace = {
                    x: chartData.x,
                    type: 'histogram',
                    name: 'Distribución',
                    marker: { color: '#28a745', opacity: 0.7 }
                };
                
                const layout = {
                    title: chartData.title,
                    xaxis: { title: 'Retorno Diario (%)' },
                    yaxis: { title: 'Frecuencia' },
                    height: 230
                };
                
                Plotly.newPlot('returnsChart', [trace], layout);
            }
            
            function createCorrelationChart(chartData) {
                const trace = {
                    z: chartData.z,
                    x: chartData.x,
                    y: chartData.y,
                    type: 'heatmap',
                    colorscale: 'RdBu',
                    zmid: 0
                };
                
                const layout = {
                    title: chartData.title,
                    height: 230
                };
                
                Plotly.newPlot('correlationChart', [trace], layout);
            }
            
            async function exportData() {
                try {
                    const response = await fetch('/api/export-dashboard', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ 
                            symbol: document.getElementById('stockSymbol').value.trim().toUpperCase(),
                            time_range: document.getElementById('timeRange').value
                        })
                    });
                    
                    if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.style.display = 'none';
                        a.href = url;
                        a.download = 'dashboard_data.csv';
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                    }
                } catch (error) {
                    alert('Error al exportar datos');
                }
            }
            
            // Cargar dashboard inicial
            loadDashboard();
        </script>
    </body>
    </html>
    '''

@dashboard_bp.route('/api/dashboard-data', methods=['POST'])
@require_login
def api_dashboard_data():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        compare_symbols = data.get('compare_symbols', '').upper().split(',')
        time_range = data.get('time_range', '6mo')
        
        if not symbol:
            return jsonify({'success': False, 'message': 'Símbolo requerido'})
        
        # Limpiar símbolos de comparación
        compare_symbols = [s.strip() for s in compare_symbols if s.strip()]
        
        # Obtener datos principales
        main_ticker = yf.Ticker(symbol)
        main_data = main_ticker.history(period=time_range)
        main_info = main_ticker.info
        
        if main_data.empty:
            return jsonify({'success': False, 'message': 'No se pudieron obtener datos'})
        
        # Preparar datos del dashboard
        dashboard_data = {
            'metrics': create_metrics_overview(main_data, main_info, symbol),
            'main_chart': create_main_chart_data(main_data, symbol),
            'comparison_chart': create_comparison_chart_data(symbol, compare_symbols, time_range),
            'volume_chart': create_volume_chart_data(main_data, symbol),
            'technical_chart': create_technical_chart_data(main_data, symbol),
            'returns_chart': create_returns_chart_data(main_data, symbol),
            'correlation_chart': create_correlation_chart_data([symbol] + compare_symbols, time_range)
        }
        
        return jsonify({'success': True, 'data': dashboard_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@dashboard_bp.route('/api/export-dashboard', methods=['POST'])
@require_login
def api_export_dashboard():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        time_range = data.get('time_range', '6mo')
        
        # Obtener datos
        ticker = yf.Ticker(symbol)
        hist_data = ticker.history(period=time_range)
        
        # Crear CSV
        csv_data = hist_data.to_csv()
        
        from flask import Response
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={symbol}_data.csv'}
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

def create_metrics_overview(data, info, symbol):
    """Crear métricas generales"""
    current_price = data['Close'].iloc[-1]
    previous_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
    price_change = current_price - previous_price
    price_change_percent = (price_change / previous_price) * 100 if previous_price != 0 else 0
    
    volume_avg = data['Volume'].mean()
    current_volume = data['Volume'].iloc[-1]
    volume_change = ((current_volume - volume_avg) / volume_avg) * 100 if volume_avg != 0 else 0
    
    high_52w = data['High'].max()
    low_52w = data['Low'].min()
    
    metrics = [
        {
            'label': f'Precio {symbol}',
            'value': f'${current_price:.2f}',
            'change': price_change_percent,
            'unit': '%'
        },
        {
            'label': 'Volumen',
            'value': f'{current_volume:,.0f}',
            'change': volume_change,
            'unit': '%'
        },
        {
            'label': 'Máximo 52S',
            'value': f'${high_52w:.2f}',
            'change': ((current_price - high_52w) / high_52w) * 100,
            'unit': '%'
        },
        {
            'label': 'Mínimo 52S',
            'value': f'${low_52w:.2f}',
            'change': ((current_price - low_52w) / low_52w) * 100,
            'unit': '%'
        }
    ]
    
    # Agregar P/E si está disponible
    pe_ratio = info.get('trailingPE')
    if pe_ratio:
        metrics.append({
            'label': 'P/E Ratio',
            'value': f'{pe_ratio:.2f}',
            'change': 0,
            'unit': ''
        })
    
    return metrics

def create_main_chart_data(data, symbol):
    """Crear datos del gráfico principal"""
    dates = [date.strftime('%Y-%m-%d') for date in data.index]
    
    return {
        'title': f'Precio de {symbol}',
        'traces': [
            {
                'x': dates,
                'y': data['Close'].tolist(),
                'name': f'{symbol} - Cierre',
                'color': '#007bff'
            },
            {
                'x': dates,
                'y': data['High'].tolist(),
                'name': f'{symbol} - Máximo',
                'color': '#28a745'
            },
            {
                'x': dates,
                'y': data['Low'].tolist(),
                'name': f'{symbol} - Mínimo',
                'color': '#dc3545'
            }
        ]
    }

def create_comparison_chart_data(main_symbol, compare_symbols, time_range):
    """Crear datos de comparación de rendimientos"""
    all_symbols = [main_symbol] + compare_symbols
    colors = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#6f42c1']
    
    traces = []
    
    for i, symbol in enumerate(all_symbols):
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=time_range)
            
            if not data.empty:
                # Calcular rendimientos acumulados
                returns = data['Close'].pct_change().fillna(0)
                cumulative_returns = (1 + returns).cumprod() - 1
                cumulative_returns_percent = cumulative_returns * 100
                
                dates = [date.strftime('%Y-%m-%d') for date in data.index]
                
                traces.append({
                    'x': dates,
                    'y': cumulative_returns_percent.tolist(),
                    'name': symbol,
                    'color': colors[i % len(colors)]
                })
        except:
            continue
    
    return {
        'title': 'Comparación de Rendimientos',
        'traces': traces
    }

def create_volume_chart_data(data, symbol):
    """Crear datos del gráfico de volumen"""
    dates = [date.strftime('%Y-%m-%d') for date in data.index]
    
    return {
        'title': f'Volumen de {symbol}',
        'x': dates,
        'y': data['Volume'].tolist()
    }

def create_technical_chart_data(data, symbol):
    """Crear datos de indicadores técnicos"""
    dates = [date.strftime('%Y-%m-%d') for date in data.index]
    
    # Calcular medias móviles
    sma_20 = data['Close'].rolling(window=20).mean()
    sma_50 = data['Close'].rolling(window=50).mean()
    
    # Calcular RSI simplificado
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return {
        'title': f'Indicadores Técnicos - {symbol}',
        'traces': [
            {
                'x': dates,
                'y': sma_20.tolist(),
                'name': 'SMA 20',
                'color': '#007bff'
            },
            {
                'x': dates,
                'y': sma_50.tolist(),
                'name': 'SMA 50',
                'color': '#28a745'
            }
        ]
    }

def create_returns_chart_data(data, symbol):
    """Crear datos de distribución de retornos"""
    daily_returns = data['Close'].pct_change().dropna() * 100
    
    return {
        'title': f'Distribución de Retornos Diarios - {symbol}',
        'x': daily_returns.tolist()
    }

def create_correlation_chart_data(symbols, time_range):
    """Crear datos de correlación"""
    try:
        # Obtener datos de todos los símbolos
        price_data = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=time_range)
                if not data.empty:
                    price_data[symbol] = data['Close']
            except:
                continue
        
        if len(price_data) < 2:
            return {
                'title': 'Correlación (datos insuficientes)',
                'x': [],
                'y': [],
                'z': []
            }
        
        # Crear DataFrame y calcular correlación
        df = pd.DataFrame(price_data)
        correlation_matrix = df.corr()
        
        return {
            'title': 'Matriz de Correlación',
            'x': correlation_matrix.columns.tolist(),
            'y': correlation_matrix.index.tolist(),
            'z': correlation_matrix.values.tolist()
        }
        
    except:
        return {
            'title': 'Correlación (error)',
            'x': [],
            'y': [],
            'z': []
        }

