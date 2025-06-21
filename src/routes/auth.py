from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__)

# Usuario de prueba (en producción esto debería estar en la base de datos)
USERS = {
    'admin': generate_password_hash('password123'),
    'user': generate_password_hash('user123')
}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Financial App</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <div style="max-width: 400px; margin: 100px auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2>Iniciar Sesión</h2>
                <form id="loginForm">
                    <div style="margin-bottom: 15px;">
                        <label for="username">Usuario:</label><br>
                        <input type="text" id="username" name="username" required style="width: 100%; padding: 8px; margin-top: 5px;">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label for="password">Contraseña:</label><br>
                        <input type="password" id="password" name="password" required style="width: 100%; padding: 8px; margin-top: 5px;">
                    </div>
                    <button type="submit" style="width: 100%; padding: 10px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Iniciar Sesión
                    </button>
                </form>
                <div id="message" style="margin-top: 15px; color: red;"></div>
                <div style="margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 4px;">
                    <strong>Usuarios de prueba:</strong><br>
                    admin / password123<br>
                    user / user123
                </div>
            </div>
            
            <script>
                document.getElementById('loginForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    
                    try {
                        const response = await fetch('/login', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ username, password })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            window.location.href = '/dashboard';
                        } else {
                            document.getElementById('message').textContent = data.message;
                        }
                    } catch (error) {
                        document.getElementById('message').textContent = 'Error de conexión';
                    }
                });
            </script>
        </body>
        </html>
        '''
    
    elif request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if username in USERS and check_password_hash(USERS[username], password):
            session['user'] = username
            return jsonify({'success': True, 'message': 'Login exitoso'})
        else:
            return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True, 'message': 'Logout exitoso'})

@auth_bp.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return '''
        <script>
            alert('Debe iniciar sesión primero');
            window.location.href = '/login';
        </script>
        '''
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Financial App</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .header { background-color: #007bff; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .nav { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
            .nav-item { background-color: white; padding: 15px; border-radius: 8px; text-decoration: none; color: #333; border: 1px solid #ddd; flex: 1; min-width: 200px; text-align: center; }
            .nav-item:hover { background-color: #f8f9fa; }
            .content { background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Dashboard Financiero</h1>
            <p>Bienvenido, ''' + session['user'] + '''</p>
            <button onclick="logout()" style="background-color: #dc3545; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                Cerrar Sesión
            </button>
        </div>
        
        <div class="nav">
            <a href="/precios-tiempo-real" class="nav-item">
                <h3>📈 Precios en Tiempo Real</h3>
                <p>Visualizar cotizaciones actuales</p>
            </a>
            <a href="/analisis-noticias" class="nav-item">
                <h3>📰 Análisis de Noticias</h3>
                <p>Noticias financieras relevantes</p>
            </a>
            <a href="/prediccion-lstm" class="nav-item">
                <h3>🤖 Predicción LSTM</h3>
                <p>Predicciones con IA</p>
            </a>
            <a href="/recomendaciones" class="nav-item">
                <h3>💡 Recomendaciones</h3>
                <p>Sugerencias de compra/venta</p>
            </a>
            <a href="/dashboard-interactivo" class="nav-item">
                <h3>📊 Dashboard Interactivo</h3>
                <p>Gráficos y análisis</p>
            </a>
        </div>
        
        <div class="content">
            <h2>Resumen del Mercado</h2>
            <p>Seleccione una de las opciones arriba para acceder a las diferentes funcionalidades del sistema.</p>
        </div>
        
        <script>
            async function logout() {
                try {
                    const response = await fetch('/logout', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });
                    
                    if (response.ok) {
                        window.location.href = '/login';
                    }
                } catch (error) {
                    console.error('Error al cerrar sesión:', error);
                }
            }
        </script>
    </body>
    </html>
    '''

