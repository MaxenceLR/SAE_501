import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import plotly.express as px
from datetime import date
from io import BytesIO

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Maison du Droit - Système Intégré", layout="wide")

# --- PARAMÈTRES DE CONNEXION ---
PG_HOST = "localhost"
PG_PORT = 5437
PG_DB = "DB_maison_du_droit"
PG_USER = "pgis"
PG_PASSWORD = "pgis"

# --- INITIALISATION DE LA CONNEXION ---
@st.cache_resource
def init_connection():
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_DB,
            user=PG_USER, password=PG_PASSWORD
        )
        # On garde autocommit=False pour gérer les transactions manuellement comme dans ton POC
        conn.autocommit = False 
        return conn
    except Exception as e:
        st.error(f"❌ Impossible de se connecter à PostgreSQL : {e}")
        st.stop()

connection = init_connection()

# =================================================================
# 📥 LOGIQUE ALIMENTATION (REPRISE EXACTE DE TON POC FORMULAIRE)
# =================================================================

@st.cache_data
def get_questionnaire_structure():
    if not connection: return {}
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    structure = {}
    try:
        cursor.execute("SELECT pos, lib FROM rubrique ORDER BY pos")
        rubriques = {row['pos']: row['lib'] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT pos, lib, commentaire, type_v, rubrique
            FROM variable
            WHERE tab = %s AND type_v IN ('MOD','NUM','CHAINE')
            ORDER BY rubrique, pos
        """, ('ENTRETIEN',))
        variables = cursor.fetchall()

        for var in variables:
            rubrique_lib = rubriques.get(var['rubrique'], "Autres Champs")
            if rubrique_lib not in structure:
                structure[rubrique_lib] = []

            var_data = {
                'pos': var['pos'], 'lib': var['lib'], 'type': var['type_v'],
                'comment': var['commentaire'], 'options': {}
            }

            if var['type_v'] == 'MOD':
                cursor.execute("SELECT code, lib_m FROM modalite WHERE tab = %s AND pos = %s ORDER BY pos_m", ('ENTRETIEN', var['pos']))
                var_data['options'] = {row['lib_m']: row['code'] for row in cursor.fetchall()}
            elif var['type_v'] == 'NUM':
                cursor.execute("SELECT val_min, val_max FROM plage WHERE tab = %s AND pos = %s", ('ENTRETIEN', var['pos']))
                plage = cursor.fetchone()
                if plage: var_data['options'] = {'min': plage['val_min'], 'max': plage['val_max']}
            elif var['type_v'] == 'CHAINE':
                cursor.execute("SELECT lib FROM valeurs_c WHERE tab = %s AND pos = %s ORDER BY pos_c", ('ENTRETIEN', var['pos']))
                var_data['options'] = [row['lib'] for row in cursor.fetchall()]

            structure[rubrique_lib].append(var_data)
        return structure
    finally:
        cursor.close()

@st.cache_data
def get_demande_solution_modalites():
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT code, lib_m FROM modalite WHERE tab = %s AND pos = 3 ORDER BY pos_m", ('DEMANDE',))
        demande_modalites = {row['lib_m']: row['code'] for row in cursor.fetchall()}
        cursor.execute("SELECT code, lib_m FROM modalite WHERE tab = %s AND pos = 3 ORDER BY pos_m", ('SOLUTION',))
        solution_modalites = {row['lib_m']: row['code'] for row in cursor.fetchall()}
        return demande_modalites, solution_modalites
    finally:
        cursor.close()

# Fonctions d'insertion (Entretien, Demandes, Solutions)
def insert_full_entretien(data, conn=connection):
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO entretien (date_ent, mode, duree, sexe, age, vient_pr, sit_fam, enfant, modele_fam, profession, ress, origine, commune, partenaire)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING num
        """, (date.today(), data.get('mode'), data.get('duree'), data.get('sexe'), data.get('age'), data.get('vient_pr'), data.get('sit_fam'), data.get('enfant'), data.get('modele_fam'), data.get('profession'), data.get('ress'), data.get('origine'), data.get('commune'), data.get('partenaire')))
        new_num = cursor.fetchone()[0]
        connection.commit()
        return new_num
    except Exception as e:
        connection.rollback()
        st.error(f"Erreur insertion : {e}")
        return None
    finally: cursor.close()

def insert_demandes(num, codes, conn=connection):
    if not codes: return
    cursor = connection.cursor()
    try:
        cursor.executemany("INSERT INTO demande (num, pos, nature) VALUES (%s,%s,%s)", [(num, i+1, c) for i,c in enumerate(codes)])
        connection.commit()
    finally: cursor.close()

def insert_solutions(num, codes, conn=connection):
    if not codes: return
    cursor = connection.cursor()
    try:
        cursor.executemany("INSERT INTO solution (num, pos, nature) VALUES (%s,%s,%s)", [(num, i+1, c) for i,c in enumerate(codes)])
        connection.commit()
    finally: cursor.close()

# =================================================================
# 📊 LOGIQUE VISUALISATION (REPRISE DE TON POC REPORTING)
# =================================================================

@st.cache_data
def get_data_for_reporting(conn=connection):
    cursor = connection.cursor(cursor_factory=RealDictCursor)
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
# 🛠️ INTERFACE PRINCIPALE (ONGLETS)
# =================================================================

tab_alimentation, tab_visualisation = st.tabs(["📥 ALIMENTATION", "📊 VISUALISATION"])

# --- ONGLET 1 : FORMULAIRE ---
with tab_alimentation:
    structure = get_questionnaire_structure()
    demande_opt, sol_opt = get_demande_solution_modalites()
    
    if structure:
        data_entretien = {}
        st.title("📋 Saisie d'Entretien")
        
        with st.form(key='main_form'):
            # REPRISE DE TA BOUCLE ORIGINALE
            for rubrique, variables in structure.items():
                st.header(f"➡️ {rubrique}")
                cols = st.columns(2)
                for i, var in enumerate(variables):
                    lib, comment, type_v = var['lib'], var['comment'], var['type']
                    with cols[i % 2]:
                        if type_v == 'MOD':
                            opts = list(var['options'].keys())
                            sel = st.selectbox(f"**{lib}**", opts, index=None, placeholder=comment, key=f"f_{lib}")
                            data_entretien[lib.lower()] = var['options'].get(sel) if sel else None
                        elif type_v == 'NUM':
                            val = st.number_input(f"**{lib}**", min_value=var['options'].get('min',0), max_value=var['options'].get('max',99), key=f"f_{lib}")
                            data_entretien[lib.lower()] = val
                        elif type_v == 'CHAINE':
                            val = st.text_input(f"**{lib}**", key=f"f_{lib}", help=comment)
                            data_entretien[lib.lower()] = val
                st.markdown("---")

            st.subheader("Natures de la demande")
            sel_dem = st.multiselect("Sélection (max 3)", list(demande_opt.keys()), max_selections=3)
            
            st.subheader("Réponses apportées")
            sel_sol = st.multiselect("Sélection (max 3)", list(sol_opt.keys()), max_selections=3)

            if st.form_submit_button("💾 ENREGISTRER L'ENTRETIEN"):
                # Validation et insertion
                if not sel_dem:
                    st.error("Sélectionnez au moins une demande.")
                else:
                    new_id = insert_full_entretien(data_entretien)
                    if new_id:
                        insert_demandes(new_id, [demande_opt[l] for l in sel_dem])
                        insert_solutions(new_id, [sol_opt[l] for l in sel_sol])
                        st.success(f"Entretien N°{new_id} enregistré !")
                        st.balloons()
    else:
        st.error("Impossible de charger les rubriques depuis la base.")

# --- ONGLET 2 : VISUALISATION ---
with tab_visualisation:
    st.title("📊 Analyse Statistique")
    df = get_data_for_reporting()
    
    if not df.empty:
        # Sous-onglets demandés
        sub1, sub2 = st.tabs(["📈 Global", "🔍 Personnalisé"])
        
        with sub1:
            st.header("📈 Tableau de Bord Global")

            # --- 1. LES 3 KPIs (Indicateurs clés) ---
            k1, k2, k3 = st.columns(3)
            
            # KPI 1 : Nombre total d'entretiens (clients)
            k1.metric("Total Entretiens", len(df))
            
            # KPI 2 : Commune la plus représentée
            if not df["commune"].empty:
                top_commune = df["commune"].mode()[0]
                k2.metric("Commune Top", top_commune)
            
            # KPI 3 : Mode d'entretien dominant
            if not df["mode"].empty:
                top_mode = df["mode"].mode()[0]
                k3.metric("Mode Dominant", top_mode)

            st.divider()

            # --- 2. RÉPARTITION SEXE ET ÂGE ---
            col_sex, col_age = st.columns(2)
            
            with col_sex:
                fig_sex = px.pie(df, names="sexe", title="Répartition par Sexe", 
                                 hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_sex, use_container_width=True)
                
            with col_age:
                # Création automatique de tranches d'âge si besoin, sinon histogramme simple
                fig_age = px.histogram(df, x="age", title="Répartition par Tranches d'Âge",
                                      color_discrete_sequence=['#636EFA'], nbins=10)
                fig_age.update_layout(bargap=0.1)
                st.plotly_chart(fig_age, use_container_width=True)

            # --- 3. VOLUME PAR COMMUNE ---
            st.subheader("📍 Volume d'activité par Commune")
            # Tri par nombre décroissant pour une lecture facile
            commune_counts = df["commune"].value_counts().reset_index()
            commune_counts.columns = ['Commune', 'Nombre']
            fig_commune = px.bar(commune_counts, x="Nombre", y="Commune", orientation='h',
                                 title="Fréquentation par zone géographique",
                                 color="Nombre", color_continuous_scale='Viridis')
            st.plotly_chart(fig_commune, use_container_width=True)

            st.divider()

            

        with sub2:
            st.header("🔍 Analyse croisée et personnalisée")
            
            # --- ZONE DE RÉGLAGES ---
            st.info("Configurez votre analyse ci-dessous :")
            col_v1, col_v2, col_type = st.columns(3)
            
            with col_v1:
                # Variable principale
                var_x = st.selectbox("1. Variable principale (Axe X)", df.columns, index=2)
            
            with col_v2:
                # Variable de croisement (optionnelle)
                # On ajoute "Aucun" en haut de la liste pour ne pas forcer le croisement
                options_croisement = [None] + list(df.columns)
                var_color = st.selectbox("2. Croiser avec (Couleur/Légende)", options_croisement, index=0)
            
            with col_type:
                # Choix du style de rendu
                chart_type = st.selectbox("3. Type de graphique", 
                                          ["Barres / Histogramme", "Secteurs (Pie Chart)", "Boîte à moustaches (Box Plot)"])

            st.divider()

            # --- GÉNÉRATION DYNAMIQUE DU GRAPHIQUE ---
            try:
                title_text = f"Analyse de {var_x}" + (f" croisée par {var_color}" if var_color else "")
                
                if chart_type == "Barres / Histogramme":
                    # barmode="group" permet de mettre les barres côte à côte pour le croisement
                    fig_custom = px.histogram(df, x=var_x, color=var_color, 
                                             barmode="group", text_auto=True, 
                                             title=title_text,
                                             color_discrete_sequence=px.colors.qualitative.Pastel)
                
                elif chart_type == "Secteurs (Pie Chart)":
                    if var_color:
                        st.warning("⚠️ Le graphique en secteurs ne peut afficher qu'une seule variable. Le croisement est ignoré.")
                    fig_custom = px.pie(df, names=var_x, title=f"Répartition de {var_x}", 
                                       hole=0.3, color_discrete_sequence=px.colors.qualitative.Safe)
                
                elif chart_type == "Boîte à moustaches (Box Plot)":
                    # Idéal pour voir la distribution d'une valeur numérique (ex: Âge) en fonction d'une catégorie
                    if "age" in df.columns:
                        fig_custom = px.box(df, x=var_x, y="age", color=var_color, 
                                           title=f"Distribution de l'Âge par {var_x}",
                                           points="all")
                    else:
                        st.error("La variable 'age' est nécessaire pour le Box Plot.")
                        fig_custom = None

                # Affichage final
                if fig_custom:
                    st.plotly_chart(fig_custom, use_container_width=True)
                
            except Exception as e:
                st.error(f"Erreur de rendu graphique : {e}")

            # --- TABLEAU DE DONNÉES ---
            with st.expander("Voir les données brutes correspondantes"):
                st.dataframe(df)