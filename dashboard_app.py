import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from pathlib import Path
import base64 # Biblioteca para processar a imagem

# --- CONFIGURAÇÃO DA APLICAÇÃO ---
# Caminho para o arquivo de credenciais
CREDENTIALS_FILE = 'static-balm-449810-m7-ef72ed9a8d30.json'
GOOGLE_SHEET_NAME = 'Relatorio_OLT'
# Nome do arquivo do seu logo
LOGO_IMAGE_FILE = "logo_claro.png"
# --------------------------------

st.set_page_config(page_title="Dashboard Claro", page_icon=LOGO_IMAGE_FILE, layout="wide")

# --- FUNÇÕES ---

def set_page_style(image_file):
    """
    Aplica um estilo personalizado à página, incluindo um logo de fundo e cores da marca.
    """
    try:
        with open(image_file, "rb") as f:
            img_bytes = f.read()
        encoded_img = base64.b64encode(img_bytes).decode()
        
        # CSS para aplicar o fundo semi-transparente e as cores da Claro
        style = f"""
        <style>
        [data-testid="stAppViewContainer"] > .main {{
            background-image: linear-gradient(rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.95)), url("data:image/png;base64,{encoded_img}");
            background-size: 200px;
            background-position: center 20%;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* Cor dos títulos principais */
        h1, h2, h3 {{
            color: #E3262E; /* Vermelho Claro */
        }}
        /* Cor do cabeçalho da tabela */
        .st-emotion-cache-16txtl3 {{
            background-color: #E3262E;
            color: white;
        }}
        </style>
        """
        st.markdown(style, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Arquivo de logo '{image_file}' não encontrado. O fundo personalizado não será aplicado.")
    except Exception as e:
        st.error(f"Erro ao aplicar o estilo de fundo: {e}")

@st.cache_data(ttl=600)
def load_data_from_gsheet() -> pd.DataFrame:
    """Conecta ao Google Sheets e carrega os dados."""
    try:
        creds_json = st.secrets["google_credentials"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
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
    set_page_style(LOGO_IMAGE_FILE)
    st.title("Dashboard de Clientes Empresariais")
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
        with col1: st.metric(label="Total de Clientes Encontrados", value=len(filtered_df))
        with col2: st.metric(label="Total de OLTs na Seleção", value=filtered_df['OLT NAME'].nunique())
        st.markdown("---")
        st.dataframe(filtered_df, use_container_width=True)
        if not filtered_df.empty:
            st.subheader("Total de Clientes por OLT (na seleção atual)")
            clients_per_olt = filtered_df['OLT NAME'].value_counts().reset_index()
            clients_per_olt.columns = ['OLT', 'Número de Clientes']
            fig = px.bar(clients_per_olt, x='OLT', y='Número de Clientes', text_auto=True, title="Distribuição de Clientes por OLT")
            fig.update_traces(marker_color='#E3262E')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não foi possível carregar os dados.")

# --- FLUXO PRINCIPAL DA APLICAÇÃO ---
if check_password():
    main_dashboard()