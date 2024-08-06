# DoubleFiles

**DoubleFiles** es una aplicación desarrollada en Python para buscar y gestionar archivos duplicados en tu sistema. Utiliza algoritmos de hashing para identificar archivos duplicados y ofrece opciones para mover estos archivos a una carpeta designada.

## Características

- **Listar directorios**: Lista todos los archivos y carpetas en un directorio especificado.
- **Calcular hashes**: Genera hashes SHA-256 para identificar archivos duplicados.
- **Base de datos**: Inserta registros de archivos y sus hashes en una base de datos SQLite.
- **Mover archivos duplicados**: Mueve archivos duplicados a una carpeta específica para su gestión.

## Requisitos

- Python 3.x
- Librerías:
  - `os`
  - `hashlib`
  - `sqlite3`
  - `traceback`
  - `logging`

## Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/drcortes/DoubleFiles.git
   ```
2. Navega al directorio del proyecto:
    ```bash
    cd DoubleFiles
    ```

## Uso
   
Se puede ejecutar DoubleFiles sin argumentos. La aplicación realizará las consultas necesarias para poder funcionar.

  ```bash
    DoubleFiles -l:C:\\Carpeta\\a\\analizar -OPCIONES
  ```


Este modo con argumentos por consola permitirá integrar el script a otra aplicación que necesite usarla

```bash
Opciones:

 -h          Muestra este menú de ayuda.
 -r          Realiza análisis recursivo. Carpeta y subcarpetas.
 -m          Mueve los archivos duplicados a una carpeta 'ElementosDuplicados', esta carpeta esta en el mismo
             lugar que esta Aplicacion.
 -a          Modo API: Esta opcion no va acompañada con otros argumentos. Se levantará un servicio API REST para consultas.

```
##       Ayuda API:   
        
El usuario y password para autenticarse en el API se crea de manera automática cada vez que se inicie la aplicacion. Estas quedarán en el archivo de 
configuracion config.py, las variables serian USER_API y PASSWORD_API. La variable SECRET_KEY se usará para realizar el JWT del token.

La aplicación usa autenticación Beared Token en la cabecera de autenticación.
Endpoints:
TODOS LOS ENDPOINT SON POST

http://127.0.0.1:5000/login

Se deberá usar una solicitud mediante el USER_API y PASSWORD_API para que entregue un beared Token
```bash
  ej: {
     usuario": "uk5lfXZXNAfHf9jdn3fY65Js",
     password": "LdmdYuc71:4a9V1u*pI_-F0B"
  }    
```
http://127.0.0.1:5000/api
Aca se debe de enviar una solicitud con la variable 'ruta' ej: C:\\CARPETA\\A\\ANALIZAR debe ir con doble backslash para que no de error.
Además se debe de enviar la variable 'recursivo' y 'mueve' con argumento yes, para que analice la carpeta mas mas subcarpetas recursivamente,
y además pueda mover los archivos a la carpeta ElementosDuplicados que se creará automaticamente en la misma ruta donde se encuentre el script corriendo.

EJ: 
```json
  {
   "ruta": "C:\\Users\\diego\\OneDrive\\Python\\Herramientas\\Prueba",
   "recursivo": "yes",
   "mueve": "No"
   }
```
## Estructura del proyecto.

  - **config.py:** contiene las configuraciones básicas para que funcione el script, de no existir la aplicación creará uno nuevo con valores predeterminados.
  - **dir_db.db:** Será la base de datos en SQLite que almacenará los hashes de los archivos para el proceso de comparacion.
  - **eventlog.log:** Será el archivo que almacene los registros de uso y errores que produzca la app.
  - **Resultado.csv:** Será el archivo en el que se almacene el resultado de la aplicacion.

## Contacto

Autor: Diego Cortes Robles
Email diego.cortes1987[at]gmail.com
