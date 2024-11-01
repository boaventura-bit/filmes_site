import sqlite3

def adicionar_coluna_capa():
    conn = sqlite3.connect('filmes.db')
    cursor = conn.cursor()
    
    # Tenta adicionar a coluna "capa" se ainda não existir
    try:
        cursor.execute("ALTER TABLE filmes ADD COLUMN capa TEXT")
        print("Coluna 'capa' adicionada com sucesso.")
    except sqlite3.OperationalError as e:
        print("Erro ao adicionar coluna 'capa':", e)
    
    conn.commit()
    conn.close()

# Chama a função para adicionar a coluna
adicionar_coluna_capa()
