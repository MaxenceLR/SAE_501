from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

# ==========================
# CONFIGURATION
# ==========================
APP_URL = "http://localhost:8501"
TIMEOUT = 20

# ==========================
# INITIALISATION DU DRIVER
# ==========================
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, TIMEOUT)

try:
    # ==========================
    # OUVERTURE DE L'APPLICATION
    # ==========================
    driver.get(APP_URL)

    # Attendre que le titre soit visible
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Saisie d'Entretien')]"))
    )

    # ==========================
    # REMPLISSAGE DES CHAMPS
    # ==========================

    # Exemple : Champ MODE (selectbox)
    mode_select = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//label[contains(.,'Mode')]/following::div[1]"))
    )
    mode_select.click()
    time.sleep(1)
    mode_select.send_keys("Présentiel")
    mode_select.send_keys(Keys.ENTER)

    # Exemple : Champ AGE (number_input)
    age_input = driver.find_element(
        By.XPATH, "//label[contains(.,'Age')]/following::input[1]"
    )
    age_input.clear()
    age_input.send_keys("35")

    # Exemple : Champ COMMUNE (text_input)
    commune_input = driver.find_element(
        By.XPATH, "//label[contains(.,'Commune')]/following::input[1]"
    )
    commune_input.send_keys("Paris")

    # ==========================
    # DEMANDES (MULTISELECT)
    # ==========================
    demande_select = driver.find_element(
        By.XPATH, "//div[contains(.,'Natures de la demande')]/following::input[1]"
    )
    demande_select.send_keys("Information juridique")
    demande_select.send_keys(Keys.ENTER)

    demande_select.send_keys("Aide administrative")
    demande_select.send_keys(Keys.ENTER)

    # ==========================
    # SOLUTIONS (MULTISELECT)
    # ==========================
    solution_select = driver.find_element(
        By.XPATH, "//div[contains(.,'Réponses apportées')]/following::input[1]"
    )
    solution_select.send_keys("Orientation")
    solution_select.send_keys(Keys.ENTER)

    # ==========================
    # SOUMISSION DU FORMULAIRE
    # ==========================
    submit_btn = driver.find_element(
        By.XPATH, "//button[contains(.,'ENREGISTRER')]"
    )
    submit_btn.click()

    # ==========================
    # VERIFICATION DU SUCCÈS
    # ==========================
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'enregistré')]")
        )
    )

    print("✅ Test réussi : entretien enregistré")

except Exception as e:
    print("❌ Test échoué :", e)

finally:
    time.sleep(3)
    driver.quit()
