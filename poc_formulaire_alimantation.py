import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date

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
        conn.autocommit = False
        return conn
    except Exception as e:
        st.error(f"❌ Impossible de se connecter à PostgreSQL : {e}")
        st.stop()

connection = init_connection()

# --- Récupération structure du questionnaire ---
@st.cache_data
def get_questionnaire_structure():
    if not connection:
        return {}
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    structure = {}
    try:
        # Rubriques
        cursor.execute("SELECT pos, lib FROM rubrique ORDER BY pos")
        rubriques = {row['pos']: row['lib'] for row in cursor.fetchall()}

        # Variables
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
                'pos': var['pos'],
                'lib': var['lib'],
                'type': var['type_v'],
                'comment': var['commentaire'],
                'options': {}
            }

            # MOD : récupérer les options
            if var['type_v'] == 'MOD':
                cursor.execute("""
                    SELECT code, lib_m
                    FROM modalite
                    WHERE tab = %s AND pos = %s
                    ORDER BY pos_m
                """, ('ENTRETIEN', var['pos']))
                var_data['options'] = {row['lib_m']: row['code'] for row in cursor.fetchall()}

            # NUM : récupérer les plages
            elif var['type_v'] == 'NUM':
                cursor.execute("""
                    SELECT val_min, val_max
                    FROM plage
                    WHERE tab = %s AND pos = %s
                """, ('ENTRETIEN', var['pos']))
                plage = cursor.fetchone()
                if plage:
                    var_data['options'] = {'min': plage['val_min'], 'max': plage['val_max']}

            # CHAINE : valeurs possibles
            elif var['type_v'] == 'CHAINE':
                cursor.execute("""
                    SELECT lib
                    FROM valeurs_c
                    WHERE tab = %s AND pos = %s
                    ORDER BY pos_c
                """, ('ENTRETIEN', var['pos']))
                var_data['options'] = [row['lib'] for row in cursor.fetchall()]

            structure[rubrique_lib].append(var_data)

        return structure
    except Exception as e:
        st.error(f"Erreur récupération structure : {e}")
        return {}
    finally:
        cursor.close()

# --- Modalités Demande / Solution ---
@st.cache_data
def get_demande_solution_modalites():
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    try:
        # DEMANDE
        cursor.execute("""
            SELECT code, lib_m
            FROM modalite
            WHERE tab = %s AND pos = 3
            ORDER BY pos_m
        """, ('DEMANDE',))
        demande_modalites = {row['lib_m']: row['code'] for row in cursor.fetchall()}

        # SOLUTION
        cursor.execute("""
            SELECT code, lib_m
            FROM modalite
            WHERE tab = %s AND pos = 3
            ORDER BY pos_m
        """, ('SOLUTION',))
        solution_modalites = {row['lib_m']: row['code'] for row in cursor.fetchall()}

        return demande_modalites, solution_modalites
    finally:
        cursor.close()

# --- Insertion entretien ---
def insert_full_entretien(data):
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO entretien
            (date_ent, mode, duree, sexe, age, vient_pr,
             sit_fam, enfant, modele_fam, profession,
             ress, origine, commune, partenaire)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING num
        """, (
            date.today(),
            data.get('mode'),
            data.get('duree'),
            data.get('sexe'),
            data.get('age'),
            data.get('vient_pr'),
            data.get('sit_fam'),
            data.get('enfant'),
            data.get('modele_fam'),
            data.get('profession'),
            data.get('ress'),
            data.get('origine'),
            data.get('commune'),
            data.get('partenaire')
        ))
        new_num = cursor.fetchone()[0]
        connection.commit()
        return new_num
    except Exception as e:
        connection.rollback()
        st.error(f"Erreur insertion entretien : {e}")
        return None
    finally:
        cursor.close()

# --- Insertion Demande / Solution ---
def insert_demandes(entretien_num, demandes_codes):
    if not demandes_codes: return
    cursor = connection.cursor()
    try:
        cursor.executemany("""
            INSERT INTO demande (num, pos, nature)
            VALUES (%s,%s,%s)
        """, [(entretien_num, i+1, c) for i,c in enumerate(demandes_codes)])
        connection.commit()
        st.success(f"✅ {len(demandes_codes)} Demande(s) insérée(s).")
    except Exception as e:
        connection.rollback()
        st.error(f"Erreur insertion DEMANDE : {e}")
    finally:
        cursor.close()

def insert_solutions(entretien_num, solutions_codes):
    if not solutions_codes: return
    cursor = connection.cursor()
    try:
        cursor.executemany("""
            INSERT INTO solution (num, pos, nature)
            VALUES (%s,%s,%s)
        """, [(entretien_num, i+1, c) for i,c in enumerate(solutions_codes)])
        connection.commit()
        st.success(f"✅ {len(solutions_codes)} Solution(s) insérée(s).")
    except Exception as e:
        connection.rollback()
        st.error(f"Erreur insertion SOLUTION : {e}")
    finally:
        cursor.close()

# --- Génération du formulaire ---
def generate_form(structure, demande_options, solution_options):
    data_entretien = {}
    st.title("📋 Fiche d'Informations Statistiques")
    st.caption(f"Connexion en tant que {PG_USER}. Base {PG_DB}")

    with st.form(key='entretien_form'):
        for rubrique, variables in structure.items():
            st.header(f"➡️ {rubrique}")
            cols = st.columns(2)
            col_index = 0
            for var in variables:
                lib, comment, type_v = var['lib'], var['comment'], var['type']
                with cols[col_index]:
                    if type_v == 'MOD':
                        options_lib = list(var['options'].keys())
                        selected_lib = st.selectbox(f"**{lib}**", options_lib, index=None, placeholder=comment, key=f"sb_{lib}")
                        data_entretien[lib.lower()] = var['options'].get(selected_lib) if selected_lib else None
                    elif type_v == 'NUM':
                        min_val = var['options'].get('min', 0)
                        max_val = var['options'].get('max', 99)
                        val = st.number_input(f"**{lib}**", min_value=min_val, max_value=max_val, value=min_val, key=f"num_{lib}", help=comment)
                        data_entretien[lib.lower()] = val
                    elif type_v == 'CHAINE':
                        if var['options']:
                            selected_val = st.selectbox(f"**{lib}**", ["--- Saisie Libre ---"] + var['options'], index=0, key=f"chainesb_{lib}", help=comment)
                            if selected_val == "--- Saisie Libre ---":
                                val = st.text_input(f"Saisir {lib}", key=f"chaineti_{lib}")
                            else:
                                val = selected_val
                        else:
                            val = st.text_input(f"**{lib}**", key=f"chaineti_{lib}", help=comment)
                        data_entretien[lib.lower()] = val
                col_index = 1 - col_index
            st.markdown("---")

        # NATURE DEMANDE
        st.header("➡️ NATURE DE LA DEMANDE")
        st.info("Sélectionnez jusqu'à 3 natures de demande.")
        selected_demandes_lib = st.multiselect("Sélectionnez les Natures de Demande", list(demande_options.keys()), max_selections=3)
        selected_demandes_codes = [demande_options[lib] for lib in selected_demandes_lib]

        # SOLUTION
        st.header("➡️ REPONSE APPORTEE")
        st.info("Sélectionnez jusqu'à 3 solutions apportées.")
        selected_solutions_lib = st.multiselect("Sélectionnez les Solutions", list(solution_options.keys()), max_selections=3)
        selected_solutions_codes = [solution_options[lib] for lib in selected_solutions_lib]

        submitted = st.form_submit_button("💾 Enregistrer l'Entretien COMPLET")
        if submitted:
            return data_entretien, selected_demandes_codes, selected_solutions_codes, True

    return {}, [], [], False

# --- Logique principale ---
if connection:
    structure_entretien = get_questionnaire_structure()
    demande_options, solution_options = get_demande_solution_modalites()

    if structure_entretien:
        data_entretien, data_demandes, data_solutions, submitted = generate_form(structure_entretien, demande_options, solution_options)

        if submitted:
            required_fields = ['mode', 'duree', 'sexe', 'age', 'vient_pr', 'sit_fam', 'profession', 'ress', 'origine', 'commune']
            missing_fields = [lib for lib in required_fields if data_entretien.get(lib) in [None, ""]]
            if missing_fields:
                st.error(f"Veuillez remplir tous les champs obligatoires : {', '.join(missing_fields)}")
            elif not data_demandes:
                st.error("Veuillez sélectionner au moins une Nature de Demande.")
            else:
                new_num = insert_full_entretien(data_entretien)
                if new_num:
                    insert_demandes(new_num, data_demandes)
                    insert_solutions(new_num, data_solutions)
                    st.success(f"Opération COMPLÈTE réussie pour l'entretien N°{new_num}.")
                    st.balloons()
    else:
        st.warning("Impossible de charger la structure du questionnaire.")
