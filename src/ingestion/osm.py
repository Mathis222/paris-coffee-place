import pandas as pd
import osmnx
import utils
import geopandas as gpd


def main():
    tourism_processed_data_path = '/Users/mathis.gj/paris-coffee-place/data/processed/tourism-processed.parquet'
    
    df_tourism = osmnx.features_from_place(
        "Paris, France",
        tags={
            'tourism': ['hotel', 'museum', 'attraction', 'artwork', 'viewpoint'],
            'historic': ['monument', 'memorial', 'castle']
        })
    
    df_tourism_filter = df_tourism[['geometry', 'tourism', 'historic']]
    df_tourism_filter['geometry'] = df_tourism_filter.geometry.to_crs(epsg=2154).centroid
    df_tourism_filter['x_tourism'], df_tourism_filter['y_tourism'] = df_tourism_filter['geometry'].x, df_tourism_filter['geometry'].y
    df_tourism_filter = df_tourism_filter.drop(columns=['geometry'])
    
    df_tourism_filter.to_parquet(tourism_processed_data_path)

if __name__ == '__main__': main()