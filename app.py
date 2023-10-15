from flask import Flask, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask_uploads import UploadNotAllowed, configure_uploads
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import sqlite3


app = Flask(__name__)

app.secret_key = 'sua_chave_secreta'  # Substitua por uma chave secreta segura

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meu_banco_de_dados.db'  # SQLite

db = SQLAlchemy()
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)


# Crie um conjunto de upload para imagens
images = UploadSet('images', IMAGES)
app.config['UPLOADED_IMAGES_DEST'] = 'C:\\Users\\Mcluc\\OneDrive\\Área de Trabalho\\ImobiLilo\\static\\images\\img'
# Configurar o Flask-Uploads para lidar com uploads de imagens
configure_uploads(app, (images,))

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255))  # Isso armazenará o nome do arquivo da imagem
    

with app.app_context():
    db.create_all()

class User(UserMixin):
    def __init__(self, user_id,is_admin=True):
        self.id = user_id
        self.is_admin = is_admin
        

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

""" Parte de rotas """
@app.route('/')
def index():
    properties = Property.query.all()
    return render_template('index.html', properties=properties)

@app.route('/login')
def login():    
    user = User(1)  # Simula um usuário autenticado
    login_user(user)
    return redirect(url_for('admin_properties'))

@app.route('/property/<int:property_id>')
def property(property_id):
    user = User(1)
    property = Property.query.get(property_id)
    if property:
        return render_template('property.html', property=property)
    else:
        return "Propriedade não encontrada."
    
@app.route('/admin/properties', methods=['GET', 'POST'])
@login_required
def admin_properties():
    user = User(1)
     
    if not current_user.is_admin:  
        return "Acesso negado. Você não é um administrador."
    
    properties = Property.query.all()
    return render_template('admin_properties.html', properties=properties)



@app.route('/admin/properties/create', methods=['GET', 'POST'])
@login_required
def create_property():
    if not current_user.is_admin:
        return "Acesso negado. Você não é um administrador."

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])

        # Verifique se foi enviado um arquivo de imagem
        if 'image' in request.files:
            image = request.files['image']

            # Verifique se o arquivo de imagem é permitido
            if image and allowed_file(image.filename):
                try:
                    # Salve a imagem no servidor
                    filename = images.save(image)
                except UploadNotAllowed:
                    return "Tipo de arquivo de imagem não permitido."

                # Crie uma nova propriedade com a imagem
                new_property = Property(title=title, description=description, price=price, image=filename)
            else:
                return "Arquivo de imagem não permitido."

        else:
            # Crie uma nova propriedade sem imagem
            new_property = Property(title=title, description=description, price=price)

        db.session.add(new_property)
        db.session.commit()

        return redirect(url_for('admin_properties'))

    return render_template('create_property.html')


@app.route('/admin/properties/edit/<int:property_id>', methods=['GET', 'POST'])
@login_required
def edit_property(property_id):
    if not current_user.is_admin:
        return "Acesso negado. Você não é um administrador."

    property = Property.query.get(property_id)

    if not property:
        return "Propriedade não encontrada."

    if request.method == 'POST':
        property.title = request.form['title']
        property.description = request.form['description']
        property.price = float(request.form['price'])

        db.session.commit()

        return redirect(url_for('admin_properties'))

    return render_template('admin_properties.html', property=property, properties = [])

@app.route('/admin/properties/delete/<int:property_id>', methods=['POST'])
@login_required
def delete_property(property_id):
    if not current_user.is_admin:
        return "Acesso negado. Você não é um administrador."

    property = Property.query.get(property_id)

    if not property:
        return "Propriedade não encontrada."

    db.session.delete(property)
    db.session.commit()

    return redirect(url_for('admin_properties'))

@app.route('/admin/properties/list')
@login_required
def list_properties():
    if not current_user.is_admin:
        return "Acesso negado. Você não é um administrador."

    properties = Property.query.all()
    return render_template('admin_properties.html', properties=properties)

# Rota para fazer logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

"""Parte que faz instanciações """

if __name__ == '__main__':
    with app.app_context():


        app.run(debug=True)