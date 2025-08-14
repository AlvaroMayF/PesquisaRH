import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 1. CONFIGURAÇÕES ---
URL_RELOGIO = "http://10.0.0.206/"
USUARIO = "ti"
SENHA = "000000"

# --- CONFIGURANDO O SELENIUM (MODO VISÍVEL PARA DEPURAÇÃO) ---
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = None

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 15)

    # --- Login e Navegação (JÁ FUNCIONANDO) ---
    print("Acessando a página de login...")
    driver.get(URL_RELOGIO)
    print("Realizando login...")
    wait.until(EC.presence_of_element_located((By.ID, 'lblLogin'))).send_keys(USUARIO)
    driver.find_element(By.ID, 'lblPass').send_keys(SENHA)
    driver.find_element(By.LINK_TEXT, 'Entrar').click()
    print("Login efetuado com sucesso!")

    print("Clicando no menu 'Eventos'...")
    eventos_button = wait.until(EC.element_to_be_clickable((By.ID, "divMenuEvents")))
    eventos_button.click()
    print("Página de eventos acessada!")

    # --- PAUSA PARA INVESTIGAÇÃO FINAL ---
    print("\n--- TAREFA FINAL ---")
    print("A página de download de eventos está aberta.")
    print("Clique com o botão direito no botão 'BAIXAR DADOS' e vá em 'Inspecionar'.")
    print("Envie o print da linha de código HTML que for destacada.")
    time.sleep(120)

except Exception as e:
    print(f"❌ Ocorreu um erro durante a execução:")
    traceback.print_exc()

finally:
    if driver:
        driver.quit()
    print("Processo finalizado.")