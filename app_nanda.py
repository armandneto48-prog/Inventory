from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# 1. GESTÃO DA BASE DE DADOS (SQLite)
# ==========================================


class GestorInventarioPreco:

    def __init__(self, db_name="inventario_loja.db"):
        self.conn = sqlite3.connect(db_name)
        self.criar_tabela()

    def criar_tabela(self):
        query = """
        CREATE TABLE IF NOT EXISTS precario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            item TEXT NOT NULL,
            preco_eur REAL NOT NULL,
            descricao TEXT
        );
        """
        self.conn.execute(query)
        self.conn.commit()

    def carregar_dados_iniciais(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM precario")
        if cursor.fetchone()[0] == 0:
            dados_excel = [
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
                (
                    "PACK",
                    "PACK MISTO 50 PEÇAS",
                    60.00,
                    "Pacote misto de 50 peças",
                ),
                (
                    "PACK",
                    "PACK MISTO 100 PEÇAS",
                    70.00,
                    "Pacote misto de 100 peças",
                ),
                (
                    "INDIVIDUAL",
                    "ROUPA BÁSICA",
                    0.85,
                    "Valor por peça individual",
                ),
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
            cursor.executemany(
                """
                INSERT INTO precario (categoria, item, preco_eur, descricao)
                VALUES (?, ?, ?, ?)
            """,
                dados_excel,
            )
            self.conn.commit()

    def ver_precario_dataframe(self):
        query = "SELECT id, categoria, item, preco_eur AS 'Preço (€)', descricao FROM precario"
        return pd.read_sql_query(query, self.conn)


# ==========================================
# 2. MODELO DE NEGÓCIO (Pedido)
# ==========================================


class PedidoModel:

    def __init__(self, limite=60.0):
        self.num_ficha = ""
        self.nome_cliente = ""
        self.contacto = ""
        self.data_inicio = datetime.now().strftime("%Y-%m-%d")
        self.valores = []
        self.limite = limite

    def adicionar_valor(self, valor):
        if valor <= 0:
            raise ValueError("O valor deve ser positivo.")
        self.valores.append(valor)

    def obter_total(self):
        return sum(self.valores)

    def obter_status_limite(self):
        total = self.obter_total()
        percentagem = (total / self.limite) * 100 if self.limite > 0 else 0

        if total == 0:
            return "Aguardando dados...", 0.0
        elif total < 0.8 * self.limite:
            return (
                f"DENTRO DO LIMITE ({percentagem:.1f}%)\nMargem: {self.limite - total:.2f}€",
                percentagem,
            )
        elif total < self.limite:
            return (
                f"⚠️ ALERTA: PRÓXIMO DO LIMITE! ({percentagem:.1f}%)\nFaltam: {self.limite - total:.2f}€",
                percentagem,
            )
        elif total == self.limite:
            return "🛑 ATENÇÃO: CHEGOU AO LIMITE EXATO! (100%)", 100.0
        else:
            excedente = total - self.limite
            return (
                f"🚨 PERIGO: LIMITE ULTRAPASSADO! (+{excedente:.2f}€)",
                100.0,
            )

    def limpar(self):
        self.num_ficha = ""
        self.nome_cliente = ""
        self.contacto = ""
        self.valores.clear()


# ==========================================
# 3. INTERFACE WEB (Streamlit)
# ==========================================

# Configuração da Página Web
st.set_page_config(
    page_title="Gestão de Pedidos", layout="centered", page_icon="📋"
)

# Inicialização da Base de Dados e Sessão
gestor = GestorInventarioPreco()
gestor.carregar_dados_iniciais()

if "model" not in st.session_state:
    st.session_state.model = PedidoModel(limite=60.0)

model = st.session_state.model

# Título da Aplicação
st.title("📋 Ficha de Pedido do Cliente")

# Preçário Interativo na Sidebar
with st.sidebar:
    st.header("💡 Tabela de Preços")
    df_precos = gestor.ver_precario_dataframe()
    st.dataframe(
        df_precos[["categoria", "item", "Preço (€)"]], use_container_width=True
    )

# Formulário - Dados do Cliente
st.subheader("👤 Dados do Cliente")
col_ficha, col_contacto = st.columns(2)
with col_ficha:
    model.num_ficha = st.text_input("Nº Ficha", value=model.num_ficha)
with col_contacto:
    model.contacto = st.text_input("Contacto", value=model.contacto)

model.nome_cliente = st.text_input("Nome do Cliente", value=model.nome_cliente)

# Lançamento de Valores
st.subheader("💶 Lançamento de Valores")
novo_valor = st.number_input(
    "Novo Valor (€)", min_value=0.0, step=0.50, format="%.2f"
)

if st.button("➕ Adicionar Valor", type="primary"):
    if novo_valor > 0:
        model.adicionar_valor(novo_valor)
        st.success(f"Valor {novo_valor:.2f}€ adicionado!")
    else:
        st.warning("Insira um valor superior a 0,00€.")

# Exibição de Resumo de Valores
if model.valores:
    texto_packs = " + ".join([f"{v:.2f}€" for v in model.valores])
    st.info(f"**Valores Lançados:** {texto_packs}")

st.metric("TOTAL ACUMULADO", f"{model.obter_total():.2f} €")

# Painel de Monitorização de Limite
st.subheader("📊 Monitorização de Limite")
msg_status, pct = model.obter_status_limite()
st.progress(min(int(pct), 100))
st.caption(msg_status)

# Botões de Ação Final
st.divider()
col_limpar, col_salvar = st.columns(2)

with col_limpar:
    if st.button("🗑️ Limpar Formulário", use_container_width=True):
        model.limpar()
        st.rerun()

with col_salvar:
    if st.button("💾 Registar Pedido", use_container_width=True):
        if model.num_ficha and model.valores:
            st.balloons()
            st.success(
                f"Pedido nº {model.num_ficha} gravado com sucesso! Total final: {model.obter_total():.2f}€"
            )
        else:
            st.error("Preencha o Nº da Ficha e insira pelo menos um valor.")