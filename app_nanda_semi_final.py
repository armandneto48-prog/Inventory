from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Engomadoria - Controlo Estrito", layout="wide", page_icon="🧺"
)

st.title("🧺 Engomadoria da Zeza — Controlo por Validade e Packs Contínuos")

# Inicialização do Session State para dados ativos e histórico antigo
if "db_clientes_v4" not in st.session_state:
  st.session_state.db_clientes_v4 = []

if "db_historico_antigo" not in st.session_state:
  st.session_state.db_historico_antigo = [
      {
          "Cliente": "Exemplo (Cliente Antigo)",
          "Telefone": "910000000",
          "Packs": "Pack 50 Peças + Pack 25 Peças",
          "Início": "2025-01-15",
          "Data Limite": "2025-02-15",
          "Estado": "Arquivado (> 1 Ano)",
      }
  ]

# Abas principais da aplicação
aba_reg, aba_cons, aba_antigo = st.tabs([
    "📝 Novo Registo / Adicionar Packs",
    "📁 Consulta e Validades",
    "📜 Histórico Antigo (> 1 Ano)",
])

# ---------------------------------------------------------
# ABA 1: NOVO REGISTO E ACUMULAÇÃO DE PACKS EM TEMPO REAL
# ---------------------------------------------------------
with aba_reg:
  st.subheader("Registar Cliente ou Adicionar Pack a Cliente Existente")
  n_cli = st.text_input("Nome do Cliente (Chave de Identificação)")
  t_cli = st.text_input("Telefone do Cliente")

  # Gestão do carrinho em tempo real para o formato: pack1 + pack2 + pack3 + ...
  if "carrinho_tempo_real" not in st.session_state:
    st.session_state.carrinho_tempo_real = []

  pk_sel = st.selectbox(
      "Escolha o Pack do Catálogo:",
      [
          "Pack 25 Peças (18.00€)",
          "Pack 50 Peças (23.00€)",
          "Pack 100 Peças (33.00€)",
          "Pack 15 Camisas/Vestidos (23.50€)",
          "Pack Lençóis 10 Jogos (33.00€)",
      ],
  )

  col_b1, col_b2 = st.columns(2)
  with col_b1:
    if st.button(
        "➕ Adicionar Pack (Modo Contínuo)", use_container_width=True
    ):
      st.session_state.carrinho_tempo_real.append(pk_sel)
      st.success(f"Adicionado à lista: {pk_sel}")
  with col_b2:
    if st.button("🗑️ Limpar Seleção de Packs", use_container_width=True):
      st.session_state.carrinho_tempo_real = []
      st.rerun()

  # Visualização em tempo real da string combinada (pack1 + pack2 + pack3...)
  if st.session_state.carrinho_tempo_real:
    packs_combinados_str = " + ".join(st.session_state.carrinho_tempo_real)
    st.markdown(
        "**Packs acumulados para este atendimento (Formato em Tempo"
        f" Real):**\n`{packs_combinados_str}`"
    )
  else:
    packs_combinados_str = pk_sel
    st.info(
        "Nenhum pack extra adicionado. Será considerado apenas o pack"
        " selecionado acima."
    )

  st.markdown("---")
  col_f1, col_f2 = st.columns(2)
  with col_f1:
    d_ini = st.date_input("Início", value=datetime.today(), key="v4_ini")
  with col_f2:
    d_limite = st.date_input(
        "Data Limite Imposta pela Loja (Freio)",
        value=datetime.today() + timedelta(days=30),
        key="v4_lim",
    )

  if st.button("💾 Gravar / Atualizar no Histórico", type="primary"):
    if n_cli:
      st.session_state.db_clientes_v4.append({
          "Cliente": n_cli,
          "Telefone": t_cli,
          "Packs": packs_combinados_str,
          "Início": str(d_ini),
          "Data Limite": str(d_limite),
          "Estado": "Ativo dentro do Prazo",
      })
      st.success(f"Registo de {n_cli} guardado com sucesso no histórico!")
      st.session_state.carrinho_tempo_real = []
    else:
      st.error("Indique o nome do cliente.")

# ---------------------------------------------------------
# ABA 2: CONSULTA E VALIDADES (Estilo Limpo e Consolidado)
# ---------------------------------------------------------
with aba_cons:
  st.subheader("Histórico Completo Consolidado — Consultas e Validades Ativas")
  if st.session_state.db_clientes_v4:
    st.dataframe(
        pd.DataFrame(st.session_state.db_clientes_v4), use_container_width=True
    )
  else:
    st.info("Nenhum dado ativo no histórico de momento.")

# ---------------------------------------------------------
# ABA 3: HISTÓRICO ANTIGO E DE LONGA DATA (> 1 ANO)
# ---------------------------------------------------------
with aba_antigo:
  st.subheader("📜 Histórico de Longa Data (Pedidos Antigos / Passados)")
  st.markdown(
      "Esta secção armazena todos os registos e pedidos de longa data (com"
      " mais de um ano ou já arquivados definitivamente)."
  )

  if st.session_state.db_historico_antigo:
    st.dataframe(
        pd.DataFrame(st.session_state.db_historico_antigo),
        use_container_width=True,
    )
  else:
    st.info("Nenhum registo antigo encontrado no arquivo.")