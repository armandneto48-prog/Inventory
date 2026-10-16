from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Engomadoria da Zeza - Modo POS", layout="wide", page_icon="🧺"
)

st.title("🧺 Engomadoria da Zeza — Terminal POS / Balcão")

if "pos_carrinho" not in st.session_state:
  st.session_state.pos_carrinho = []
if "pos_historico" not in st.session_state:
  st.session_state.pos_historico = []

col_l, col_r = st.columns([1.2, 0.8], gap="large")

with col_l:
    st.subheader("📋 Catálogo de Serviços (Clique para Adicionar)")
    catalogo = [
        {"id": 1, "nome": "Pack 25 Peças", "preco": 18.00},
        {"id": 2, "nome": "Pack 50 Peças", "preco": 23.00},
        {"id": 3, "nome": "Pack 100 Peças", "preco": 33.00},
        {"id": 4, "nome": "Pack 15 Camisas/Vestidos", "preco": 23.50},
        {"id": 5, "nome": "Pack Lençóis (10 Jogos)", "preco": 33.00},
        {"id": 6, "nome": "Lavar Roupa Básica (Un.)", "preco": 0.85},
    ]
    
    for item in catalogo:
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"**{item['nome']}**")
        c2.markdown(f"`{item['preco']:.2f}€`")
        if c3.button("➕", key=f"pos_{item['id']}"):
            st.session_state.pos_carrinho.append(item)
            st.rerun()

with col_r:
    st.subheader("🛒 Ficha do Cliente Atual")
    nome_c = st.text_input("Nome", key="pos_n")
    tel_c = st.text_input("Telefone", key="pos_t")
    limite_dt = st.date_input("Data Limite (Freio)", value=datetime.today() + timedelta(days=30), key="pos_d")
    
    if st.session_state.pos_carrinho:
        df_p = pd.DataFrame(st.session_state.pos_carrinho)
        st.dataframe(df_p[["nome", "preco"]], use_container_width=True)
        t_val = df_p["preco"].sum()
        st.metric("Total Acumulado", f"{t_val:.2f} €")
        
        if st.button("💾 Concluir e Gravar no Histórico", type="primary", use_container_width=True):
            if nome_c:
                st.session_state.pos_historico.append({
                    "Cliente": nome_c,
                    "Contacto": tel_c,
                    "Packs": " + ".join(df_p["nome"].tolist()),
                    "Total (€)": t_val,
                    "Validade": str(limite_dt)
                })
                st.success("Registo efetuado com sucesso!")
                st.session_state.pos_carrinho = []
            else:
                st.error("Insira o nome do cliente.")
    else:
        st.info("Nenhum pack selecionado ainda.")

st.divider()
st.subheader("📊 Histórico de Clientes Gravados")
if st.session_state.pos_historico:
    st.dataframe(pd.DataFrame(st.session_state.pos_historico), use_container_width=True)
else:
    st.info("Sem registos recentes.")