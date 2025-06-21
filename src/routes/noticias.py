from flask import Blueprint, request, jsonify, session
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

noticias_bp = Blueprint('noticias', __name__)

def require_login(f):
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Debe iniciar sesión'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@noticias_bp.route('/analisis-noticias')
@require_login
def analisis_noticias():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Análisis de Noticias Financieras</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .header { background-color: #007bff; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .content { background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }
            .search-form { margin-bottom: 20px; }
            .search-input { padding: 10px; margin-right: 10px; border: 1px solid #ddd; border-radius: 4px; width: 300px; }
            .btn { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background-color: #0056b3; }
            .news-item { margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #007bff; }
            .news-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #333; }
            .news-summary { margin-bottom: 10px; line-height: 1.5; }
            .news-sentiment { padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
            .sentiment-positive { background-color: #d4edda; color: #155724; }
            .sentiment-negative { background-color: #f8d7da; color: #721c24; }
            .sentiment-neutral { background-color: #d1ecf1; color: #0c5460; }
            .news-source { font-size: 12px; color: #6c757d; margin-top: 10px; }
            .loading { color: #6c757d; text-align: center; padding: 20px; }
            .analysis-summary { background-color: #e9ecef; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📰 Análisis de Noticias Financieras</h1>
            <a href="/dashboard" style="color: white; text-decoration: none;">← Volver al Dashboard</a>
        </div>
        
        <div class="content">
            <div class="search-form">
                <input type="text" id="companySymbol" class="search-input" placeholder="Símbolo de empresa (ej: AAPL, GOOGL, TSLA)" value="AAPL">
                <button onclick="analyzeNews()" class="btn">Analizar Noticias</button>
            </div>
            
            <div id="analysisSummary" class="analysis-summary" style="display: none;">
                <h3>Resumen del Análisis</h3>
                <div id="summaryContent"></div>
            </div>
            
            <div id="newsContainer"></div>
            <div id="loading" class="loading" style="display: none;">Analizando noticias...</div>
            <div id="error" style="color: red; display: none;"></div>
        </div>
        
        <script>
            async function analyzeNews() {
                const symbol = document.getElementById('companySymbol').value.trim().toUpperCase();
                if (!symbol) {
                    alert('Por favor ingrese un símbolo');
                    return;
                }
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('newsContainer').innerHTML = '';
                document.getElementById('analysisSummary').style.display = 'none';
                document.getElementById('error').style.display = 'none';
                
                try {
                    const response = await fetch('/api/analyze-news', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ symbol: symbol })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        displayNewsAnalysis(data.data);
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
            
            function displayNewsAnalysis(data) {
                // Mostrar resumen
                const summaryContent = document.getElementById('summaryContent');
                summaryContent.innerHTML = 
                    '<strong>Empresa:</strong> ' + data.company_name + ' (' + data.symbol + ')<br>' +
                    '<strong>Total de noticias analizadas:</strong> ' + data.news.length + '<br>' +
                    '<strong>Sentimiento general:</strong> <span class="news-sentiment sentiment-' + data.overall_sentiment.toLowerCase() + '">' + 
                    data.overall_sentiment + '</span><br>' +
                    '<strong>Puntuación de sentimiento:</strong> ' + data.sentiment_score.toFixed(2) + '/5.0';
                
                document.getElementById('analysisSummary').style.display = 'block';
                
                // Mostrar noticias
                const container = document.getElementById('newsContainer');
                data.news.forEach(news => {
                    const newsElement = document.createElement('div');
                    newsElement.className = 'news-item';
                    newsElement.innerHTML = 
                        '<div class="news-title">' + news.title + '</div>' +
                        '<div class="news-summary">' + news.summary + '</div>' +
                        '<span class="news-sentiment sentiment-' + news.sentiment.toLowerCase() + '">' + 
                        news.sentiment + '</span>' +
                        '<div class="news-source">Fuente: ' + news.source + ' | ' + news.date + '</div>';
                    
                    container.appendChild(newsElement);
                });
            }
            
            // Cargar análisis inicial
            analyzeNews();
        </script>
    </body>
    </html>
    '''

@noticias_bp.route('/api/analyze-news', methods=['POST'])
@require_login
def api_analyze_news():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        
        if not symbol:
            return jsonify({'success': False, 'message': 'Símbolo requerido'})
        
        # Obtener información de la empresa
        ticker = yf.Ticker(symbol)
        info = ticker.info
        company_name = info.get('longName', symbol)
        
        # Simular análisis de noticias (en producción usarías APIs de noticias reales)
        news_data = generate_sample_news(symbol, company_name)
        
        # Calcular sentimiento general
        sentiment_scores = {'POSITIVO': 1, 'NEUTRAL': 0, 'NEGATIVO': -1}
        total_score = sum(sentiment_scores.get(news['sentiment'], 0) for news in news_data)
        avg_score = total_score / len(news_data) if news_data else 0
        
        # Determinar sentimiento general
        if avg_score > 0.3:
            overall_sentiment = 'POSITIVO'
        elif avg_score < -0.3:
            overall_sentiment = 'NEGATIVO'
        else:
            overall_sentiment = 'NEUTRAL'
        
        # Convertir a escala 1-5
        sentiment_score = (avg_score + 1) * 2.5
        
        result = {
            'symbol': symbol,
            'company_name': company_name,
            'news': news_data,
            'overall_sentiment': overall_sentiment,
            'sentiment_score': sentiment_score,
            'analysis_date': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

def generate_sample_news(symbol, company_name):
    """Genera noticias de ejemplo para demostración"""
    sample_news = [
        {
            'title': f'{company_name} reporta ganancias trimestrales sólidas',
            'summary': f'La empresa {company_name} ({symbol}) superó las expectativas de ganancias del trimestre, mostrando un crecimiento del 15% en ingresos comparado con el año anterior.',
            'sentiment': 'POSITIVO',
            'source': 'Financial Times',
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        },
        {
            'title': f'Analistas revisan al alza las proyecciones para {symbol}',
            'summary': f'Varios analistas de Wall Street han aumentado sus objetivos de precio para {company_name} después de los resultados positivos del último trimestre.',
            'sentiment': 'POSITIVO',
            'source': 'Reuters',
            'date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        },
        {
            'title': f'Preocupaciones sobre la cadena de suministro afectan a {symbol}',
            'summary': f'{company_name} enfrenta desafíos en su cadena de suministro que podrían impactar la producción en el próximo trimestre.',
            'sentiment': 'NEGATIVO',
            'source': 'Bloomberg',
            'date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        },
        {
            'title': f'{company_name} anuncia nueva estrategia de sostenibilidad',
            'summary': f'La empresa ha presentado un plan ambicioso para reducir su huella de carbono en un 50% para 2030, lo que podría atraer inversores ESG.',
            'sentiment': 'POSITIVO',
            'source': 'Wall Street Journal',
            'date': (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d')
        },
        {
            'title': f'Volatilidad del mercado afecta el sector de {symbol}',
            'summary': f'La incertidumbre económica global ha generado volatilidad en el sector, afectando a empresas como {company_name}.',
            'sentiment': 'NEUTRAL',
            'source': 'CNBC',
            'date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        }
    ]
    
    return sample_news

