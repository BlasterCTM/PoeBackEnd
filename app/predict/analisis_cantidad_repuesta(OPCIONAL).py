import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Cargar el dataset crudo
ruta = 'datos_simulados_ML_anual.csv'
df = pd.read_csv(ruta)

# Filtrar solo donde hubo reposición
df_repos = df[df['etiqueta_reposicion'] == 1]

# Estadísticas descriptivas
print('Estadísticas de cantidad_repuesta (solo reposiciones):')
print(df_repos['cantidad_repuesta'].describe())
print('\nDistribución por categoría:')
print(df_repos.groupby('categoria_producto')['cantidad_repuesta'].describe())

# Histograma global
plt.figure(figsize=(8,4))
sns.histplot(df_repos['cantidad_repuesta'], bins=30, kde=True)
plt.title('Histograma de cantidad_repuesta (solo reposiciones)')
plt.xlabel('Cantidad repuesta')
plt.ylabel('Frecuencia')
plt.tight_layout()
plt.show()

# Boxplot por categoría
plt.figure(figsize=(10,5))
sns.boxplot(x='categoria_producto', y='cantidad_repuesta', data=df_repos)
plt.title('Boxplot de cantidad_repuesta por categoría')
plt.xlabel('Categoría de producto')
plt.ylabel('Cantidad repuesta')
plt.tight_layout()
plt.show()
