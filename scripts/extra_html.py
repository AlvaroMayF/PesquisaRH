import time
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

URL_RELOGIO = "http://10.0.0.206/"
driver = None

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    print("Acessando a página de login...")
    driver.get(URL_RELOGIO)

    print("Aguardando 5 segundos para a página carregar...")
    time.sleep(5)

    print("Salvando o código-fonte da página...")
    with open("pagina_login.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    print("✅ Arquivo 'pagina_login.html' salvo no mesmo diretório do script.")
    print("Por favor, abra este arquivo e verifique se 'idLogin' existe nele.")

except Exception as e:
    print(f"❌ Ocorreu um erro durante a execução:")
    traceback.print_exc()

finally:
    if driver:
        driver.quit()
    print("Processo finalizado.")