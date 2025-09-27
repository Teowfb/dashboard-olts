import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from pathlib import Path
import base64 # Biblioteca para processar a imagem

# --- CONFIGURAÇÃO DA APLICAÇÃO ---
SCRIPT_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = SCRIPT_DIR / "static-balm-449810-m7-ef72ed9a8d30.json"
GOOGLE_SHEET_NAME = 'Relatorio_OLT'
LOGO_IMAGE_FILE = SCRIPT_DIR / "logo_claro.png" # Nome do arquivo do seu logo
# --------------------------------

st.set_page_config(page_title="Dashboard Claro", page_icon=str(LOGO_IMAGE_FILE), layout="wide")

# --- FUNÇÕES ---

def set_background(image_file):
    """
    Função para definir uma imagem de fundo na aplicação Streamlit.
    """
    try:
        with open(image_file, "rb") as f:
            img_bytes = f.read()
        encoded_img = base64.b64encode(img_bytes).decode()
        
        # CSS para aplicar o fundo e as cores da Claro
        style = f"""
        <style>
        [data-testid="stAppViewContainer"] > .main {{
            background-image: url("data:image/png;base64,{encoded_img}");
            background-size: 150px;
            background-position: center 15%;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        [data-testid="stHeader"] {{
            background-color: rgba(0,0,0,0);
        }}
        h1, h2, h3 {{
            color: #E3262E; /* Vermelho Claro */
        }}
        .st-emotion-cache-16txtl3 {{
            background-color: #E3262E; /* Vermelho Claro para o header da tabela */
        }}
        </style>
        """
        st.markdown(style, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo de logo não encontrado. O fundo não será aplicado.")
    except Exception as e:
        st.error(f"Erro ao aplicar o fundo: {e}")

@st.cache_data(ttl=600)
def load_data_from_gsheet() -> pd.DataFrame:
    # (Esta função permanece a mesma da versão anterior)
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
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
    # (Esta função permanece a mesma da versão anterior)
    if st.session_state.get("password_correct", False):
        return True
    st.title("🔒 Autenticação Necessária")
    st.markdown("Por favor, insira suas credenciais para acessar o dashboard.")
    try:
        correct_username = st.secrets["credentials"]["username"]
        correct_password = st.secrets["credentials"]["password"]
    except FileNotFoundError:
        st.error("Arquivo de segredos (.streamlit/secrets.toml) não encontrado.")
        return False
    
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
    # Aplica o fundo e as cores da Claro
    set_background(LOGO_IMAGE_FILE)

    st.title("Dashboard de Clientes Empresariais")
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
        else:
            filtered_df = df
        
        st.subheader(f"Resultados da Busca ({len(filtered_df)} encontrados)")
        st.dataframe(filtered_df, use_container_width=True)

        if not filtered_df.empty and olt_search_term == "":
            st.subheader("Total de Clientes por OLT")
            clients_per_olt = df['OLT NAME'].value_counts().reset_index()
            clients_per_olt.columns = ['OLT', 'Número de Clientes']
            fig = px.bar(clients_per_olt, x='OLT', y='Número de Clientes', text_auto=True, title="Distribuição de Clientes por OLT")
            fig.update_traces(textposition='outside', marker_color='#E3262E')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não foi possível carregar os dados. Verifique se a planilha do Google Sheets contém dados.")

# --- FLUXO PRINCIPAL DA APLICAÇÃO ---
if check_password():
    main_dashboard()