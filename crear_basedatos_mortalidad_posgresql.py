54# -*- coding: utf-8 -*-
"""
Este script ejecuta las siguientes tareas
- Crea un base de datos Postgresql y PostGIS
- Crea una series de tablas necesarias y las popula
- Importa datos SIG necesarios


Autor: r4dsct@gmail.com
github: xxx
"""

# Librerías necesarias
import psycopg
from psycopg import sql
import csv
import os
import geopandas as gpd
from sqlalchemy import create_engine
from funciones_estadisticas import interpola_extrapolar


# Funciones
def create_db_connection(host_name, port_n, user_name, password_pg, dbname_new):
    # Crea una conexión a la base de datos postgresql
    try:
        # Conexión
        connection = psycopg.connect(
            host=host_name,
            port=port_n,
            user=user_name,
            password=password_pg,
            dbname= dbname_new,
            autocommit=True
        )
    except psycopg.Error as e:
        print(f"Error: {e}")
        
    print("Conexión a base de datos {} creada.".format(dbname_new))
    return connection
        
    


def create_database(connection_object, dbname_new, create_schemas=True, close_connection=False):
    # Crea nueva base de datos.
    try:
        
        cursor = connection_object.cursor()
            
        # 3. Create the database using sql.SQL and sql.Identifier to prevent SQL injection
        sql_statement = sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(dbname_new)
        )
        
        cursor.execute(sql_statement)
        print(f"Base de datos {dbname_new} creada excitosamente.".format(dbname_new))
        
    except psycopg.Error as e:
        print(f"Error: {e}")

    finally:
        cursor.close()
        # 4. Close the connection
        if close_connection:
            
            connection_object.close()
            print("Conexión a base de datos cerrada.")
            
def creaSchemas(connection_object, schema_name_list=['espacial'], close_connection=False):
    # crea un esquema nuevo en la base de datos. Empieza con el crea el esquema 'espacial' donde van los datos geoespaciales 
    try:
        
        cursor = connection_object.cursor()
        for schema_i in schema_name_list:
            sql_statement = sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema_i)
                                                                             )
        
            cursor.execute(sql_statement)
            print('Schema {} creado.'.format(schema_i))
    except psycopg.Error as e:
        print(f"Error: {e}")

    finally:
        # 4. Close the connection
        cursor.close()
        if close_connection:    
            connection_object.close()
            print("Conexión a base de datos cerrada.")
        
    
def add_postgis(connection_object, dbname_new, close_connection=False):
    # habilita la extensiób postgis para subir datos geoespaciales adecuadamente
    try:
            
        
        cursor = connection_object.cursor()
        
        # Create postgis extension in data 
        cursor.execute("CREATE EXTENSION  postgis;")
        
        # Verify the installation by checking the version
        cursor.execute("SELECT PostGIS_Full_Version();")
        version = cursor.fetchone()[0]
        print(f"Detalles de la versión: {version}")
        
        
        print(f"PostGIS habilitado excitosamente en base de datos {dbname_new}".format(dbname_new))

    except psycopg.Error as e:
        print(f"Error: {e}")

    finally:
        # 4. Close the connection
        if close_connection:
            cursor.close()
            connection_object.close()
            print("Conexión a base de datos cerrada.")
    
    
def create_table(connection_object, table_name_str, table_col_dict):
    # Crea una nueva tabla. table_name_str corresponde al nombre que tendrá la tabla. table_col_dict es un diccionario con llaves
    # equivalentes al nombre de la columna y elementos detallando la estructura de los datos.
    
    table_col_dict = {table_name_str+'_pk': 'SERIAL PRIMARY KEY', **table_col_dict}
             
     
    # 1. Build individual column definitions ("column_name" DATA_TYPE)
    # Note: Column names are treated as Identifiers, while Data Types are treated as raw SQL
    column_definitions = []
    for col_name, col_type in table_col_dict.items():
        definition = sql.SQL("{} {}").format(sql.Identifier(col_name),
                                                 sql.SQL(col_type)
                                                 )
        column_definitions.append(definition)
   
    # 2. Join all column definition fragments with commas
    joined_columns = sql.SQL(", ").join(column_definitions)
        
   
    # 3. Construct the complete final CREATE TABLE query safely
    query_create_table = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({});").format(
        sql.Identifier(table_name_str),
        joined_columns
        )
        
    
    # 4. Open a cursor, execute the command, and commit the transaction
    try:
        with connection_object.cursor() as cur:
            cur.execute(query_create_table)
           
            connection_object.commit()
            print("Tabla {} creada exitosamente.".format(table_name_str))
    except Exception as e:
        connection_object.rollback()
        print(f"Error occurred while creating table: {e}")
        raise e
        

def import_populationtable(connection_obj, nombre_tabla_str='poblacion_distrito_20112026', schema='public'):
    # importa la con censos del INEC del 2011 y el 2026. Al final estos datos no se utilizan en el análisis.
    
    try:
        # 2. Open a cursor using RealDictCursor
        with connection_obj.cursor() as cursor:
            # 3. Execute the SQL query
            
            # query = sql.SQL("SELECT cod_distrito, pob_total2011, pob_fem_2011, pob_hom_2011, pob_total2022, pob_fem_2022, pob_hom_2022 FROM  {}.{};").format(
            # sql.Identifier(schema),
            # sql.Identifier(nombre_tabla_str)
            # )
            
            cursor.execute(sql.SQL("SET search_path TO {}, {};").format(
            sql.Identifier(nombre_tabla_str),
            sql.Identifier(schema)))
            
            query = sql.SQL("SELECT cod_distrito, pob_mujer_2011 ,pob_hombre_2011, pob_mujer_2022, pob_hombre_2022 FROM {}.{} WHERE pob_mujer_2011 IS NOT NULL AND pob_mujer_2022 IS NOT NULL;").format(
            sql.Identifier(schema),
            sql.Identifier(nombre_tabla_str)
            )
            
            
            cursor.execute(query)
        
            # 4. Fetch all rows as a list of dictionaries
            datos_poblacion_lst = cursor.fetchall()
    
    except Exception as e:
        connection_obj.rollback()
        print(f"Error occurred while creating table: {e}")
        raise e
        
    finally:
        
        return datos_poblacion_lst


def interpolarDatos_poblacion(connection_object, nombre_tabla_str='poblacion_distrito_20112026', schema='public', tabla_estimados_nombre ='estimados_poblacion_distrito'):
    # crea una tabla con datos de población distrital anual (2011 a 2026) interpolando los valores en los censos del INEC del 2011 y 2026.
    # estos datos no se utilizan en el análisis
    try:
        
        population_list = import_populationtable(connection_obj=connection_object)
        
        for distrito_i in population_list:
            cod_distrito= distrito_i[0]
            poblacion_mu_2011 = distrito_i[1]
            poblacion_hom_2011 = distrito_i[2]
            poblacion_mu_2022 = distrito_i[3]
            poblacion_hom_2022 = distrito_i[4]
            
            estimados_fem =interpola_extrapolar([poblacion_mu_2011,poblacion_mu_2022])
            estimados_hom =interpola_extrapolar([poblacion_hom_2011, poblacion_hom_2022])
            
            distrito_list = [cod_distrito]*len(estimados_fem[0])
            
            query = sql.SQL("INSERT INTO {} (cod_distrito, anho, poblacion_mujer, poblacion_hombre, poblacion_total) VALUES (%s, %s, %s, %s, %s);").format(
            sql.Identifier(tabla_estimados_nombre)
            )
            
            combo_list = zip(distrito_list, estimados_fem[0], estimados_fem[1], estimados_hom[1], estimados_fem[1]+estimados_hom[1])
            with connection_object.cursor() as cur:
                cur.executemany(query, combo_list)
        
            
    
    except Exception as e:
        connection_object.rollback()
        print(f"Error occurred while creating table: {e}")
        raise e
    
    finally:
        print("Estimados de población por distritos creados excitosamente")
    

def append_csv_to_postgres(conn, csv_file_path, table_name):
    """
    Copia los datos en un csv en la tabla postgresql correspondiente.
    """
    try:
        # 1. Read CSV to get headers
        with open(csv_file_path, mode='r', encoding='ISO-8859-1') as f:
            reader = csv.DictReader(f)
            csv_columns = reader.fieldnames
            
            if not csv_columns:
                raise ValueError("El CSV está vacío o le faltan títulos de las columnas.")

        # 2. Build the COPY FROM query and append data
        with conn.cursor() as cur:
            # Dynamically format the COPY statement with only the CSV columns
            query = sql.SQL(
                "COPY {table} ({fields}) FROM STDIN WITH CSV HEADER"
            ).format(
                table=sql.Identifier(table_name),
                fields=sql.SQL(', ').join(map(sql.Identifier, csv_columns))
            )

            with cur.copy(query) as copy:
                with open(csv_file_path, mode='r', encoding='ISO-8859-1') as f:
                    # Stream the file content directly into the copy object
                    copy.write(f.read())
                    
        # 3. Commit the transaction
        conn.commit()
        print("Datos copiados exitosamente en {}.".format(table_name))

    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
        
def import_shp_to_postgis(shp_path_str, engine, table_name, schema='espacial'):
    """
    Copia un .shp en postgis
    """
    os.environ["SHAPE_RESTORE_SHX"] = "YES"
    try:
        # 1. Create the database connection engine
        # 2. Read the shapefile into a GeoDataFrame
        print("Abriendo el shapefile: {}".format(shp_path_str))
        gdf = gpd.read_file(shp_path_str)
        
        # 3. Write the GeoDataFrame to PostGIS
        print("Copiando dato en PostGIS : {}.{}...".format(schema, table_name))
        gdf.to_postgis(
            name=table_name, 
            con=engine, 
            if_exists="replace",  # Options: 'fail', 'replace', 'append'
            schema=schema,
            index=False
        )
        
        print("Shapefile importado a PostGIS exitosamente!")

    except Exception as e:
        print("ocurrió un error: {}".format(e))



    


def run_main(host_name, port_n, user_name, password_pg, dbname_new, table_list, source_list, sig_list):
    # Ejecuta los comando necesarios para crear las base de datos requerida en el análisis.
    # conexión
    connection_object = create_db_connection(host_name, port_n, user_name, password_pg, dbname_new='postgres')
    
    # crea base de datos
    create_database(connection_object, dbname_new)
    
    connection_object.close()
    
    # Crea conexión con la base de datos recién creada
    connection_object = create_db_connection(host_name, port_n, user_name, password_pg, dbname_new)
    
    # activa postgis
    add_postgis(connection_object, dbname_new)
    
    # nuevos schemas
    creaSchemas(connection_object)
    
    # crea todas las tablas
    
    for table_i in table_list:
        create_table(connection_object, table_name_str=table_i[0], table_col_dict=table_i[1])
        
        
    # importa los datos en los .csv
    for source_i in source_list:
        append_csv_to_postgres(connection_object, source_i[1], source_i[0])
        
    
    # otro tipo de conexión para importar los datos sig
    connection_url = connection_url = f"postgresql+psycopg://{user_name}:{password_pg}@{host_name}:{port_n}/{dbname_new}"
    engine = create_engine(connection_url)
        
    # importa datos geoespaciales
    for sig_layer_i in sig_list:
        
        import_shp_to_postgis(sig_layer_i[1], engine, sig_layer_i[0],)
        
        
    # Crea tabla de población por distrito y año interpolando los estimados del 2011 y 2022
    nombre_tabla_str = 'estimados_poblacion_distrito'
    
    tabla_pobdistritos_col_dic = {'cod_distrito': 'integer',
                                'anho': 'integer',
                                'poblacion_mujer': 'NUMERIC(10, 2)',
                                'poblacion_hombre': 'NUMERIC(10, 2)',
                                'poblacion_total': 'NUMERIC(10, 2)'}
    # primero la tabla
    create_table(connection_object, table_name_str=nombre_tabla_str, table_col_dict=tabla_pobdistritos_col_dic)
    
    interpolarDatos_poblacion(connection_object=connection_object)
    
    # Crea tabla para guardar los estimados resumenes básicos por distritos
    nombre_tabla_str = 'resumen_mortalidad_distrito'
        
    tabla_resumen_estadisticos_distrito_col_dic = {'cod_distrito': 'integer',
                                
                                "defunciones_total_prom": 'NUMERIC(10, 2)',
                                'defunciones_total_med': 'NUMERIC(10, 2)',
                                "poblacion_total_prom": 'NUMERIC(10, 2)',
                                'poblacion_total_med': 'NUMERIC(10, 2)',
                                "def100mil_total_prom":'NUMERIC(10, 2)',
                                "def100mil_total_med":'NUMERIC(10, 2)'
                                }
    
    create_table(connection_object, table_name_str=nombre_tabla_str, table_col_dict=tabla_resumen_estadisticos_distrito_col_dic)
    
    
    
    # Crea tabla para guardar los parámetros de los modelos lineales
    # una versión en los datos absoultos y otra con los datos normalizadod
    nombre_tabla_str = 'parametros_modelo_linealmixto_distrito'
    
    tabla_parametros_distrito_col_dic = {'cod_distrito': 'integer',
                                "estimado": 'NUMERIC(10, 2)',
                                "def_100mil_promedio": 'NUMERIC(10, 2)',
                                'pendiente': 'NUMERIC(10, 2)',
                                'error_estandar': 'NUMERIC(10, 2)',
                                'pendiente_corregida': 'NUMERIC(10, 2)' 
                                }
    create_table(connection_object, table_name_str=nombre_tabla_str, table_col_dict=tabla_parametros_distrito_col_dic)   
    
    # cierra la conexión a la base de dtos
    connection_object.close()
    

if __name__ == '__main__':
    # actualizar estos parámetro de ser necesario
    host_str = 'localhost'
    port_str = '5432'
    # 1. Parámetros de la conexión a la base de datos
    user_str = 'postgres'
    password_str = str(input("Clave de base de datos postgresql: ")) # pide la clave a la base de datos
    new_db_name_str = 'mortalidadCR_dev' # nombre de la base de datos
    
    # table information
    # Mortalidad
    tabla_mortalidad_nombre = 'defunciones_todas'
    tabla_mortalidad_col_dic = {'cod_canton': 'integer',
                                'cod_distrito': 'integer',
                                'anho': 'integer',
                                'defunciones_mujeres': 'integer',
                                'defunciones_hombres': 'integer',
                                'defunciones_total': 'integer'}
    
    tabla_mortalidad_index_dic = {'idx_anho':'anho'}
    
    # Cantones
    tabla_cantones_cr_2026_nombre = 'cantones_2026'
    tabla_cantones_col_dic = {'cod_provincia': 'integer',
                              'provincia_nombre':'varchar(50)',
                                'cod_canton': 'integer',
                                'canton_nombre':'varchar(50)',
                                'area_km2': 'DECIMAL'}
    
    tabla_cantones_index_dic = {'idx_canton':['provincia_nombre','canton_nombre']}
    
    
    # Distritos
    tabla_distritos_cr_2026_nombre = 'distritos_2026'
    tabla_distritos_col_dic = {'cod_canton': 'integer',
                               'cod_distrito': 'integer',
                                'distrito_nombre':'varchar(50)',
                                'area_km2': 'DECIMAL'}
    
    tabla_distritos_index_dic = {'idx_canton':['distrito_nombre']}
    
    # Población
    tabla_poblacion_cr_2026_nombre = 'poblacion_distrito_20112026'
    tabla_poblacion_col_dic = {'cod_canton': 'integer',
                               'cod_distrito': 'integer',
                               'pob_total_2011': 'integer',
                               'pob_mujer_2011': 'integer',
                               'pob_hombre_2011': 'integer',	
                               'por_0a14anhos_2011': 'DECIMAL',	
                               'por_15a65anhos_2011': 'DECIMAL',	
                               'por_mayor65anhos_2011': 'DECIMAL',		
                               'edad_media_2011': 'DECIMAL',		
                               'por_poburbana_2011': 'DECIMAL',		
                               'prom_hijos_2011': 'DECIMAL',		
                               'por_mujfertil_2011': 'DECIMAL',		
                               'por_madres_2011': 'DECIMAL',		
                               'por_madres_solteras_2011': 'DECIMAL',		
                               'por_madres_adolescentes_2011': 'DECIMAL',		
                               'poblacion_total_2022': 'integer',	
                               'pob_hombre_2022': 'integer',	
                               'pob_mujer_2022': 'integer',
                               'cambio_mujer_porcent': 'NUMERIC(10, 2)',
                               'cambio_hombre_porcent': 'NUMERIC(10, 2)',
                               'cambio_total_porcent': 'NUMERIC(10, 2)',
                               'cambio_mujer_absoluto': 'NUMERIC(10, 2)',
                               'cambio_hombre_absoluto': 'NUMERIC(10, 2)',
                               'cambio_total_absoluto': 'NUMERIC(10, 2)'
                               }
    
    # Tabla estimados de población INEC 2025
    tabla_estimadosInec_2025_nombre = 'estimados_poblacion_inec2025'
    tabla_estimadosInec_2025_col_dic = {'cod_distrito': 'integer',
                               'anho': 'integer',
                                'crecimient_pob': 'NUMERIC(10, 2)', 
                                'tasa100': 'NUMERIC(10, 2)', 
                                'pob_0a14': 'NUMERIC(10, 2)',
                                'pob_15a64': 'NUMERIC(10, 2)',
                                'pob_65mas': 'NUMERIC(10, 2)',
                                'denspob': 'NUMERIC(10, 2)',
                                'razon_total': 'NUMERIC(10, 2)', 
                                'razon_ninhez': 'NUMERIC(10, 2)',
                                'razon3': 'NUMERIC(10, 2)',
                                'edad_media_total': 'NUMERIC(10, 2)', 
                                'edad_media_hombre': 'NUMERIC(10, 2)', 
                                'edad_media_muejer': 'NUMERIC(10, 2)',
                                'indice_envej65_total': 'NUMERIC(10, 2)',
                                'indice_envej65_hombre': 'NUMERIC(10, 2)',
                                'indice_envej65_mujer': 'NUMERIC(10, 2)',
                                'indice_envej85_total': 'NUMERIC(10, 2)',
                                'indice_envej85_hombre': 'NUMERIC(10, 2)',
                                'indice_envej85_mujer': 'NUMERIC(10, 2)',
                                'pob_total': 'NUMERIC(10, 2)'}



                              
    table_list = [[tabla_mortalidad_nombre, tabla_mortalidad_col_dic, tabla_mortalidad_index_dic],
                  [tabla_cantones_cr_2026_nombre, tabla_cantones_col_dic, tabla_mortalidad_index_dic],
                  [tabla_distritos_cr_2026_nombre, tabla_distritos_col_dic, tabla_distritos_index_dic],
                  [tabla_poblacion_cr_2026_nombre, tabla_poblacion_col_dic],
                  [tabla_estimadosInec_2025_nombre,tabla_estimadosInec_2025_col_dic]
                  ]    
    
    
    # directorio de datos
    directorio_principal_str = os.getcwd()
    directorio_datos_str = os.path.join(directorio_principal_str, 'datos_mortalidad')
    datos_mortalidad_csv_str = os.path.join(directorio_datos_str, 'mortalidad_20142024.csv')
    cantones_csv_str = os.path.join(directorio_datos_str, 'cantones_cr_2026.csv')
    distritos_csv_str = os.path.join(directorio_datos_str, 'distritos_cr_2026.csv')
    poblacion_csv_str = os.path.join(directorio_datos_str, 'poblacion2011_2022.csv')
    estimadosINEC_2025_csv_str = os.path.join(directorio_datos_str, 'estimados_poblacion_distrito_inec2025.csv')
    
    
    source_list = [[tabla_mortalidad_nombre, datos_mortalidad_csv_str],
                   [tabla_cantones_cr_2026_nombre, cantones_csv_str],
                   [tabla_distritos_cr_2026_nombre, distritos_csv_str],
                   [tabla_poblacion_cr_2026_nombre, poblacion_csv_str],
                   [tabla_estimadosInec_2025_nombre, estimadosINEC_2025_csv_str]]
    
    # datos SIG
    directorio_sig_str = os.path.join(directorio_principal_str, 'sig_cr')
    
    cantones_cr_sig_str = os.path.join(directorio_sig_str,'limitecantonal_5k.shp')
    cantones_cr_sig_nombrefinal_str = 'cantones_2026_espacial'
    distritos_cr_sig_str = os.path.join(directorio_sig_str,'limitedistrital_5k.shp')
    distritos_cr_sig_nombrefinal_str = 'distritos_2026_espacial'
    ciudades_cr_sig_str = os.path.join(directorio_sig_str,'centros_poblados_localidades_seleccion.shp')
    ciudades_cr_sig_nombrefinal_str = 'ciudades_2026_espacial'
    
    paises_sig_str = os.path.join(directorio_sig_str,'paises_vecinos.shp')
    paises_sig_nombrefinal_str = 'paises_vecinos_2026_espacial'
    
    sig_list = [[cantones_cr_sig_nombrefinal_str, cantones_cr_sig_str],
                [distritos_cr_sig_nombrefinal_str, distritos_cr_sig_str],
                [ciudades_cr_sig_nombrefinal_str, ciudades_cr_sig_str],
                [paises_sig_nombrefinal_str, paises_sig_str]
                ]
    

    run_main(host_name=host_str,
             port_n=port_str,
             user_name=user_str,
             password_pg=password_str,
             dbname_new=new_db_name_str,
             table_list=table_list,
             source_list = source_list,
             sig_list = sig_list)
    

    
    
