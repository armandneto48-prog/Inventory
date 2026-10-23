from datetime import datetime, timedelta
import os
import sqlite3
import pandas as pd
import psycopg2
import streamlit as st

# Configuração de Conexão
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
        conn = sqlite3.connect("engomadoria_zeza.db")
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
                CREATE TABLE IF NOT EXISTS clientes_historico (
                    id SERIAL PRIMARY KEY,
                    nome TEXT NOT NULL,
                    telefone TEXT NOT NULL,
                    packs_escolhidos TEXT NOT NULL,
                    valor_total NUMERIC(10,2) NOT NULL,
                    data_inicio DATE NOT NULL,
                    data_fim DATE NOT NULL,
                    status TEXT DEFAULT 'Ativo',
                    data_registo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS servicos (
                    id SERIAL PRIMARY KEY,
                    nome_servico TEXT NOT NULL,
                    preco_eur NUMERIC(10,2) NOT NULL,
                    limite_pecas INTEGER DEFAULT 50
                );
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes_historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    telefone TEXT NOT NULL,
                    packs_escolhidos TEXT NOT NULL,
                    valor_total REAL NOT NULL,
                    data_inicio TEXT NOT NULL,
                    data_fim TEXT NOT NULL,
                    status TEXT DEFAULT 'Ativo',
                    data_registo TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS servicos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_servico TEXT NOT NULL,
                    preco_eur REAL NOT NULL,
                    limite_pecas INTEGER DEFAULT 50
                );
            """)
        self.conn.commit()
        cursor.close()

    def carregar_servicos_iniciais(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM servicos")
        if cursor.fetchone()[0] == 0:
            servicos_padrao = [
                ("Pack 25 Peças", 18.00, 25),
                ("Pack 50 Peças", 23.00, 50),
                ("Pack 100 Peças", 33.00, 100),
                ("Pack 15 Camisas/Vestidos", 23.50, 15),
                ("Pack Lençóis (10 Jogos)", 33.00, 10),
                ("Pack Misto 50 Peças", 60.00, 50),
            ]
            ph = "%s, %s, %s" if "PostgreSQL" in self.tipo_db else "?, ?, ?"
            cursor.executemany(
                f"INSERT INTO servicos (nome_servico, preco_eur, limite_pecas) VALUES ({ph})",
                servicos_padrao,
            )
            self.conn.commit()
        cursor.close()


st.set_page_config(
    page_title="Engomadoria do Faial", layout="wide", page_icon="🧺"
)
db = GestorBaseDados()

st.title("🧺 Engomadoria do Faial")

# Carregar serviços disponíveis da Base de Dados
df_servicos = pd.read_sql(
    "SELECT nome_servico, preco_eur, limite_pecas FROM servicos", db.conn
)

if "carrinho_balcao" not in st.session_state:
    st.session_state.carrinho_balcao = []

if "mostrar_clientes" not in st.session_state:
    st.session_state.mostrar_clientes = False

col_esq, col_dir = st.columns([1, 1], gap="large")

# --- COLUNA DA ESQUERDA: RESUMO DA FICHA E SELEÇÃO INICIAL ---
with col_esq:
    st.subheader("1️⃣ Seleção Inicial de Packs")
    pack_selecionado = st.selectbox(
        "Escolha o Pack da Loja:",
        df_servicos["nome_servico"].tolist(),
        key="sb_principal",
    )
    preco_pack = df_servicos[df_servicos["nome_servico"] == pack_selecionado][
        "preco_eur"
    ].values[0]
    limite_pack = df_servicos[df_servicos["nome_servico"] == pack_selecionado][
        "limite_pecas"
    ].values[0]

    if st.button("➕ Adicionar Pack à Ficha", type="primary"):
        st.session_state.carrinho_balcao.append(
            {"pack": pack_selecionado, "preco": preco_pack, "limite": limite_pack}
        )
        st.success(f"Adicionado: {pack_selecionado}")

    st.markdown("---")
    st.subheader("📋 Resumo do Pedido Atual")
    if st.session_state.carrinho_balcao:
        df_carr = pd.DataFrame(st.session_state.carrinho_balcao)
        st.dataframe(df_carr, use_container_width=True)
        total_val = df_carr["preco"].sum()
        total_lim = df_carr["limite"].sum()
        st.metric("Total a Pagar", f"{total_val:.2f} €")
        st.metric("Limite de Peças Acumulado", f"{total_lim} Pçs")

        if st.button("🗑️ Limpar Seleção"):
            st.session_state.carrinho_balcao = []
            st.rerun()
    else:
        st.info("Nenhum pack adicionado ao pedido.")

# --- COLUNA DA DIREITA: DADOS DO CLIENTE, SEGUNDA LISTA E GRAVAÇÃO ---
with col_dir:
    st.subheader("2️⃣ Dados do Cliente")
    nome_cli = st.text_input("Nome")
    tel_cli = st.text_input("Contacto")

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        data_ini = st.date_input("Data de Início", value=datetime.today())
    with col_d2:
        data_Fim = st.date_input(
            "Data Limite", value=datetime.today() + timedelta(days=30)
        )

    st.markdown("---")
    st.markdown("##### 📦 Adicionar Mais Packs")
    extra_pack_selecionado = st.selectbox(
        "Selecionar item ou pack adicional:",
        df_servicos["nome_servico"].tolist(),
        key="sb_extra",
    )
    extra_preco = df_servicos[
        df_servicos["nome_servico"] == extra_pack_selecionado
    ]["preco_eur"].values[0]
    extra_limite = df_servicos[
        df_servicos["nome_servico"] == extra_pack_selecionado
    ]["limite_pecas"].values[0]

    if st.button("➕ Adicionar Pack Extra ao Mesmo Cliente"):
        st.session_state.carrinho_balcao.append(
            {
                "pack": extra_pack_selecionado,
                "preco": extra_preco,
                "limite": extra_limite,
            }
        )
        st.success(f"Pack extra adicionado: {extra_pack_selecionado}")
        st.rerun()

    st.markdown("---")

    # Botão de Gravação no Histórico
    if st.button(
        "💾 Registar e Gravar no Histórico", type="primary", use_container_width=True
    ):
        if nome_cli and tel_cli and st.session_state.carrinho_balcao:
            cursor = db.conn.cursor()
            packs_str = " + ".join(
                [c["pack"] for c in st.session_state.carrinho_balcao]
            )
            total_v = sum([c["preco"] for c in st.session_state.carrinho_balcao])

            ph = (
                "%s, %s, %s, %s, %s, %s, %s"
                if "PostgreSQL" in db.tipo_db
                else "?, ?, ?, ?, ?, ?, ?"
            )
            cursor.execute(
                f"INSERT INTO clientes_historico (nome, telefone, packs_escolhidos, valor_total, data_inicio, data_fim, status) VALUES ({ph})",
                (
                    nome_cli,
                    tel_cli,
                    packs_str,
                    float(total_v),
                    str(data_ini),
                    str(data_Fim),
                    "Ativo",
                ),
            )
            db.conn.commit()
            cursor.close()
            st.success(
                f"Registo de {nome_cli} gravado com sucesso no histórico!"
            )
            st.session_state.carrinho_balcao = []
            st.rerun()
        else:
            st.error(
                "Preencha o nome, o contacto e adicione pelo menos um pack ao pedido."
            )

    st.markdown("---")

    # Botão Clientes para ver o histórico guardado na aba/seção
    if st.button("👥 Clientes (Ver Histórico Geral)", use_container_width=True):
        st.session_state.mostrar_clientes = not st.session_state.mostrar_clientes

# --- SECÇÃO DE VISUALIZAÇÃO DE CLIENTES (ABAIXO OU EM ECRÃ COMPLETO) ---
if st.session_state.mostrar_clientes:
    st.markdown("---")
    st.subheader("🗂️ Registo de Clientes")
    try:
        df_clientes = pd.read_sql(
            "SELECT * FROM clientes_historico ORDER BY id DESC", db.conn
        )
        if not df_clientes.empty:
            st.dataframe(df_clientes, use_container_width=True)
        else:
            st.info("Ainda não existem clientes registados.")
    except Exception as e:
        st.error(f"Erro ao carregar o histórico: {e}")