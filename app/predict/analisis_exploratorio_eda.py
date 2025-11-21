
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def preparar_df_enriquecido(graficar=True):
    # Cargar el nuevo dataset anual
    df = pd.read_csv('datos_simulados_ML_anual.csv')

    # Convertir timestamp a tipo datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp_reposicion']):
        df['timestamp_reposicion'] = pd.to_datetime(df['timestamp_reposicion'])

    # Extraer variables temporales
    if 'hora' not in df.columns:
        df['hora'] = df['timestamp_reposicion'].dt.hour
    if 'dia_semana' not in df.columns:
        df['dia_semana'] = df['timestamp_reposicion'].dt.day_name()
    df['mes'] = df['timestamp_reposicion'].dt.month
    # Calcular semana del mes
    if 'dia_del_mes' not in df.columns:
        df['dia_del_mes'] = df['timestamp_reposicion'].dt.day
    df['semana_mes'] = (df['dia_del_mes'] - 1) // 7 + 1

    # EDA: Análisis exploratorio
    import __main__
    if graficar and (__main__.__file__ == __file__):
        print('Primeras filas:')
        print(df.head())
        print('\nInformación general:')
        print(df.info())
        print('\nValores nulos por columna:')
        print(df.isnull().sum())
        print('\nEstadísticas descriptivas:')
        print(df.describe(include='all'))
        print('\nDistribución de categorías:')
        print(df['categoria_producto'].value_counts())
        print('\nDistribución de etiqueta de reposición:')
        print(df['etiqueta_reposicion'].value_counts(normalize=True))

    if graficar:
        # Visualizaciones básicas
        plt.figure(figsize=(10,4))
        sns.countplot(x='categoria_producto', data=df)
        plt.title('Frecuencia por categoría de producto')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

        plt.figure(figsize=(8,4))
        sns.countplot(x='mes', data=df)
        plt.title('Reposiciones por mes')
        plt.tight_layout()
        plt.show()

        plt.figure(figsize=(8,4))
        sns.countplot(x='dia_semana', data=df, order=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
        plt.title('Reposiciones por día de la semana')
        plt.tight_layout()
        plt.show()

        plt.figure(figsize=(8,4))
        sns.countplot(x='hora', data=df)
        plt.title('Reposiciones por hora')
        plt.tight_layout()
        plt.show()

    return df
