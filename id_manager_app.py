import streamlit as st
import yaml
import os
import argparse
import signal
from datetime import datetime

# --- 1. CONFIGURAÇÃO DE ARGUMENTOS ---
def get_args():
    parser = argparse.ArgumentParser(description="Gestor de IDs Scouting com Paginação")
    parser.add_argument("--game_data", type=str, required=True, help="Ficheiro YAML")
    parser.add_argument("--gallery", type=str, required=True, help="Pasta da galeria")
    args, _ = parser.parse_known_args()
    return args

if 'args' not in st.session_state:
    st.session_state.args = get_args()
args = st.session_state.args

# --- 2. FUNÇÕES DE DADOS ---
def load_yaml(path):
    if not os.path.exists(path):
        return {"squad": {}, "ignore_ids": [], "same_as": {}, "processing_version": 0}
    with open(path, 'r', encoding="utf-8") as f:
        content = yaml.safe_load(f) or {}
        for key in ['squad', 'ignore_ids', 'same_as']:
            if key not in content: content[key] = {} if key != 'ignore_ids' else []
        if 'processing_version' not in content: content['processing_version'] = 0
        return content

def save_yaml(path, data):
    data['processing_version'] += 1
    data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(path, 'w', encoding="utf-8") as f:
        data['ignore_ids'] = sorted(list(set([int(x) for x in data['ignore_ids']])))
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    st.toast(f"✅ Versão {data['processing_version']} salva!")

# --- 3. CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="ID Manager (Paginação)", layout="wide")

if 'data' not in st.session_state:
    st.session_state.data = load_yaml(args.game_data)
data = st.session_state.data

# Inicializar estado da página
if 'page_index' not in st.session_state:
    st.session_state.page_index = 0

ITEMS_PER_PAGE = 50

# --- BARRA LATERAL ---
with st.sidebar:
    st.header(f"⚙️ Painel v{data['processing_version']}")

    if st.button("💾 Salvar YAML", use_container_width=True):
        save_yaml(args.game_data, data)

    st.divider()
    st.subheader("👥 Jogadores Atuais")
    identified = list(data['squad'].keys())
    if identified:
        p_del = st.selectbox("Remover ID:", ["--"] + [str(x) for x in identified if x != 'referee_id'])
        if p_del != "--" and st.button(f"🗑️ Apagar {p_del}"):
            del data['squad'][p_del]
            save_yaml(args.game_data, data)
            st.rerun()

    st.divider()
    if st.button("❌ Sair e Fechar", use_container_width=True, type="primary"):
        save_yaml(args.game_data, data)
        os.kill(os.getpid(), signal.SIGINT)

# --- 4. LÓGICA DE FILTRAGEM E PAGINAÇÃO ---
if os.path.exists(args.gallery):
    files = [f for f in os.listdir(args.gallery) if f.endswith("_crop.jpg")]

    ignored = [str(x) for x in data['ignore_ids']]
    mapped = list(data['same_as'].keys())
    ref_id = str(data['squad'].get('referee_id', ''))

    # Lista total de IDs pendentes
    all_unidentified = sorted([
        f.split("_")[1] for f in files
        if f.split("_")[1] not in identified
        and f.split("_")[1] not in ignored
        and f.split("_")[1] not in mapped
        and f.split("_")[1] != ref_id
    ], key=int)
else:
    all_unidentified = []

# Cálculos de página
total_ids = len(all_unidentified)
max_pages = (total_ids - 1) // ITEMS_PER_PAGE + 1 if total_ids > 0 else 1

# Garantir que o index da página é válido após remoções
if st.session_state.page_index >= max_pages:
    st.session_state.page_index = max_pages - 1

# --- 5. INTERFACE PRINCIPAL ---
st.title("⚽ Identificação por Grupos")

if total_ids > 0:
    # Controles de Navegação Superiores
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ Anterior", disabled=st.session_state.page_index == 0, use_container_width=True):
            st.session_state.page_index -= 1
            st.rerun()
    with col_info:
        st.markdown(f"<center>Página <b>{st.session_state.page_index + 1}</b> de {max_pages}<br><small>({total_ids} IDs restantes)</small></center>", unsafe_allow_html=True)
    with col_next:
        if st.button("Próximo ➡️", disabled=st.session_state.page_index >= max_pages - 1, use_container_width=True):
            st.session_state.page_index += 1
            st.rerun()

    st.divider()

    # IDs da página atual
    start_idx = st.session_state.page_index * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_batch = all_unidentified[start_idx:end_idx]

    # Exibição dos IDs
    for p_id in current_batch:
        with st.container(border=True):
            col_img, col_form = st.columns([2, 1])

            with col_img:
                t1, t2 = st.tabs([f"🔍 ID {p_id}", "🌍 Campo"])
                with t1: st.image(os.path.join(args.gallery, f"unidentified_{p_id}_crop.jpg"))
                with t2: st.image(os.path.join(args.gallery, f"unidentified_{p_id}_full.jpg"))

            with col_form:
                nome = st.text_input("Novo Nome:", key=f"n_{p_id}")
                if st.button("✅ Novo", key=f"b1_{p_id}", use_container_width=True):
                    data['squad'][str(p_id)] = nome
                    save_yaml(args.game_data, data)
                    st.rerun()

                if identified:
                    target = st.selectbox("Unificar com:", ["--"] + identified, key=f"s_{p_id}")
                    if target != "--" and st.button(f"🔗 Unificar", key=f"b2_{p_id}", use_container_width=True):
                        data['same_as'][str(p_id)] = str(target)
                        save_yaml(args.game_data, data)
                        st.rerun()

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🏁 Ref", key=f"ref_{p_id}", use_container_width=True):
                        data['squad']['referee_id'] = int(p_id)
                        save_yaml(args.game_data, data)
                        st.rerun()
                with c2:
                    if st.button("🚫 Ignorar", key=f"ign_{p_id}", use_container_width=True):
                        data['ignore_ids'].append(int(p_id))
                        save_yaml(args.game_data, data)
                        st.rerun()

    st.divider()

    # Controles Inferiores (para não ter de subir a página)
    if total_ids > ITEMS_PER_PAGE:
        c_prev2, _, c_next2 = st.columns([1, 2, 1])
        with c_prev2:
            if st.button("Anterior", key="prev_down", disabled=st.session_state.page_index == 0, use_container_width=True):
                st.session_state.page_index -= 1
                st.rerun()
        with c_next2:
            if st.button("Próximo", key="next_down", disabled=st.session_state.page_index >= max_pages - 1, use_container_width=True):
                st.session_state.page_index += 1
                st.rerun()
else:
    st.balloons()
    st.success("Todos os IDs foram processados para este jogo!")
