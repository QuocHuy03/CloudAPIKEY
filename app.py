from flask import Flask
from api.voice import voice_bp
from api.image import image_bp
from api.clone_voice import clone_voice_bp
from api.music import music_bp
from api.make_video_ai import make_video_ai_bp
from api.merger_video_ai import merger_video_ai_bp
from routes.misc import misc_bp
from routes.admin import admin_bp
import os

def create_app():
    app = Flask(__name__)
    
    # Cấu hình secret key cho session
    app.secret_key = 'your-secret-key-change-this-in-production'
    
    # Performance optimizations
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600  # Cache static files for 1 hour
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    # Register blueprints
    app.register_blueprint(voice_bp, url_prefix='/api/voice')
    app.register_blueprint(image_bp, url_prefix='/api/image')
    app.register_blueprint(clone_voice_bp, url_prefix='/api/clone_voice')
    app.register_blueprint(music_bp, url_prefix='/api/music')
    app.register_blueprint(make_video_ai_bp, url_prefix='/api/make_video_ai')
    app.register_blueprint(merger_video_ai_bp, url_prefix='/api/merger_video_ai')
    app.register_blueprint(misc_bp)
    app.register_blueprint(admin_bp)
    
    # Performance middleware
    @app.after_request
    def add_performance_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Environment-based configuration
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    app.run(
        host=host, 
        port=port, 
        debug=debug_mode,
        threaded=True,  # Enable threading for better performance
        use_reloader=debug_mode
    )
