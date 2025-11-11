# scraper_fifa_visible_columna.py

from selenium import webdriver  # Controla el navegador Chrome
from selenium.webdriver.chrome.service import Service  # Maneja el servicio de ChromeDriver
from selenium.webdriver.common.by import By  # Proporciona estrategias de búsqueda (CSS, XPATH, etc.)
from selenium.webdriver.chrome.options import Options  # Permite configurar opciones del navegador Chrome
from webdriver_manager.chrome import ChromeDriverManager  # Descarga y prepara ChromeDriver automáticamente
import json  # Permite guardar resultados en un archivo JSON
import time  # Permite pausas para visualizar el proceso con calma

URL = "https://en.wikipedia.org/wiki/FIFA_Men%27s_World_Ranking"  # URL de la página de Wikipedia del ranking FIFA
PAUSA_CORTA = 0.35  # Define una pausa corta en segundos para resaltar elementos
PAUSA_LARGA = 0.8   # Define una pausa un poco más larga para transiciones llamativas

def normalizar_texto(texto):  # Limpia el texto recibido
    texto = (texto or "").strip()  # Asegura que sea string y recorta espacios laterales
    return " ".join(texto.split())  # Colapsa espacios intermedios a uno

def resaltar(navegador, elemento, color_fondo="yellow", borde="3px solid orange"):  # Aplica un resaltado visual a un elemento
    navegador.execute_script("arguments[0].style.backgroundColor=arguments[1]; arguments[0].style.outline=arguments[2];", elemento, color_fondo, borde)  # Inyecta CSS para destacar

def quitar_resaltado(navegador, elemento):  # Quita el resaltado visual de un elemento
    navegador.execute_script("arguments[0].style.backgroundColor=''; arguments[0].style.outline='';", elemento)  # Restaura estilos

def detectar_indices_por_encabezado(tabla):  # Detecta índices de columnas para Rango, País y Puntos a partir de los encabezados
    filas_encabezado = tabla.find_elements(By.CSS_SELECTOR, "thead tr, tr")  # Toma filas del thead o, si no hay, de la tabla
    for fila in filas_encabezado:  # Recorre filas posibles de encabezado
        ths = fila.find_elements(By.CSS_SELECTOR, "th")  # Obtiene celdas de encabezado (th)
        if len(ths) < 2:  # Si hay muy pocas, no sirve como encabezado
            continue  # Sigue probando
        textos = [normalizar_texto(th.text).lower() for th in ths]  # Toma texto de cada th en minúsculas
        indice_rango = indice_pais = indice_puntos = None  # Inicializa índices

        for i, t in enumerate(textos):  # Recorre cada texto de encabezado con su índice
            if indice_rango is None and ("rank" in t or t == "#" or "position" in t):  # Palabras clave para rango
                indice_rango = i  # Guarda índice de rango
            if indice_pais is None and ("team" in t or "nation" in t or "country" in t):  # Palabras clave para país/equipo
                indice_pais = i  # Guarda índice de país/equipo
            if indice_puntos is None and ("points" in t or t == "pts"):  # Palabras clave para puntos
                indice_puntos = i  # Guarda índice de puntos

        if None not in (indice_rango, indice_pais, indice_puntos):  # Si encontró los tres
            return indice_rango, indice_pais, indice_puntos  # Devuelve tupla de índices

    return None, None, None  # Si no detectó, devuelve Nones

def mostrar_columna_equipo_despacio(navegador, tabla, indice_pais):  # Pinta el header y cada celda de la columna de equipos con pausas
    # 1) Resalta el encabezado de la columna de equipos
    posibles_headers = tabla.find_elements(By.CSS_SELECTOR, "thead tr th")  # Obtiene th del thead si existe
    if posibles_headers and indice_pais < len(posibles_headers):  # Verifica que haya encabezado visible del thead
        th_equipo = posibles_headers[indice_pais]  # Toma el th de la columna de equipos
        resaltar(navegador, th_equipo, "khaki", "3px solid #b8860b")  # Resalta el th de la columna de equipos
        time.sleep(PAUSA_LARGA)  # Pausa para que la clase lo vea claro
    # 2) Recorre el tbody y resalta celda por celda en esa columna
    cuerpo = tabla.find_element(By.TAG_NAME, "tbody")  # Toma el cuerpo de la tabla
    filas = cuerpo.find_elements(By.CSS_SELECTOR, "tr")  # Lista de filas del cuerpo
    for fila in filas:  # Recorre filas
        celdas = fila.find_elements(By.CSS_SELECTOR, "th, td")  # Algunas tablas traen th en la primera columna del cuerpo
        if len(celdas) <= indice_pais:  # Si la fila no tiene esa cantidad de celdas
            continue  # Salta la fila
        celda_equipo = celdas[indice_pais]  # Toma la celda de la columna de equipos
        navegador.execute_script("arguments[0].scrollIntoView({block:'center'});", celda_equipo)  # Desplaza para centrar la celda en viewport
        resaltar(navegador, celda_equipo, "lightyellow", "2px solid #ff9800")  # Resalta la celda actual
        time.sleep(PAUSA_CORTA)  # Pausa corta para que se note el efecto
        quitar_resaltado(navegador, celda_equipo)  # Quita resaltado para seguir con la siguiente
    # 3) Quita resaltado al header si lo tenía
    if posibles_headers and indice_pais < len(posibles_headers):  # Verifica de nuevo
        quitar_resaltado(navegador, posibles_headers[indice_pais])  # Limpia resaltado del encabezado

def extraer_top20_desde_tabla(tabla, indices):  # Extrae Top 20 usando índices detectados
    indice_rango, indice_pais, indice_puntos = indices  # Desempaqueta índices
    cuerpo = tabla.find_element(By.TAG_NAME, "tbody")  # Toma el cuerpo de la tabla
    filas = cuerpo.find_elements(By.CSS_SELECTOR, "tr")  # Lista de filas
    resultados = []  # Acumula registros válidos
    for fila in filas:  # Recorre filas
        celdas = fila.find_elements(By.CSS_SELECTOR, "th, td")  # Algunas tablas mezclan th/td
        if len(celdas) <= max(indices):  # Si la fila no tiene suficientes columnas
            continue  # Salta la fila
        rango_txt = normalizar_texto(celdas[indice_rango].text)  # Texto de rango
        # Intenta tomar el primer número del rango (p. ej. "1 (↑1)" -> 1)
        digitos = "".join(ch for ch in rango_txt.split()[0] if ch.isdigit())  # Deja sólo dígitos del primer token
        if not digitos.isdigit():  # Verifica que haya números
            continue  # Salta si no es un rango válido
        rango = int(digitos)  # Convierte a entero

        celda_pais = celdas[indice_pais]  # Toma la celda de país/equipo
        enlaces = celda_pais.find_elements(By.CSS_SELECTOR, "a")  # Busca enlaces dentro (su texto suele ser más limpio)
        pais = normalizar_texto(enlaces[0].text) if enlaces else normalizar_texto(celda_pais.text)  # Toma texto del primer enlace o de la celda
        if not pais:  # Si no hay país
            continue  # Salta esta fila

        puntos = normalizar_texto(celdas[indice_puntos].text)  # Toma texto de puntos (se deja como string)

        resultados.append({"rango": rango, "pais": pais, "puntos": puntos})  # Agrega registro limpio
        if len(resultados) >= 20:  # Limita a Top 20
            break  # Detiene el bucle
    return resultados  # Devuelve lista de registros

def obtener_top20_fifa_visible_columna():  # Orquesta el scraping visible y la demo de columna
    opciones = Options()  # Crea opciones de Chrome
    # opciones.add_argument("--headless=new")  # Dejar comentado para ver el navegador
    opciones.add_argument("--start-maximized")  # Inicia la ventana maximizada
    opciones.add_experimental_option("detach", True)  # Mantiene la ventana abierta al finalizar
    servicio = Service(ChromeDriverManager().install())  # Prepara ChromeDriver
    navegador = webdriver.Chrome(service=servicio, options=opciones)  # Inicia Chrome con las opciones

    navegador.get(URL)  # Abre la página de Wikipedia con el ranking
    time.sleep(PAUSA_LARGA)  # Pausa para que cargue el HTML y la clase ubique la página

    tablas = navegador.find_elements(By.CSS_SELECTOR, "table.wikitable")  # Busca tablas con clase 'wikitable'
    if not tablas:  # Si no encontró tablas
        print("No encontré tablas .wikitable")  # Mensaje de diagnóstico
        return []  # Devuelve vacío

    tabla_objetivo = None  # Inicializa la tabla objetivo
    indices_validos = None  # Inicializa la tupla de índices

    for t in tablas:  # Recorre cada tabla posible
        i_r, i_p, i_pts = detectar_indices_por_encabezado(t)  # Detecta índices por encabezado
        if None not in (i_r, i_p, i_pts):  # Si encontró los tres
            tabla_objetivo = t  # Marca esta tabla como objetivo
            indices_validos = (i_r, i_p, i_pts)  # Guarda índices
            break  # Deja de buscar

    if tabla_objetivo is None:  # Si no encontró tabla válida
        print("No encontré una tabla con encabezados Rank/Team/Points")  # Mensaje de diagnóstico
        return []  # Devuelve vacío

    resaltar(navegador, tabla_objetivo, "khaki", "3px solid #b8860b")  # Resalta toda la tabla para ubicarla
    time.sleep(PAUSA_LARGA)  # Pausa para que se note el resaltado

    mostrar_columna_equipo_despacio(navegador, tabla_objetivo, indices_validos[1])  # Recorre y pinta la columna de equipos con pausas

    top20 = extraer_top20_desde_tabla(tabla_objetivo, indices_validos)  # Extrae el Top 20 usando índices correctos

    with open("fifa_ranking.json", "w", encoding="utf-8") as f:  # Abre archivo JSON para escritura
        json.dump(top20, f, ensure_ascii=False, indent=2)  # Guarda el Top 20 en formato legible

    print(f"Leídos {len(top20)} registros (Top 20).")  # Imprime cuántos registros obtuvo
    print(top20)  # Muestra el Top 20 por consola

    # navegador.quit()  # Opcional: ciérralo automáticamente; si prefieres verlo, deja comentado
    return top20  # Devuelve el Top 20

#if __name__ == "__main__":  # Punto de entrada del script
obtener_top20_fifa_visible_columna()  # Ejecuta la demo visible con resaltado por columna
