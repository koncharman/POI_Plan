
from rag_base import *
from user_input_analysis import *
from datetime import datetime,timedelta
from weather_api import *

def check_date(user_input):


    date_response_man = extract_date_man(user_input)

    if len(date_response_man)!=4:
        return None,None

    weak_day=date_response_man[0]
    date_str=construct_date(date_response_man[1],date_response_man[2],date_response_man[3])

    return weak_day,date_str

def check_time(user_input):

    time_range = time_range_search(user_input)
    time_range.sort()

    if len(time_range) < 2:

        dur_response_llm = extract_dur(user_input)

        dur_fin = dur_response_llm['Dur'].input_duration_minutes

        if not isinstance(dur_fin, (int, float)):
            dur_fin = 24 * 60

        if len(time_range) == 1:
            time_range.append(time_range[0] + timedelta(minutes=dur_fin)).strftime("%H:%M")
        else:
            time_range=None

    else:
        dur_fin = (time_range[1] - time_range[0]).total_seconds() / 60

    return time_range , dur_fin


def check_stops(user_input,llm_base):
    stops_now=extract_stops_new(user_input,llm_base)

    if stops_now=="None":
        return None
    else:
        return stops_now

def check_stetting(poi_df_filtered,rag_response_tags):

    #########If user requests indoor or outdoor
    rag_response_tags_set = rag_response_tags.loc[rag_response_tags['type'] == 'setting', :]

    indoor_outdoor=False
    if len(rag_response_tags_set) == 1:
        setting_temp = [rag_response_tags_set.iloc[0, 0], 'mixed']
        poi_df_filtered = poi_df_filtered.loc[poi_df_filtered['setting'].isin(setting_temp), :]
        indoor_outdoor=setting_temp[0]
    return poi_df_filtered.reset_index(drop=True),indoor_outdoor

def check_family(poi_df_filtered,rag_response_tags):
    rag_response_tags_set = rag_response_tags.loc[rag_response_tags['type'] == 'family', :]

    is_family=False
    if len(rag_response_tags_set) >= 1:
        poi_df_filtered = poi_df_filtered.loc[poi_df_filtered['family_suitability_fixture']==True, :]
        is_family=True
    return poi_df_filtered.reset_index(drop=True),is_family

def check_tag_rag(poi_df_filtered,tag_df,rag_response_tags):

    # if not check tags
    ids_docs = []
    #########Check tags
    if len(rag_response_tags) > 0:
        rag_response_tags_filtered = rag_response_tags.loc[rag_response_tags['type'] == "area"]
        if len(rag_response_tags_filtered) > 0:
            ids_docs.extend(poi_df_filtered.loc[poi_df_filtered['area'].isin(rag_response_tags_filtered['id']), 'id'].to_list())

        rag_response_tags_filtered = rag_response_tags.loc[rag_response_tags['type'] == "category"]
        if len(rag_response_tags_filtered) > 0:
            ids_docs.extend(poi_df_filtered.loc[poi_df_filtered['category'].isin(rag_response_tags_filtered['id']), 'id'].to_list())

        if len(rag_response_tags)>0:
            tag_df_filtered=tag_df.loc[tag_df['id'].isin(poi_df_filtered['id'])]

            ids_docs.extend(tag_df_filtered.loc[tag_df_filtered['tag'].isin(rag_response_tags['id']),'id'].to_list())

        poi_df_filtered=poi_df_filtered.loc[poi_df_filtered['id'].isin(ids_docs),]

    return poi_df_filtered.reset_index(drop=True)


def check_rain_rag(rag_response_tags,poi_df_filtered,time_range,date_str,API_URL):

    #######Rain
    rag_response_tags_rain = rag_response_tags.loc[rag_response_tags['type'] == 'rain', :]
    is_rain = False
    if len(rag_response_tags_rain) == 1:

        API_response = predict_rain(poi_df_filtered.loc[0, 'loc_lat'], poi_df_filtered.loc[0, 'loc_long'], API_URL,
                                    time_range, date_str)
        is_rain_mat = handle_weather_response(API_response, time_range)

        if any(is_rain_mat):

            is_rain = True

            poi_df_filtered = poi_df_filtered.loc[poi_df_filtered['setting'].isin(['indoor','mixed']), :]

    return poi_df_filtered.reset_index(drop=True) , is_rain



def extract_filter(user_input,poi_df,tag_df,API_URL,vector_store_poi,vector_store_tag,llm_base,weak_day=None,date_str=None,time_range=None,dur_fin=None,no_stops=None):

    poi_df_filtered=poi_df.copy()
    user_input=user_input.lower()

    if (weak_day is None) or (date_str is None):

        weak_day,date_str=check_date(user_input)

        if weak_day is None:
            return "ERROR No Week day was found"

    if (time_range is None) or (dur_fin is None):

        time_range , dur_fin = check_time(user_input)

    if no_stops is None:

        no_stops=check_stops(user_input,llm_base)

    rag_response_docs = retrieve_docs_rag(poi_df_filtered,vector_store_poi,user_input)
    rag_response_tags = retrieve_tags_rag(vector_store_tag,user_input)

    ########If user requested specific POIs

    if len(rag_response_docs)>0:
        poi_df_filtered = poi_df_filtered.loc[poi_df_filtered['id'].isin(rag_response_docs['id']), :]
    else:
        #Else check tags
        poi_df_filtered = check_tag_rag(poi_df_filtered,tag_df,rag_response_tags)

    if len(poi_df_filtered)<=0 :
        poi_df_filtered=poi_df.copy()
        #return "ERROR No Destinations Matching the criteria were found"

    ###Check if outdoor is captured

    poi_df_filtered , indoor_outdoor = check_stetting(poi_df_filtered, rag_response_tags)

    if len(poi_df_filtered) <= 0:
        poi_df_filtered=poi_df.copy()
        #return "ERROR No Destinations Matching the criteria were found"

    ###Check if family is mentioned
    poi_df_filtered , is_family = check_family(poi_df_filtered, rag_response_tags)

    if len(poi_df_filtered) <= 0:
        poi_df_filtered=poi_df.copy()
        return "ERROR No Destinations Matching the criteria were found"

    ###Check rain
    poi_df_filtered , is_rain = check_rain_rag(rag_response_tags,poi_df_filtered,time_range,date_str,API_URL)

    if len(poi_df_filtered) <= 0:
        poi_df_filtered=poi_df.copy()
        #return "ERROR No Destinations Matching the criteria were found"

    return {"POIs Filtered":poi_df_filtered ,
            "POIs Rag":rag_response_docs,
            "POIs Tag":rag_response_tags,
            "Time":time_range,
            "Day":weak_day,
            "Date":date_str,
            "Duration": dur_fin,
            "No Stops": no_stops,
            "Is Rain":is_rain,
            "Is Family":is_family,
            "Is Setting":indoor_outdoor}


def test_all():

    user_input="Historic places and Museum, Thursday, 8 October, 2026, rain, indoor from 15:00 to 17:00. I have a child."
    user_input="Plan a four-hour walking itinerary in Corfu focused on historical attractions on Tuesday, October 6, 2026, from 11:00 to 15:00."

    structured_result_rag=extract_filter(user_input,poi_df,tag_df,API_URL,vector_store_poi,vector_store_tag,llm_base)


    structured_result_rag=extract_filter(user_input,
                                         structured_result_rag["POIs Filtered"],tag_df,
                                         API_URL,vector_store_poi,vector_store_tag,llm_base,
                                         weak_day=structured_result_rag['Date'],
                                         date_str=structured_result_rag['Day'],
                                         time_range=structured_result_rag['Time'],
                                         no_stops=structured_result_rag['No Stops'],
                                         dur_fin=structured_result_rag['Duration']
                                         )





def examples():

    input_examples = [
        "Plan a four-hour visit to Corfu focused on art and museums on Monday, October 5, 2026, from 13:00 to 17:00.",
        "Plan a four-hour walking itinerary in Corfu focused on historical attractions on Tuesday, October 6, 2026, from 11:00 to 15:00.",
        "Can I visit Old Fortress, New Fortress, Achilleion Palace, Mon Repos Museum of Palaiopolis, and Museum of Asian Art on foot in just 90 minutes on Tuesday, October 6, 2026, between 11:00 and 12:30? Create an itinerary if possible.",
        "Plan a four-hour itinerary in Corfu focused on outdoor historical attractions on Wednesday, October 7, 2026, from 13:00 to 17:00.",
        "What should I see if I enjoy Venetian history?",
        "Make me a realistic four-hour walking plan starting at 11:00.",
        "Replace the second stop; my child would prefer something outdoors",
        "Will it rain later? Adjust the plan if necessary.",
        "Can I fit five attractions into 90 minutes?"
    ]


    #user_input=input_examples[0]
    user_input="Old town, historic, New Fortress Art , Museum, Thursday, 8 October, 2026, rain, indoor from 15:00 to 17:00. I have child."
    print(user_input)

    poi_df_filtered = poi_df.copy()
    user_input = user_input.lower()

    weak_day, date_str = check_date(user_input)

    print(weak_day)
    print(date_str)

    if weak_day is None:
        return None

    time_range, dur_fin = check_time(user_input)
    print(time_range)
    print(dur_fin)

    rag_response_docs = retrieve_docs_rag(poi_df_filtered,vector_store_poi, user_input)
    rag_response_tags = retrieve_tags_rag(vector_store_tag,user_input)


    ###Check if outdoor is captured
    poi_df_filtered_test_indoor , indoor_outdoor =check_stetting(poi_df_filtered,rag_response_tags)

    ###Check family
    poi_df_filtered_test_family , is_family = check_family(poi_df_filtered, rag_response_tags)

    ###Check rain
    poi_df_filtered_test_rain , is_rain  = check_rain_rag(rag_response_tags,poi_df_filtered,time_range,date_str,API_URL)

    ###Check tags
    poi_df_filtered_test_tags = check_tag_rag(poi_df_filtered,tag_df, rag_response_tags)



