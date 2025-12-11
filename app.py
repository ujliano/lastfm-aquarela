import streamlit as st
import pylast
import colorgram
import requests
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Aquarela Musical", page_icon="🎨")

st.title("🎨 Sua Aquarela Musical")
st.write("Descubra a paleta de cores dos álbuns que você mais ouve.")

# --- SIDEBAR (INPUTS) ---
with st.sidebar:
    st.header("Configurações")
    username = st.text_input("Usuário Last.fm", value="rj") # Valor padrão
    period_option = st.selectbox(
        "Período",
        ["7 Dias", "1 Mês", "3 Meses", "6 Meses", "12 Meses", "Geral"]
    )
    limit = st.slider("Qtd. de Álbuns", 10, 100, 20)
    
    # Mapeamento do texto para constantes do Pylast
    period_map = {
        "7 Dias": pylast.PERIOD_7DAYS,
        "1 Mês": pylast.PERIOD_1MONTH,
        "3 Meses": pylast.PERIOD_3MONTHS,
        "6 Meses": pylast.PERIOD_6MONTHS,
        "12 Meses": pylast.PERIOD_12MONTHS,
        "Geral": pylast.PERIOD_OVERALL
    }

# --- FUNÇÕES DE BACKEND ---
# Cache para não chamar a API toda hora se nada mudou
@st.cache_data
def get_data(user_input, period_input, limit_input, api_key, api_secret):
    try:
        network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret)
        user = network.get_user(user_input)
        top_albums = user.get_top_albums(period=period_input, limit=limit_input)
        
        data = []
        for item in top_albums:
            album = item.item
            # Pega URL da capa
            cover_url = album.get_cover_image()
            
            if cover_url:
                try:
                    response = requests.get(cover_url)
                    img = BytesIO(response.content)
                    colors = colorgram.extract(img, 1)
                    if colors:
                        rgb = colors[0].rgb
                        hex_color = '#%02x%02x%02x' % rgb
                        data.append({"Hex": hex_color})
                except:
                    pass
        return pd.DataFrame(data)
    except Exception as e:
        return str(e)

# --- O BOTÃO DE AÇÃO ---
if st.button("Gerar Aquarela 🚀"):
    # Pegando as chaves dos segredos do Streamlit (Explico abaixo)
    API_KEY = st.secrets["LASTFM_KEY"]
    API_SECRET = st.secrets["LASTFM_SECRET"]

    with st.spinner('Pintando seus dados... (isso demora um pouquinho)'):
        result = get_data(username, period_map[period_option], limit, API_KEY, API_SECRET)

        if isinstance(result, str): # Se voltou erro
            st.error(f"Erro ao buscar usuário: {result}")
        elif result.empty:
            st.warning("Nenhum álbum com capa encontrado para este período.")
        else:
            # PLOTAGEM
            fig, ax = plt.subplots(figsize=(10, 2))
            ax.set_axis_off()
            
            for i, row in result.iterrows():
                rect = patches.Rectangle((i, 0), 1, 1, linewidth=0, edgecolor='none', facecolor=row['Hex'])
                ax.add_patch(rect)
            
            plt.xlim(0, len(result))
            plt.ylim(0, 1)
            
            st.pyplot(fig)
            st.success(f"Analisados {len(result)} álbuns com sucesso!")
