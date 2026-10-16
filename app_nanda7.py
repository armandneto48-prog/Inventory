from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Engomadoria - Controlo Estrito", layout="wide", page_icon="🧺")

st.title("🧺 Engomadoria da Zeza — Controlo por Validade e Packs Contínuos")

if "db_clientes_v4" not in st.session_state:
    st.session_state.db_clientes_v4 = []

aba_reg, aba_cons = st.tabs(["📝 Novo Registo / Adicionar Packs", "📁 Consulta e Validades"])

with aba_reg:
    st.subheader("Registar Cliente ou Adicionar Pack a Cliente Existente")
    n_cli = st.text_input("Nome do Cliente (Chave de Identificação)")
    t_cli = st.text_input("Telefone do Cliente")
    
    pk_sel = st.selectbox("Escolha o Pack:", ["Pack 25 Peças (18.00€)", "Pack 50 Peças (23.00€)", "Pack 100 Peças (33.00€)"])
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        d_ini = st.date_input("Início", value=datetime.today(), key="v4_ini")
    with col_f2:
        d_limite = st.date_input("Data Limite Imposta pela Loja (Freio)", value=datetime.today() + timedelta(days=30), key="v4_lim")
        
    if st.button("💾 Gravar / Atualizar no Histórico", type="primary"):
        if n_cli:
            st.session_state.db_clientes_v4.append({
                "Cliente": n_cli,
                "Telefone": t_cli,
                "Pack": pk_sel,
                "Início": str(d_ini),
                "Data Limite": str(d_limite),
                "Estado": "Ativo dentro do Prazo"
            })
            st.success(f"Registo de {n_cli} guardado com sucesso!")
        else:
            st.error("Indique o nome do cliente.")

with aba_cons:
    st.subheader("Histórico Completo Consolidado")
    if st.session_state.db_clientes_v4:
        st.dataframe(pd.DataFrame(st.session_state.db_clientes_v4), use_container_width=True)
    else:
        st.info("Nenhum dado no histórico.")