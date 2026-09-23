import pandas as pd
import numpy as np
import utils

def main():
    loc_data_path = '/Users/mathis.gj/paris-coffee-place/data/raw/emplacement-des-gares-idf.parquet'
    trafic_data_path = '/Users/mathis.gj/paris-coffee-place/data/raw/trafic-annuel-entrant-par-station-du-reseau-ferre-2021.parquet'
    ratp_processed_data_path = '/Users/mathis.gj/paris-coffee-place/data/processed/ratp-processed.parquet'
    
    #df_loc = utils.explore_parquet(loc_data_path)
    #df_trafic = utils.explore_parquet(trafic_data_path)
    
    df_loc = pd.read_parquet(loc_data_path)
    df_trafic = pd.read_parquet(trafic_data_path)
    
    df_loc['station_key'] = df_loc['nom_gares'].str.upper()
    #print(df_loc[df_loc['station_key'].str.startswith('GARE')]['station_key'])
    df_trafic['station_key'] = df_trafic['station'].str.upper()
    df_trafic['station_key'] = df_trafic['station_key'].str.replace('-RER', '')
    #print(df_trafic[df_trafic['station_key'].str.startswith('GARE')]['station_key'])
    
    df_global = df_loc.merge(df_trafic, on='station_key', how='left')
    
    utils.print_df(df_global, nom_col=['station_key'])
    print(df_global['reseau'].isna().sum())
    df_nan = df_global[df_global['reseau'].isna()]
    df_global = df_global.dropna(subset=['reseau'])
    df_global = df_global.groupby('station_key').agg({
        'trafic':'sum',
        'x': 'first',
        'y': 'first',
        'arrondissement_pour_paris': 'first'
    }).reset_index()
    utils.print_df(df_global)
    #utils.print_df(df_global, nom_col=['station_key'])
    #utils.print_df(df_nan, 15, nom_col=['station_key', 'nom_gares', 'reseau', 'ville'])
    
    df_global.to_parquet(ratp_processed_data_path)


if __name__ == '__main__': main()