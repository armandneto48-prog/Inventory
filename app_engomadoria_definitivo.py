from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Engomadoria da Zeza - Controlo Contínuo",
    layout="wide",
    page_icon="🧺",
)

st.title("🧺 Engomadoria da Zeza — Controlo por Validade e Packs Contínuos")

# Inicialização de bases de dados locais em session_state
if "db_clientes_v4" not in st.session_state:
  st.session_state.db_clientes_v4 = []

if "db_historico_antigo" not in st.session_state:
  st.session_state.db_historico_antigo = [
      {
          "Cliente": "Cliente Exemplo Antigo",
          "Telefone": "910000000",
          "Packs": "Pack 50 Peças + Pack 25 Peças",
          "Total Peças": 75,
          "Início": "2025-01-10",
          "Data Limite": "2025-02-10",
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
# ABA 1: NOVO REGISTO, ACUMULAÇÃO E BARRA DE PROGRESSO
# ---------------------------------------------------------
with aba_reg:
  st.subheader("Registar Cliente e Monitorizar Limite de Packs em Tempo Real")

  col_n1, col_n2 = st.columns(2)
  with col_n1:
    n_cli = st.text_input("Nome do Cliente (Chave de Identificação)")
  with col_n2:
    t_cli = st.text_input("Telefone do Cliente")

  # Gestão do carrinho em tempo real para o formato: pack1 + pack2 + pack3 + ...
  if "carrinho_tempo_real" not in st.session_state:
    st.session_state.carrinho_tempo_real = []

  # Catálogo com indicação de limite de peças por pack
  catalogo_packs = {
      "Pack 25 Peças (18.00€)": {"limite": 25, "preco": 18.00},
      "Pack 50 Peças (23.00€)": {"limite": 50, "preco": 23.00},
      "Pack 100 Peças (33.00€)": {"limite": 100, "preco": 33.00},
      "Pack 15 Camisas/Vestidos (23.50€)": {"limite": 15, "preco": 23.50},
      "Pack Lençóis 10 Jogos (33.00€)": {"limite": 10, "preco": 33.00},
  }

  pk_sel = st.selectbox("Escolha o Pack do Catálogo:", list(catalogo_packs.keys()))

  col_b1, col_b2 = st.columns(2)
  with col_b1:
    if st.button(
        "➕ Adicionar Pack (Modo Contínuo)", use_container_width=True
    ):
      st.session_state.carrinho_tempo_real.append({
          "nome": pk_sel,
          "limite": catalogo_packs[pk_sel]["limite"],
          "preco": catalogo_packs[pk_sel]["preco"],
      })
      st.success(f"Adicionado à lista: {pk_sel}")
  with col_b2:
    if st.button("🗑️ Limpar Seleção de Packs", use_container_width=True):
      st.session_state.carrinho_tempo_real = []
      st.rerun()

  # Calcular acumulados em tempo real
  if st.session_state.carrinho_tempo_real:
    packs_combinados_str = " + ".join(
        [c["nome"] for c in st.session_state.carrinho_tempo_real]
    )
    total_pecas_acumulado = sum(
        [c["limite"] for c in st.session_state.carrinho_tempo_real]
    )
    total_preco_acumulado = sum(
        [c["preco"] for c in st.session_state.carrinho_tempo_real]
    )
  else:
    packs_combinados_str = pk_sel
    total_pecas_acumulado = catalogo_packs[pk_sel]["limite"]
    total_preco_acumulado = catalogo_packs[pk_sel]["preco"]

  st.markdown(
      "**Packs acumulados em tempo real:**\n`"
      + packs_combinados_str
      + f"` | **Total Estimado:** `{total_preco_acumulado:.2f}€`"
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

  # --- BARRA DE INPUT DE DADOS E MONITORIZAÇÃO EM TEMPO REAL ---
  st.markdown("### 📊 Monitorização de Limite de Peças (Barra em Tempo Real)")
  # Definimos uma referência máxima de teto por defeito (ex: 100 peças para pacotes grandes)
  teto_referencia = max(100, total_pecas_acumulado)
  progresso_val = min(total_pecas_acumulado / teto_referencia, 1.0)

  st.progress(
      progresso_val,
      text=(
          f"Contagem Atual: {total_pecas_acumulado} peças associadas"
          f" (Progresso face ao teto de referência)"
      ),
  )

  if total_pecas_acumulado >= teto_referencia:
    st.error("🛑 Limite máximo do pack de referência atingido/excedido!")
  elif progresso_val >= 0.8:
    st.warning("⚠️ Próximo do limite estipulado para este ciclo.")
  else:
    st.success("✅ Dentro dos parâmetros normais do pack.")

  st.markdown("---")
  if st.button("💾 Gravar / Atualizar no Histórico", type="primary"):
    if n_cli:
      st.session_state.db_clientes_v4.append({
          "Cliente": n_cli,
          "Telefone": t_cli,
          "Packs": packs_combinados_str,
          "Total Peças": total_pecas_acumulado,
          "Total (€)": f"{total_preco_acumulado:.2f}€",
          "Início": str(d_ini),
          "Data Limite": str(d_limite),
          "Estado": "Ativo dentro do Prazo",
      })
      st.success(f"Registo de {n_cli} guardado com sucesso no histórico!")
      st.session_state.carrinho_tempo_real = []
    else:
      st.error("Indique o nome do cliente.")

# ---------------------------------------------------------
# ABA 2: CONSULTA E VALIDADES
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
      "Esta secção armazena todos os registos de longa data (com mais de um"
      " ano ou arquivados)."
  )
  if st.session_state.db_historico_antigo:
    st.dataframe(
        pd.DataFrame(st.session_state.db_historico_antigo),
        use_container_width=True,
    )
  else:
    st.info("Nenhum registo antigo encontrado no arquivo.")