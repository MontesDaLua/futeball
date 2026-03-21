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
        return {"squad": {}, "ignore_ids": [], "same_as": {}, "available_players": []}
    with open(path, 'r', encoding="utf-8") as f:
        content = yaml.safe_load(f) or {}
        for key in ['squad', 'ignore_ids', 'same_as', 'available_players']:
            if key not in content:
                content[key] = [] if key in ['ignore_ids', 'available_players'] else {}
        return content

def save_yaml(path, data):
    with open(path, 'w', encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    st.toast("✅ YAML Atualizado!")

st.set_page_config(page_title="Scouting ID Manager", layout="wide")

if 'args' not in st.session_state:
    st.session_state.args = get_args()

data = load_yaml(st.session_state.args.game_data)
args = st.session_state.args

if 'page_index' not in st.session_state:
    st.session_state.page_index = 0

# --- LÓGICA DE NOMES E IDENTIFICADOS ---
squad_dict = data.get('squad', {})
# Nomes já em campo (exclui referee_id)
names_in_field = sorted([v for k, v in squad_dict.items() if k != 'referee_id' and isinstance(v, str)])
# Nomes ainda por entrar
available_to_assign = sorted([n for n in data.get('available_players', []) if n not in names_in_field])

# --- BARRA LATERAL ---
st.sidebar.title("📋 Estado do Plantel")
st.sidebar.subheader("⏳ Disponíveis")
for n in available_to_assign:
    st.sidebar.text(f"• {n}")

st.sidebar.divider()
st.sidebar.subheader("✅ Em Campo")
for k, v in squad_dict.items():
    if k != 'referee_id':
        col_s1, col_s2 = st.sidebar.columns([4, 1])
        # Mostrar quantos IDs extras este jogador tem
        num_aliases = len(data.get('same_as', {}).get(k, []))
        extra = f" (+{num_aliases})" if num_aliases > 0 else ""
        col_s1.text(f"{v} (ID {k}){extra}")
        if col_s2.button("🗑️", key=f"del_side_{k}"):
            del data['squad'][k]
            if k in data['same_as']: del data['same_as'][k]
            save_yaml(args.game_data, data)
            st.rerun()

# --- FILTRAGEM DE PENDENTES ---
pending_list = []
if os.path.exists(args.gallery):
    all_crops = sorted([f for f in os.listdir(args.gallery) if f.endswith("_crop.jpg")])
    ignored = [str(x) for x in data.get('ignore_ids', [])]

    # IDs que já são aliases (não precisam de nova identificação)
    all_aliases = []
    for val in data.get('same_as', {}).values():
        if isinstance(val, list): all_aliases.extend([str(x) for x in val])
        else: all_aliases.append(str(val))

    for fname in all_crops:
        p_id = fname.split("_")[1]
        if (p_id not in squad_dict and
            p_id not in ignored and
            p_id not in all_aliases and
            p_id != str(squad_dict.get('referee_id', ''))):
            pending_list.append({'id': p_id, 'color': fname.split("_")[0], 'crop': fname})

# --- PAGINAÇÃO ---
ITEMS_PER_PAGE = 50
total_items = len(pending_list)
max_pages = max(1, (total_items - 1) // ITEMS_PER_PAGE + 1)
start_idx = st.session_state.page_index * ITEMS_PER_PAGE
current_batch = pending_list[start_idx : start_idx + ITEMS_PER_PAGE]

st.title(f"⚽ Identificação de IDs ({total_items} pendentes)")

if total_items > 0:
    # Navegação
    c_n1, c_n2, c_n3 = st.columns([1, 2, 1])
    with c_n1:
        if st.button("⬅️ Anterior", disabled=st.session_state.page_index == 0):
            st.session_state.page_index -= 1
            st.rerun()
    with c_n2:
        st.markdown(f"<p style='text-align:center'>Página {st.session_state.page_index+1} de {max_pages}</p>", unsafe_allow_html=True)
    with c_n3:
        if st.button("Próximo ➡️", disabled=st.session_state.page_index >= max_pages - 1):
            st.session_state.page_index += 1
            st.rerun()

    for item in current_batch:
        p_id = item['id']
        with st.container(border=True):
            col_img, col_ctx, col_actions = st.columns([1, 2, 1.5])

            with col_img:
                st.image(os.path.join(args.gallery, item['crop']))
                st.caption(f"ID Detetado: {p_id}")

            with col_ctx:
                full_path = os.path.join(args.gallery, item['crop'].replace("_crop.jpg", "_full.jpg"))
                if os.path.exists(full_path):
                    st.image(full_path, use_container_width=True)

            with col_actions:
                # OPÇÃO 1: NOVO NO CAMPO
                st.write("**Entrada de Novo Jogador:**")
                escolha_nova = st.selectbox("Selecione da lista:", [""] + available_to_assign, key=f"new_{p_id}", label_visibility="collapsed")
                if st.button("➕ Confirmar Entrada", key=f"btn_new_{p_id}", use_container_width=True):
                    if escolha_nova:
                        data['squad'][str(p_id)] = escolha_nova
                        save_yaml(args.game_data, data)
                        st.rerun()

                st.divider()

                # OPÇÃO 2: JOGADOR JÁ IDENTIFICADO (VÍNCULO)
                st.write("**Vincular a Jogador já em Campo:**")
                escolha_vinculo = st.selectbox("Selecione quem é:", [""] + names_in_field, key=f"link_{p_id}", label_visibility="collapsed")
                if st.button("🔗 Mesclar com Existente", key=f"btn_link_{p_id}", use_container_width=True):
                    if escolha_vinculo:
                        # Encontra o ID "Mestre" (o primeiro ID atribuído a este nome)
                        master_id = [k for k, v in squad_dict.items() if v == escolha_vinculo][0]
                        if master_id not in data['same_as']: data['same_as'][master_id] = []
                        data['same_as'][master_id].append(int(p_id))
                        save_yaml(args.game_data, data)
                        st.rerun()

                st.divider()

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🏁 Árbitro", key=f"ref_{p_id}", use_container_width=True):
                        data['squad']['referee_id'] = int(p_id)
                        save_yaml(args.game_data, data)
                        st.rerun()
                with c2:
                    if st.button("🚫 Ignorar", key=f"ign_{p_id}", use_container_width=True):
                        data['ignore_ids'].append(int(p_id))
                        save_yaml(args.game_data, data)
                        st.rerun()

else:
    st.success("🎉 Scouting completo! Todos os IDs foram atribuídos ou vinculados.")

st.sidebar.divider()
if st.sidebar.button("❌ Encerrar"):
    os.kill(os.getpid(), signal.SIGINT)
