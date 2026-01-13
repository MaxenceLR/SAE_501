import streamlit as st
import sys
import json
import os
import datetime
from streamlit.web import cli as stcli

# --- 1. DONNÉES PAR DÉFAUT COMPLÈTES ---
current_year = datetime.date.today().year
start_date = f"{current_year}-01-01"
end_date = f"{current_year}-12-31"

DONNEES_INITIALES = {
    "L'ENTRETIEN": {
        "position": 1,
        "variables": {
            "Mode d'entretien": {
                "position": 1, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "RDV",
                "modalites": ["RDV", "Sans RDV", "Téléphonique", "Courrier", "Mail"]
            },
            "Durée de l'entretien": {
                "position": 2, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "15 à 30 min",
                "modalites": ["- 15 min.", "15 à 30 min", "30 à 45 min", "45 à 60 min", "+ de 60 min"]
            }
        }
    },
    "L'USAGER": {
        "position": 2,
        "variables": {
            "Sexe": {
                "position": 1, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "Femme",
                "modalites": ["Homme", "Femme"]
            },
             "Type usager": {
                "position": 2, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "Particulier",
                "modalites": ["Couple", "Professionnel", "Personne morale"]
            },
            "Tranche d'âge": {
                "position": 3, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "26-40 ans",
                "modalites": ["-18 ans", "18-25 ans", "26-40 ans", "41-60 ans", "+ 60 ans"]
            },
            "Vient pour (Bénéficiaire)": {
                "position": 4, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "Soi",
                "modalites": ["Soi", "Conjoint", "Parent", "Enfant", "Autre"]
            },
            "Situation familiale": {
                "position": 5, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "Célibataire",
                "modalites": ["Célibataire", "Concubin", "Pacsé", "Marié", "Séparé/divorcé", "Veuf/ve"]
            },
            "Situation enfants": {
                "position": 6, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "Sans enf. à charge",
                "modalites": ["Sans enf. à charge", "Avec enf. en garde alternée", "Avec enf. en garde principale", "Avec enf. en droit de visite/hbgt", "Parent isolé", "Séparés sous le même toit"]
            },
            "Profession (CSP)": {
                "position": 7, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "Employé",
                "modalites": ["Scolaire/étudiant/formation", "Pêcheur/agriculteur", "Chef d'entreprise", "Libéral", "Militaire", "Employé", "Ouvrier", "Cadre", "Retraité", "En recherche d'emploi", "Sans profession", "Non renseigné"]
            },
            "Sources de revenus": {
                "position": 8, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "Salaire",
                "modalites": ["Salaire", "Revenus pro.", "Retraite/réversion", "Allocations chômage", "RSA", "AAH/invalidité", "USS", "Bourse d'études.", "Sans revenu", "Autre"]
            }
        }
    },
    "CONTEXTE / DISPOSITIF": {
        "position": 3,
        "variables": {
            "Prescripteur (Qui a orienté)": {
                "position": 1, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "Internet",
                "modalites": ["Bouche à oreille", "Internet", "Presse", "Tribunaux", "Police/gendarmerie", "Avocat/Notaire/Huissier", "Mairie/EPCI", "CAF", "Maison France Service", "Assistante sociale", "France Victimes", "Assoc. consommateurs", "ADIL", "Déjà venu"]
            }
        }
    },
    "NATURE DE LA DEMANDE": {
        "position": 4,
        "variables": {
            "Droit de la famille": {
                "position": 1, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "",
                "modalites": ["Séparation / divorce", "PA/PC", "Droit de garde", "Autorité parentale", "Filiation adoption", "Régimes matrimoniaux", "Protection des majeurs", "Successions", "Assistance éducative", "Violences conjugales"]
            },
            "Logement & Conso": {
                "position": 2, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "",
                "modalites": ["Litiges locatifs", "Expulsion", "Achat/vente", "Copropriété", "Conflit voisinage", "Crédit/dette", "Banque/Assurance", "Surendettement", "Téléphonie/internet"]
            },
            "Travail / Social / Pénal": {
                "position": 3, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "",
                "modalites": ["Contrat de travail", "Licenciement/Rupture", "Droit des étrangers", "Aides sociales", "Retraite", "Auteur infraction", "Victime infraction", "Litige administration"]
            }
        }
    },
    "RÉPONSE APPORTÉE": {
        "position": 5,
        "variables": {
            "Type de réponse": {
                "position": 1, "type": "Texte (Liste)", "date_debut": start_date, "date_fin": end_date, "defaut": "Information",
                "modalites": ["Information", "Aide rédaction courrier", "Aide démarches en ligne", "Orientation Avocat", "Orientation Notaire/Huissier", "Orientation Tribunal", "Orientation Conciliateur/Médiateur", "Orientation CAF/Social", "Orientation Assoc. spécialisée"]
            }
        }
    }
}

NOM_FICHIER_SAUVEGARDE = "sauvegarde_modele_complet.json"

# --- UTILITAIRES ---
def get_current_year_dates():
    today = datetime.date.today()
    return datetime.date(today.year, 1, 1), datetime.date(today.year, 12, 31)

def charger_donnees():
    if os.path.exists(NOM_FICHIER_SAUVEGARDE):
        try:
            with open(NOM_FICHIER_SAUVEGARDE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return DONNEES_INITIALES.copy()
    return DONNEES_INITIALES.copy()

def sauvegarder_sur_disque(data):
    with open(NOM_FICHIER_SAUVEGARDE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_next_position(dictionnaire_objets):
    """CORRECTION : Calcule la position max + 1 (au lieu de +10)"""
    if not dictionnaire_objets:
        return 1
    positions = [v.get('position', 0) for k, v in dictionnaire_objets.items()]
    # On ajoute simplement 1 à la dernière position trouvée
    return max(positions) + 1 if positions else 1

def main():
    st.set_page_config(page_title="Configurateur BDD", layout="wide")
    st.title("🛠️ Configurateur Structure Base de Données")
    st.markdown("Structure : **Rubrique** ➤ **Variable** ➤ **Modalités**")

    # Initialisation
    if 'db_struct' not in st.session_state:
        st.session_state.db_struct = charger_donnees()

    data = st.session_state.db_struct

    # ==========================================
    # 1. GESTION DE LA RUBRIQUE
    # ==========================================
    st.header("1. La Rubrique")
    col_rub_sel, col_rub_new = st.columns([1, 1])

    liste_rubriques = list(data.keys())
    opt_rubriques = ["➕ Créer une nouvelle rubrique"] + liste_rubriques
    
    with col_rub_sel:
        choix_rubrique = st.selectbox("Sélectionner une rubrique", opt_rubriques)

    # Définition des valeurs Rubrique
    if choix_rubrique == "➕ Créer une nouvelle rubrique":
        rub_nom_defaut = ""
        # Auto-calcul position rubrique (CORRIGÉ : Pas de +1)
        rub_pos_defaut = get_next_position(data)
        is_new_rubrique = True
    else:
        rub_nom_defaut = choix_rubrique
        rub_pos_defaut = data[choix_rubrique].get("position", 0)
        is_new_rubrique = False

    with col_rub_new:
        if is_new_rubrique:
            nom_rubrique = st.text_input("Nom de la nouvelle rubrique", value=rub_nom_defaut)
        else:
            st.info(f"Rubrique active : **{rub_nom_defaut}**")
            nom_rubrique = rub_nom_defaut
            
        pos_rubrique = st.number_input("Position Rubrique", value=rub_pos_defaut, step=1)

    st.divider()

    if not nom_rubrique:
        st.warning("Veuillez nommer la rubrique pour continuer.")
        return

    # ==========================================
    # 2. GESTION DE LA VARIABLE
    # ==========================================
    st.header(f"2. Variable (dans '{nom_rubrique}')")
    
    variables_existantes = {}
    if not is_new_rubrique:
        variables_existantes = data[choix_rubrique].get("variables", {})

    liste_vars = list(variables_existantes.keys())
    opt_vars = ["➕ Créer une nouvelle variable"] + liste_vars
    
    col_var_sel, col_vide = st.columns([1, 1])
    with col_var_sel:
        choix_variable = st.selectbox("Sélectionner une variable", opt_vars)

    # --- Préparation des données par défaut ---
    janvier_defaut, decembre_defaut = get_current_year_dates()
    
    if choix_variable == "➕ Créer une nouvelle variable":
        var_nom_defaut = ""
        # CORRECTION : Position max + 1
        var_pos_defaut = get_next_position(variables_existantes) if variables_existantes else 1
        var_type_defaut = "Texte (Liste)"
        var_debut_defaut = janvier_defaut
        var_fin_defaut = decembre_defaut
        var_val_defaut = ""
        var_modalites_defaut = []
        current_id = "new_var"
    else:
        var_data = variables_existantes[choix_variable]
        var_nom_defaut = choix_variable
        var_pos_defaut = var_data.get("position", 1)
        var_type_defaut = var_data.get("type", "Texte (Liste)")
        try:
            var_debut_defaut = datetime.datetime.strptime(var_data.get("date_debut"), "%Y-%m-%d").date()
            var_fin_defaut = datetime.datetime.strptime(var_data.get("date_fin"), "%Y-%m-%d").date()
        except:
            var_debut_defaut = janvier_defaut
            var_fin_defaut = decembre_defaut

        var_val_defaut = var_data.get("defaut", "")
        var_modalites_defaut = var_data.get("modalites", [])
        current_id = choix_variable

    # --- CORRECTION : SORTIR LE COMPTEUR DE MODALITÉS HORS DU FORMULAIRE ---
    # Cela permet à la page de se recharger dès qu'on change le nombre,
    # affichant ainsi immédiatement les cases vides.
    
    nb_mods = 0
    if "Texte" in var_type_defaut: # Seulement si c'est une liste
        st.markdown("#### Configuration des Modalités")
        col_nb_mods, col_info = st.columns([1,3])
        with col_nb_mods:
             # Initialisation à la taille de la liste existante, ou 2 par défaut
            valeur_init_mods = max(2, len(var_modalites_defaut))
            nb_mods = st.number_input(
                "Nombre de choix possibles", 
                min_value=1, 
                value=valeur_init_mods, 
                step=1,
                key=f"nb_mods_trigger_{current_id}" # Clé unique pour éviter les conflits
            )
        with col_info:
            if nb_mods > len(var_modalites_defaut):
                st.info(f"💡 {nb_mods - len(var_modalites_defaut)} nouvelle(s) case(s) ajoutée(s) ci-dessous.")

    # --- DÉBUT DU FORMULAIRE DE SAISIE ---
    with st.form(key=f"form_var_{current_id}"):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            nom_variable = st.text_input("Nom de la variable", value=var_nom_defaut)
        with c2:
            position_variable = st.number_input("Position", value=var_pos_defaut, step=1)
        with c3:
            type_valeur = st.selectbox("Type de valeur", 
                                       ["Texte (Liste)", "Numérique", "Date", "Booléen"], 
                                       index=0 if "Texte" in var_type_defaut else 1)

        c4, c5, c6 = st.columns(3)
        with c4:
            date_debut = st.date_input("Début Validité", value=var_debut_defaut)
        with c5:
            date_fin = st.date_input("Fin Validité", value=var_fin_defaut)
        with c6:
            valeur_par_defaut = st.text_input("Valeur par défaut", value=var_val_defaut)

        # --- Gestion des Modalités (Affichage dynamique) ---
        liste_modalites_finale = []
        if "Texte" in type_valeur:
            st.caption("Saisissez les libellés des modalités :")
            
            cols_mods = st.columns(2)
            # On utilise le nb_mods défini HORS du formulaire
            for i in range(int(nb_mods)):
                val_mod = ""
                # Si la modalité existe déjà en mémoire, on la pré-remplit
                if i < len(var_modalites_defaut):
                    val_mod = var_modalites_defaut[i]
                
                with cols_mods[i % 2]:
                    # Clé unique indispensable
                    m = st.text_input(f"Choix {i+1}", value=val_mod, key=f"mod_{i}_{current_id}")
                    if m.strip():
                        liste_modalites_finale.append(m)
        
        st.markdown("---")
        submitted = st.form_submit_button("💾 Enregistrer Variable & Rubrique")

    # ==========================================
    # 3. LOGIQUE DE SAUVEGARDE
    # ==========================================
    if submitted:
        if not nom_variable:
            st.error("Le nom de la variable est obligatoire.")
        else:
            nouvelle_var_obj = {
                "position": position_variable,
                "type": type_valeur,
                "date_debut": str(date_debut),
                "date_fin": str(date_fin),
                "defaut": valeur_par_defaut,
                "modalites": liste_modalites_finale
            }

            if nom_rubrique not in st.session_state.db_struct:
                st.session_state.db_struct[nom_rubrique] = {
                    "position": pos_rubrique,
                    "variables": {}
                }
            
            st.session_state.db_struct[nom_rubrique]["position"] = pos_rubrique
            vars_dict = st.session_state.db_struct[nom_rubrique]["variables"]

            if choix_variable != "➕ Créer une nouvelle variable" and choix_variable != nom_variable:
                if choix_variable in vars_dict:
                    del vars_dict[choix_variable]
            
            vars_dict[nom_variable] = nouvelle_var_obj

            sauvegarder_sur_disque(st.session_state.db_struct)
            st.success(f"Sauvegardé : Rubrique '{nom_rubrique}' > Variable '{nom_variable}'")
            st.rerun()

    with st.expander(" Voir le JSON complet"):
        st.json(st.session_state.db_struct)

    with st.expander("Zone de danger"):
        if st.button("Réinitialiser toutes les données"):
            if os.path.exists(NOM_FICHIER_SAUVEGARDE):
                os.remove(NOM_FICHIER_SAUVEGARDE)
            del st.session_state.db_struct
            st.rerun()

if __name__ == "__main__":
    if st.runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())