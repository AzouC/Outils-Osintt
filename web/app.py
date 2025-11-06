# web/app.py
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO
import asyncio
import json

def create_app(framework):
    app = Flask(__name__)
    socketio = SocketIO(app, async_mode='threading')
    
    @app.route('/')
    def index():
        return render_template('dashboard.html')
    
    @app.route('/investigate', methods=['POST'])
    async def investigate():
        data = request.json
        target_type = data.get('type')
        target_value = data.get('value')
        depth = data.get('depth', 2)
        
        results = await framework.investigate(target_type, target_value, depth)
        
        # Émettre les résultats en temps réel via WebSocket
        socketio.emit('investigation_update', results)
        
        return jsonify(results)
    
    @app.route('/monitoring')
    def monitoring():
        return render_template('monitoring.html')
    
    @app.route('/reports')
    def reports():
        return render_template('reports.html')
    
    @app.route('/visualization')
    def visualization():
        return render_template('visualization.html')
    
    return app
