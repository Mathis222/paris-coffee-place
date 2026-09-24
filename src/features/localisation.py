import pandas as pd
import numpy as np
from scipy.spatial import KDTree
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'..', 'ingestion'))
import utils


def main():
    ratp_processed_data_path = '/Users/mathis.gj/paris-coffee-place/data/processed/ratp-processed.parquet'
    siren_actual_processed_data_path = '/Users/mathis.gj/paris-coffee-place/data/processed/siren-actual-processed.parquet'
    siren_neighbors_processed_data_path = '/Users/mathis.gj/paris-coffee-place/data/processed/siren-neighbors-processed.parquet'
    tourism_processed_data_path = '/Users/mathis.gj/paris-coffee-place/data/processed/tourism-processed.parquet'
    
    df_ratp = pd.read_parquet(ratp_processed_data_path)
    df_siren = pd.read_parquet(siren_actual_processed_data_path)
    df_siren['coordonneeLambertAbscisseEtablissement'] = pd.to_numeric(df_siren['coordonneeLambertAbscisseEtablissement'], errors='coerce')
    df_siren['coordonneeLambertOrdonneeEtablissement'] = pd.to_numeric(df_siren['coordonneeLambertOrdonneeEtablissement'], errors='coerce')
    df_siren = df_siren.dropna(subset=['coordonneeLambertAbscisseEtablissement', 'coordonneeLambertOrdonneeEtablissement'])
    df_siren = df_siren.rename(columns={
        'coordonneeLambertAbscisseEtablissement': 'x_cafe',
        'coordonneeLambertOrdonneeEtablissement': 'y_cafe'
    })
    df_ratp = df_ratp.rename(columns={
        'x': 'x_station',
        'y': 'y_station'
    })
    
    station_coords = df_ratp[['x_station', 'y_station']].to_numpy()
    cafe_coords = df_siren[['x_cafe', 'y_cafe']].to_numpy()
    tree_station = KDTree(station_coords)
    distances, indices = tree_station.query(cafe_coords)
    
    df_siren['dist_station_proche'] = distances
    df_siren['trafic_station_proche'] = df_ratp['trafic'].iloc[indices].to_numpy()
    
    tree_cafe = KDTree(cafe_coords)
    
    neighbors_200 = tree_cafe.query_ball_point(cafe_coords,r=200)
    neighbors_500 = tree_cafe.query_ball_point(cafe_coords,r=500)
    df_siren['nb_voisin_200'] = [len(n) - 1 for n in neighbors_200]
    df_siren['nb_voisin_500'] = [len(n) - 1 for n in neighbors_500]
    utils.print_df(df_siren, nom_col = ['nb_voisin_200', 'nb_voisin_500'])
    
    
    df_tourism = pd.read_parquet(tourism_processed_data_path)
    tourism_coords = df_tourism[['x_tourism', 'y_tourism']].to_numpy()
    
    tree_tourism = KDTree(tourism_coords)
    
    distances_tourism, indices_tourism = tree_tourism.query(cafe_coords)
    tourism_200 = tree_tourism.query_ball_point(cafe_coords,r=200)
    tourism_500 = tree_tourism.query_ball_point(cafe_coords,r=500)
    df_siren['nb_tourism_200'] = [len(n) for n in tourism_200]
    df_siren['nb_tourism_500'] = [len(n) for n in tourism_500]
    df_siren['dist_tourism_proche'] = distances_tourism
    
    utils.print_df(df_siren, nom_col = ['nb_tourism_200', 'nb_tourism_500'])
    
    df_siren.to_parquet(siren_neighbors_processed_data_path)


if __name__ == '__main__': main()