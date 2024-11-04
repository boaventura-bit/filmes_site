from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import psycopg2  # Biblioteca para conectar ao PostgreSQL (CockroachDB)
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/movies'
app.config['COVER_FOLDER'] = 'static/capas'  # Adicionada a pasta de capas
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'  # Altere para uma chave forte
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

# Configurações do banco de dados CockroachDB
DB_HOST = "leaner-bunny-2865.jxf.gcp-southamerica-east1.cockroachlabs.cloud"  # Substitua pelo seu host do CockroachDB
DB_PORT = "26257"  # Porta padrão do CockroachDB
DB_NAME = "stream"  # Nome do seu banco de dados
DB_USER = "boaventura_bit"  # Substitua pelo seu usuário
DB_PASSWORD = "OlPY4AIfr5bClanV2XfF8g"  # Substitua pela sua senha

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")  # Imprime o erro de conexão
        return None

@app.route('/')
def index():
    conn = get_db_connection()
    if conn is None:
        return "Erro ao conectar ao banco de dados.", 500
    
    try:
        cursor = conn.cursor()  # Crie um cursor válido
        cursor.execute('SELECT * FROM filmes')  # Execute a consulta
        filmes = cursor.fetchall()  # Obtenha todos os resultados
        cursor.close()  # Feche o cursor
    except Exception as e:
        return f"Erro ao buscar filmes: {e}", 500
    finally:
        conn.close()  # Garante que a conexão será fechada

    return render_template('index.html', filmes=filmes)  # Renderiza a galeria de filmes

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form['senha']
        if senha == 'Kant22756700*':
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

    conn = get_db_connection()
    if conn is None:
        return "Erro ao conectar ao banco de dados.", 500

    try:
        cursor = conn.cursor()  # Crie um cursor válido
        cursor.execute('SELECT * FROM filmes')  # Execute a consulta
        filmes = cursor.fetchall()  # Obtenha todos os resultados
    except Exception as e:
        return f"Erro ao buscar filmes: {e}", 500
    finally:
        conn.close()  # Garante que a conexão será fechada

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
            capa.save(os.path.join(app.config['COVER_FOLDER'], capa_filename))  # Salvar a capa no diretório específico
            
            conn = get_db_connection()
            if conn is None:
                return "Erro ao conectar ao banco de dados.", 500
            
            cursor = conn.cursor()  # Crie um cursor válido
            cursor.execute('INSERT INTO filmes (titulo, descricao, arquivo, capa) VALUES (%s, %s, %s, %s)',
                           (titulo, descricao, video_filename, capa_filename))
            conn.commit()
            cursor.close()  # Feche o cursor após a inserção
        except Exception as e:
            return render_template('admin.html', error=f"Erro ao salvar o filme: {e}")
        finally:
            conn.close()  # Garante que a conexão será fechada

    return redirect(url_for('admin'))

@app.route('/remove_filme/<int:filme_id>', methods=['POST'])
def remove_filme(filme_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        return "Erro ao conectar ao banco de dados.", 500

    try:
        cursor = conn.cursor()  # Crie um cursor válido
        cursor.execute('DELETE FROM filmes WHERE id = %s', (filme_id,))
        conn.commit()
        cursor.close()  # Feche o cursor após a exclusão
    except Exception as e:
        return f"Erro ao remover filme: {e}", 500
    finally:
        conn.close()  # Garante que a conexão será fechada

    return redirect(url_for('admin'))

@app.route('/filme/<int:filme_id>')
def filme(filme_id):
    conn = get_db_connection()
    if conn is None:
        return "Erro ao conectar ao banco de dados.", 500

    try:
        cursor = conn.cursor()  # Crie um cursor válido
        cursor.execute('SELECT * FROM filmes WHERE id = %s', (filme_id,))
        filme = cursor.fetchone()  # Obtenha um único resultado
        cursor.close()  # Feche o cursor
        if filme is None:
            return "Filme não encontrado!", 404
    except Exception as e:
        return f"Erro ao buscar filme: {e}", 500
    finally:
        conn.close()  # Garante que a conexão será fechada

    return render_template('movie.html', filme=filme)

if __name__ == '__main__':
    app.run(debug=True)
