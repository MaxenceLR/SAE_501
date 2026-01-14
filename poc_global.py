import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import plotly.express as px
from datetime import date
from io import BytesIO

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Maison du Droit - Système Intégré", layout="wide")

# --- CONSTANTES (Corrige les Code Smells SonarCloud) ---
DB_CONFIG = {
    "host": "localhost",
    "port": 5437,
    "database": "DB_maison_du_droit",
    "user": "pgis",
    "password": "pgis"
}
TAB_ENTRETIEN = 'ENTRETIEN'
TYPE_MOD = 'MOD'
TYPE_NUM = 'NUM'
TYPE_CHAINE = 'CHAINE'

# --- INITIALISATION DE LA CONNEXION ---
@st.cache_resource
def init_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False 
        return conn
    except Exception as e:
        st.error(f"❌ Connexion PostgreSQL impossible : {e}")
        st.stop()

connection = init_connection()

# =================================================================
# 📥 LOGIQUE ALIMENTATION (Optimisée pour la testabilité)
# =================================================================

@st.cache_data
def get_questionnaire_structure():
    if not connection: return {}
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    structure = {}
    try:
        cursor.execute("SELECT pos, lib FROM rubrique ORDER BY pos")
        rubriques = {row['pos']: row['lib'] for row in cursor.fetchall()}

        cursor.execute(f"""
            SELECT pos, lib, commentaire, type_v, rubrique
            FROM variable
            WHERE tab = %s AND type_v IN ('{TYPE_MOD}','{TYPE_NUM}','{TYPE_CHAINE}')
            ORDER BY rubrique, pos
        """, (TAB_ENTRETIEN,))
        variables = cursor.fetchall()

        for var in variables:
            rub_lib = rubriques.get(var['rubrique'], "Autres Champs")
            if rub_lib not in structure: structure[rub_lib] = []
            
            var_data = {'pos': var['pos'], 'lib': var['lib'], 'type': var['type_v'], 'comment': var['commentaire'], 'options': {}}

            if var['type_v'] == TYPE_MOD:
                cursor.execute("SELECT code, lib_m FROM modalite WHERE tab = %s AND pos = %s ORDER BY pos_m", (TAB_ENTRETIEN, var['pos']))
                var_data['options'] = {row['lib_m']: row['code'] for row in cursor.fetchall()}
            elif var['type_v'] == TYPE_NUM:
                cursor.execute("SELECT val_min, val_max FROM plage WHERE tab = %s AND pos = %s", (TAB_ENTRETIEN, var['pos']))
                plage = cursor.fetchone()
                if plage: var_data['options'] = {'min': plage['val_min'], 'max': plage['val_max']}
            elif var['type_v'] == TYPE_CHAINE:
                cursor.execute("SELECT lib FROM valeurs_c WHERE tab = %s AND pos = %s ORDER BY pos_c", (TAB_ENTRETIEN, var['pos']))
                var_data['options'] = [row['lib'] for row in cursor.fetchall()]

            structure[rub_lib].append(var_data)
        return structure
    finally: cursor.close()

@st.cache_data
def get_demande_solution_modalites():
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT code, lib_m FROM modalite WHERE tab = %s AND pos = 3 ORDER BY pos_m", ('DEMANDE',))
        dem_mod = {row['lib_m']: row['code'] for row in cursor.fetchall()}
        cursor.execute("SELECT code, lib_m FROM modalite WHERE tab = %s AND pos = 3 ORDER BY pos_m", ('SOLUTION',))
        sol_mod = {row['lib_m']: row['code'] for row in cursor.fetchall()}
        return dem_mod, sol_mod
    finally: cursor.close()

def insert_full_entretien(data, conn=None):
    curr_conn = conn if conn else connection
    cursor = curr_conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO entretien (date_ent, mode, duree, sexe, age, vient_pr, sit_fam, enfant, modele_fam, profession, ress, origine, commune, partenaire)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING num
        """, (date.today(), data.get('mode'), data.get('duree'), data.get('sexe'), data.get('age'), data.get('vient_pr'), data.get('sit_fam'), data.get('enfant'), data.get('modele_fam'), data.get('profession'), data.get('ress'), data.get('origine'), data.get('commune'), data.get('partenaire')))
        new_num = cursor.fetchone()[0]
        curr_conn.commit()
        return new_num
    except Exception as e:
        curr_conn.rollback(); st.error(f"Erreur insertion : {e}"); return None
    finally: cursor.close()

def insert_demandes(num, codes, conn=None):
    if not codes: return
    curr_conn = conn if conn else connection
    cursor = curr_conn.cursor()
    try:
        cursor.executemany("INSERT INTO demande (num, pos, nature) VALUES (%s,%s,%s)", [(num, i+1, c) for i,c in enumerate(codes)])
        curr_conn.commit()
    finally: cursor.close()

def insert_solutions(num, codes, conn=None):
    if not codes: return
    curr_conn = conn if conn else connection
    cursor = curr_conn.cursor()
    try:
        cursor.executemany("INSERT INTO solution (num, pos, nature) VALUES (%s,%s,%s)", [(num, i+1, c) for i,c in enumerate(codes)])
        curr_conn.commit()
    finally: cursor.close()

# =================================================================
# 📊 LOGIQUE VISUALISATION
# =================================================================

@st.cache_data
def get_data_for_reporting(conn=None):
    curr_conn = conn if conn else connection
    cursor = curr_conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT num, date_ent, sexe, age, sit_fam, profession, duree, commune, mode, vient_pr FROM entretien")
        return pd.DataFrame(cursor.fetchall())
    finally: cursor.close()

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Export')
    return output.getvalue()

# =================================================================
# 🛠️ HELPERS D'INTERFACE (Réduit la complexité cognitive)
# =================================================================

def render_dynamic_field(var, col):
    """Gère l'affichage d'un champ unique selon son type."""
    lib, comment, type_v = var['lib'], var['comment'], var['type']
    with col:
        if type_v == TYPE_MOD:
            opts = list(var['options'].keys())
            sel = st.selectbox(f"**{lib}**", opts, index=None, placeholder=comment, key=f"f_{lib}")
            return var['options'].get(sel) if sel else None
        elif type_v == TYPE_NUM:
            return st.number_input(f"**{lib}**", min_value=var['options'].get('min', 0), max_value=var['options'].get('max', 99), key=f"f_{lib}")
        elif type_v == TYPE_CHAINE:
            return st.text_input(f"**{lib}**", key=f"f_{lib}", help=comment)
    return None

# =================================================================
# 🚀 RENDU DES ONGLETS
# =================================================================

tab_alimentation, tab_visualisation = st.tabs(["📥 ALIMENTATION", "📊 VISUALISATION"])

with tab_alimentation:
    structure = get_questionnaire_structure()
    demande_opt, sol_opt = get_demande_solution_modalites()
    
    if structure:
        data_entretien = {}
        st.title("📋 Saisie d'Entretien")
        with st.form(key='main_form'):
            for rubrique, variables in structure.items():
                st.header(f"➡️ {rubrique}")
                cols = st.columns(2)
                for i, var in enumerate(variables):
                    val = render_dynamic_field(var, cols[i % 2])
                    data_entretien[var['lib'].lower()] = val
                st.markdown("---")

            st.subheader("Natures de la demande")
            sel_dem = st.multiselect("Sélection (max 3)", list(demande_opt.keys()), max_selections=3)
            st.subheader("Réponses apportées")
            sel_sol = st.multiselect("Sélection (max 3)", list(sol_opt.keys()), max_selections=3)

            if st.form_submit_button("💾 ENREGISTRER L'ENTRETIEN"):
                if not sel_dem: st.error("Sélectionnez au moins une demande.")
                else:
                    new_id = insert_full_entretien(data_entretien)
                    if new_id:
                        insert_demandes(new_id, [demande_opt[l] for l in sel_dem])
                        insert_solutions(new_id, [sol_opt[l] for l in sel_sol])
                        st.success(f"Entretien N°{new_id} enregistré !"); st.balloons()
    else: st.error("Impossible de charger les rubriques.")

with tab_visualisation:
    # ... (Garder ton code de visualisation tel quel, il est déjà correct)
    st.title("📊 Analyse Statistique")
    # Appel simplifié grâce à la valeur par défaut du paramètre conn
    df = get_data_for_reporting() 
    # (Tes graphiques ici...)