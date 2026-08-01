# Notas
# Creado por: Sebastian Castro Tanzi- sebastiancastro28@gmail.com, 7/10/2026
# 
# Descripción:
# Ajusta un modelo lineal mixto a los datos de defunciones distritales recopilados por el INEC, años 2013 a 2024.


# importa los paquetes
library(ggplot2)
library(this.path)
library(DBI)
library(RPostgres)
library(lme4)
library(tidyverse)
library(broom)
library(MuMIn)
library(DHARMa)
library(performance)
library(see)
library(stringr)



# Define directorio principal y crea un folder con el análisis
main_directory <- here() # change this
result_directory <-file.path(main_directory,'analysis_preliminar')

# clave de su base de datos postgres.
pw_db<-as.character(readline(prompt = "Clave de base de datos postgresql: "))


if (!dir.exists(result_directory)){
  dir.create(result_directory)
}

# Toma el texto con el sql necesario para importar los datos que necesitamos
query_texto_path_str <- file.path(main_directory,'crea_tabla_mortalidadypoblacion.sql')
query_string <- paste(readLines(query_texto_path_str, warn = FALSE), collapse = "\n")


# Conexión a la base de datos.
con <- dbConnect(
  RPostgres::Postgres(),
  dbname = "mortalidadCR_dev",
  host = "localhost",           # or your server IP address
  port = 5432,                  # default PostgreSQL port
  user = "postgres",
  password = pw_db  # cambiar
)

# importa los datos y los limpia un poco
datos_df <- dbGetQuery(con, query_string)

# rescala los años a uno para no terminar con un intercepto ridículo en el años cero absoluto.
min_anho <-min(datos_df$anho)
datos_df$anho <-as.integer(datos_df$anho-min_anho+1)

# resumen de conteos por provincia, cantón y distrito
count_df <- datos_df %>%
  group_by(cod_distrito, distrito_nombre,cod_canton,canton_nombre,provincia_nombre) %>%
  summarise(n_years =n()) %>%
  as.data.frame()

write.csv(count_df, file.path(result_directory,'frequencia_anho_pordistrito.csv'))
cod_distritos_bajo_n <- as.vector(count_df$cod_distrito[count_df$n_years<6])


# excluye distritos con menos de 6 años de datos
# excluye distritos cabecera y urbanos con mortalidades muy altas
datos_df <- datos_df %>%
  filter(!cod_distrito %in% cod_distritos_bajo_n) %>%
  as.data.frame()


# Gráfico de la relación población y mortalidad por distrito
ggplot(data = datos_df, aes(x = poblacion_total, y = defunciones_total)) +
  facet_wrap(~I(anho+min_anho-1))+
  geom_point(size = 1.5, color='blue') +
  geom_smooth(method = "lm", color='red')+
  labs(
x = "Población",
title = "Relación entre mortalidad y población a nivel de distrito",
    y = "Defunciones")+
  theme_bw()+
  theme(strip.text = element_text(size=12, face='bold'),
axis.text = element_text(size=8),
axis.title=element_text(size=12))
ggsave(file.path(result_directory,'relacion_mortalidadypoblacion_distrito.png'))

 
# calcula muertes por cada cien mil habitantes
datos_df$def_100mil <- (datos_df$defunciones_total/datos_df$poblacion_total)*100000

# exploración de datos

# histograma defunciones por cien mil habitantes
ggplot(data = datos_df, aes(x=def_100mil)) +
  facet_wrap(~(anho+min_anho-1))+
  geom_histogram(fill='blue', col='black') +
  labs(
x = "Defunciones por cient mil habitantes",
y="Número de distritos",
title = "Distribución de la mortalidad a nivel de distrito")+
  theme_bw()+
  theme(strip.text = element_text(size=12, face='bold'),
axis.text = element_text(size=10),
axis.title=element_text(size=12))
ggsave(file.path(result_directory,'histograma_defuncionespercapitaporDistritoanho.png'))

# Mortalidad por distrito, 2013 a 2024
ggplot(data = datos_df, aes(x=as.factor(I(anho+min_anho-1)), y=def_100mil)) +
  geom_boxplot() +
  labs(
x = "Año",
title = "Mortalidad a nivel de distrito, 2013-2024",
    y = "Defunciones por cien mil habitantes")+
  theme_bw()+
  theme(strip.text = element_text(size=12, face='bold'),
axis.text = element_text(size=10),
axis.title=element_text(size=12))
ggsave(file.path(result_directory,'boxplot_defuncionespercapitaporanho.png'))

# Crea tabla resumen por distrito

resumen_distrito_df <- datos_df %>%
  group_by(cod_distrito) %>%
  summarise(
defunciones_total_prom = mean(defunciones_total, na.rm = TRUE),
defunciones_total_med = median(defunciones_total, na.rm = TRUE),
poblacion_total_prom = mean(poblacion_total, na.rm = TRUE),
poblacion_total_med = median(poblacion_total, na.rm = TRUE),
def100mil_total_prom = mean(def_100mil, na.rm = TRUE),
def100mil_total_med = median(def_100mil, na.rm = TRUE)
) %>% 
  mutate(across(where(is.numeric), round, digits = 2)) %>%
as.data.frame()


# salva la tabla en la base de datos
dbWriteTable(
  conn      = con, 
  name      = "resumen_mortalidad_distrito", 
  value     = resumen_distrito_df, 
  append    = TRUE,           # Append data to the existing table
  overwrite = FALSE,          # Do not drop or replace the table
  row.names = FALSE           # Do not write row numbers as a column
)

# # testing a linear mixed model to 
hist(datos_df$def_100mil)
hist(log(datos_df$def_100mil+35))

min(datos_df$def_100mil)


# columna con nombre completo de cantón
datos_df$canton_nombre2 <-paste(datos_df$cod_canton,datos_df$canton_nombre,sep='-')
datos_df$distrito_nombre2 <-paste(datos_df$cod_distrito,datos_df$distrito_nombre,sep='-')

# Consideramos dos modelos por simplicidad. Se excluye un tercer model con la interacción canton y año
# por su difícil interpretación

distrito_modelo1 <- lmer(def_100mil~anho +(anho|distrito_nombre2),data=datos_df)
distrito_modelo2 <- lmer(def_100mil~canton_nombre2+anho +(anho|distrito_nombre2),data=datos_df)


# Comparamos cuál modelo es más parsimonioso
AICc(distrito_modelo1,distrito_modelo2)
# y exploramos su capacidad predictiva
model_performance(distrito_modelo2)

# el modelo con el factor de cantón y año es escogido
distrito_modelo <-distrito_modelo2

summary(distrito_modelo2)


options(max.print=5.5E5)
summary(distrito_modelo)

# Valoramos la calidad del modelo.
# Tiene cierto problemas, especialmente en las colas
simulate_model1 <- simulateResiduals(distrito_modelo)
residual_simple_model1 <-residuals(distrito_modelo)


png(file.path(result_directory,'QualityPlots_LinearMixedModel.png'))
plot(simulate_model1)
dev.off()

png(file.path(result_directory,'histogram_LinearMixedModel.png'))
hist(simulate_model1)
dev.off()


# Creamos las predicciones.
pred_df <- datos_df[,c('cod_distrito','cod_canton','provincia_nombre','canton_nombre2', 'distrito_nombre2','anho', 'def_100mil')]
pred_df$y_w <- predict(distrito_modelo, 
  newdata = datos_df,
re.form=NULL)
pred_df$y_w0 <- predict(distrito_modelo, 
  newdata = datos_df,
re.form=NA)

# Comparamos entradas y predicciones.
ggplot(data = pred_df, aes(x=def_100mil, y = y_w)) +
  geom_point(size = 1.5) +
  geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "red")+
  labs(
x = "Mortalidad observada (defunciones/100 mil habitantes",
    y = "Mortalidad predecidad (defunciones/100 mil habitantes")+
  theme_bw()+
  theme(strip.text = element_text(size=10, face='bold'),
axis.text = element_text(size=10),
axis.title=element_text(size=12))
ggsave(file.path(result_directory,paste0('observados_vrs_predicciones','.png')))


# gráfico de predicciones
# añade número serial por cantón para facilitar los gráficos

# Add group-wise serial number

# cantones_df <-unique(pred_df[,c('cod_canton', 'cod_distrito')])

# cantones_df <- cantones_df %>%
#   group_by(cod_canton) %>%
#   mutate(cod_dist_serial = row_number()) %>%
#   ungroup() %>%
#   as.data.frame()

# pred_df <-merge(pred_df,
# cantones_df[c('cod_canton','cod_distrito','cod_dist_serial')],
# by=c('cod_canton','cod_distrito'))



# gráficos de predicciones agrupados por cantones
cantones_directory <-file.path(result_directory,'cantones')
if (!dir.exists(cantones_directory)){
  dir.create(cantones_directory)
}

# por conveniencia, se agrupan los cantones por provincia


for (provincia_i in unique(pred_df$canton_nombre2)){

  esta_provincia_df <- pred_df[pred_df$canton_nombre2==provincia_i,]

  esta_provincia_df$anho <-esta_provincia_df$anho+min_anho-1

  ggplot(data = esta_provincia_df, aes(x = anho, y = def_100mil, col=distrito_nombre2)) +
  geom_point(size = 1.5) +
  geom_line(aes(y=y_w, x=anho, data=esta_provincia_df), show.legend = FALSE )+
  geom_line(aes(y=y_w0, x=anho, data=esta_provincia_df), color='black', show.legend = FALSE )+
  labs(
x = "Año",
title = paste0('Mortalidad por año y distrito. Cantón: ',provincia_i),
    y = "Defunciones por cien mil habitantes",
  color='Distrito')+
  theme_bw()+
  theme(strip.text = element_text(size=10, face='bold'),
axis.text = element_text(size=10),
axis.title=element_text(size=12))+
scale_x_continuous(breaks = seq(min(esta_provincia_df$anho),max(esta_provincia_df$anho),2))
ggsave(file.path(cantones_directory,paste0('xyplot_mortalidadAnho_',provincia_i,'.png')))

}

# Salva los resultados

# extrae pendientes e interceptos del componente aleatorio del modelo
llm_random_df <-broom.mixed::tidy(distrito_modelo, effects='ran_vals', conf.int=TRUE)
# extrae los componentes fijos del model.
llm_fixed_df <-broom.mixed::tidy(distrito_modelo, conf.int=TRUE)

print(llm_fixed_df)

# limpia un poco las columnas
llm_fixed_df$term <- str_remove(llm_fixed_df$term,"canton_nombre2")
llm_fixed_df$group[llm_fixed_df$term=='anho'] <-'pendiente anho'
llm_fixed_df$group[is.na(llm_fixed_df$group)] <-'cantón'



# extrae estadísticas del componente aleatorio del modelo
llm_random2_df <-broom.mixed::tidy(distrito_modelo, effects = "ran_pars", scales = "vcov")

# salva los distintos grupos de parámetros extraídos del modelo
write.csv(llm_random_df, file.path(result_directory,'linearmixedmodel_random_parameters.csv'))
write.csv(llm_fixed_df, file.path(result_directory,'linearmixedmodel_fixed_parameters.csv'))
write.csv(llm_random2_df, file.path(result_directory,'linearmixedmodel_random_stats.csv'))

# Salva los datos que ayudan a valorar la calidad del modelo
write.csv(as.data.frame(model_performance(distrito_modelo)), 
file.path(result_directory,'linearmixedmodel_fixed_GOF.csv'))



# tabla resumen con parámetros del modelo para visualizar los resultados

# Salva indicadores distritales extraídos del model

# primero utilizamos la predicción de defunciones al año (2013 a 2024) como indicador del nivel de mortalidad
resumen_modelo_df <- pred_df %>%
  group_by(cod_distrito) %>%
  summarise(def_100mil_promedio = mean(y_w, na.rm=TRUE)) %>%
  as.data.frame()

# luego extraemos las pendientes aleatorias asociadas a cada distrito. Limpiamos las columnas
pendiente_df <- llm_random_df[llm_random_df$term=='anho',c('level', 'estimate','std.error')]
pendiente_df$cod_distrito <- as.integer(substr(pendiente_df$level, 1, 5))
names(pendiente_df) <-c('term','pendiente','error_estandar', 'cod_distrito')

# luego calculamos una tasa de incremento anual (defunciones por 100 mil habitantes/año)
# esta la definimos como pendiente_corregida=pendiente_aleatorio_distrital+pendiente_fijo_anho
# pendiente_alazar_distrital es la pendiente asociada al componente aleatorio distrital del model, mientras que
# pendiente_fijo_anho es la pendiente controlada del año.

pendiente_df$pendiente_corregida <- llm_fixed_df$estimate[llm_fixed_df$group=='pendiente anho']+pendiente_df$pendiente

resumen_modelo_df <-merge(resumen_modelo_df,
  pendiente_df[,c('pendiente', 'pendiente_corregida', 'error_estandar', 'cod_distrito')],
  by='cod_distrito')

# salva la tabla en la base de datos. Ya la tabla estaba lista
dbWriteTable(
  conn      = con, 
  name      = "parametros_modelo_linealmixto_distrito", 
  value     = resumen_modelo_df, 
  append    = TRUE,           # Append data to the existing table
  overwrite = FALSE,          # Do not drop or replace the table
  row.names = FALSE           # Do not write row numbers as a column
)

# # cierra la conexión con la base de datos
dbDisconnect(con)
# hist(resumen_modelo_df$def_100mil_promedio)
# quantile(resumen_modelo_df$def_100mil_promedio)


# hist(resumen_modelo_df$pendiente_corregida)
# quantile(resumen_modelo_df$pendiente_corregida)

plot(resumen_modelo_df$def_100mil_promedio[resumen_modelo_df$def_100mil_promedio<1500],
   resumen_modelo_df$pendiente_corregida[resumen_modelo_df$def_100mil_promedio<1500])


