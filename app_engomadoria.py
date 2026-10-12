from datetime import datetime
import hashlib
import os
import re
import pandas as pd
import psycopg2
import streamlit as st

# ==========================================
# 1. CONFIGURAÇÃO DA BASE DE DADOS
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
    import sqlite3

    conn = sqlite3.connect("engomadoria_faial_fallback.db")
    return conn, "SQLite (Fallback)"


class GestorBaseDados:

  def __init__(self):
    self.conn, self.tipo_db = obter_conexao()
    self.criar_tabelas()
    self.carregar_precario_inicial()

  def criar_tabelas(self):
    cursor = self.conn.cursor()
    if "PostgreSQL" in self.tipo_db:
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS precario (
                    id SERIAL PRIMARY KEY,
                    categoria TEXT NOT NULL,
                    item TEXT NOT NULL,
                    preco_eur NUMERIC(10,2) NOT NULL,
                    descricao TEXT,
                    limite_pecas INTEGER DEFAULT 50
                );
                CREATE TABLE IF NOT EXISTS clientes (
                    id SERIAL PRIMARY KEY,
                    num_ficha TEXT UNIQUE NOT NULL,
                    nome TEXT NOT NULL,
                    contacto TEXT,
                    data_inicio DATE,
                    data_fim DATE,
                    assinatura TEXT,
                    status TEXT DEFAULT 'Ativo'
                );
                CREATE TABLE IF NOT EXISTS pedidos (
                    id SERIAL PRIMARY KEY,
                    num_ficha TEXT,
                    pack_limite TEXT,
                    itens_detalhe TEXT,
                    total_eur NUMERIC(10,2),
                    status_fabrica TEXT DEFAULT 'EM PROCESSO',
                    data_registo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    else:
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS precario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    categoria TEXT NOT NULL,
                    item TEXT NOT NULL,
                    preco_eur REAL NOT NULL,
                    descricao TEXT,
                    limite_pecas INTEGER DEFAULT 50
                );
            """)
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    num_ficha TEXT UNIQUE NOT NULL,
                    nome TEXT NOT NULL,
                    contacto TEXT,
                    data_inicio TEXT,
                    data_fim TEXT,
                    assinatura TEXT,
                    status TEXT DEFAULT 'Ativo'
                );
            """)
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    num_ficha TEXT,
                    pack_limite TEXT,
                    itens_detalhe TEXT,
                    total_eur REAL,
                    status_fabrica TEXT DEFAULT 'EM PROCESSO',
                    data_registo TEXT
                );
            """)
    self.conn.commit()
    cursor.close()

  def carregar_precario_inicial(self):
    cursor = self.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM precario")
    count = cursor.fetchone()[0]
    if count == 0:
      dados = [
          ("PACK", "25 PEÇAS", 18.00, "Pacote até 25 peças", 25),
          ("PACK", "50 PEÇAS", 23.00, "Pacote até 50 peças", 50),
          ("PACK", "100 PEÇAS", 33.00, "Pacote até 100 peças", 100),
          (
              "PACK",
              "PACK 15 CAMISAS/VESTIDOS",
              23.50,
              "Pacote de 15 camisas ou vestidos",
              15,
          ),
          (
              "PACK",
              "PACK LENÇÓIS (10 JOGOS)",
              33.00,
              "10 Jogos de lençóis/capas/almofadas",
              10,
          ),
          ("PACK", "PACK MISTO 50 PEÇAS", 60.00, "Pacote misto de 50 peças", 50),
          ("PACK", "PACK MISTO 100 PEÇAS", 70.00, "Pacote misto de 100 peças", 100),
          ("INDIVIDUAL", "ROUPA BÁSICA", 0.85, "Valor por peça individual", 1),
          ("INDIVIDUAL", "CAMISAS", 2.50, "Valor por peça individual", 1),
          ("INDIVIDUAL", "VESTIDOS", 3.00, "Valor por peça individual", 1),
      ]
      ph = "%s, %s, %s, %s, %s" if "PostgreSQL" in self.tipo_db else "?, ?, ?, ?, ?"
      for cat, item, preco, desc, lim in dados:
        cursor.execute(
            f"INSERT INTO precario (categoria, item, preco_eur, descricao, limite_pecas) VALUES ({ph})",
            (cat, item, preco, desc, lim),
        )
      self.conn.commit()
    cursor.close()


# ==========================================
# 2. INTERFACE WEB (Streamlit)
# ==========================================
st.set_page_config(
    page_title="Engomadoria do Faial - Sistema de Gestão",
    layout="wide",
    page_icon="🧺",
)

db = GestorBaseDados()

# Cabeçalho Principal da Loja
st.title("🧺 Engomadoria do Faial")
st.markdown("---")

# Ecrã Inicial com os 2 Botões Principais
col_nav1, col_nav2 = st.columns(2)
with col_nav1:
  btn_novo = st.button(
      "➕ Novo Cliente", use_container_width=True, type="primary"
  )
with col_nav2:
  btn_lista = st.button(
      "📋 Lista de Clientes (Histórico)", use_container_width=True
  )

if "modo_app" not in st.session_state:
  st.session_state.modo_app = "Novo Cliente"

if btn_novo:
  st.session_state.modo_app = "Novo Cliente"
if btn_lista:
  st.session_state.modo_app = "Lista de Clientes"

# ------------------------------------------
# SECÇÃO 1: NOVO CLIENTE & REGISTO DE PEDIDO
# ------------------------------------------
if st.session_state.modo_app == "Novo Cliente":
  st.subheader("📝 Ficha de Registo — Novo Cliente & Entrada de Roupa")

  col_esq, col_dir = st.columns([1, 1], gap="large")

  with col_esq:
    st.markdown("### 👤 Dados do Cliente")
    num_ficha = st.text_input(
        "Número do Pedido / Ficha", value=f"F#{datetime.now().strftime('%H%M%S')}"
    )
    nome_cliente = st.text_input("Nome do Cliente")
    contacto = st.text_input("Contacto Telefónico")

    col_d1, col_d2 = st.columns(2)
    with col_d1:
      data_inicio = st.date_input(
          "Data de Início", value=datetime.today().date()
      )
    with col_d2:
      data_fim = st.date_input("Data de Fim (Previsão)", value=datetime.today())

    st.markdown("### ✍️ Assinatura do Cliente")
    assinatura_cliente = st.text_input(
        "Assinatura Digital / Confirmação do Cliente",
        placeholder="Escreva o nome ou rubrica digital do cliente",
    )

  with col_dir:
    st.markdown("### 📦 Seleção de Packs e Serviços (Disponíveis na Loja)")

    df_precario = pd.read_sql(
        "SELECT id, item, preco_eur, limite_pecas FROM precario", db.conn
    )
    opcoes_packs = {
        f"{row['item']} — {row['preco_eur']:.2f}€ (Lim: {row['limite_pecas']} pçs)": {
            "item": row["item"],
            "preco": row["preco_eur"],
            "limite": row["limite_pecas"],
        }
        for _, row in df_precario.iterrows()
    }

    pack_escolhido_str = st.selectbox(
        "Selecione o Pack da Loja:", list(opcoes_packs.keys())
    )
    dados_pack = opcoes_packs[pack_escolhido_str]

    if "carrinho_atual" not in st.session_state:
      st.session_state.carrinho_atual = []

    st.markdown("#### ➕ Adicionar / Acumular Packs (Pack1 + Pack2 + ...)")
    col_add1, col_add2 = st.columns(2)
    with col_add1:
      if st.button(
          f"Adicionar {dados_pack['item']}",
          type="primary",
          use_container_width=True,
      ):
        st.session_state.carrinho_atual.append({
            "pack": dados_pack["item"],
            "preco": dados_pack["preco"],
            "limite": dados_pack["limite"],
        })
        st.success(f"Adicionado ao pedido: {dados_pack['item']}")
    with col_add2:
      if st.button("🗑️ Limpar Adições", use_container_width=True):
        st.session_state.carrinho_atual = []
        st.rerun()

    if st.session_state.carrinho_atual:
      st.markdown("---")
      st.markdown("#### 🛒 Conjunto de Packs Acumulados neste Pedido:")
      df_carrinho = pd.DataFrame(st.session_state.carrinho_atual)
      st.dataframe(df_carrinho, use_container_width=True)

      total_eur = df_carrinho["preco"].sum()
      total_limite = df_carrinho["limite"].sum()

      st.metric("VALOR TOTAL A PAGAR", f"{total_eur:.2f} €")
      st.metric("LIMITE TOTAL DE PEÇAS", f"{total_limite} Peças")

      if st.button(
          "💾 Registar e Gravar Pedido na Base de Dados",
          type="primary",
          use_container_width=True,
      ):
        if nome_cliente and num_ficha:
          cursor = db.conn.cursor()
          itens_combinados = " + ".join([c["pack"] for c in st.session_state.carrinho_atual])
          pack_limite_str = f"Limite Total: {total_limite} pçs"

          ph = (
              "%s, %s, %s, %s, %s"
              if "PostgreSQL" in db.tipo_db
              else "?, ?, ?, ?, ?"
          )
          cursor.execute(
              f"INSERT INTO pedidos (num_ficha, pack_limite, itens_detalhe, total_eur, status_fabrica) VALUES ({ph})",
              (
                  num_ficha,
                  pack_limite_str,
                  itens_combinados,
                  float(total_eur),
                  "EM PROCESSO",
              ),
          )

          ph_cli = "%s, %s, %s, %s, %s, %s, %s" if "PostgreSQL" in db.tipo_db else "?, ?, ?, ?, ?, ?, ?"
          cursor.execute(
              f"INSERT INTO clientes (num_ficha, nome, contacto, data_inicio, data_fim, assinatura, status) VALUES ({ph_cli}) ON CONFLICT (num_ficha) DO NOTHING",
              (
                  num_ficha,
                  nome_cliente,
                  contacto,
                  str(data_inicio),
                  str(data_fim),
                  assinatura_cliente,
                  "Ativo",
              ),
          )
          db.conn.commit()
          cursor.close()

          st.balloons()
          st.success(
              f"Pedido da Ficha #{num_ficha} guardado com sucesso para"
              f" {nome_cliente}!"
          )
          st.session_state.carrinho_atual = []
        else:
          st.error(
              "Por favor preencha o Número de Ficha e o Nome do Cliente antes"
              " de gravar."
          )

# ------------------------------------------
# SECÇÃO 2: LISTA HISTÓRICA DE CLIENTES E PEDIDOS
# ------------------------------------------
elif st.session_state.modo_app == "Lista de Clientes":
  st.subheader("📋 Lista Histórica de Clientes e Pedidos Efetuados")

  df_cli_db = pd.read_sql("SELECT * FROM clientes", db.conn)
  df_ped_db = pd.read_sql("SELECT * FROM pedidos", db.conn)

  if not df_cli_db.empty:
    st.markdown("### 👥 Todos os Clientes Registados")
    st.dataframe(df_cli_db, use_container_width=True)

    st.markdown("### 📦 Histórico Consolidado de Pedidos e Packs por Cliente")
    if not df_ped_db.empty:
      st.dataframe(df_ped_db, use_container_width=True)
    else:
      st.info("Ainda não existem pedidos registados.")

    st.markdown("### ⚙️ Gestão / Alterar Estado do Cliente")
    ficha_sel = st.selectbox(
        "Selecione o Nº de Ficha / Pedido", df_cli_db["num_ficha"].tolist()
    )
    acao = st.radio(
        "Ação:", ["Marcar como Concluído / Inativo", "Reativar Cliente", "Eliminar Registo"]
    )

    if st.button("Aplicar Alteração"):
      cursor = db.conn.cursor()
      if acao == "Eliminar Registo":
        ph = "%s" if "PostgreSQL" in db.tipo_db else "?"
        cursor.execute(f"DELETE FROM clientes WHERE num_ficha = {ph}", (ficha_sel,))
        cursor.execute(f"DELETE FROM pedidos WHERE num_ficha = {ph}", (ficha_sel,))
        st.warning(f"Registo da ficha {ficha_sel} eliminado.")
      else:
        novo_st = "Inativo" if acao == "Marcar como Concluído / Inativo" else "Ativo"
        ph = "%s, %s" if "PostgreSQL" in db.tipo_db else "?, ?"
        cursor.execute(
            f"UPDATE clientes SET status = {'%s' if 'PostgreSQL' in db.tipo_db else '?'} WHERE num_ficha = {'%s' if 'PostgreSQL' in db.tipo_db else '?'}",
            (novo_st, ficha_sel),
        )
        st.success(f"Estado alterado para: {novo_st}")
      db.conn.commit()
      cursor.close()
      st.rerun()
  else:
    st.info("Ainda não existem clientes registados no sistema.")