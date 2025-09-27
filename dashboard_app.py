import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# --- CONFIGURAÇÃO DA APLICAÇÃO ---
# O nome do arquivo .json é removido, pois agora lemos dos segredos
GOOGLE_SHEET_NAME = 'Relatorio_OLT'
# --------------------------------

st.set_page_config(page_title="Dashboard de Clientes", page_icon="📊", layout="wide")

# --- FUNÇÃO DE DADOS ATUALIZADA PARA LER DOS SEGREDOS ---
@st.cache_data(ttl=600)
def load_data_from_gsheet() -> pd.DataFrame:
    """Conecta ao Google Sheets usando as credenciais armazenadas no Streamlit Secrets."""
    try:
        # Pega as credenciais do Google que colamos nos Segredos do Streamlit
        creds_json = st.secrets["google_credentials"]
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Autoriza usando as informações dos segredos, não mais um arquivo
        creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open(GOOGLE_SHEET_NAME)
        worksheet = spreadsheet.sheet1
        data = worksheet.get_all_records()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data)
        if 'ONT ID' in df.columns: df['ONT ID'] = df['ONT ID'].astype(str)
        return df
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados: {e}")
        return pd.DataFrame()

def check_password():
    """Verifica a senha usando os segredos do Streamlit."""
    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 Autenticação Necessária")
    st.markdown("Por favor, insira suas credenciais para acessar o dashboard.")

    correct_username = st.secrets["credentials"]["username"]
    correct_password = st.secrets["credentials"]["password"]

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Login"):
        if username == correct_username and password == correct_password:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorreta.")
    
    return False

def main_dashboard():
    """Exibe o dashboard principal após o login."""
    # (O restante do código do dashboard permanece o mesmo)
    st.title("📊 Dashboard de Clientes Empresariais")
    st.markdown("Utilize a busca na barra lateral para encontrar clientes por OLT.")
    
    if st.sidebar.button("Logout"):
        st.session_state["password_correct"] = False
        st.rerun()

    df = load_data_from_gsheet()

    if not df.empty:
        st.sidebar.header("Busca")
        olt_search_term = st.sidebar.text_input("Digite o nome da OLT:")

        if olt_search_term:
            filtered_df = df[df['OLT NAME'].str.contains(olt_search_term, case=False, na=False)]
            st.subheader(f"Exibindo resultados para a busca: '{olt_search_term}'")
        else:
            filtered_df = df
            st.subheader("Exibindo todos os clientes")
        
        col1, col2 = st.columns(2)
        total_clients = len(filtered_df)
        total_olts = filtered_df['OLT NAME'].nunique()
        
        with col1: st.metric(label="Total de Clientes Encontrados", value=total_clients)
        with col2: st.metric(label="Total de OLTs na Seleção", value=total_olts)
        
        st.markdown("---")
        st.subheader("Detalhes dos Clientes")
        st.dataframe(filtered_df, use_container_width=True)

        if not filtered_df.empty:
            st.subheader("Total de Clientes por OLT (na seleção atual)")
            clients_per_olt = filtered_df['OLT NAME'].value_counts().reset_index()
            clients_per_olt.columns = ['OLT', 'Número de Clientes']
            fig = px.bar(clients_per_olt, x='OLT', y='Número de Clientes', text_auto=True, title="Distribuição de Clientes por OLT")
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não foi possível carregar os dados. Verifique se a planilha do Google Sheets contém dados.")

# --- FLUXO PRINCIPAL DA APLICAÇÃO ---
if check_password():
    main_dashboard()