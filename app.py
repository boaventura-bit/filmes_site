from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/movies'
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'  # Altere para uma chave forte
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

# Cria a pasta de uploads, se não existir
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_db_connection():
    conn = sqlite3.connect('filmes.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    filmes = conn.execute('SELECT * FROM filmes').fetchall()
    conn.close()
    return render_template('index.html', filmes=filmes)  # Renderiza a galeria de filmes

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form['senha']
        # Substitua 'sua_senha' pela senha desejada
        if senha == 'Kant22756700*':
            session['logged_in'] = True
            return redirect(url_for('admin'))  # Redireciona para a página de administração
        else:
            return render_template('login.html', error="Senha incorreta, tente novamente.")  # Retorna erro

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    filmes = conn.execute('SELECT * FROM filmes').fetchall()
    conn.close()
    return render_template('admin.html', filmes=filmes)

@app.route('/add_filme', methods=['POST'])
def add_filme():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    titulo = request.form['titulo']
    descricao = request.form['descricao']
    arquivo = request.files['arquivo']
    capa = request.files['capa']  # Novo campo para a capa

    if arquivo and arquivo.filename and capa and capa.filename:
        try:
            # Salva o vídeo e a capa nos diretórios apropriados
            video_filename = secure_filename(arquivo.filename)
            arquivo.save(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))
            
            capa_filename = secure_filename(capa.filename)
            capa.save(os.path.join(app.config['UPLOAD_FOLDER'], 'capas', capa_filename))  # Salva em uma subpasta "capas"
            
            conn = get_db_connection()
            conn.execute('INSERT INTO filmes (titulo, descricao, arquivo, capa) VALUES (?, ?, ?, ?)',
                         (titulo, descricao, video_filename, capa_filename))
            conn.commit()
            conn.close()
        except Exception as e:
            return render_template('admin.html', error=f"Erro ao salvar o filme: {e}")

    return redirect(url_for('admin'))

@app.route('/remove_filme/<int:filme_id>', methods=['POST'])
def remove_filme(filme_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM filmes WHERE id = ?', (filme_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))  # Redireciona para a página de administração

@app.route('/filme/<int:filme_id>')
def filme(filme_id):
    conn = get_db_connection()
    filme = conn.execute('SELECT * FROM filmes WHERE id = ?', (filme_id,)).fetchone()
    conn.close()
    if filme is None:
        return "Filme não encontrado!", 404
    return render_template('movie.html', filme=filme)

if __name__ == '__main__':
    app.run(debug=True)
