from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import psycopg2
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/movies'
app.config['COVER_FOLDER'] = 'static/capas'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'Kant22756700*')  # Variável de ambiente
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

# Configurações do banco de dados CockroachDB
DB_HOST = os.environ.get('DB_HOST', "leaner-bunny-2865.jxf.gcp-southamerica-east1.cockroachlabs.cloud")
DB_PORT = os.environ.get('DB_PORT', "26257")
DB_NAME = os.environ.get('DB_NAME', "stream")
DB_USER = os.environ.get('DB_USER', "boaventura_bit")
DB_PASSWORD = os.environ.get('DB_PASSWORD', "OlPY4AIfr5bClanV2XfF8g")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            sslmode='require'  # Ajuste conforme necessário
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

@app.route('/')
def index():
    filmes = fetch_filmes()
    if filmes is None:
        return "Erro ao conectar ao banco de dados.", 500

    return render_template('index.html', filmes=filmes)

def fetch_filmes():
    with get_db_connection() as conn:
        if conn is None:
            return None
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM filmes')
            return cursor.fetchall()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form['senha']
        if senha == app.config['SECRET_KEY']:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Senha incorreta, tente novamente.")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    filmes = fetch_filmes()
    if filmes is None:
        return "Erro ao conectar ao banco de dados.", 500

    return render_template('admin.html', filmes=filmes)

@app.route('/add_filme', methods=['POST'])
def add_filme():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    titulo = request.form['titulo']
    descricao = request.form['descricao']
    arquivo = request.files['arquivo']
    capa = request.files['capa']

    if arquivo and arquivo.filename and capa and capa.filename:
        try:
            video_filename = secure_filename(arquivo.filename)
            arquivo.save(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))
            
            capa_filename = secure_filename(capa.filename)
            capa.save(os.path.join(app.config['COVER_FOLDER'], capa_filename))

            with get_db_connection() as conn:
                if conn is None:
                    return "Erro ao conectar ao banco de dados.", 500
                with conn.cursor() as cursor:
                    cursor.execute(
                        'INSERT INTO filmes (titulo, descricao, arquivo, capa) VALUES (%s, %s, %s, %s)',
                        (titulo, descricao, video_filename, capa_filename)
                    )
                    conn.commit()
        except Exception as e:
            return render_template('admin.html', error=f"Erro ao salvar o filme: {e}")

    return redirect(url_for('admin'))

@app.route('/remove_filme/<int:filme_id>', methods=['POST'])
def remove_filme(filme_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        if conn is None:
            return "Erro ao conectar ao banco de dados.", 500
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM filmes WHERE id = %s', (filme_id,))
            conn.commit()

    return redirect(url_for('admin'))

@app.route('/filme/<int:filme_id>')
def filme(filme_id):
    conn = get_db_connection()
    if conn is None:
        return "Erro ao conectar ao banco de dados.", 500

    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM filmes WHERE id = %s', (filme_id,))
            filme = cursor.fetchone()
            if filme is None:
                return "Filme não encontrado!", 404
    except Exception as e:
        return f"Erro ao buscar filme: {e}", 500
    finally:
        conn.close()

    return render_template('movie.html', filme=filme)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
