"""Entrenamiento OFFLINE del modelo de duración de procedimientos.

Se ejecuta en la laptop (o en Colab), NO en el servidor. Produce un archivo
`models/modelo_duracion.joblib` que la aplicación web carga para inferencia ligera.

Uso:
    python entrenar.py --datos data/citas.csv
"""
import argparse
import joblib
import pandas as pd
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

CATEGORICAS = ['tipo_procedimiento', 'odontologo', 'dia_semana']
NUMERICAS = ['hora_inicio']
OBJETIVO = 'duracion_real'


def main(ruta_datos: str):
    df = pd.read_csv(ruta_datos)
    X = df[CATEGORICAS + NUMERICAS]
    y = df[OBJETIVO]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    pre = ColumnTransformer([('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAS)],
                            remainder='passthrough')
    modelo = Pipeline([('pre', pre),
                       ('rf', RandomForestRegressor(n_estimators=200, random_state=42))])
    modelo.fit(X_tr, y_tr)

    pred = modelo.predict(X_te)
    print(f"MAE : {mean_absolute_error(y_te, pred):.2f} min")
    print(f"RMSE: {mean_squared_error(y_te, pred) ** 0.5:.2f} min")
    print(f"R2  : {r2_score(y_te, pred):.3f}")

    Path('models').mkdir(exist_ok=True)
    joblib.dump(modelo, 'models/modelo_duracion.joblib')
    print("Modelo guardado en models/modelo_duracion.joblib")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--datos', default='data/citas.csv')
    main(ap.parse_args().datos)
