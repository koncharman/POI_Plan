
import pandas as pd
from geopy.distance import geodesic
import numpy as np
import datetime as dt

def calculate_time_distance(la_1,lo_1,la_2,lo_2,speed=5):

    distance=geodesic(
        (la_1,lo_1),
        (la_2,lo_2)
    ).km

    minutes = (distance / speed) * 60

    return np.round(minutes,3)

def create_time_matrix(poi_df_filtered):

    loc_mat=poi_df_filtered.loc[:,["loc_lat","loc_long"]].to_numpy()

    time_mat = np.zeros((len(loc_mat), len(loc_mat)))

    for i in range(len(loc_mat)-1):
        la_i=loc_mat[i,0]
        lo_i=loc_mat[i,1]
        for j in range(i+1,len(loc_mat)):
            la_j = loc_mat[j, 0]
            lo_j = loc_mat[j, 1]

            time_temp = calculate_time_distance(la_i,lo_i,la_j,lo_j)

            time_mat[i,j]=time_temp
            time_mat[j,i]=time_temp

    return pd.DataFrame(time_mat,index=poi_df_filtered['id'],columns=poi_df_filtered['id'])


def check_new_dest(poi_df_filtered,fixture_df,id_now,day_now,time_range,time_now,dur_left):

    fixture_single = fixture_df.loc[fixture_df['id'] == id_now]
    fixture_single = fixture_single.loc[fixture_df['Day'] == day_now].iloc[0]
    poi_single = poi_df_filtered.loc[poi_df_filtered['id'] == id_now].iloc[0]

    if time_range is not None:
        if poi_single['suggested_visit_minutes']<=dur_left:

            if pd.isna(fixture_single['Start']):
                return True,f"{id_now} has NA visit times"



            if time_now.time()>=fixture_single['Start']:

                time_check = time_now + dt.timedelta(minutes=float(poi_single['suggested_visit_minutes']))
                if time_check.time()<=fixture_single['End']:
                    return True,""
                else:
                    return False,""
            else:
                return False,""

        else:
            return False,""
    else:
        if poi_single['suggested_visit_minutes']<=dur_left:
            return True,""
        else:
            return False,""


def create_plan(poi_df_filtered,fixture_df,duration=24*60,day=None,time_range=None,no_stops=50):

    time_matrix=create_time_matrix(poi_df_filtered)
    ids = poi_df_filtered["id"].tolist()
    visit_minutes=dict(zip(poi_df_filtered["id"],poi_df_filtered["suggested_visit_minutes"]))


    plan_list = []
    dur_list = []
    total_dur = []
    warnings = []


    def plan_development(temp_plan,temp_warn,temp_dur_list,duration_spend=0):

        if no_stops is not None:
            if (no_stops==len(temp_plan)) and (temp_plan not in plan_list):
                plan_list.append(temp_plan)
                dur_list.append(temp_dur_list)
                total_dur.append(np.round(duration_spend,2))
                warnings.append(temp_warn)
                return
        if time_range is not None:
            time_now= time_range[0] + dt.timedelta(minutes=float(duration_spend))
        else:
            time_now=None

        check_id_list=[]

        for new_id in ids:
            if new_id not in temp_plan:
                if len(temp_plan) >0:
                    wt=time_matrix.loc[temp_plan[len(temp_plan)-1],new_id].copy()
                else:
                    wt=0

                if time_now is not None:
                   arrival_time= time_now + dt.timedelta(minutes=float(wt))
                else:
                   arrival_time=None

                check_id, warn_now = check_new_dest(poi_df_filtered, fixture_df, new_id, day, time_range, time_now=arrival_time,dur_left=duration-duration_spend-wt)
                if check_id:
                    check_id_list.append(new_id)

        if len(check_id_list)>0:
            for new_id in check_id_list:

                if len(temp_plan) >0:
                    wt=time_matrix.loc[temp_plan[len(temp_plan)-1],new_id].copy()
                else:
                    wt=0

                if time_now is not None:
                    arrival_time = time_now + dt.timedelta(minutes=float(wt))
                else:
                    arrival_time = None

                check_id, warn_now = check_new_dest(poi_df_filtered, fixture_df, new_id, day, time_range, time_now=arrival_time,dur_left=duration-duration_spend-wt)

                new_plan = temp_plan + [new_id]

                new_warn = temp_warn.copy()

                if len(warn_now) > 0:
                    new_warn.append(warn_now)

                new_duration_spend = duration_spend+ float(visit_minutes[new_id])+wt

                new_dur_list = temp_dur_list + [wt,float(visit_minutes[new_id])]

                plan_development(new_plan,new_warn,new_dur_list,duration_spend=new_duration_spend)

        else:
            if (temp_plan not in plan_list):
                plan_list.append(temp_plan)
                dur_list.append(temp_dur_list)
                total_dur.append(np.round(duration_spend,2))
                warnings.append(temp_warn)



    plan_development([],[],[],0)

    return  {"POIs":plan_list ,"Duration List":dur_list, "Duration":total_dur , "Warnings":warnings}



def test_plan():

    input_examples = [
        "Plan a four-hour visit to Corfu focused on art and museums on Monday, October 5, 2026, from 13:00 to 17:00.",
        "Plan a four-hour walking itinerary in Corfu focused on historical attractions on Tuesday, October 6, 2026, from 11:00 to 15:00.",
        "Can I visit Old Fortress, New Fortress, Achilleion Palace, Mon Repos Museum of Palaiopolis, and Museum of Asian Art on foot in just 90 minutes on Tuesday, October 6, 2026, between 11:00 and 12:30? Create an itinerary if possible.",
        "Plan a four-hour itinerary in Corfu focused on outdoor historical attractions on Wednesday, October 7, 2026, from 13:00 to 17:00."
        , "What should I see if I enjoy Venetian history?",
        "Make me a realistic four-hour walking plan starting at 11:00.",
        "Replace the second stop; my child would prefer something outdoors",
        "Will it rain later? Adjust the plan if necessary.",
        "Can I fit five attractions into 90 minutes?"
    ]

    user_input = input_examples[0]

    day='mon'
    poi_df_filtered = poi_df.iloc[range(3),:].copy()

    plans , durs , warnings = create_plan(poi_df_filtered=poi_df_filtered,fixture_df=fixture_df,duration=100,no_stops=3,day='mon')


    dur_response = extract_dur(user_input)['Dur'].input_duration_minutes
    time_range = time_range_search(user_input)


    plans , durs , warnings = create_plan(poi_df_filtered=poi_df_filtered,
                                          fixture_df=fixture_df,duration=dur_response,no_stops=3,
                                          time_range=time_range,day=day)

    i_0=0
    i_1=1

    time_matrix_change_0_1 = (
            time_range[0]
            + dt.timedelta(minutes=float(poi_df_filtered.iloc[i_0, 8]))
            + dt.timedelta(minutes=float(time_matrix.iloc[i_0, i_1]))
            + dt.timedelta(minutes=float(poi_df_filtered.iloc[i_1, 8]))
    )

    check_new_dest(poi_df_filtered=poi_df_filtered,fixture_df=fixture_df,day_now='mon',id_now='CF-002',time_range=time_range,time_now=time_range[0]+ dt.timedelta(minutes=float(poi_df_filtered.iloc[i_0, 8])) +  dt.timedelta(minutes=float(time_matrix.iloc[i_0, i_1])),dur_left=240)


    print(time_matrix_change_0_1)
    print(user_input)

