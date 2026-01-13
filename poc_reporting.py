import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import plotly.express as px
import numpy as np
from io import BytesIO

# --- Configuration de la page --- 
st.set_page_config(page_title="Reporting Statistique - Maison du Droit", layout="wide")

# --- Configuration PostgreSQL ---
PG_HOST = "localhost"
PG_PORT = 5437
PG_DB = "DB_Maison_du_droit"
PG_USER = "pgis"
PG_PASSWORD = "pgis"

# --- Connexion PostgreSQL ---
@st.cache_resource
def init_connection():
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        return conn
    except Exception as e:
        st.error(f"❌ Erreur connexion PostgreSQL : {e}")
        st.stop()

connection = init_connection()

# --- Récupération des données ---
@st.cache_data
def get_data_for_reporting():
    if not connection:
        return pd.DataFrame()
    
    # Utilisation de RealDictCursor pour récupérer les noms de colonnes facilement
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    try:
        # Note : On récupère les libellés via des JOIN pour éviter le mapping manuel lourd
        query = """
        SELECT 
            e.num as "Numéro",
            e.date_ent as "Date",
            e.sexe as "Sexe",
            e.age as "Age",
            e.sit_fam as "Situation familiale",
            e.enfant as "Enfants à charge",
            e.profession as "Profession",
            e.duree as "Durée",
            e.commune as "Commune",
            e.mode as "Mode d'entretien",
            e.vient_pr as "Vient pour"
        FROM entretien e
        """
        cursor.execute(query)
        data = cursor.fetchall()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erreur SQL : {e}")
        return pd.DataFrame()
    finally:
        cursor.close()

# --- Fonction d'export Excel (Demande Client) ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Export_Entretiens')
    return output.getvalue()

# --- Interface Principale ---
def main():
    st.title("📊 Reporting - Analyse des Entretiens (PostgreSQL)")

    df = get_data_for_reporting()

    if df.empty:
        st.warning("Aucune donnée disponible dans la base PostgreSQL.")
        return

    # --- Nettoyage rapide ---
    df = df.fillna("Non Renseigné")

    # --- Barre latérale : Filtres et Export ---
    st.sidebar.header("Options")
    
    # Bouton d'export Excel
    excel_data = to_excel(df)
    st.sidebar.download_button(
        label="📥 Télécharger l'export Excel",
        data=excel_data,
        file_name=f"export_maison_du_droit_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- Organisation en Onglets ---
    tab_dash, tab_custom = st.tabs(["📈 Tableau de Bord", "🔍 Explorateur de données"])

    with tab_dash:
        # KPIs
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Entretiens", len(df))
        k2.metric("Commune Principale", df["Commune"].mode()[0])
        k3.metric("Mode Dominant", df["Mode d'entretien"].mode()[0])

        st.divider()

        # Graphiques
        c1, c2 = st.columns(2)
        with c1:
            fig_sexe = px.pie(df, names="Sexe", title="Répartition par Sexe", hole=0.4)
            st.plotly_chart(fig_sexe, use_container_width=True)
        
        with c2:
            fig_age = px.histogram(df, x="Age", title="Répartition par Tranche d'Âge", color="Sexe")
            st.plotly_chart(fig_age, use_container_width=True)

        st.subheader("Volume par Commune")
        fig_commune = px.bar(df["Commune"].value_counts().reset_index(), x="count", y="Commune", orientation='h')
        st.plotly_chart(fig_commune, use_container_width=True)

    with tab_custom:
        st.header("Analyse croisée personnalisée")
        var_x = st.selectbox("Choisir l'axe X", df.columns, index=2)
        var_color = st.selectbox("Croiser avec (Couleur)", [None] + list(df.columns), index=0)
        
        fig_custom = px.histogram(df, x=var_x, color=var_color, barmode="group", text_auto=True)
        st.plotly_chart(fig_custom, use_container_width=True)
        
        st.dataframe(df)

if __name__ == "__main__":
    main()