from datetime import datetime
import hashlib
import os
import re
import pandas as pd
import psycopg2  # Conexão com PostgreSQL
import streamlit as st

# ==========================================
# 1. CONFIGURAÇÃO DA BASE DE DADOS (PostgreSQL)
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

    conn = sqlite3.connect("inventario_loja_fallback.db")
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
                    descricao TEXT
                );
                CREATE TABLE IF NOT EXISTS clientes (
                    id SERIAL PRIMARY KEY,
                    num_ficha TEXT UNIQUE NOT NULL,
                    nome TEXT NOT NULL,
                    contacto TEXT,
                    status TEXT DEFAULT 'Ativo'
                );
                CREATE TABLE IF NOT EXISTS pedidos (
                    id SERIAL PRIMARY KEY,
                    num_ficha TEXT,
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
                    descricao TEXT
                );
            """)
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    num_ficha TEXT UNIQUE NOT NULL,
                    nome TEXT NOT NULL,
                    contacto TEXT,
                    status TEXT DEFAULT 'Ativo'
                );
            """)
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    num_ficha TEXT,
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
          ("PACK", "25 PEÇAS", 18.00, "Pacote até 25 peças"),
          ("PACK", "50 PEÇAS", 23.00, "Pacote até 50 peças"),
          ("PACK", "100 PEÇAS", 33.00, "Pacote até 100 peças"),
          (
              "PACK",
              "PACK 15 CAMISAS/VESTIDOS",
              23.50,
              "Pacote de 15 camisas ou vestidos",
          ),
          (
              "PACK",
              "PACK DE LENÇÓIS (2 MESES)",
              33.00,
              "10 Jogos de lençóis/capas/almofadas",
          ),
          ("PACK", "PACK MISTO 50 PEÇAS", 60.00, "Pacote misto de 50 peças"),
          ("PACK", "PACK MISTO 100 PEÇAS", 70.00, "Pacote misto de 100 peças"),
          ("INDIVIDUAL", "ROUPA BÁSICA", 0.85, "Valor por peça individual"),
          ("INDIVIDUAL", "CAMISAS", 2.50, "Valor por peça individual"),
          ("INDIVIDUAL", "VESTIDOS", 3.00, "Valor por peça individual"),
          (
              "INDIVIDUAL",
              "LENÇÓIS (UNIDADE)",
              2.00,
              "Valor por unidade individual",
          ),
          (
              "INDIVIDUAL",
              "CAPA DE EDREDÃO",
              3.00,
              "Valor por unidade individual",
          ),
      ]
      for cat, item, preco, desc in dados:
        cursor.execute(
            """
                    INSERT INTO precario (categoria, item, preco_eur, descricao)
                    VALUES (%s, %s, %s, %s)
                """
            if "PostgreSQL" in self.tipo_db
            else """
                    INSERT INTO precario (categoria, item, preco_eur, descricao)
                    VALUES (?, ?, ?, ?)
                """,
            (cat, item, preco, desc),
        )
      self.conn.commit()
    cursor.close()


# ==========================================
# 2. INTERFACE WEB (Streamlit)
# ==========================================
st.set_page_config(
    page_title="Sistema de Gestão - Lavandaria", layout="wide", page_icon="🧺"
)

db = GestorBaseDados()

ADMIN_USER = "admin"
ADMIN_PASS_HASH = hashlib.sha256("nanda85".encode()).hexdigest()

st.sidebar.title("🧭 Navegação")
modo = st.sidebar.radio(
    "Escolha o Painel:", ["Registo de Pedidos (Operador)", "Área de Administração"]
)

# ------------------------------------------
# PAINEL 1: OPERADOR / CLIENTE
# ------------------------------------------
if modo == "Registo de Pedidos (Operador)":
  st.title("📋 Ficha de Pedido e Controlo de Packs")

  col1, col2 = st.columns(2)
  with col1:
    num_ficha = st.text_input("Nº da Ficha do Cliente")
    nome_cliente = st.text_input("Nome do Cliente")
  with col2:
    contacto = st.text_input("Contacto Telefónico")
    tipo_pack = st.selectbox(
        "Selecionar Tipo de Pack / Serviço",
        [
            "25 Peças (18.00€)",
            "50 Peças (23.00€)",
            "100 Peças (33.00€)",
            "Pack 15 Camisas/Vestidos (23.50€)",
            "Pack Lençóis 10 Jogos (33.00€)",
            "Pack Misto 50 Peças (60.00€)",
            "Pack Misto 100 Peças (70.00€)",
            "Peças Individuais / Personalizado",
        ],
    )

  tabela_precos_ref = {
      "25 Peças (18.00€)": 18.00,
      "50 Peças (23.00€)": 23.00,
      "100 Peças (33.00€)": 33.00,
      "Pack 15 Camisas/Vestidos (23.50€)": 23.50,
      "Pack Lençóis 10 Jogos (33.00€)": 33.00,
      "Pack Misto 50 Peças (60.00€)": 60.00,
      "Pack Misto 100 Peças (70.00€)": 70.00,
  }

  if "carrinho" not in st.session_state:
    st.session_state.carrinho = []

  if tipo_pack != "Peças Individuais / Personalizado":
    preco_atual = tabela_precos_ref[tipo_pack]
    if st.button("➕ Adicionar Pack ao Pedido", type="primary"):
      st.session_state.carrinho.append({"item": tipo_pack, "preco": preco_atual})
      st.success(f"Adicionado: {tipo_pack}")
  else:
    expressao_soma = st.text_input(
        "Insira os valores somados de peças (Ex: 20 + 30 + 40)"
    )
    if st.button("➕ Adicionar Soma Personalizada"):
      try:
        numeros = [int(n) for n in re.findall(r"\d+", expressao_soma)]
        soma_pecas = sum(numeros)
        preco_calculado = soma_pecas * 0.85
        item_desc = (
            f"Soma Personalizada ({' + '.join(map(str, numeros))}) ="
            f" {soma_pecas} pçs"
        )
        st.session_state.carrinho.append(
            {"item": item_desc, "preco": preco_calculado}
        )
        st.success(f"Adicionado com sucesso: {soma_pecas} peças calculadas!")
      except Exception:
        st.error(
            "Formato inválido. Insira os números separados por '+' (Ex: 20 +"
            " 30 + 40)."
        )

  if st.session_state.carrinho:
    st.divider()
    st.subheader("🛒 Resumo dos Packs Selecionados")
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    st.dataframe(df_carrinho, use_container_width=True)

    total_geral = df_carrinho["preco"].sum()
    st.metric("VALOR TOTAL A PAGAR", f"{total_geral:.2f} €")

    limite_orcamento = 60.00
    pct = (total_geral / limite_orcamento) * 100
    st.progress(min(pct / 100.0, 1.0))

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
      if st.button("🗑️ Limpar Carrinho"):
        st.session_state.carrinho = []
        st.rerun()
    with col_btn2:
      if st.button("💾 Registar Pedido na Fábrica", type="primary"):
        if num_ficha and nome_cliente:
          cursor = db.conn.cursor()
          itens_str = " | ".join([c["item"] for c in st.session_state.carrinho])
          if "PostgreSQL" in db.tipo_db:
            cursor.execute(
                """
                            INSERT INTO pedidos (num_ficha, itens_detalhe, total_eur, status_fabrica)
                            VALUES (%s, %s, %s, 'EM PROCESSO')
                        """,
                (num_ficha, itens_str, float(total_geral)),
            )
            cursor.execute(
                """
                            INSERT INTO clientes (num_ficha, nome, contacto, status)
                            VALUES (%s, %s, %s, 'Ativo')
                            ON CONFLICT (num_ficha) DO NOTHING
                        """,
                (num_ficha, nome_cliente, contacto),
            )
          else:
            cursor.execute(
                """
                            INSERT INTO pedidos (num_ficha, itens_detalhe, total_eur, status_fabrica, data_registo)
                            VALUES (?, ?, ?, 'EM PROCESSO', datetime('now'))
                        """,
                (num_ficha, itens_str, float(total_geral)),
            )
            cursor.execute(
                """
                            INSERT OR IGNORE INTO clientes (num_ficha, nome, contacto, status)
                            VALUES (?, ?, ?, 'Ativo')
                        """,
                (num_ficha, nome_cliente, contacto),
            )
          db.conn.commit()
          cursor.close()
          st.balloons()
          st.success(
              f"Pedido da Ficha #{num_ficha} enviado para a fábrica com sucesso!"
          )
          st.session_state.carrinho = []
        else:
          st.error("Preencha o Nº da Ficha e o Nome do Cliente.")

# ------------------------------------------
# PAINEL 2: ADMINISTRADOR
# ------------------------------------------
elif modo == "Área de Administração":
  st.title("🔐 Painel de Controlo da Administração")

  senha_digitada = st.text_input("Introduza a Senha de Administrador", type="password")
  senha_hash = hashlib.sha256(senha_digitada.encode()).hexdigest()

  if senha_hash == ADMIN_PASS_HASH:
    st.success("Acesso autorizado com sucesso!")
    st.divider()

    aba1, aba2, aba3 = st.tabs(
        ["📊 Estado de Fábrica (Processos)", "👥 Gestão de Clientes", "💶 Tabela de Preços"]
    )

    # ABA 1: SINALIZAÇÃO DE PROCESSOS E BOTÕES TÁTEIS DE APROXIMAÇÃO
    with aba1:
      st.subheader(
          "⚙️ Controlo de Produção e Adição Tátil de Peças (Algoritmo de"
          " Proximidade)"
      )
      query_pedidos = "SELECT id, num_ficha, itens_detalhe, total_eur, status_fabrica, data_registo FROM pedidos"
      df_pedidos = pd.read_sql(query_pedidos, db.conn)

      if not df_pedidos.empty:
        st.dataframe(df_pedidos, use_container_width=True)

        st.markdown(
            "### 🎛️ Ecrã Tátil: Atualização Rápida de Peças por Pedido"
        )

        pedido_id_sel = st.selectbox(
            "Selecione o ID do Pedido para Adicionar Peças Interativamente",
            df_pedidos["id"].tolist(),
        )

        pedido_atual_row = df_pedidos[df_pedidos["id"] == pedido_id_sel].iloc[0]
        detalhes_atuais = str(pedido_atual_row["itens_detalhe"])

        # Determinar limite com base no preçário inicial
        limite_pack = 50
        if "25 PEÇAS" in detalhes_atuais:
          limite_pack = 25
        elif "50 PEÇAS" in detalhes_atuais:
          limite_pack = 50
        elif "100 PEÇAS" in detalhes_atuais:
          limite_pack = 100
        elif "15 CAMISAS" in detalhes_atuais:
          limite_pack = 15

        numeros_existentes = [int(n) for n in re.findall(r"\d+", detalhes_atuais)]

        st.info(
            f"**Pedido ID {pedido_id_sel} (Ficha #{pedido_atual_row['num_ficha']})**"
            f" — Detalhes atuais: `{detalhes_atuais}` | Limite do Pack: **{limite_pack}"
            " peças**"
        )

        st.markdown(
            "**Toque nos botões abaixo para adicionar peças instantaneamente com"
            " o dedo / rato:**"
        )

        def adicionar_pecas_rapido(qtd_incremento):
          cursor_up = db.conn.cursor()
          novo_detalhe = f"{detalhes_atuais} + {qtd_incremento}"
          if "PostgreSQL" in db.tipo_db:
            cursor_up.execute(
                "UPDATE pedidos SET itens_detalhe = %s WHERE id = %s",
                (novo_detalhe, pedido_id_sel),
            )
          else:
            cursor_up.execute(
                "UPDATE pedidos SET itens_detalhe = ? WHERE id = ?",
                (novo_detalhe, pedido_id_sel),
            )
          db.conn.commit()
          cursor_up.close()
          st.success(f"Adicionadas {qtd_incremento} peças ao pedido!")
          st.rerun()

        # Linha 1 de botões táteis (1, 5, 10)
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
          if st.button("➕ 1 Peça", use_container_width=True):
            adicionar_pecas_rapido(1)
        with col_t2:
          if st.button("➕ 5 Peças", use_container_width=True):
            adicionar_pecas_rapido(5)
        with col_t3:
          if st.button("➕ 10 Peças", use_container_width=True):
            adicionar_pecas_rapido(10)

        # Linha 2 de botões táteis (25, 50, 100)
        col_t4, col_t5, col_t6 = st.columns(3)
        with col_t4:
          if st.button("➕ 25 Peças", use_container_width=True):
            adicionar_pecas_rapido(25)
        with col_t5:
          if st.button("➕ 50 Peças (Pack)", use_container_width=True):
            adicionar_pecas_rapido(50)
        with col_t6:
          if st.button("➕ 100 Peças (Pack)", use_container_width=True):
            adicionar_pecas_rapido(100)

        st.divider()
        st.markdown("### 📊 Análise Algorítmica de Proximidade de Todos os Packs")

        for index, row in df_pedidos.iterrows():
          detalhes = str(row["itens_detalhe"])
          lim_p = 50
          if "25 PEÇAS" in detalhes:
            lim_p = 25
          elif "50 PEÇAS" in detalhes:
            lim_p = 50
          elif "100 PEÇAS" in detalhes:
            lim_p = 100
          elif "15 CAMISAS" in detalhes:
            lim_p = 15

          nums = [int(n) for n in re.findall(r"\d+", detalhes)]
          tot_pecas = (
              sum(nums) if len(nums) > 1 else (nums[0] if nums else 0)
          )
          prog = min(tot_pecas / lim_p, 1.0) if lim_p > 0 else 0.0

          with st.container():
            st.markdown(
                f"**ID: {row['id']} | Ficha: {row['num_ficha']}** — Dados:"
                f" `{detalhes}`"
            )
            col_info1, col_info2 = st.columns([3, 1])
            with col_info1:
              st.progress(
                  prog,
                  text=(
                      f"Progresso face ao Pack (Ref: {lim_p} pçs) | Contagem:"
                      f" {tot_pecas} peças ({prog*100:.1f}%)"
                  ),
              )
            with col_info2:
              if tot_pecas >= lim_p:
                st.error("🛑 Pack Atingido/Excedido")
              elif prog >= 0.8:
                st.warning("⚠️ Próximo do Limite")
              else:
                st.success("✅ Dentro do Pack")
            st.divider()

        st.markdown("### Atualizar Estado de Fabrico")
        pedido_id_status = st.selectbox(
            "Selecione o ID do Pedido para Atualizar Estado",
            df_pedidos["id"].tolist(),
            key="status_sel",
        )
        novo_status = st.selectbox(
            "Novo Estado", ["EM PROCESSO", "TERMINADO", "SUSPENSO"]
        )

        if st.button("Atualizar Estado na Fábrica"):
          cursor = db.conn.cursor()
          if "PostgreSQL" in db.tipo_db:
            cursor.execute(
                "UPDATE pedidos SET status_fabrica = %s WHERE id = %s",
                (novo_status, pedido_id_status),
            )
          else:
            cursor.execute(
                "UPDATE pedidos SET status_fabrica = ? WHERE id = ?",
                (novo_status, pedido_id_status),
            )
          db.conn.commit()
          cursor.close()
          st.success(
              f"Pedido ID {pedido_id_status} atualizado para: {novo_status}"
          )
          st.rerun()
      else:
        st.info("Ainda não existem pedidos registados na base de dados.")

    with aba2:
      st.subheader("👥 Lista de Clientes e Histórico")
      df_clientes = pd.read_sql("SELECT * FROM clientes", db.conn)
      st.dataframe(df_clientes, use_container_width=True)

      st.markdown("### Alterar Estado do Cliente (Ativo / Suspenso / Excluído)")
      if not df_clientes.empty:
        cliente_ficha = st.selectbox(
            "Selecione o Nº de Ficha", df_clientes["num_ficha"].tolist()
        )
        acao = st.radio(
            "Ação pretendida:", ["Marcar como Suspenso", "Ativar", "Eliminar Registo"]
        )

        if st.button("Aplicar Ação ao Cliente"):
          cursor = db.conn.cursor()
          if acao == "Eliminar Registo":
            if "PostgreSQL" in db.tipo_db:
              cursor.execute(
                  "DELETE FROM clientes WHERE num_ficha = %s", (cliente_ficha,)
              )
            else:
              cursor.execute(
                  "DELETE FROM clientes WHERE num_ficha = ?", (cliente_ficha,)
              )
            st.warning(f"Cliente da ficha {cliente_ficha} eliminado.")
          else:
            novo_estado = "Suspenso" if acao == "Marcar como Suspenso" else "Ativo"
            if "PostgreSQL" in db.tipo_db:
              cursor.execute(
                  "UPDATE clientes SET status = %s WHERE num_ficha = %s",
                  (novo_estado, cliente_ficha),
              )
            else:
              cursor.execute(
                  "UPDATE clientes SET status = ? WHERE num_ficha = ?",
                  (novo_estado, cliente_ficha),
              )
            st.success(f"Cliente atualizado para: {novo_estado}")
          db.conn.commit()
          cursor.close()
          st.rerun()

    with aba3:
      st.subheader("💡 Tabela de Preços Ativa")
      df_precario = pd.read_sql("SELECT * FROM precario", db.conn)
      st.dataframe(df_precario, use_container_width=True)

  elif senha_digitada != "":
    st.error("Senha de administrador incorreta.")
  else:
    st.info(
        "Insira a senha de administrador (nanda85) para aceder aos controlos"
        " avançados."
    )