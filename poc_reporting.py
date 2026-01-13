import streamlit as st
import oracledb
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import date

# --- Configuration de la page Streamlit --- 
st.set_page_config(page_title="Reporting Statistique", layout="wide")

# --- Configuration de la Base de Données ---
USER = "DARTIES3"
PASSWD = "DARTIES3"
HOST = "ora23ai"
PORT = 1521
SERVICE_NAME = "ORAETUD"
SCHEMA_OWNER = "DARTIES3"

DSN = oracledb.makedsn(HOST, PORT, service_name=SERVICE_NAME)

# --- Fonctions de Connexion et de Récupération des Données ---
@st.cache_resource
def init_connection():
    """Crée et retourne une connexion persistante à Oracle."""
    try:
        connection = oracledb.connect(user=USER, password=PASSWD, dsn=DSN)
        return connection
    except Exception as e:
        st.error(f"Impossible de se connecter à Oracle : {e}")
        st.stop()
        return None

connection = init_connection()

# --- MODALITÉS COMPLÈTES (Basé sur le fichier PDF fourni) ---
MODALITES_COMPLETES = {
    'sexe': {
        '1': 'Homme',
        '2': 'Femme',
        '3': 'Couple',
        '4': 'Professionnel',
    },
    'duree': {
        '1': '1 - 15 min',
        '2': '15 à 30 min',
        '3': '30 à 45 min',
        '4': '45 à 60 min',
        '5': '+ de 60 min',
    },
    'mode_ent': {
        '1': 'RDV',
        '2': 'Sans RDV',
        '3': 'Téléphonique',
        '4': 'Courrier',
        '5': 'Mail',
    },
    'age': {
        '1': '-18 ans',
        '2': '18-25 ans',
        '3': '26-40 ans',
        '4': '41-60 ans',
        '5': '+ 60 ans',
    },
    'vient_pour': {
        '1': 'Soi',
        '2': 'Conjoint',
        '3': 'Parent',
        '4': 'Enfant',
        '5': 'Personne morale',
        '6': 'Autre',
    },
    'sit_fam': {
        '1': 'Célibataire',
        '2': 'Concubin',
        '3': 'Pacsé',
        '4': 'Marié',
        '5': 'Séparé/divorcé',
        '51': '5a Sans enf. à charge',
        '5a': '5a Sans enf. à charge',
        '5b': '5b Avec enf. en garde alternée',
        '5c': '5c Avec enf. en garde principale',
        '5d': '5d Avec enf. en droit de visite/hbgt',
        '5e': '5e Parent isolé',
        '5f': '5f Séparés sous le même toit',
        '6': 'Veuf/ve',
        '61': '6a Sans enf. à charge',
        '6a': '6a Sans enf. à charge',
        '6b': '6b Avec enf. à charge',
        '7': 'Non renseigné',
    },
    'enfant': {
        '0': 'Sans enfant',
        '1': '1 enfant',
        '2': '2 enfants',
        '3': '3 enfants',
        '4': '4 enfants',
        '5': '5 enfants',
        '6': '6 enfants',
        '7': '7 enfants',
        '8': '8 enfants',
        '9': '9 enfants',
        '10': '10 enfants',
    }
}

@st.cache_data
def get_modalites():
    return MODALITES_COMPLETES

@st.cache_data
def get_data_for_reporting():
    """Charge les données pour les reportings."""
    if not connection:
        return pd.DataFrame()
    
    cursor = connection.cursor()
    try:
        query = f"""
        SELECT 
            SEXE, AGE, SIT_FAM, ENFANT, PROFESSION, DUREE, COMMUNE, NUM, MODE_ENT, VIENT_PR
        FROM {SCHEMA_OWNER}.ENTRETIEN
        """
        cursor.execute(query)
        data = cursor.fetchall()

        df = pd.DataFrame(data, columns=[
            "Sexe", "Age", "Situation familiale", "Enfants à charge", "Profession",
            "Durée", "Commune", "Numéro", "Mode d'entretien", "Vient pour"
        ])

        return df

    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return pd.DataFrame()
    finally:
        cursor.close()

# --- Création du Dashboard ---
def main():
    st.title("Reporting - Analyse des Entretiens")

    df = get_data_for_reporting()
    modalites = get_modalites()

    if df.empty:
        st.warning("Aucune donnée à afficher pour le moment.")
        return
    
    # --- Nettoyage & Mapping ---
    cols_to_map = ["Sexe", "Situation familiale", "Enfants à charge", "Durée",
                   "Mode d'entretien", "Vient pour", "Age"]
    
    for col in cols_to_map:
        df[col] = df[col].astype(str).str.replace('nan', '', regex=False).str.replace('None', '', regex=False)

    df['Sexe'] = df['Sexe'].map(modalites['sexe']).fillna(df['Sexe'])
    df['Situation familiale'] = df['Situation familiale'].map(modalites['sit_fam']).fillna(df['Situation familiale'])
    df['Enfants à charge'] = df['Enfants à charge'].map(modalites['enfant']).fillna(df['Enfants à charge'])
    df['Durée'] = df['Durée'].map(modalites['duree']).fillna(df['Durée'])
    df["Mode d'entretien"] = df["Mode d'entretien"].map(modalites['mode_ent']).fillna(df["Mode d'entretien"])
    df['Age'] = df['Age'].map(modalites['age']).fillna(df['Age'])
    df['Vient pour'] = df['Vient pour'].map(modalites['vient_pour']).fillna(df['Vient pour'])

    df = df.replace(r'^\s*$', np.nan, regex=True).fillna('Non Renseigné')


    # -------------------------------------------------------------------------
    # ONGLET 1 : DASHBOARD
    # -------------------------------------------------------------------------
    tab_dashboard, tab_createur = st.tabs(["Tableau de Bord", "Créateur de Graphique"])

    with tab_dashboard:
        st.markdown("### Vue d'ensemble de l'activité")

        df_dash_clean = df[
            (df['Durée'] != 'Non Renseigné') &
            (df['Profession'] != 'Non Renseigné') &
            (df['Commune'] != 'Non Renseigné')
        ].copy()

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Dossiers", df['Numéro'].nunique())

        duree_mode = df_dash_clean['Durée'].mode()
        k2.metric("Durée la plus fréquente", duree_mode[0] if not duree_mode.empty else "N/A")

        # 🔥 CHANGEMENT ICI : remplacement de "Top Public"
        mode_frequent = df_dash_clean["Mode d'entretien"].mode()[0] if not df_dash_clean["Mode d'entretien"].empty else "N/A"
        k3.metric("Mode d'entretien le plus fréquent", mode_frequent)

        k4.metric("Top Commune", df_dash_clean["Commune"].mode()[0] if not df_dash_clean["Commune"].empty else "N/A")

        # LIGNE 1
        c1, c2, c3 = st.columns(3)
        with c1:
            df_sexe = df_dash_clean[df_dash_clean['Sexe'] != 'Non Renseigné']
            fig_sexe = px.pie(df_sexe, names="Sexe", title="Répartition par Sexe", hole=0.3)
            st.plotly_chart(fig_sexe, use_container_width=True)
        with c2:
            df_sit_fam = df_dash_clean[df_dash_clean['Situation familiale'] != 'Non Renseigné']
            fig_sit_fam = px.histogram(df_sit_fam, x="Situation familiale", title="Situation Familiale", text_auto=True)
            fig_sit_fam.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig_sit_fam, use_container_width=True)
        with c3:
            df_enf = df_dash_clean[df_dash_clean['Enfants à charge'] != 'Non Renseigné']
            fig_enf = px.pie(df_enf, names="Enfants à charge", title="Enfants à charge", hole=0.3)
            st.plotly_chart(fig_enf, use_container_width=True)

        # ---------------------------------------------------------------------
        # CLASSEMENT DES DEMANDES LES PLUS FRÉQUENTES
        # ---------------------------------------------------------------------
        c4, c5 = st.columns([2, 1])
        with c4:
            df_vp = df_dash_clean["Vient pour"].value_counts().reset_index()
            df_vp.columns = ["Vient pour", "Volume"]

            fig_vp = px.bar(
                df_vp,
                x="Volume",
                y="Vient pour",
                orientation='h',
                title="Demandes les plus fréquentes",
                text_auto=True
            )
            fig_vp.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_vp, use_container_width=True)

        with c5:
            fig_commune = px.treemap(df_dash_clean, path=['Commune'], title="Répartition des Communes")
            st.plotly_chart(fig_commune, use_container_width=True)

    # -------------------------------------------------------------------------
    # ONGLET 2 : CRÉATEUR DE GRAPHIQUE
    # -------------------------------------------------------------------------
    with tab_createur:
        st.header("Exploration Personnalisée")
        st.markdown("Construisez votre propre visualisation en sélectionnant les paramètres.")

        # CONFIGURATION
        with st.container():
            col_config1, col_config2, col_config3 = st.columns(3)

            colonnes_dispos = [c for c in df.columns if c not in ["Durée", "Numéro", "Age"]]

            with col_config1:
                type_graphique = st.selectbox(
                    "1. Type de graphique",
                    ["Diagramme Circulaire", "Diagramme en Barres", "Histogramme", "Treemap", "Nuage de points"]
                )

            with col_config2:
                if type_graphique in ["Histogramme", "Nuage de points"]:
                    dispo_current = [c for c in df.columns if c not in ["Numéro"]]
                else:
                    dispo_current = colonnes_dispos

                try:
                    default_index = dispo_current.index("Commune")
                except ValueError:
                    default_index = 0

                var_principale = st.selectbox("2. Variable à analyser", dispo_current, index=default_index)

            with col_config3:
                var_secondaire = st.selectbox(
                    "3. Croiser avec (optionnel)", ["Aucun"] + dispo_current, index=0
                )

        st.divider()

        # AFFICHAGE
        color_arg = None if var_secondaire == "Aucun" else var_secondaire
        df_filtered = df[df[var_principale] != 'Non Renseigné'].copy()

        if type_graphique == "Diagramme Circulaire":
            st.subheader(f"Répartition de : {var_principale}")
            fig = px.pie(df_filtered, names=var_principale, color=color_arg if color_arg else var_principale, hole=0.3)
            st.plotly_chart(fig, use_container_width=True)

        elif type_graphique == "Diagramme en Barres":
            st.subheader(f"Comptage par : {var_principale}")
            fig = px.histogram(df_filtered, x=var_principale, color=color_arg, barmode='group', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

        elif type_graphique == "Histogramme":
            st.subheader(f"Distribution de : {var_principale}")
            fig = px.histogram(df_filtered, x=var_principale, color=color_arg)
            st.plotly_chart(fig, use_container_width=True)

        elif type_graphique == "Treemap":
            st.subheader(f"Hiérarchie : {var_principale}")
            path_list = [var_principale]
            if color_arg:
                path_list.append(color_arg)

            df_treemap = df_filtered.copy()
            if color_arg:
                df_treemap = df_treemap[df_treemap[color_arg] != 'Non Renseigné']

            if df_treemap.empty:
                st.warning("Aucune donnée significative à afficher.")
            else:
                fig = px.treemap(df_treemap, path=path_list)
                st.plotly_chart(fig, use_container_width=True)

        elif type_graphique == "Nuage de points":
            st.subheader(f"Durée Moyenne par : {var_principale}")

            df_scatter = df[(df[var_principale] != 'Non Renseigné') & (df['Durée'] != 'Non Renseigné')].copy()

            try:
                code_to_duree = {v: k for k, v in modalites['duree'].items()}
                df_scatter['Durée_Code'] = df_scatter['Durée'].map(code_to_duree).astype(float)

                df_grouped = df_scatter.groupby([var_principale]).agg({"Durée_Code": "mean"}).reset_index()
                df_grouped.rename(columns={'Durée_Code': 'Durée Moyenne (Code Classe)'}, inplace=True)

                fig = px.scatter(
                    df_grouped,
                    x=var_principale,
                    y="Durée Moyenne (Code Classe)",
                    color=color_arg,
                    size="Durée Moyenne (Code Classe)"
                )
                st.plotly_chart(fig, use_container_width=True)

            except Exception:
                st.error("Impossible de créer le Nuage de points.")

        with st.expander("Voir les données brutes"):
            cols_to_show = [var_principale]
            if color_arg is not None:
                cols_to_show.append(color_arg)
            cols_to_show.extend(["Durée", "Age", "Numéro"])
            cols_to_show = list(dict.fromkeys(cols_to_show))

            st.dataframe(df[cols_to_show].head(50))


if __name__ == "__main__":
    main()
