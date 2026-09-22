import pandas as pd
import zipfile
import utils


def read_csv(raw_data_path, csv_file):
    with zipfile.ZipFile(raw_data_path).open(csv_file) as file:
        chunk = next(pd.read_csv(file, chunksize=100000, dtype=str))
        print(chunk.columns)
        print(chunk['etatAdministratifEtablissement'].unique())
        print(pd.to_datetime(chunk['dateDebut']).max())
        return chunk


def filtre_paris_cafe(csv_file):
    return(csv_file[(csv_file['activitePrincipaleEtablissement'] == '56.30Z')
                    & (csv_file['codeCommuneEtablissement'].str.startswith('75'))])


def build_cafe_paris_dataset(data_path):
    liste_totale = []
    count = 0
    
    csv_files = utils.explore_columns(data_path)
    
    with zipfile.ZipFile(data_path).open(csv_files[0]) as file:
        reader = pd.read_csv(file, chunksize=100000, dtype=str)
        for chunk in reader:
            chunk_filtre = filtre_paris_cafe(chunk)
            liste_totale.append(chunk_filtre)
            print(f"chunk {count} processed")
            count += 1
    
    df_final = pd.concat(liste_totale)
    return df_final


def main():
    actual_raw_data_path = '/Users/mathis.gj/paris-coffee-place/data/raw/siren-actual.zip'
    processed_path = '/Users/mathis.gj/paris-coffee-place/data/processed/siren-actual-processed.parquet'
    
    # csv_files = explore_columns(actual_raw_data_path)
    # for csv_info in csv_files:
    #     chunk = read_csv(actual_raw_data_path, csv_info.filename)
    #     chunk_filtre = filtre_paris_cafe(chunk)
    #     print(len(chunk))
    #     print(len(chunk_filtre))
        
    #     utils.print_df(chunk_filtre, 10, ['siren', 'siret', 'dateDebut', 'codeCommuneEtablissement', 'etatAdministratifEtablissement'])
    df_processed = build_cafe_paris_dataset(actual_raw_data_path)
    print(len(df_processed))
    df_processed.to_parquet(processed_path)


if __name__ == '__main__': main()