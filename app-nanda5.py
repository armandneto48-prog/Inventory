from datetime import datetime, timedelta
import os
import sqlite3
import pandas as pd
import psycopg2
import streamlit as st

# (Usa a mesma classe de DB da Opção 1)
# Para poupar espaço de código repetido, mantemos a lógica de ligação.
st.set_page_config(
    page_title="Engomadoria da Zeza - Grelha Visual", layout="wide", page_icon="🧺"
)


# Exemplo simplificado da interface em grelha de cartões
def app_grelha():
  st.title("🧺 Engomadoria da Zeza — Seleção Rápida por Grelha Visual")

  # Simulação de base de dados em session_state para demonstração imediata da UI
  if "carrinho_grelha" not in st.session_state:
    st.session_state.carrinho_grelha = []
  if "historico_geral" not in st.session_state:
    st.session_state.historico_geral = []

  col_1, col_2 = st.columns([2, 1])

  with col_1:
    st.subheader("📦 Toque num Pack para Adicionar")
    packs_disponiveis = [
        {"nome": "Pack 25 Peças", "preco": 18.00, "limite": 25},
        {"nome": "Pack 50 Peças", "preco": 23.00, "limite": 50},
        {"nome": "Pack 100 Peças", "preco": 33.00, "limite": 100},
        {"nome": "Pack 15 Camisas", "preco": 23.50, "limite": 15},
    ]

    # Criar uma grelha de botões táteis
    cols = st.columns(2)
    for i, p in enumerate(packs_disponiveis):
      with cols[i % 2]:
        if st.button(
            f"➕ {p['nome']}\n({p['preco']:.2f}€)",
            use_container_width=True,
            key=f"btn_{i}",
        ):
          st.session_state.carrinho_grelha.append(p)
          st.success(f"Adicionado: {p['nome']}")

    if st.session_state.carrinho_grelha:
      st.markdown("---")
      st.subheader("🛒 Carrinho Atual do Cliente")
      df_c = pd.DataFrame(st.session_state.carrinho_grelha)
      st.dataframe(df_c, use_container_width=True)
      st.metric("Total a Pagar", f"{df_c['preco'].sum():.2f} €")
      if st.button("🗑️ Limpar Carrinho"):
        st.session_state.carrinho_grelha = []
        st.rerun()

  with col_2:
    st.subheader("👤 Dados e Validade")
    nome = st.text_input("Nome do Cliente", key="g_nome")
    tel = st.text_input("Telemóvel", key="g_tel")
    dt_fim = st.date_input(
        "Data Limite (Freio da Loja)",
        value=datetime.today() + timedelta(days=30),
        key="g_fim",
    )

    if st.button(
        "💾 Gravar Pedido no Histórico", type="primary", use_container_width=True
    ):
      if nome and st.session_state.carrinho_grelha:
        registo = {
            "Cliente": nome,
            "Telemóvel": tel,
            "Packs": " + ".join([x["nome"] for x in st.session_state.carrinho_grelha]),
            "Total": sum([x["preco"] for x in st.session_state.carrinho_grelha]),
            "Validade": str(dt_fim),
        }
        st.session_state.historico_geral.append(registo)
        st.success("Guardado no histórico com sucesso!")
        st.session_state.carrinho_grelha = []
      else:
        st.error("Insira o nome e adicione packs.")

  st.divider()
  st.subheader("📋 Histórico Consolidado")
  if st.session_state.historico_geral:
    st.dataframe(
        pd.DataFrame(st.session_state.historico_geral), use_container_width=True
    )


app_grelha()