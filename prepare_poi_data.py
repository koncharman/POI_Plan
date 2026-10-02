

import json
import pandas as pd
import datetime as dt
def prepare_main_poi_data(file_path="data/corfu_dataset.json"):

    with open(file_path, "r", encoding="utf-8") as f:
        data_corfu = json.load(f)

    poi_df = {"id": [], "name": [], "area": [], 'category': [],
              'loc_lat': [], 'loc_long': [],
              "description": [], 'setting': [], 'suggested_visit_minutes': [], 'family_suitability_fixture': []}

    tag_df = {"id": [], "tag": []}

    fixture_df = {"id": [], "Day": [], "Start": [], "End": []}

    #Used for testing
    #fixt_info = [len(i["opening_hours_fixture"]) if i["opening_hours_fixture"] is not None else 0 for i in data_corfu["pois"]]

    days_list = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

    for i in data_corfu['pois']:

        ###Record main information
        for k, v in poi_df.items():
            if k == 'loc_lat':
                poi_df[k].append(i['location']['latitude'])
            elif k == 'loc_long':
                poi_df[k].append(i['location']['longitude'])
            else:
                poi_df[k].append(i[k])

        ###Record Tags
        if len(i['tags']) > 0:
            for j in i['tags']:
                tag_df['id'].append(i['id'])
                tag_df['tag'].append(j)

        ####Record Opening Hours
        if i['opening_hours_fixture'] != None:

            if len(i['opening_hours_fixture']) > 0:
                for k, v in i["opening_hours_fixture"].items():

                    fixture_df['id'].append(i['id'])
                    fixture_df['Day'].append(k)

                    if v != None:
                        split_time = v.split("-")
                        fixture_df['Start'].append(split_time[0])
                        fixture_df['End'].append(split_time[1])
                    else:
                        fixture_df['Start'].append(None)
                        fixture_df['End'].append(None)
        else:
            for d in days_list:
                fixture_df['id'].append(i['id'])
                fixture_df['Day'].append(d)
                fixture_df['Start'].append(None)
                fixture_df['End'].append(None)

    poi_df = pd.DataFrame(poi_df)
    poi_df['name']=poi_df['name'].apply(lambda k:k.lower())
    poi_df['area']=poi_df['area'].apply(lambda k:k.lower())
    poi_df['category']=poi_df['category'].apply(lambda k:k.lower())
    poi_df['description']=poi_df['description'].apply(lambda k:k.lower())
    poi_df['setting']=poi_df['setting'].apply(lambda k:k.lower())


    tag_df = pd.DataFrame(tag_df)
    tag_df['tag']=tag_df['tag'].apply(lambda k:k.lower())

    fixture_df = pd.DataFrame(fixture_df)
    fixture_df["Start"] = fixture_df["Start"].replace("24:00", "00:00")
    fixture_df["End"] = fixture_df["End"].replace("24:00", "00:00")
    fixture_df["Start"] = pd.to_datetime(fixture_df["Start"], format="mixed").dt.time
    fixture_df["End"] = pd.to_datetime(fixture_df["End"], format="mixed").dt.time

    fixture_df.loc[fixture_df["End"]==dt.time(0, 0),'End']=dt.time(23, 59,59)

    return poi_df,tag_df,fixture_df


