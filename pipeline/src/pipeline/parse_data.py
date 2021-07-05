from azure.storage.blob import BlobServiceClient, BlobClient
import logging
import os
import ssl
import ast
import pandas as pd
import numpy as np
from utils import clean_text, translate_dataframe, geolocate_dataframe, filter_by_keywords, get_blob_service_client


def parse_data(keywords):

    # load and parse tweets
    twitter_data_path = "./twitter"
    tweets_path = twitter_data_path + "/tweets_latest.csv"
    df_tweets = pd.read_csv(tweets_path)
    df_tweets['user'] = df_tweets['user'].astype(str).apply(ast.literal_eval)
    df_tweets['source'] = df_tweets['user'].apply(lambda x: x['name'])
    df_tweets['screen_name'] = df_tweets['user'].apply(lambda x: x['screen_name'])
    df_tweets['entities'] = df_tweets['entities'].astype(str).apply(ast.literal_eval)
    df_tweets['url'] = df_tweets['entities'].apply(get_url_from_entities)
    df_tweets['twitter_url'] = df_tweets.apply(get_url_from_tweet, axis=1)
    df_tweets['url'] = df_tweets['url'].fillna(df_tweets['twitter_url'])
    df_tweets = df_tweets.drop(columns={'entities', 'screen_name', 'twitter_url', 'user', 'extended_entities'})

    # if retweet, get full text of original tweet
    df_tweets['full_text'] = df_tweets.apply(get_retweet, axis=1)
    # clean text (if in english)
    df_tweets['full_text'] = df_tweets.apply(clean_text, args=('full_text',), axis=1)

    # translate tweets
    df_tweets = translate_dataframe(df_tweets, 'full_text')

    # filter by keywords
    df_tweets = filter_by_keywords(df_tweets, ['full_text'], keywords)
    out_dir_filter = 'tweets_processed/tweets_latest_filtered.csv'
    df_tweets.to_csv(out_dir_filter, index=False)

    location_file = r"vector/eth_admbnda_admALL_simple.shp"
    adm0_file = r"vector/eth_admbnda_adm0_csa_bofed_20201008.shp"
    df_tweets = geolocate_dataframe(df_tweets, location_file, adm0_file, ['full_text'], 'place')

    # save processed tweets
    processed_tweets_path = twitter_data_path + "/tweets_latest_processed.csv"
    df_tweets.to_csv(processed_tweets_path, index=False)

    # upload to datalake
    blob_client = get_blob_service_client('twitter/tweets_latest_processed.csv')
    with open(processed_tweets_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    # append to existing twitter dataframe
    tweets_all_path = twitter_data_path + "/tweets_all_processed.csv"
    try:
        with open(tweets_all_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
        if not os.path.exists(tweets_all_path):
            logging.warning("No older processed tweets found")
        df_old_tweets = pd.read_csv(tweets_all_path, lines=True)
        df_all_tweets = df_old_tweets.append(df_tweets, ignore_index=True)
    except:
        df_all_tweets = df_tweets.copy()

    # drop duplicates and save
    df_all_tweets = df_all_tweets.drop_duplicates(subset=['id'])
    df_all_tweets.to_csv(tweets_all_path, index=False)

    # upload to datalake
    blob_client = get_blob_service_client('twitter/tweets_all_processed.csv')
    with open(tweets_all_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    ####################################################################################################################

    # load and parse youtube
    youtube_data_path = "./youtube"
    videos_path = youtube_data_path + "/videos_latest.csv"
    df_videos = pd.read_csv(videos_path)
    df_videos['user'] = df_videos['user'].astype(str).apply(ast.literal_eval)
    df_videos['source'] = df_videos['user'].apply(lambda x: x['name'])
    df_videos['screen_name'] = df_videos['user'].apply(lambda x: x['screen_name'])
    df_videos['entities'] = df_videos['entities'].astype(str).apply(ast.literal_eval)
    df_videos['url'] = df_videos['entities'].apply(get_url_from_entities)
    df_videos['youtube_url'] = df_videos.apply(get_url_from_tweet, axis=1)
    df_videos['url'] = df_videos['url'].fillna(df_videos['youtube_url'])
    df_videos = df_videos.drop(columns={'entities', 'screen_name', 'youtube_url', 'user', 'extended_entities'})

    # if retweet, get full text of original tweet
    df_videos['full_text'] = df_videos.apply(get_retweet, axis=1)
    # clean text (if in english)
    df_videos['full_text'] = df_videos.apply(clean_text, args=('full_text',), axis=1)

    # translate videos
    df_videos = translate_dataframe(df_videos, 'full_text')

    # filter by keywords
    df_videos = filter_by_keywords(df_videos, ['full_text'], keywords)
    out_dir_filter = 'videos_processed/videos_latest_filtered.csv'
    df_videos.to_csv(out_dir_filter, index=False)

    location_file = r"vector/eth_admbnda_admALL_simple.shp"
    adm0_file = r"vector/eth_admbnda_adm0_csa_bofed_20201008.shp"
    df_videos = geolocate_dataframe(df_videos, location_file, adm0_file, ['full_text'], 'place')

    # save processed videos
    processed_videos_path = youtube_data_path + "/videos_latest_processed.csv"
    df_videos.to_csv(processed_videos_path, index=False)

    # upload to datalake
    blob_client = get_blob_service_client('youtube/videos_latest_processed.csv')
    with open(processed_videos_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    # append to existing twitter dataframe
    videos_all_path = twitter_data_path + "/videos_all_processed.csv"
    try:
        with open(videos_all_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
        if not os.path.exists(videos_all_path):
            logging.warning("No older processed videos found")
            df_old_videos = pd.read_csv(videos_all_path, lines=True)
            df_all_videos = df_old_videos.append(df_videos, ignore_index=True)
    except:
        df_all_videos = df_videos.copy()

    # drop duplicates and save
    df_all_videos = df_all_videos.drop_duplicates(subset=['id'])
    df_all_videos.to_csv(videos_all_path, index=False)

    # upload to datalake
    blob_client = get_blob_service_client('youtube/videos_all_processed.csv')
    with open(videos_all_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    ####################################################################################################################

    # merge everything
    merged_data_path = "./merged"
    os.makedirs(merged_data_path, exist_ok=True)
    merged_path = merged_data_path + "/merged_latest.csv"

    df_all_videos = df_all_videos.rename(columns={'title': 'full_text'})
    df_merged = df_all_tweets.append(df_all_videos, ignore_index=True)
    df_merged.to_csv(merged_path, index=False)

    # upload to datalake
    blob_client = get_blob_service_client('merged/merged_all.csv')
    with open(merged_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
