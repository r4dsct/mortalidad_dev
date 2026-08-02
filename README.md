# mortalidad\_dev

Contiene los datos y scripts necesarios para llevar a cabo un análisis estadístico de los datos de mortalidad distrital recopilados por el INEC (2013 a 2024)







Lista de datos compilados y su origen:



1. Defunciones:

Datos obtenidos del sitio web del INEC. Los archivos tienen nombres como 'rePoblacNac\_combo de defunciones\_web2022.xlsx'. Los archivos del 2013 al 2024 fueron descargados, con excepción del correspondiente al 2015. Este nuca fue encontrado. Los datos fueron procesados para darles un formato más adecuado para su incorporación a una base de datos. El resultado de estos datos se encuentra en la tabla 'datos\_mortalidad\\mortalidad\_20142024.csv'. Es importante señalar que la transcripción de estos datos fue revisada superficialmente y en el futuro se espera hacerlo detalladamente.



El archivo 'datos\_mortalidad\\mortalidad\_20142024.csv' incorpora cambios en la pertenencia cantonal de varios distritos, con el propósito de reflejar cambios en estatus administrativo. Prontamente se dará detalle de estos distritos.





2\. Estimados de población



Se utilizaron los estimados de población distrital del INEC. Estos incluyen estimados de población para cada año, comenzando en el 2020. El nombre del archive es 'repoblaceppsubnaciokitcuadros2000-2050.\_0.xlsx'. Los datos fueron procesados para darles un formato más adecuado para su incorporación a una base de datos. Estos se encuentran en el archive 'datos\_mortalidad\\estimados\_poblacion\_distrito\_inec2025.csv'. Es importante señalar que la transcripción de estos datos fue revisada superficialmente y en el futuro se espera hacerlo detalladamente.



3\. Censos de población distrital



Estos datos se incorporan, pero no son utilizados. En un futuro se dará más referencia de ellos



4\. Lista de cantones y distritos



La lista de cantones y distritos se obtuvo en el sitio web del Instituto Geográfico Nacional. Especificamente, se utilizó el archive 'DTA-TABLA POR PROVINCIA-CANTÓN-DISTRITO 2026.xlsx'. Esta información fue transcribida a los siguientes archivos:'datos\_mortalidad\\cantones\_cr\_2026.csv' y 'datos\_mortalidad\\distritos\_cr\_2026.csv'.



5\. Límites administrativos.

Se incluyen los siguientes datos geoespaciales obtenidos del sitio web del Sistema Nacional de Información Territorial:

\- límites distritales: limitedistrital\_5k.shp y archivos asociados.

\- límites cantonales: limitecantonal\_5k.shp y archivos asociados

\- Localidades de Costa Rica: centros\_poblados\_localidades.shp y archivos asociados. De este archivo, unicamente se incluyen una cuantas ciudades que funcionan como puntos de referencia.









Scripts:



Se incluyen dos scripts:

'crear\_basedatos\_mortalidad\_posgresql.py' se utiliza para crear una base de datos PostgreSQL e importar los datos recopilados en ella. La extension PostGIS debe de estar abilitada. Al ejecutar el script, el usuario debe de proveer la clave para conectarse a PostgreSQL. 



'funciones\_estadisticas.py' TBD



'ModeloLinearMixto.R' es un script de r que ajusta un modelo lineal mixto a la tasa de mortalidad. Más detalles del mismo se proveran pronto.

