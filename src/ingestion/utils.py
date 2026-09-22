import pandas as pd
import zipfile

def explore_columns(raw_data_path):
    with zipfile.ZipFile(raw_data_path) as file:
        archive = file.infolist()
        csv_files = []
        for single_file in archive:
            if single_file.filename.endswith(".csv"): 
                csv_files.append(single_file)
        return csv_files

def print_df(df, nb_row=5, nom_col=None):
    if nom_col is None :
        print(df.head(nb_row))
        return
    df_filtre = df[nom_col]
    print(df_filtre.head(nb_row))
    return