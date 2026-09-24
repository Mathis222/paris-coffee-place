import pandas as pd
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'.', 'ingestion'))
import utils
from sklearn.model_selection import train_test_split


def final_df(cafe_data_path, loc_data_path, final_data_path):
    df_cafe = pd.read_parquet(cafe_data_path)
    df_loc = pd.read_parquet(loc_data_path)
    df_cafe_slim = df_cafe[['siret', 'survecu_2ans','est_chaine']]
    df_loc_slim = df_loc[['siret', 'x_cafe', 'y_cafe', 'dist_station_proche', 'trafic_station_proche', 'nb_voisin_200', 'nb_voisin_500', 'nb_tourism_200', 'nb_tourism_500', 'dist_tourism_proche']]
    
    df_global = df_cafe_slim.merge(df_loc_slim, on='siret', how='inner')
    df_global.to_parquet(final_data_path)


def main():
    cafe_data_path = '/Users/mathis.gj/paris-coffee-place/data/processed/cafe-labeled-chaine.parquet'
    loc_data_path = '/Users/mathis.gj/paris-coffee-place/data/processed/siren-neighbors-processed.parquet'
    final_data_path = '/Users/mathis.gj/paris-coffee-place/data/processed/final-processed.parquet'
    
    df = pd.read_parquet(final_data_path)

    X = df[['est_chaine', 'dist_station_proche', 'trafic_station_proche', 'nb_voisin_200', 'nb_voisin_500', 'nb_tourism_200', 'nb_tourism_500', 'dist_tourism_proche']]
    y = df['survecu_2ans']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    print(len(X_train), len(X_test))
    print(y_train.value_counts(normalize=True))
    print(y_test.value_counts(normalize=True))

if __name__ == "__main__": main()