# -*- coding: UTF-8 -*-
import os,sys
import hashlib
import sqlite3
import logging
import traceback
import string
import random
import jwt as jwt_function type: ignore
from flask import Flask, request, jsonify # type: ignore
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity # type: ingore





def init_autenticacion():
    min = string.ascii_lowercase
    may = string.ascii_uppercase
    num = string.digits
    simbolos = "!@#$%&*_-+=()[]|;:./<>?"
    all = min + may + num + simbolos
    long = 24 #Largo de string resultante
    password = "".join(random.choice(all) for a in range(long))
    user= "".join(random.choice(min+may+num) for a in range(long))
    secret_key = "".join(random.choice(min+may+num) for a in range(32))
    return (user,password,secret_key)



def create_file_config():
    configfile = os.path.dirname(os.path.abspath(__file__))+"\\config.py"
    if not os.path.exists(configfile):
        USER_API, PASSWORD_API, SECRET_KEY = init_autenticacion()

        with open("config.py","w") as config:
            config.write("###Lista de Configuraciones###\n")
            config.write("#Nombre del Archivo de la base de datos\n")
            config.write("DATA_BASE = 'dir_db.db'\n")
            config.write("# Configurar TRUE si se desea comparar todos los archivos, esto no consideraría las listas de documentos, imagenes audio y video que aparecen mas abajo\n")
            config.write("SCANALL = False\n")
            config.write("EXCLUDE_EXT=''\n")
            config.write("### MAX_SIZE_FILE Esta definido en MB si no esta el default son 1024 MB\n")
            config.write("MAX_SIZE_FILE = 1024\n")
            config.write("### Pueden agregarse mas extensiones respetando el formato. Las extensiones que aparezcan en estas listas\n")
            config.write("#son las que seran comparadas. \n")
            config.write("DOCUMENT_EXT=['.doc','.docx','.pdf','.xlsx','.txt','.rtf','.csv','.xls','.ppt','.pptx','.odp','.accdb']\n")
            config.write("IMAGE_EXT = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico', '.psd']\n")
            config.write("AUDIO_EXT = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma', '.aiff', '.ape', '.amr']\n")
            config.write("VIDEO_EXT = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.mpeg', '.mpg', '.3gp', '.webm', '.ts']\n")
            config.write("#El nivel de log puede ser: DEBUG,INFO,WARING,ERROR,CRITICAL\n")
            config.write("LOG_FILE= 'eventlog.log'\n")
            config.write("LOG_LEVEL = 'INFO'\n")
            config.write("USER_API = '"+USER_API+"'\n")
            config.write("PASSWORD_API = '"+PASSWORD_API+"'\n")
            config.write("SECRET_KEY = '"+SECRET_KEY+"'\n")

create_file_config()

try:
    import config
except ImportError as e:
    create_file_config()

### Asignación de Variables


try:
    LOG_LEVEL = config.LOG_LEVEL
except AttributeError as e:
    LOG_LEVEL = "INFO"
try:
    LOG_FILE = config.LOG_FILE
except AttributeError as e:
    LOG_FILE = 'eventlog.log'
try:
    MAX_SIZE_FILE = config.MAX_SIZE_FILE * 1024 * 1024
except AttributeError as e:
    MAX_SIZE_FILE = 1024*1024*1024
try:
    DOCUMENT_EXT = config.DOCUMENT_EXT
except AttributeError as e:
    DOCUMENT_EXT = ['.doc','.docx','.pdf','.xlsx','.txt','.rtf','.csv','.xls','.ppt','.pptx','.odp','.accdb']
try:
    IMAGE_EXT = config.IMAGE_EXT
except AttributeError as e:
    IMAGE_EXT = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico', '.psd']
try:
    AUDIO_EXT = config.AUDIO_EXT
except AttributeError as e:
    AUDIO_EXT = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma', '.aiff', '.ape', '.amr']
try:
    VIDEO_EXT = config.VIDEO_EXT
except AttributeError as e:
    VIDEO_EXT = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.mpeg', '.mpg', '.3gp', '.webm', '.ts']

ListaDuplicados = []
argumentos = sys.argv
argv_val_ruta = 0
argv_recursivo = 0
argv_mov = 0
mododesatendido = 0
argv_ruta = ""

USER_API=config.USER_API
PASSWORD_API = config.PASSWORD_API
SECRET_KEY=config.SECRET_KEY

### Inicializacion de Logs

logger = logging.getLogger(LOG_FILE)
if 'INFO' in LOG_LEVEL:
    logger.setLevel(logging.INFO)
elif 'DEBUG' in LOG_LEVEL:
    logger.setLevel(logging.DEBUG)
elif 'WARNING' in LOG_LEVEL:
    logger.setLevel(logging.WARNING)
elif 'ERROR' in LOG_LEVEL:
    logger.setLevel(logging.ERROR)
elif 'CRITICAL' in LOG_LEVEL:
    logger.setLevel(logging.CRITICAL)
else:
    logger.setLevel(logging.INFO)

fh = logging.FileHandler(LOG_FILE,mode='w')
formatolog = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatolog)
logger.addHandler(fh)


def cerrar_loggers(logger):
    
    handlers = logger.handlers[:]
    for handler in handlers:
        handler.close()
        logger.removeHandler(handler)

### Funciones 

def ConexionSql():
    #Si existe ya el archivo de base de datos se remueve para evitar falsos positivos.
    
    if os.path.isfile(os.path.dirname(os.path.abspath(__file__))+"\\"+config.DATA_BASE):
        logger.debug("Se elimina BBDD" + os.path.dirname(os.path.abspath(__file__))+"\\"+config.DATA_BASE)
        os.remove(os.path.dirname(os.path.abspath(__file__))+"\\"+config.DATA_BASE)
    try:
        if not config.DATA_BASE:
            print("Error en archivo de configuracion config.py, no existe o no esa configurado el parametro DATA_BASE")
            logger.critical("Error en archivo de configuracion config.py, no existe o no esa configurado el parametro DATA_BASE")
            sys.exit(1)
        conn = sqlite3.connect(config.DATA_BASE)
        logger.debug(f"Se crea base de datos: {config.DATA_BASE}")
        # Crear un cursor para ejecutar consultas
        cursor = conn.cursor()
        # Crear la tabla archivos si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS archivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ruta TEXT NOT NULL,            
                hash TEXT NOT NULL,
                fecha TEXT NOT NULL              
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS archivos_duplicados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ruta TEXT NOT NULL,            
                fecha TEXT NOT NULL,
                hash TEXT NOT NULL              
            )
        ''')
        
        # Guardar los cambios
        conn.commit()
        # Cerrar la conexión
        conn.close()
    except PermissionError as e:
        logger.critical("La base de datos no esta accesible, posiblemente otro proceso lo este ocupando")
        sys.exit(1)
    except AttributeError as e:
        logger.error("Error en archivo de configuracion config.py, no existe o no esa configurado el parametro DATA_BASE")
        sys.exit(1)

def listaCompletaDuplicados():
    try:
        conn = sqlite3.connect(config.DATA_BASE)
        cursor = conn.cursor()
        cursor.execute("SELECT ruta,hash,fecha FROM archivos_duplicados")
        conn.commit()
        respuesta = cursor.fetchall()
        cursor.close()
        conn.close()
        return respuesta
    except sqlite3.Error as e:
         traceback.print_exc()
         print (e)
   
def update_registro(ruta,hash,fecha):
    conn = None
    cursor = None
    try:
        conn = sqlite3.connect(config.DATA_BASE)
        cursor = conn.cursor()
        cursor.execute("SELECT ruta,fecha FROM archivos WHERE hash = ?",(hash,))        
        respuesta = cursor.fetchone()
        ruta_db, fecha_db = respuesta

        if ruta != ruta_db:

            if float(fecha)>float(fecha_db):
                cursor.execute("UPDATE archivos SET ruta = ?, fecha = ? WHERE hash = ?",(ruta,fecha,hash))
                
                cursor.execute("SELECT ruta FROM archivos_duplicados WHERE ruta = ?",(ruta,))
                resp = cursor.fetchone()
                if not resp:
                    cursor.execute("INSERT INTO archivos_duplicados (ruta,fecha,hash) VALUES (?,?,?) ",(ruta_db,fecha_db,hash))
                conn.commit()

            else:
                cursor.execute("INSERT INTO archivos_duplicados (ruta,fecha,hash) VALUES (?,?,?) ",(ruta,fecha,hash))
                conn.commit()

        return True

    except sqlite3.Error as e:
        traceback.print_exc()
        return False
        print(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def inserta_registro(ruta,  hash):
    try:
        conn = sqlite3.connect(config.DATA_BASE)
        logger.debug(f"Se conecta a la base de datos: {config.DATA_BASE}")
        cursor = conn.cursor()
        # Ejecutar la consulta de inserción
        cursor.execute('INSERT INTO archivos (ruta, hash, fecha) VALUES (?, ?, ?)', (ruta, hash, os.path.getctime(ruta)))        
        logger.debug (f"Se inserta ruta: {ruta} con hash: {hash}".encode("utf-8"))
        # Guardar los cambios
        conn.commit()

    except sqlite3.Error as e:
        print(f"Error SQLite: {e}")
        logger.error(f"Error SQLLITE: {e}")

    finally:
        # Cerrar la conexión
        conn.close()

def agrega_lista(lista,ruta,tipo):
    lista.append((ruta,tipo))

def ordenaDirectorioFecha(directorio):
    ListaDesordenada = os.listdir(directorio)
    ListaArchivos = []
    for item in ListaDesordenada:
        fecha_creacion = os.path.getctime(directorio+"\\"+item)
        ListaArchivos.append((item,fecha_creacion))
    ListaArchivos.sort(key=lambda archivo: archivo[1])
    return [archivo[0] for archivo in ListaArchivos]

def listaDirectorio(path):
    #Lista DIrectorio e indica si es carpeta o archivo
    logger.info(f"Se lista directorio {path}")
    ListaFinal = []
    ListaArchivos = ordenaDirectorioFecha(path)
    for archivo in ListaArchivos:
        if os.path.isfile(path+"\\"+archivo):
            agrega_lista(ListaFinal,path+"\\"+archivo,"Archivo")
        if os.path.isdir(path+"\\"+archivo):
            agrega_lista(ListaFinal,(path+"\\"+archivo),"Carpeta")   
    return ListaFinal    

def hashfile(archivo):
    #Saca Hash de un archivo
    try:
        hasher = hashlib.sha256()
        with open (archivo, 'rb') as file:
            for bloque in iter(lambda: file.read(4096), b""):
                hasher.update(bloque)
        logger.debug(f"Se obtiene hash de archivo {archivo}".encode("utf-8"))
        return hasher.hexdigest()
    except FileNotFoundError as e:
        logger.info(f"El archivo {archivo} ya no existe, no se podra procesar. Detalle {e}".encode("utf-8"))
        return False
    except Exception as e:
        logger.error(e)
        #traceback.print_exc()
        return False
 
def val_file_size(path):
    try:
        if int(os.path.getsize(filename=path) < MAX_SIZE_FILE):            
            return True
        else:
            logger.debug(f"El archivo {path} es mayor a {MAX_SIZE_FILE/1024/1024} MB")
            False  
    except FileNotFoundError as e:
        logger.info(f"El archivo {path} ya no existe.")
        return False

def val_file_ext(path):
    ext = os.path.splitext(path)    
    ext = str(ext[1]).lower()
    logger.debug(f"Extension: {ext} de archivo {path}".encode("utf-8"))
    for exclude in config.EXCLUDE_EXT:
        if ext == exclude:
            logger.debug(f"Extension {ext} dentro de lista de Exclusion")
            return False
    if config.SCANALL:        
        return True
    for Document in DOCUMENT_EXT:
        if ext == Document:
            logger.debug(f"Extension {ext} dentro de lista de DOCUMENT_EXT")
            return True
    for AUDIO in AUDIO_EXT:
        if ext == AUDIO:
            logger.debug(f"Extension {ext} dentro de lista de AUDIO_EXT")
            return True
    for IMAGE in IMAGE_EXT:
        if ext == IMAGE:
            logger.debug(f"Extension {ext} dentro de lista de IMAGE_EXT")
            return True
    for VIDEO in VIDEO_EXT:
        if ext == VIDEO:
            logger.debug(f"Extension {ext} dentro de lista de VIDEO_EXT")
            return True        
    logger.debug(f"Extension {ext} no esta dentro de ninguna lista.")    
    return False

def listaRecursivaArchivos(directorio):
    #Obtiene solo lista de archivos de manera recursiva entre carpetas
    ListaFinal = []   
    ListaDebug = []
    #logger.info(f"Se obtiene lista de directorio: {directorio}")
    ListaArchivos = ordenaDirectorioFecha(directorio)
    for elemento in ListaArchivos:
        if os.path.isdir(directorio+"\\"+elemento):
            ListaFinal += listaRecursivaArchivos(directorio+"\\"+elemento)
        elif os.path.isfile(directorio+"\\"+elemento):
            if val_file_ext(directorio+"\\"+elemento) and val_file_size(directorio+"\\"+elemento):
                ListaFinal.append(directorio+"\\"+elemento)
            else:
                logger.debug("El archivo fue excepcionado por extension o por que supera la cantidad a MB configuradas a procesar. Ajuste parametros en config.py")
    if LOG_LEVEL == 'DEBUG':
        for lista in ListaFinal:
            ListaDebug.append(os.path.basename(lista))    
    return ListaFinal

def valida_duplicado(ruta):
    try:
        conn = sqlite3.connect(config.DATA_BASE)
        cursor = conn.cursor()       
        
        cursor.execute("SELECT ruta FROM archivos WHERE ruta = ? ",(ruta,))      
        respuesta = cursor.fetchall()   
        cursor.close()
        conn.close()        
        
        if respuesta:
            return True
        else:
            return False
    except sqlite3.Error as e:
        traceback.print_exc()
        print (e)

def validar_registro_existente(ruta, hash):
    try:
        conn = sqlite3.connect(config.DATA_BASE)
        cursor = conn.cursor()
        # Consultar si existe un registro con la ruta especificada
        cursor.execute('SELECT ruta, hash from archivos WHERE hash = ?', (hash,))
        #cursor.execute('SELECT ruta, COUNT(*) FROM archivos WHERE hash = ? GROUP BY ruta HAVING COUNT(*) > 1', (hash,))
        registros = cursor.fetchall()
        conn.commit()
        conn.close()

        # Filtrar los registros para comparar la ruta si el hash coincide
        for registro in registros:
            ruta_bd, hash_db = registro
            if ruta_bd != ruta:
                return ruta_bd  # Hay un archivo duplicado

        return False  # No hay duplicados

    except sqlite3.Error as e:
        print(f"Error SQLite: {e}")
        logger.error(f"Error SQLite: {e}")
        return False

def mover_archivo(ruta_origen, carpeta_destino):
    contador = 0

    try:
        # Extraer el nombre del archivo de la ruta de origen
        nombre_archivo_origen = os.path.basename(ruta_origen)
        carpeta_Origen = os.path.dirname(ruta_origen)         
        if not os.path.isfile(ruta_origen):            
            logger.debug(f"{ruta_origen} ya no existe")
            return False        
        if os.path.isdir(carpeta_destino):
            while os.path.isfile(carpeta_destino+"\\"+nombre_archivo_origen):
                nombre_archivo = os.path.splitext(nombre_archivo_origen)[:1]
                extension = os.path.splitext(nombre_archivo_origen)[1:]
                nombre_archivo_origen = str(nombre_archivo[0]) + f" ({contador})"+str(extension[0])
                logger.info(f"Archivo ya existe.Se renombra archivo a {nombre_archivo_origen}".encode("utf-8"))
                contador += 1
            # comando = f'move "{ruta_origen}" "{carpeta_destino+"\\"+nombre_archivo_origen}"'
            # proceso = subprocess.run(comando, shell=True, capture_output=True)
            # if proceso.returncode == 0:
            #     logger.debug(f"Archivo movido a: {carpeta_destino+"\\"+nombre_archivo_origen}")
            # else:
            #     logger.error(f"Error al mover archivo: {proceso.stderr.decode('utf-8')}")
            os.system(f'move "{ruta_origen}" "{carpeta_destino+"\\"+nombre_archivo_origen}"')
            logger.debug(f"Se mueve archivo {ruta_origen}".encode("utf-8"))
        else:
            return False
        return True
        
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error al mover el archivo: {e}")

def obtiene_de_archivos_byHash(hash):
    try:
        conn = sqlite3.connect(config.DATA_BASE)
        cursor = conn.cursor()
        cursor.execute("SELECT ruta, hash, fecha FROM archivos WHERE hash = ?",((hash,)))
        conn.commit()
        respuesta = cursor.fetchone()
        return respuesta
    except sqlite3.Error as e:
        logger.error(f"Error SQLITE {e}")
    finally:
        cursor.close()
        conn.close()

def mueve_archivos_resultado(ListaDuplicados):
   
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    
# Nombre de la nueva carpeta a crear
    nombre_nueva_carpeta = 'ElementosDuplicados'

    ruta_nueva_carpeta = os.path.join(ruta_actual, nombre_nueva_carpeta)
    if not os.path.exists(ruta_nueva_carpeta):
        os.makedirs(ruta_nueva_carpeta)
    
    if LOG_LEVEL == 'DEBUG':
        logger.debug("###############Resultado de duplicados################")
        for aux1, aux2 in ListaDuplicados:
            logger.debug(str(aux1)+" "+str(aux2))
        logger.debug("##################FIN LISTA DUPLICADOS#################")
    try:
        valorduplicado = listaCompletaDuplicados()
        for valor in valorduplicado: 
            valor = valor[0]
            if not valida_duplicado(valor):
                mover_archivo(valor,ruta_nueva_carpeta)        
                    
    except FileNotFoundError as e:
        logger.debug("No se encuentra archivo. Puede darse por que se movio en el ciclo anterior y no hay como volver a compararlo.")
        logger.error(e)
        traceback.print_exc()

def Analisis_recursivo(directorio):
    List = listaRecursivaArchivos(directorio)
    logger.debug(f"Se procesarán todos estos archivos: {List}".encode("utf-8"))
    for a in List:
        hash = hashfile(a)
        if hash:
            ruta_db = validar_registro_existente(a,hash)
            if not ruta_db:
                inserta_registro(a,hash)
            else:
                fecha = os.path.getctime(a)
                update_registro(a,hash,fecha)                            
                ListaDuplicados.append((a,ruta_db))
                print("Archivo Duplicado: " +a+ " , " +ruta_db)   
                logger.debug(str("Archivo Duplicado: " +a+ " , " +ruta_db).encode("utf-8"))        

def Analisis_no_recursivo(directorio):
    List = listaDirectorio(directorio)
    for ruta, tipo in List:
        if tipo in "Archivo":
            hash = hashfile(ruta)
            ruta_db = validar_registro_existente(ruta,hash)
            if not ruta_db:
                inserta_registro(ruta,hash)
            else:
                ListaDuplicados.append((ruta,ruta_db))
                update_registro(ruta,hash,os.path.getctime(ruta))                            
                print("Archivo Duplicado: " + ruta + " , " +ruta_db) 
                logger.debug("Archivo Duplicado: " + ruta + " , " +ruta_db)         

def retorna_resultado_json():
    respuesta_json = []
    contador = 0
    Lista=listaCompletaDuplicados()
    print(Lista)
    for ruta,hash,fecha in Lista:
        contador += 1
        ruta_db,hash_db,fecha_db = obtiene_de_archivos_byHash(hash)
        datos_procesados = {
             'Ruta_Duplicada':ruta,
             'Fecha_Duplicada':fecha,
             'Ruta_archivo':ruta_db,
             'fecha_db':fecha_db
        } 
        respuesta_json.append(datos_procesados)
        response = {
            'message': 'Ejecucion Correcta',
            'data':respuesta_json
        }        
    return jsonify(response)
          
def limpia_db():
    try:
        conn = sqlite3.connect(config.DATA_BASE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM archivos")
        cursor.execute("DELETE FROM archivos_duplicados")
        conn.commit()
        cursor.close
        conn.close()
    except sqlite3.Error as e:
        print (e)

##########################################FUNCIONES API#############################

app = Flask(__name__) # type: ignore
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hora en segundos
app.config["JWT_ALGORITHM"] = "HS256" 
app.config['JWT_SECRET_KEY'] = SECRET_KEY
jwt = JWTManager(app)
jwt.init_app(app)

##el @app.route va antes de la funcion a llamar
@app.route("/login", methods=["POST"])
def login_api():
    data_login = request.get_json()
    user = data_login.get('usuario')
    password = data_login.get('password')
    print(data_login)
    print("User",user," USER_API ",USER_API)
    print(password,PASSWORD_API)
    if USER_API == user:
        if PASSWORD_API ==password:
            access_token = create_access_token(identity=user)
            return jsonify({"access_token": access_token})
        else:
             return jsonify({"error": "Credenciales inválidas"}), 401 
    else:
             return jsonify({"error": "Credenciales inválidas"}), 401 


 
@app.route('/api',methods=['POST'])
@jwt_required()
def Inicia_Api():
    # Obtiene los parámetros del cuerpo de la solicitud

    termino = 0
    mododesatendido = 1
    authorization_header = request.headers.get("Authorization")
    if authorization_header:
        token = authorization_header.split(" ")[1]
        try:
            print("Token:",token)
            payload = jwt_function.decode(token, app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
            print(payload)
        except Exception:
            traceback.print_exc()
            return jsonify({"error": "Token JWT inválido"}), 401

        data = request.get_json()
        ruta = data.get('ruta')
        recursivo = str(data.get('recursivo'))
        mueve = data.get('mueve')
        limpia_db()
        if os.path.isdir(ruta):
            if recursivo.lower() == 'yes':
                Analisis_recursivo(ruta)
                response = retorna_resultado_json()
                termino = 1
            elif recursivo.lower() == 'No':
                Analisis_no_recursivo(ruta)  
                response = retorna_resultado_json()      
                termino = 1
        # Procesa los parámetros y crea una respuesta
            if termino == 1 and mueve.lower() == 'yes':
                mueve_archivos_resultado(ListaDuplicados)
        else:
            response = {            
                'message': 'La ruta proporcionada no existe.'
            }
            response = jsonify(response)
        # Devuelve la respuesta como JSON
        return response # type: ignore


    

    

############################ INICIO DE LA APP #############################



if argumentos.__len__() > 1:
    mododesatendido = 1

for arg in argumentos[1:]:
    if arg.startswith("-l"):
        argv_ruta = arg.split("-l:")[1:][0]
        
        if os.path.isdir(argv_ruta):
            argv_val_ruta = 1
           
    elif arg == "-a":
        if __name__ == '__main__':
            app.run(debug=True)
        
        Inicia_Api()
    elif arg == "-r":
        if argv_val_ruta == 1:
            argv_recursivo = 1            
        else:
            print("No se definio una ruta a analizar")
            print("")
            sys.exit(0)
    elif arg == "-m":
        if argv_val_ruta == 1:
            argv_mov = 1
        else:
            print("No se definio una ruta a analizar")
            print("")
            sys.exit(0)
    elif arg == "-h":
        print("Ayuda:")
        print("Ejecución Manual",)
        print(f"     {sys.argv[0]}")
        print(f" El modo {sys.argv[0]} permite el modo manual de la aplicación donde no será necesario el uso de argumentos. La aplicación")
        print(f"realizará las consultas necesarias para poder funcionar.")
        print("")
        print(f"     {sys.argv[0]} -l:C:\\Carpeta\\a\\analizar -OPCIONES")
        print(f" Este modo con argumentos por consola permitirá integrar el script a otra aplicación que necesite usarla")
        print("")
        print("Opciones:")
        print("")
        print(" -h          Muestra este menú de ayuda.")
        print(" -r          Realiza análisis recursivo. Carpeta y subcarpetas.")
        print(" -m          Mueve los archivos duplicados a una carpeta 'ElementosDuplicados', esta carpeta esta en el mismo")
        print("             lugar que esta Aplicacion")
        print(" -a          Modo API: Esta opcion no va acompañada con otros argumentos. Se levantará un servicio API REST para consultas.")
        print("")
        sys.exit(0)
    else:
        print(f"Debe de seleccionar las opciones correctas, para mas ayuda ejecute {sys.argv[0]} -h")
        print("")
        sys.exit(0)


###########################################################################


ConexionSql()
if 'INFO' != LOG_LEVEL and 'DEBUG' != LOG_LEVEL:
    print(f"Nivel de Log: {LOG_LEVEL}")
logger.info("Se inicia programa exitosamente")

if mododesatendido == 0:
    print(" Comparador de duplicidad de Archivos - Se pueden realizar configuraciones de la app en config.py")
if config.SCANALL:
    logger.debug(f"Se Evaluan todos las extensiones ya que esta SCANALL como True")

losmuevo = 0
while True:    
    if mododesatendido == 0:
        directorio = input("Ingrese directorio a Evaluar: ")    
    elif mododesatendido == 1:
        if argv_val_ruta == 1:
            directorio = argv_ruta
        else:
            sys.exit(1)
    if os.path.exists(directorio):
        directorio = directorio.strip()
        logger.info(f"Se analiza directorio: {directorio}")
        while True:
            if mododesatendido == 0:
                recursivo = input("Desea comparar archivos de manera recursiva? Si/No: ")
            elif mododesatendido == 1:
                if argv_recursivo == 1:
                    recursivo = "Si"
                elif argv_recursivo == 0:
                    recursivo = "No"
            while True:
                if mododesatendido == 0:
                    mover_duplicados = input("Desea Mover los archivos duplicados a una Carpeta? Si/No: ")
                elif mododesatendido == 1:
                    if argv_mov == 0:
                        mover_duplicados = 'No'
                    elif argv_mov == 1:
                        mover_duplicados = 'Si'
                if "Si" in mover_duplicados:
                    losmuevo = 1
                    break
                elif "No" in mover_duplicados:
                    losmuevo = 0
                    break
                else:
                    print ("Debe elegir Si o No")                    
            if "Si" in str(recursivo):
                Analisis_recursivo(directorio)         
                break
            elif "No" in str(recursivo):
                Analisis_no_recursivo(directorio)
                break
            else:
                print("Debe ingresar Si o No: ")
        break
    else:
        print("Debe ingresar un Directorio Valido")

try:
    with open ('Resultado.csv','w') as resultadocsv:
        for archivo1, archivo2 in ListaDuplicados:
            escrituraArchivo = str(archivo1)+","+str(archivo2)+"\n"
            
            resultadocsv.write(str(escrituraArchivo.encode("utf-8")))
        logger.info("Se crea el archivo Resultado.csv con la informacion procesada")
except TypeError as e:
    traceback.print_exc()
    
    
if losmuevo == 1 and ListaDuplicados:
    mueve_archivos_resultado(ListaDuplicados)


logger.info("Se cierra APP")
cerrar_loggers(logger)
