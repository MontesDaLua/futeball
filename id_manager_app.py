"""
Interface de Gestão de IDs:
- Paginação de 50 em 50.
- Atribuição de ID ao Árbitro.
- Crop em tamanho original e Vista de campo expandida.
"""
import streamlit as st
import yaml
import os
import argparse
import signal

def get_args():
    parser = argparse.ArgumentParser(description="ID Manager Scouting")
    parser.add_argument("--game_data", type=str, required=True, help="Ficheiro YAML")
    parser.add_argument("--gallery", type=str, required=True, help="Pasta da galeria")
    args, _ = parser.parse_known_args()
    return args

def load_yaml(path):
    if not os.path.exists(path):
        return {"squad": {}, "ignore_ids": [], "same_as": {}, "processing_version": 0}
    with open(path, 'r', encoding="utf-8") as f:
        content = yaml.safe_load(f) or {}
        # Garantir estrutura básica
        if 'squad' not in content: content['squad'] = {}
        if 'ignore_ids' not in content: content['ignore_ids'] = []
        return content

def save_yaml(path, data):
    data['processing_version'] = data.get('processing_version', 0) + 1
    with open(path, 'w', encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    st.toast("✅ Configuração Guardada!")

st.set_page_config(page_title="Scouting ID Manager", layout="wide")

if 'args' not in st.session_state:
    st.session_state.args = get_args()
args = st.session_state.args

if 'data' not in st.session_state:
    st.session_state.data = load_yaml(args.game_data)
data = st.session_state.data

if 'page_index' not in st.session_state:
    st.session_state.page_index = 0

# --- 1. MAPEAMENTO E FILTRAGEM ---
pending_list = []
if os.path.exists(args.gallery):
    all_crops = sorted([f for f in os.listdir(args.gallery) if f.endswith("_crop.jpg")])
    ignored = [str(x) for x in data.get('ignore_ids', [])]
    identified = data.get('squad', {}).keys()
    current_ref = str(data.get('squad', {}).get('referee_id', ''))

    for fname in all_crops:
        parts = fname.split("_")
        if len(parts) >= 2:
            color, p_id = parts[0], parts[1]
            # Não mostrar se já for jogador, se estiver ignorado ou se já for o árbitro
            if p_id not in identified and p_id not in ignored and p_id != current_ref:
                pending_list.append({'id': p_id, 'color': color, 'crop': fname})

# --- 2. PAGINAÇÃO ---
ITEMS_PER_PAGE = 50
total_items = len(pending_list)
max_pages = (total_items - 1) // ITEMS_PER_PAGE + 1 if total_items > 0 else 1
if st.session_state.page_index >= max_pages:
    st.session_state.page_index = max(0, max_pages - 1)

st.title(f"⚽ Identificação de IDs ({total_items} pendentes)")

# Mostrar ID do árbitro atual, se existir
if data.get('squad', {}).get('referee_id'):
    st.sidebar.success(f"🏁 Árbitro Atual: ID {data['squad']['referee_id']}")

if total_items > 0:
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    with col_nav1:
        if st.button("⬅️ Anterior", disabled=st.session_state.page_index == 0, use_container_width=True):
            st.session_state.page_index -= 1
            st.rerun()
    with col_nav2:
        st.markdown(f"<h4 style='text-align: center;'>Página {st.session_state.page_index + 1} de {max_pages}</h4>", unsafe_allow_html=True)
    with col_nav3:
        if st.button("Próximo ➡️", disabled=st.session_state.page_index >= max_pages - 1, use_container_width=True):
            st.session_state.page_index += 1
            st.rerun()

    start_idx = st.session_state.page_index * ITEMS_PER_PAGE
    current_batch = pending_list[start_idx : start_idx + ITEMS_PER_PAGE]

    for item in current_batch:
        p_id = item['id']
        color = item['color']
        crop_name = item['crop']
        full_name = crop_name.replace("_crop.jpg", "_full.jpg")

        with st.container(border=True):
            col_crop, col_full, col_form = st.columns([1, 3, 1.2])

            with col_crop:
                st.caption(f"🔍 ID: {p_id}")
                st.image(os.path.join(args.gallery, crop_name))
                st.info(f"🎨 Cor: {color.upper()}")

            with col_full:
                full_path = os.path.join(args.gallery, full_name)
                if os.path.exists(full_path):
                    st.image(full_path, use_container_width=True)

            with col_form:
                st.write("### Atribuir")
                nome = st.text_input(f"Nome do Jogador:", key=f"in_{p_id}")

                # Botões de Ação
                if st.button("✅ Salvar Jogador", key=f"s_{p_id}", use_container_width=True):
                    if nome:
                        data['squad'][str(p_id)] = nome
                        save_yaml(args.game_data, data)
                        st.rerun()

                # NOVO: Botão para Árbitro
                if st.button("🏁 Definir como Árbitro", key=f"ref_{p_id}", use_container_width=True):
                    data['squad']['referee_id'] = int(p_id)
                    save_yaml(args.game_data, data)
                    st.rerun()

                if st.button("🚫 Ignorar ID", key=f"i_{p_id}", use_container_width=True):
                    data['ignore_ids'].append(int(p_id))
                    save_yaml(args.game_data, data)
                    st.rerun()

else:
    st.success("🎉 Todos os IDs processados!")

if st.sidebar.button("❌ Sair"):
    os.kill(os.getpid(), signal.SIGINT)
