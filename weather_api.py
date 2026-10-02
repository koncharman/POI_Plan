

import os
import requests
from dotenv import load_dotenv
from datetime import datetime


def predict_rain(latitude,longitude,API_key,time_range=None,date=None):

        # DD-MM-YYYY -> YYYY-MM-DD
        date_obj = datetime.strptime(date, "%d-%m-%Y")
        api_date = date_obj.strftime("%Y-%m-%d")

        start_time = time_range[0]
        end_time = time_range[1]

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": [
                "temperature_2m",
                "precipitation_probability",
                #"rain"
                "weather_code"
            ],
            "timezone": "auto",
            "start_date": api_date,
            "end_date": api_date
        }

        response = requests.get(
            API_key,
            params=params
        )

        return  response

def handle_weather_response(response, time_range=None):

    RAIN_CODES = [51, 53, 55, 56, 57,61, 63, 65, 66, 67,80, 81, 82,95, 96, 97, 99]
    #SNOW_CODES = [71, 73, 75, 77, 85, 86]

    data = response.json()
    data_codes = data["hourly"]["weather_code"]

    if time_range is not None:

        start_hour = time_range[0].time().hour
        end_hour = time_range[1].time().hour

        data_codes = data_codes[start_hour:end_hour + 1]

    else:
        start_hour = 0
        end_hour = 24

    data_codes_rain = {
        "Hour": list(range(start_hour, end_hour + 1)),
        "Rain": [dc in RAIN_CODES for dc in data_codes]
    }

    return data_codes_rain






def test_example():

    from prepare_poi_data import prepare_main_poi_data

    poi_df, tag_df, fixture_df = prepare_main_poi_data()

    import os
    import requests
    from dotenv import load_dotenv
    from datetime import datetime

    load_dotenv(dotenv_path=".env")
    API_URL = os.getenv("OPEN_METEO_URL")

    loc_lat=poi_df.loc[0,'loc_lat'].copy()
    loc_lon=poi_df.loc[0,'loc_long'].copy()

    date='17-10-2026'

    time_range=[
        datetime.strptime("13:00", "%H:%M"),
        datetime.strptime("17:00","%H:%M")
    ]


    API_response=predict_rain(loc_lat,loc_lon,API_URL,time_range,date)

    is_rain=handle_weather_response(API_response,time_range)

