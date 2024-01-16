import requests
from bs4 import BeautifulSoup
import sqlite3 ,os, re
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

labels=["h1","h2","h3","h4","h5","p","a","img"]
bdd = 'scrapping.db'
ruta = os.path.join(os.path.abspath(os.path.dirname(__file__)), bdd)

#Metodo para conectar a la base de datos
def conectar_bd():    
  if not os.path.exists(ruta):
    # La base de datos no existe y la creamos
    with sqlite3.connect(ruta) as conexion:
      cursor = conexion.cursor()

      # TABLAS PARA LOS DATOS
      for label in labels:
        cursor.execute(f"""
          CREATE TABLE IF NOT EXISTS {label} (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          url VARCHAR(255) NOT NULL,
          datos VARCHAR(255) NOT NULL
          );""")

      # TABLA DE URLS
      cursor.execute("""               
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url VARCHAR(255) NOT NULL
        );""")

      # Guardamos los cambios haciendo un commit
      conexion.commit()

  else:
    # Conectarse a la base de datos y realizar otras operaciones
    conexion = sqlite3.connect(ruta)

  return conexion


def cargar_urls():
  try:
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT url FROM urls")
    urls = cursor.fetchall()

    area_urls.config(state=tk.NORMAL)
    for url in urls:
      area_urls.insert(tk.END, url[0] + '\n')
    area_urls.config(state=tk.DISABLED)
  except sqlite3.Error as e:
    print(f"Error al cargar las URLs iniciales: {e}")
  finally:
    if conexion:
      conexion.close()

def insertar(label,datos,url,conexion):

  cursor = conexion.cursor()
  try:
    cursor.execute(f"SELECT * FROM {label} WHERE url = ? AND datos = ?", (url, datos))
    if cursor.fetchone() is None and datos is not None:
      cursor.execute(f"INSERT INTO {label} (url, datos) VALUES (?, ?)", (url, datos))
      conexion.commit()
  except sqlite3.Error as e:
    print(f"Error al insertar en la tabla {label}: {e}")


def scrapping(labels, url):
  conexion = conectar_bd()
  cursor = conexion.cursor()
  cursor.execute(f"SELECT * FROM urls WHERE url = ?", (url,))
  if cursor.fetchone() is None:
    cursor.execute(f"INSERT INTO urls (url) VALUES (?)", (url,))
    conexion.commit()
  cont = requests.get(url)
  sopa = BeautifulSoup(cont.text, 'html.parser')

  for label in labels:
    elementos = sopa.find_all(label) 
    for elemento in elementos:
      if label == 'a':
        datos = elemento.get('href')
        if datos is not None and not datos.startswith(("http:",'https:')):
          continue
      elif label == 'img':
        datos = elemento.get('src')
        if datos is not None and not datos.startswith(("http:",'https:','//')):
          continue
      else:
        datos = elemento.text.strip()
        
      insertar(label, datos, url, conexion)
  
  conexion.close()

import sqlite3

def buscartermino(termino):
    resultados = {}
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()

        for label in labels:
            cursor.execute(
                f"SELECT *, LENGTH(datos) - LENGTH(REPLACE(datos, ?, '')) as coincidencias FROM {label} WHERE UPPER(datos) LIKE UPPER(?) ORDER BY coincidencias DESC LIMIT 5",
                ('%' + termino + '%','%' + termino + '%')
            )
            resultados[label] = cursor.fetchall()
            
    except sqlite3.Error as e:
        print(f"Error al buscar en la base de datos: {e}")
    finally:
        conexion.close()

    return resultados

def generar_html(resultados):
  html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resultados de búsqueda</title>
    </head>
    <body>
        <h1>Resultados de búsqueda</h1>
    """

  for label, registros in resultados.items():
    html += f"<h2>{label}</h2>"
    if registros:
      html += "<ul>"
      for registro in registros:
        if label=='img':
          html += f"<li><img src='{registro[2]}'></li>"
        if label=='a':
          html += f"<li><a href='{registro[2]}'>{registro[2]}</a></li>"
        else:
          html += f"<li>{registro[2]}</li>"
      html += "</ul>"
    else:
      html += "<p>No se encontraron resultados.</p>"

  html += """
  </body>
  </html>
  """
  return html

def raspar():
    url = entry_url.get()
    scrapping(labels,url)

    area_urls.config(state=tk.NORMAL)
    area_urls.insert(tk.END, url + '\n')
    area_urls.update_idletasks()
    area_urls.config(state=tk.DISABLED)

def generar():
    file=os.path.join(os.path.abspath(os.path.dirname(__file__)), "resultados_busqueda.html")
    tematica = entry_tematica.get()
    # Aquí iría el código para generar el contenido según la temática
    if len(tematica) == 0:
        mensaje.config(text='Introuce un tema')
    else:
        mensaje.config(text='Generando contenido...')
        resultados = buscartermino(tematica)
        html_resultados = generar_html(resultados)
        with open(file, "w", encoding="utf-8") as archivo:
            archivo.write(html_resultados)

root = tk.Tk()
root.title('Raspador y Generador')

root.geometry('440x300+100+200') #Tamaño de la ventana
root.resizable(0,0) #No se puede cambiar el ancho y el alto

# URL
label_url = tk.Label(root, text='URL:')
label_url.grid(row=0, column=0, padx=10, pady=10, sticky='w')
entry_url = tk.Entry(root, width=40)
entry_url.grid(row=0, column=1, padx=10, pady=10, sticky='w')
button_rasp = tk.Button(root, text='RASPAR', command=raspar)
button_rasp.grid(row=0, column=2, padx=10, pady=10, sticky='w')

# URLs
area_urls = scrolledtext.ScrolledText(root, width=50, height=7)
area_urls.grid(row=1, column=0, columnspan=3, padx=10, pady=(10, 20))
area_urls.config(state=tk.DISABLED)

# ERRORES
mensaje = tk.Label(root, text="")
mensaje.grid(row=2, column=0, columnspan=3, pady=2)

# Separador
separador = ttk.Separator(root, orient='horizontal')
separador.grid(row=3, column=0, columnspan=3, pady=10, padx=20, sticky='ew')

# TEMÁTICA
label_tematica = tk.Label(root, text='TEMÁTICA:')
label_tematica.grid(row=4, column=0, padx=10, pady=10, sticky='w')
entry_tematica = tk.Entry(root, width=30)
entry_tematica.grid(row=4, column=1, padx=10, pady=10, sticky='w')
button_generar = tk.Button(root, text='GENERAR', command=generar)
button_generar.grid(row=4, column=2, padx=10, pady=10, sticky='w')

cargar_urls()
root.mainloop()