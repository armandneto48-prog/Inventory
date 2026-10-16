from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# Tentar importar o componente de assinatura digital para tablet
try:
  from streamlit_drawable_canvas import st_canvas

  HAS_CANVAS = True
except ImportError:
  HAS_CANVAS = False

st.set_page_config(
    page_title="Engomadoria - Controlo Estrito", layout="wide", page_icon="🧺"
)

st.title("🧺 Engomadoria da Zeza") # CENTRALIZAR

if "db_clientes_v4" not in st.session_state:
  st.session_state.db_clientes_v4 = []

aba_reg, aba_cons, aba_antigo = st.tabs([
    "📝 Novo Registo / Adicionar Packs",
    "📁 Consulta e Validades",
    "📜 Histórico Antigo (> 1 Ano)",
])

# INCREMENTAR CSS NESTA APLICAÇÃO

with aba_reg:
  st.subheader("Registar Cliente")  # PÔR BOTÃO VERDE
  n_cli = st.text_input("Nome do Cliente (Chave de Identificação)")
  t_cli = st.text_input("Telefone do Cliente")

  if "carrinho_tempo_real" not in st.session_state:
    st.session_state.carrinho_tempo_real = []

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
      st.success(f"Adicionado: {pk_sel}")
  with col_b2:
    if st.button("🗑️ Limpar Seleção", use_container_width=True):
      st.session_state.carrinho_tempo_real = []
      st.rerun()

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
      f"**Packs acumulados:** `{packs_combinados_str}` | **Total:**"
      f" `{total_preco_acumulado:.2f}€`"
  )

  st.markdown("---")
  col_f1, col_f2 = st.columns(2)
  with col_f1:
    d_ini = st.date_input("Início", value=datetime.today(), key="v4_ini")
  with col_f2:
    d_limite = st.date_input(
        "Data Limite (Freio da Loja)",
        value=datetime.today() + timedelta(days=30),
        key="v4_lim",
    )

  # Barra de Progresso em Tempo Real
  st.markdown("### 📊 Monitorização de Limite de Peças")
  teto_referencia = max(100, total_pecas_acumulado)
  progresso_val = min(total_pecas_acumulado / teto_referencia, 1.0)
  st.progress(
      progresso_val,
      text=f"Contagem Atual: {total_pecas_acumulado} peças associadas",
  )

  st.markdown("---")
  st.subheader("✍️ Assinatura Digital")
  if HAS_CANVAS:
    st.info(
        "Use a caneta digital ou o dedo para assinar no espaço abaixo:"
    )
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=120,
        width=350,
        drawing_mode="freedraw",
        key="canvas_assinatura_tablet",
    )
    assinatura_feita = (
        "Sim (Assinado no Ecrã)"
        if canvas_result.image_data is not None
        else "Pendente"
    )
  else:
    assinatura_feita = st.text_input(
        "Assinatura (Nome/Confirmação)", placeholder="Escreva o nome do cliente"
    )

  if st.button("💾 Gravar ", type="primary"):
    if n_cli:
      st.session_state.db_clientes_v4.append({
          "Cliente": n_cli,
          "Telefone": t_cli,
          "Packs": packs_combinados_str,
          "Total Peças": total_pecas_acumulado,
          "Total (€)": f"{total_preco_acumulado:.2f}€",
          "Início": str(d_ini),
          "Data Limite": str(d_limite),
          "Assinatura": assinatura_feita,
          "Estado": "Ativo dentro do Prazo",
      })
      st.success(f"Registo e assinatura de {n_cli} guardados com sucesso!")
      st.session_state.carrinho_tempo_real = []
    else:
      st.error("Indique o nome do cliente.")

# CRIAR TABELA DE MANIPULAÇÃO DE HISTÓRICO DE PEDIDOS

with aba_cons:
  st.subheader("Histórico")
  if st.session_state.db_clientes_v4:
    st.dataframe(
        pd.DataFrame(st.session_state.db_clientes_v4), use_container_width=True
    )
  else:
    st.info("Nenhum dado ativo no histórico.")

with aba_antigo:
  st.subheader("📜 Filtrar pedidos por período")
  st.info("Arquivo de pedidos passados.")