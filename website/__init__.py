from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from concurrent.futures import ThreadPoolExecutor

mail = Mail()
executor = ThreadPoolExecutor(max_workers=4)
db = SQLAlchemy()

def createApp():
    app = Flask(__name__)
    from config import Config
    app.config.from_object(Config)

    mail.init_app(app)

    

    from .auth import auth
    from .views import views
    from .models import User, Appointments

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/logged/')

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def user_loader(id):
        return User.query.get(id)


    with app.app_context():
        db.init_app(app)
        db.create_all()

    return app