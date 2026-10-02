

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from typing import Optional,List, Literal
import re
from dateparser.search import search_dates
import datetime as dt



class DateInput(BaseModel):
    '''

    input_day: Optional[str] = Field(
        default=None,
        description="""
               Find the day of the activity or event.
               Check date and/or given day to return only the week day. Transform the day to:
               'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', or 'Sunday'
               If no information is discussed return default (None)
               """
    )

    '''


    input_date: Optional[str] = Field(
        default=None,
        description="""
            Find and Transform the date to DD-MM-YYYY.
            """
    )

class DurInput(BaseModel):

    input_duration_minutes: Optional[int] = Field(
        default=None,
        description="""
                 Find the duration of the trip or activity in minutes. 
                 Convert durations such as '2 hours' to '120' minutes.
                 If no information is discussed return default (None)
                 """
    )



class OtherInput(BaseModel):

    input_stops: Optional[int] = Field(
        default=None,
        description="""
        Imagine a trip was planned. 
        Someone may want to discuss the number of stops.
        Find the total number of stops mentioned.
        If no information is discussed return default (None)
        """
    )

    input_replace: Optional[int] = Field(
        default=None,
        description="""
        Imagine a trip was planned.
        Someone may want to replace one of the places in the trip.
        Find the ordinal position of the itinerary stop the user wants to replace.
        If no information is discussed return default (None)
        """
    )


def extract_stops_new(user_input,llm_base):
    prompt = f"""
        Extract the number of stops from the text.

        Return ONLY one integer or None if not found.
        Do not return words, JSON, or explanation.

        Text:
        {user_input}
        """

    response = llm_base.invoke(prompt)

    if response.content != "None":
        duration = int(response.content.strip())
    else:
        duration="None"

    return duration

def extract_date(user_input,date_llm):

    input_l=user_input.lower()

    result_date= date_llm.invoke(input_l)

    return  {"Date":result_date}

def extract_date_new(user_input,llm_base):
    prompt = f"""
        Extract the Date in DD-MM-YYYY from the text.

        Return ONLY one Date or None if not found.
        Do not return words, JSON, or explanation.

        Text:
        {user_input}
        """
    response = llm_base.invoke(prompt)

    return response.content

def extract_dur(user_input,dure_llm):
    input_l=user_input.lower()
    result_dur= dure_llm.invoke(input_l)

    return  {"Dur":result_dur}


def extract_dur_new(user_input,llm_base):
    prompt = f"""
    Extract the duration in minutes from the text.

    Return ONLY one integer or None if not found.
    Do not return words, JSON, or explanation.

    Text:
    {user_input}
    """

    response = llm_base.invoke(prompt)


    if response.content != "None":
        duration = int(response.content.strip())
    else:
        duration = "None"
    return duration


def extract_dur_man(user_input):

    pattern = r'\b(\d+(?:\.\d+)?)\s*(hours?|hrs?|minutes?|mins?)\b'
    match = re.search(pattern, user_input.lower())


def extract_date_man(user_input):

    user_input=user_input.lower()

    months = [
        'january', 'february', 'march', 'april',
        'may', 'june', 'july', 'august',
        'september', 'october', 'november', 'december'
    ]

    week_days=['monday','tuesday','wednesday','thursday','friday','saturday','sunday']



    month = None
    day = None
    year = None
    week_day = None

    for m in months:
        if m in user_input:
            month = m
            break
    if month is not None:

        for d in week_days:
            if d in user_input:
                week_day = d
                break

        input_split=user_input.split()

        m_index=[i for i in range(len(input_split)) if month in input_split[i]]

        input_refix=""

        min_t = max(0, m_index[0] - 3)
        max_t = min(len(input_split), m_index[0] + 4)

        for k in range(min_t,max_t):
         input_refix=input_refix+ " "+input_split[k]

        day = re.findall(r"\b(?:[1-9]|[12]\d|3[01])\b", input_refix)
        if len(day)>=1:
            day=day[0]
        else:
            day=None

        year = re.findall(r"\b20\d{2}\b", input_refix)
        if len(year)>=1:
            year=year[0]
        else:
            year=None

        if (day is not None) and (year is None):
            year=2026
        if (day is None):
            month=None
            year=None

    return week_day, day , month, year

def construct_date(day,month,year):

    month_map = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12
    }

    return f"{int(day):02d}-{month_map[month]:02d}-{int(year)}"



def extract_date_lib(user_input):
    dates = search_dates(user_input, languages=["en"])


def time_range_search(user_input):

    input_l=user_input.lower()

    time_info = re.findall(r"\b(?:[01]\d|2[0-3]):[0-5]\d\b", input_l)

    for i in range(len(time_info)):
        time_info[i]=dt.datetime.strptime(time_info[i], "%H:%M")

    return time_info




def examples_test(date_llm):

    input_examples = [
        "Plan a four-hour visit to Corfu focused on art and museums on Monday, October 5, 2026, from 13:00 to 17:00.",
        "Plan a four-hour walking itinerary in Corfu focused on historical attractions on Tuesday, October 6, 2026, from 11:00 to 15:00.",
        "Can I visit Old Fortress, New Fortress, Achilleion Palace, Mon Repos Museum of Palaiopolis, and Museum of Asian Art on foot in just 90 minutes on Tuesday, October 6, 2026, between 11:00 and 12:30? Create an itinerary if possible.",
        "Plan a four-hour itinerary in Corfu focused on outdoor historical attractions on Wednesday, October 7, 2026, from 13:00 to 17:00."
        ,"What should I see if I enjoy Venetian history?",
        "Make me a realistic four-hour walking plan starting at 11:00.",
        "Replace the second stop; my child would prefer something outdoors",
        "Will it rain later? Adjust the plan if necessary.",
        "Can I fit five attractions into 90 minutes?"
    ]

    for i in input_examples:
        print(extract_date_new(i,llm_base))
        #print(extract_dur_new(i,llm_base))
        #print(extract_stops_new(i,llm_base))


    user_input=input_examples[2]
    print(user_input)

    date_vars=extract_date_man(user_input)
    date_str=construct_date(date_vars[1],date_vars[2],date_vars[3])
    print(date_vars)
    times_vars=time_range_search(user_input)
    print(times_vars)

    user_input = input_examples[3]
    print(user_input)
    struct_date=extract_date(user_input,date_llm)

    print(struct_date)
    struct_dur=extract_dur(user_input,dure_llm)

