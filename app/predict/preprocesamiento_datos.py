
from sklearn.preprocessing import LabelEncoder, StandardScaler

def preprocesar_df(df):
	# Codificar la variable categórica
	le = LabelEncoder()
	df['categoria_producto'] = le.fit_transform(df['categoria_producto'])

	# Codificar día de la semana
	le_dia = LabelEncoder()
	df['dia_semana'] = le_dia.fit_transform(df['dia_semana'])

	# Escalar variables numéricas
	scaler = StandardScaler()
	num_cols = ['ubicacion_mueble', 'hora', 'mes', 'semana_mes']
	df[num_cols] = scaler.fit_transform(df[num_cols])

	# Mostrar info solo si se solicita explícitamente
	import __main__
	if __main__.__file__ == __file__:
		print('Primeras filas del dataset preprocesado:')
		print(df.head())
	return df, le

# Ejemplo de uso: importar y procesar el dataframe enriquecido
if __name__ == "__main__":
	from analisis_exploratorio_eda import preparar_df_enriquecido
	df_enriquecido = preparar_df_enriquecido()
	df_preprocesado = preprocesar_df(df_enriquecido)
