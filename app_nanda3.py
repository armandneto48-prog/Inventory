import os
import sqlite3
import pandas as pd
import psycopg2
import streamlit as st

# ==========================================
# 1. CONFIGURAÇÃO E LIGAÇÃO À BASE DE DADOS
# ==========================================
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "inventario_loja")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "sua_senha")
DB_PORT = os.getenv("DB_PORT", "5432")


def obter_conexao():
  try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
    )
    return conn, "PostgreSQL"
  except Exception:
    conn = sqlite3.connect("inventario_loja.db")
    return conn, "SQLite"


class GestorBaseDados:

  def __init__(self):
    self.conn, self.tipo_db = obter_conexao()
    self.criar_tabelas()
    self.carregar_servicos_iniciais()

  def criar_tabelas(self):
    cursor = self.conn.cursor()
    if "PostgreSQL" in self.tipo_db:
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id SERIAL PRIMARY KEY,
                    nome TEXT NOT NULL,
                    telefone TEXT UNIQUE NOT NULL
                );
                CREATE TABLE IF NOT EXISTS servicos (
                    id SERIAL PRIMARY KEY,
                    nome_servico TEXT NOT NULL,
                    preco_eur NUMERIC(10,2) NOT NULL
                );
                CREATE TABLE IF NOT EXISTS pedidos (
                    id SERIAL PRIMARY KEY,
                    cliente_id INTEGER REFERENCES clientes(id),
                    servico_id INTEGER REFERENCES servicos(id),
                    status TEXT DEFAULT 'Pendente',
                    data_registo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    else:
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    telefone TEXT UNIQUE NOT NULL
                );
            """)
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS servicos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_servico TEXT NOT NULL,
                    preco_eur REAL NOT NULL
                );
            """)
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    servico_id INTEGER,
                    status TEXT DEFAULT 'Pendente',
                    data_registo TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(cliente_id) REFERENCES clientes(id),
                    FOREIGN KEY(servico_id) REFERENCES servicos(id)
                );
            """)
    self.conn.commit()
    cursor.close()

  def carregar_servicos_iniciais(self):
    cursor = self.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM servicos")
    if cursor.fetchone()[0] == 0:
      servicos_padrao = [
          ("Pack 25 Peças", 18.00),
          ("Pack 50 Peças", 23.00),
          ("Pack 100 Peças", 33.00),
          ("Pack 15 Camisas/Vestidos", 23.50),
          ("Pack Lençóis (2 Meses / 10 Jogos)", 33.00),
          ("Lavar Roupa Básica (Unidade)", 0.85),
          ("Passar Camisa (Unidade)", 2.50),
          ("Lavar Capa Edredão", 3.00),
      ]
      ph = "%s, %s" if "PostgreSQL" in self.tipo_db else "?, ?"
      cursor.executemany(
          f"INSERT INTO servicos (nome_servico, preco_eur) VALUES ({ph})",
          servicos_padrao,
      )
      self.conn.commit()
    cursor.close()


# ==========================================
# 2. INTERFACE WEB (Streamlit)
# ==========================================
st.set_page_config(
    page_title="Gestão de Clientes e Serviços", layout="wide", page_icon="🧺"
)
db = GestorBaseDados()

st.title("🧺 Sistema de Engomadoria da Zeza")

aba1, aba2 = st.tabs(
    ["👤 1. Registo de Cliente", "📋 2. Consulta, Pedidos e Progresso"]
)

# ------------------------------------------
# TELA 1: REGISTO DE CLIENTE
# ------------------------------------------
with aba1:
  st.subheader("Registar Novo Cliente")
  with st.form("form_cliente", clear_on_submit=True):
    nome_input = st.text_input("Nome do Cliente")
    telefone_input = st.text_input("Número de Telefone")
    submetido = st.form_submit_button("💾 Guardar Cliente", type="primary")

    if submetido:
      if nome_input and telefone_input:
        cursor = db.conn.cursor()
        try:
          ph = "%s, %s" if "PostgreSQL" in db.tipo_db else "?, ?"
          cursor.execute(
              f"INSERT INTO clientes (nome, telefone) VALUES ({ph})",
              (nome_input, telefone_input),
          )
          db.conn.commit()
          st.success(f"Cliente '{nome_input}' registado com sucesso!")
        except Exception as e:
          st.error(
              "Erro ao registar cliente. Verifique se o telefone já existe na"
              " base de dados."
          )
        finally:
          cursor.close()
      else:
        st.warning("Por favor, preencha o Nome e o Número de Telefone.")

# ------------------------------------------
# TELA 2: CONSULTA, DROPDOWN E PROGRESSO
# ------------------------------------------
with aba2:
  st.subheader("Consultar Cliente e Associar Serviços")

  # Buscar lista de clientes registados
  df_clientes = pd.read_sql("SELECT id, nome, telefone FROM clientes", db.conn)

  if not df_clientes.empty:
    opcoes_clientes = {
        f"{row['nome']} ({row['telefone']})": row["id"]
        for _, row in df_clientes.iterrows()
    }
    cliente_selecionado = st.selectbox(
        "Selecione um Cliente Registado:", list(opcoes_clientes.keys())
    )
    cliente_id = opcoes_clientes[cliente_selecionado]

    st.divider()

    # Dropdown da Tabela de Serviços
    df_servicos = pd.read_sql(
        "SELECT id, nome_servico, preco_eur FROM servicos", db.conn
    )
    opcoes_servicos = {
        f"{row['nome_servico']} — {row['preco_eur']:.2f}€": row["id"]
        for _, row in df_servicos.iterrows()
    }

    st.markdown("### Associar Novo Serviço")
    col_serv, col_btn = st.columns([3, 1])

    with col_serv:
      servico_selecionado = st.selectbox(
          "Lista de Serviços Disponíveis:", list(opcoes_servicos.keys())
      )
      servico_id = opcoes_servicos[servico_selecionado]

    with col_btn:
      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("➕ Gerar Pedido", type="primary"):
        cursor = db.conn.cursor()
        ph = "%s, %s" if "PostgreSQL" in db.tipo_db else "?, ?"
        cursor.execute(
            f"INSERT INTO pedidos (cliente_id, servico_id, status) VALUES ({ph},"
            " 'Pendente')",
            (cliente_id, servico_id),
        )
        db.conn.commit()
        cursor.close()
        st.success("Serviço associado e pedido gerado com sucesso!")
        st.rerun()

    st.divider()

    # Apresentar lista de serviços anexos ao mesmo cliente
    st.markdown(f"### 📑 Serviços Anexados ao Cliente: **{cliente_selecionado}**")

    query_pedidos = f"""
            SELECT p.id as pedido_id, s.nome_servico, s.preco_eur, p.status, p.data_registo
            FROM pedidos p
            JOIN servicos s ON p.servico_id = s.id
            WHERE p.cliente_id = {'%s' if 'PostgreSQL' in db.tipo_db else '?'}
        """

    cursor = db.conn.cursor()
    cursor.execute(
        query_pedidos,
        (cliente_id,),
    )
    rows = cursor.fetchall()
    cursor.close()

    if rows:
      df_pedidos_cliente = pd.DataFrame(
          rows,
          columns=[
              "ID Pedido",
              "Serviço",
              "Valor (€)",
              "Estado",
              "Data de Registo",
          ],
      )

      # Mostrar tabela de serviços com opção interativa de atualizar estado
      st.dataframe(df_pedidos_cliente, use_container_width=True)

      # Opção rápida para alterar estado do serviço
      col_sel_p, col_sel_st, col_btn_up = st.columns([2, 2, 1])
      with col_sel_p:
        ped_id = st.selectbox(
            "Alterar Estado do Pedido ID:", df_pedidos_cliente["ID Pedido"]
        )
      with col_sel_st:
        novo_st = st.selectbox(
            "Novo Estado:", ["Pendente", "Em Processo", "Efetuado"]
        )
      with col_btn_up:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Atualizar Estado"):
          cursor = db.conn.cursor()
          ph = "%s, %s" if "PostgreSQL" in db.tipo_db else "?, ?"
          cursor.execute(
              f"UPDATE pedidos SET status = {'%s' if 'PostgreSQL' in db.tipo_db else '?'} WHERE id = {'%s' if 'PostgreSQL' in db.tipo_db else '?'}",
              (novo_st, ped_id),
          )
          db.conn.commit()
          cursor.close()
          st.success("Estado atualizado!")
          st.rerun()

      st.divider()

      # Contabilização de Valores e Barra de Progresso do Serviço Efetuado
      val_total = df_pedidos_cliente["Valor (€)"].sum()
      val_efetuado = df_pedidos_cliente[
          df_pedidos_cliente["Estado"] == "Efetuado"
      ]["Valor (€)"].sum()

      pct_progresso = (val_efetuado / val_total) if val_total > 0 else 0.0

      st.markdown("### 📊 Progresso de Serviços Efetuados")
      col_m1, col_m2, col_m3 = st.columns(3)
      col_m1.metric("Valor Total Acumulado", f"{val_total:.2f} €")
      col_m2.metric("Valor Concluído (Efetuado)", f"{val_efetuado:.2f} €")
      col_m3.metric("Percentagem Concluída", f"{pct_progresso * 100:.1f} %")

      st.progress(
          min(pct_progresso, 1.0),
          text=(
              f"Progresso: {pct_progresso * 100:.1f}% dos serviços efetuados"
              f" ({val_efetuado:.2f}€ de {val_total:.2f}€)"
          ),
      )

    else:
      st.info(
          "Ainda não existem serviços associados a este cliente. Selecione um"
          " serviço no dropdown acima e clique em 'Gerar Pedido'."
      )

  else:
    st.warning(
        "Nenhum cliente registado no banco de dados. Vá à aba '1. Registo de"
        " Cliente' para adicionar o primeiro."
    )