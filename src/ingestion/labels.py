import pandas as pd
import zipfile
import utils
import datetime as dt
import numpy as np


def filtre_siret(historic_csv_file, liste_siret_cafes):
    all_siret = historic_csv_file[(historic_csv_file['siret'].isin(liste_siret_cafes))]
    return all_siret 


def build_label(data_path, liste_siret_cafes):
    liste_totale = []
    count = 0
    
    csv_files = utils.explore_columns(data_path)
    
    with zipfile.ZipFile(data_path).open(csv_files[0]) as file:
        reader = pd.read_csv(file, chunksize=100000, dtype=str)
        for chunk in reader:
            chunk_filtre = filtre_siret(chunk, liste_siret_cafes)
            liste_totale.append(chunk_filtre)
            print(f"chunk {count} processed")
            count += 1
    
    df_final = pd.concat(liste_totale)
    return df_final

def build_chaine_label(df):
    df['nb_etablissement_siren'] = df.groupby('siren')['siret'].transform('count')
    df['est_chaine'] = df['nb_etablissement_siren'] > 1
    return df


def main():
    historic_raw_data_path = '/Users/mathis.gj/paris-coffee-place/data/raw/siren-historic.zip'
    actual_processed_data_path = '/Users/mathis.gj/paris-coffee-place/data/processed/siren-actual-processed.parquet'
    processed_path = '/Users/mathis.gj/paris-coffee-place/data/processed/cafe-labeled.parquet'
    cafe_labeled_data = '/Users/mathis.gj/paris-coffee-place/data/processed/cafe-labeled-chaine.parquet'
    fixed_datetime = dt.datetime(2026, 9, 1, 0, 0, 0)
    
    # actual_df = pd.read_parquet(actual_processed_data_path)
    # liste_siret_cafes = actual_df['siret'].tolist()
    
    # df_labels = build_label(historic_raw_data_path, liste_siret_cafes)
    # print(len(df_labels))
    # df_labels = df_labels[(df_labels['etatAdministratifEtablissement'] == 'F') 
    #                     & (df_labels['changementEtatAdministratifEtablissement'] == 'true')
    #                     ].groupby('siret')['dateDebut'].min().reset_index().rename(columns={'dateDebut': 'dateFermeture'})
    # print(len(df_labels))
    
    # df_global = actual_df.merge(df_labels, on='siret', how='left')

    # df_global['dateCreationEtablissement'] = pd.to_datetime(df_global['dateCreationEtablissement'])
    # df_global['duree_annee_observee'] = np.where(df_global['etatAdministratifEtablissement'] == 'F', 
    #                             (pd.to_datetime(df_global['dateFermeture']) - df_global['dateCreationEtablissement']).dt.days/365.25,
    #                             (fixed_datetime - df_global['dateCreationEtablissement']).dt.days/365.25)
    # df_global['survecu_2ans'] = df_global['duree_annee_observee'] >= 2
    
    # df_global['survecu_2ans'] = np.where((df_global['duree_annee_observee'] < 2) & (df_global['etatAdministratifEtablissement'] == 'A')
    #                                     | ((df_global['etatAdministratifEtablissement'] == 'F') & df_global['dateFermeture'].isna()),
    #                             np.nan,
    #                             df_global['survecu_2ans'])
    
    # df_global = df_global.dropna(subset=['survecu_2ans'])
    
    df_global = pd.read_parquet(processed_path)
    print("vérif mislabeling : ")
    print(len(df_global[(df_global['etatAdministratifEtablissement'] == 'F') & (df_global['dateFermeture'].isna())]))
    print(df_global[df_global['dateFermeture'].notna()][['dateDebut', 'dateFermeture']].head())
    print(df_global['survecu_2ans'].value_counts())
    
    df_global = build_chaine_label(df_global)
    print(df_global['est_chaine'].value_counts())
    
    df_global.to_parquet(cafe_labeled_data)


if __name__ == '__main__': main()