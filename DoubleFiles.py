import os,sys
import hashlib
import sqlite3
import logging
import traceback
import subprocess

def create_file_config():
    configfile = os.path.dirname(os.path.abspath(__file__))+"\\config.py"
    if not os.path.exists(configfile):
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
        cursor.execute("SELECT ruta FROM archivos_duplicados")
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
                print(":::",resp)
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
        logger.debug (f"Se inserta ruta: {ruta} con hash: {hash}")
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
        logger.debug(f"Se obtiene hash de archivo {archivo}")
        return hasher.hexdigest()
    except FileNotFoundError as e:
        logger.info(f"El archivo {archivo} ya no existe, no se podra procesar. Detalle {e}")
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
    ext = str(ext[1])
    logger.debug(f"Extension: {ext} de archivo {path}")
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
                logger.info(f"Archivo ya existe.Se renombra archivo a {nombre_archivo_origen}")
                contador += 1
            # comando = f'move "{ruta_origen}" "{carpeta_destino+"\\"+nombre_archivo_origen}"'
            # proceso = subprocess.run(comando, shell=True, capture_output=True)
            # if proceso.returncode == 0:
            #     logger.debug(f"Archivo movido a: {carpeta_destino+"\\"+nombre_archivo_origen}")
            # else:
            #     logger.error(f"Error al mover archivo: {proceso.stderr.decode('utf-8')}")
            os.system(f'move "{ruta_origen}" "{carpeta_destino+"\\"+nombre_archivo_origen}"')
            logger.debug(f"Se mueve archivo {ruta_origen}")
        else:
            return False
        return True
        
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error al mover el archivo: {e}")

           

############################ INICIO DE LA APP #############################

ConexionSql()
if 'INFO' != LOG_LEVEL and 'DEBUG' != LOG_LEVEL:
    print(f"Nivel de Log: {LOG_LEVEL}")
logger.info("Se inicia programa exitosamente")

print(" Comparador de duplicidad de Archivos - Se pueden realizar configuraciones de la app en config.py")
if config.SCANALL:
    logger.debug(f"Se Evaluan todos las extensiones ya que esta SCANALL como True")
ListaDuplicados = []
losmuevo = 0
while True:    
    directorio = input("Ingrese directorio a Evaluar: ")    
    if os.path.exists(directorio):
        directorio = directorio.strip()
        logger.info(f"Se analiza directorio: {directorio}")
        while True:
            recursivo = input("Desea comparar archivos de manera recursiva? Si/No: ")
            while True:
                mover_duplicados = input("Desea Mover los archivos duplicados a una Carpeta? Si/No: ")
                if "Si" in mover_duplicados:
                    losmuevo = 1
                    break
                elif "No" in mover_duplicados:
                    losmuevo = 0
                    break
                else:
                    print ("Debe elegir Si o No")                    
            if "Si" in str(recursivo):
                List = listaRecursivaArchivos(directorio)
                logger.debug(f"Se procesarán todos estos archivos: {List}")
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
                            logger.debug("Archivo Duplicado: " +a+ " , " +ruta_db)                 
                break
            elif "No" in str(recursivo):
                List = listaDirectorio(directorio)
                for ruta, tipo in List:
                    if tipo in "Archivo":
                        hash = hashfile(ruta)
                        ruta_db = validar_registro_existente(ruta,hash)
                        if not ruta_db:
                            inserta_registro(ruta,hash)
                        else:
                            ListaDuplicados.append((ruta,ruta_db))
                            fecha = os.path.getctime(ruta)
                            update_registro(ruta,hash,os.path.getctime(ruta))                            
                            print("Archivo Duplicado: " + ruta + " , " +ruta_db) 
                            logger.debug("Archivo Duplicado: " + ruta + " , " +ruta_db)          
                break
            else:
                print("Debe ingresar Si o No: ")
        break
    else:
        print("Debe ingresar un Directorio Valido")

with open ('Resultado.csv','w') as resultadocsv:
    for archivo1, archivo2 in ListaDuplicados:
        resultadocsv.write(archivo1+","+archivo2+"\n")
    logger.info("Se crea el archivo Resultado.csv con la informacion procesada")

    
if losmuevo == 1 and ListaDuplicados:
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

logger.info("Se cierra APP")
cerrar_loggers(logger)