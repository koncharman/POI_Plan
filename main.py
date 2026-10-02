
import streamlit as st
import pandas as pd

from user_input_analysis import *
from rag_base import *
from filtering_suggestions import *
from planning_handling import *
from weather_api import *

from datetime import time , date , timedelta
import os
from dotenv import load_dotenv



@st.cache_resource
def initialize_main_data():

    poi_df, tag_df, fixture_df = prepare_main_poi_data()



    load_dotenv(dotenv_path=".env")
    API_URL = os.getenv("OPEN_METEO_URL")

    return poi_df, tag_df, fixture_df, API_URL
poi_df, tag_df, fixture_df, API_URL = initialize_main_data()

####For ChatBot
# Initialize only once
if "poi_df_filtered" not in st.session_state:
    st.session_state.poi_df_filtered = poi_df.copy()

if "weak_day_instruct" not in st.session_state:
    st.session_state.weak_day_instruct = None

if "date_str_instruct" not in st.session_state:
    st.session_state.date_str_instruct = None

if "time_range_instruct" not in st.session_state:
    st.session_state.time_range_instruct = None

if "dur_fin_instruct" not in st.session_state:
    st.session_state.dur_fin_instruct = None

if "no_stops_instruct" not in st.session_state:
    st.session_state.no_stops_instruct = None

@st.cache_resource
def initialize_embeddings():

    # Run only once when the app initializes
    if os.path.exists("./chroma_poi"):
        shutil.rmtree("./chroma_poi", ignore_errors=True)

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://localhost:11434"
    )

    documents_poi, vector_store_poi = store_data_poi(poi_df, embeddings)

    tag_poi, vector_store_tag = store_tags_poi(poi_df, embeddings,tag_df)



    return embeddings, documents_poi, vector_store_poi, tag_poi, vector_store_tag

embeddings , documents_poi, vector_store_poi, tag_poi, vector_store_tag  = initialize_embeddings()

@st.cache_resource
def initialize_structured_llm():

    llm_base = ChatOllama(model="llama3.2:3b",  # qwen3:4b qwen3:8b  llama3.2:3b phi4-mini qwen2.5:3b deepseek-r1:7b
                          temperature=0,
                          reasoning=False,
                          base_url="http://localhost:11434")

    date_llm = llm_base.with_structured_output(DateInput)
    dure_llm = llm_base.with_structured_output(DurInput)

    return llm_base, date_llm, dure_llm

llm_base, date_llm, dure_llm = initialize_structured_llm()


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


demo_examples=[
"Plan a four-hour visit to Corfu focused on art and museums on Monday, October 5, 2026, from 13:00 to 17:00.",
"Plan a four-hour walking itinerary in Corfu focused on historical attractions on Tuesday, October 6, 2026, from 11:00 to 15:00.",
"Replace the second stop with something suitable for my 10-year-old daughter. Keep the rest of my itinerary and make sure we still finish by 15:00.",
"Can I visit Old Fortress, New Fortress, Achilleion Palace, Mon Repos Museum of Palaiopolis, and Museum of Asian Art on foot in just 90 minutes on Tuesday, October 6, 2026, between 11:00 and 12:30? Create an itinerary if possible.",
"Plan a four-hour itinerary in Corfu focused on outdoor historical attractions on Wednesday, October 7, 2026, from 13:00 to 17:00.",
"Can you check the weather for Wednesday, October 7, 2026, afternoon and adapt my existing itinerary if needed while keeping the original 13:00 - 17:00 time window?"
]

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Corfu Advisor",
    page_icon="🚀",
    layout="wide"
)

# --------------------------------------------------
# Simple styling
# --------------------------------------------------
st.markdown("""
<style>

    .stApp {
        background-color: #f7f8fc;
    }

    .main-title {
        font-size: 38px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-bottom: 30px;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
    }

    .info-box {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown(
    '<div class="main-title">Corfu Advisor</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">A simple Streamlit application for trip planning in Corfu.</div>',
    unsafe_allow_html=True
)

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# --------------------------------------------------
# Tabs
# --------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Extraction",
    "🔎 Planning",
    "⚙️ Weather",
    "🤖 Full Conversation"
])


# ==================================================
# TAB 1
# ==================================================
with tab1:

    st.header("Extract Entities from text")

    text = st.text_area(
        "Instructions",
        height=180,
        placeholder="I want to see art and museums, on Monday, 28 October, 2026"
    )

    if st.button(
            "Extract",
            type="primary"
    ):

        if text.strip():

            # Save input
            st.session_state.input_text = text

            # Indicate analysis completed
            st.session_state.analysis_done = True

        else:
            st.warning("Please enter some text.")

    if st.session_state.analysis_done:
        st.divider()

        st.subheader("Entities")

        result_tab1, result_tab2, result_tab3 = st.tabs([
            "📋 Docs",
            "🏷️ Tags",
            "⏱️ Date"
        ])

        with result_tab1:

            text_result = st.session_state.input_text

            retrieve_docs_rag = retrieve_docs_rag(poi_df=poi_df,vector_store_poi=vector_store_poi , user_input=text_result)

            st.metric(
                    "Retrieved Docs",
                    len(retrieve_docs_rag)
                )

            st.dataframe(
                    retrieve_docs_rag,
                    use_container_width=True
                )


            st.write(text_result)

        with result_tab2:

            text_result = st.session_state.input_text

            retrieve_tags_rag = retrieve_tags_rag(vector_store_tag,text_result)


            st.metric(
                    "Retrieved Tags",
                    len(retrieve_tags_rag)
                )

            st.dataframe(
                    retrieve_tags_rag,
                    use_container_width=True
                )

            st.write(text_result)

        with result_tab3:

            text_result = st.session_state.input_text

            date_response_man = extract_date_man(text_result)

            if date_response_man[0] is not None:

                date_fin = " ".join(date_response_man).upper()
                date_str = construct_date(date_response_man[1],date_response_man[2],date_response_man[3])
            else:
                date_fin = None
                date_str = None

            if date_fin is None:
                st.warning("Please enter a valid date.")
            else:

                time_range = time_range_search(text_result)
                time_range.sort()

                dur_fin=None

                if len(time_range) < 2:

                    dur_response_llm = extract_dur(text_result,dure_llm)

                    dur_fin = dur_response_llm['Dur'].input_duration_minutes

                    if not isinstance(dur_fin, (int, float)):
                        dur_fin = 24 * 60

                    if len(time_range) == 1:
                        time_range.append(time_range[0] + timedelta(minutes=dur_fin)).strftime("%H:%M")

                else:
                    dur_fin = (time_range[1] - time_range[0]).total_seconds() / 60

                col3_date, = st.columns(1)
                with col3_date:
                    st.metric("Date", f"{date_fin} ({date_str})")


                col1_date , col2_date = st.columns(2)

                with col1_date:
                    date_value = " - ".join(
                        t.strftime("%H:%M") if hasattr(t, "strftime") else str(t)
                        for t in time_range
                    ) if time_range else "Not specified"

                    st.metric("Time Range", date_value)

                with col2_date:
                    st.metric(
                        "Duration",
                        f"{dur_fin} min" if dur_fin is not None else "Not specified"
                    )




# ==================================================
# TAB 2
# ==================================================
with tab2:

    st.header("Planning")

    st.markdown("""
    <div class="info-box">
        Select some parameters for planning.
    </div>
    """, unsafe_allow_html=True)

    col_time_start, col_time_end = st.columns(2)

    with col_time_start:
        user_time_start = st.time_input(
            "Start Time",
            value=time(13, 00),
            step=60*15
        )
        user_time_start_dt = datetime.combine(
            date.today(),
            user_time_start
        )

    with col_time_end:
        user_time_end = st.time_input(
            "End Time",
            value=time(17, 00),
            step=60*15
        )
        user_time_end_dt = datetime.combine(
            date.today(),
            user_time_end
        )

    weekdays = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]

    user_day = st.selectbox(
        "Select Weekday",
        options=weekdays,
    )

    col_dur , col_stops = st.columns(2)

    with col_dur:
        user_dur = st.number_input(
            "Duration (in minutes)",
            value=240
        )
    with col_stops:
        user_stops = st.number_input(
            "Number of stops",
            value=3
        )


    col_pois, = st.columns(1)

    with col_pois:
        user_pois = st.multiselect(
            "POIs to Visit",
            options=poi_df['id'].to_list(),
            default=poi_df['id'].iloc[:4].to_list()
        )

    if st.button("Plan Analysis"):

        user_planning = create_plan(
            poi_df_filtered=poi_df.loc[poi_df['id'].isin(user_pois),:],
            fixture_df=fixture_df,
            day=user_day.lower()[0:3],
            duration=user_dur,
            no_stops=user_stops,
            time_range=[user_time_start_dt,user_time_end_dt]
        )

        if len(user_planning["POIs"]) > 0:

            st.success(
                f"{len(user_planning['POIs'])} plan(s) available"
            )

            for i, plan in enumerate(user_planning["POIs"]):

                duration = user_planning["Duration"][i]
                warnings = user_planning["Warnings"][i]

                with st.expander(
                        f"Plan {i + 1} — {duration} min",
                        expanded=(i == 0)
                ):

                    st.metric(
                        "Total Duration",
                        f"{duration} min"
                    )

                    st.subheader("POIs")

                    for j, poi in enumerate(plan):

                        col_poi, col_warning = st.columns([2, 3])

                        with col_poi:
                            st.write(f"**{j + 1}. {poi} (wt->{user_planning['Duration List'][i][j*2]} vt-> {user_planning['Duration List'][i][j*2+1]})**")

                        with col_warning:
                            if j < len(warnings):
                                st.write(warnings[j])

        else:
            st.warning(
                "No plan available for the selected settings"
            )


# ==================================================
# TAB 3
# ==================================================
with tab3:
    st.header("Weather API")

    selected_poi = st.selectbox(
        "Select POI",
        options=poi_df['id'].to_list(),
    )

    selected_date = st.date_input(
        "Select Date"
    )

    col1, col2 = st.columns(2)

    with col1:
        start_time = st.time_input(
            "Start Time",
            value=time(13, 0)
        )

    with col2:
        end_time = st.time_input(
            "End Time",
            value=time(17, 0)
        )

    if st.button("Check Weather"):
        # Convert date -> DD-MM-YYYY
        date_str = selected_date.strftime("%d-%m-%Y")

        loc_lat=poi_df.loc[poi_df['id']==selected_poi,'loc_lat']
        loc_long=poi_df.loc[poi_df['id']==selected_poi,'loc_long']

        # Convert time -> datetime
        start_dt = datetime.combine(
            selected_date,
            start_time
        )

        end_dt = datetime.combine(
            selected_date,
            end_time
        )

        time_range = [
            start_dt,
            end_dt
        ]

        response = predict_rain(
            latitude=loc_lat,
            longitude=loc_long,
            API_key=API_URL,
            time_range=time_range,
            date=date_str
        )

        weather = handle_weather_response(
            response,
            time_range
        )

        st.subheader("Weather Result")

        st.dataframe(weather)



# ==================================================
# TAB 4
# ==================================================
with tab4:

    st.header("Corfu Trip planning Chat Bot")

    st.text("ChatBot application that enables Entity Extraction, Provides Multiple Plans, and Accounts for weather when asked")

    instructions = st.text_area(
        "Provide you instructions Here",
        height=180,
        placeholder="I want to see art and museums, on Monday, 28 October, 2026"
    )

    if st.button(
        "Reset",
        "Primary"
    ):
            st.session_state.poi_df_filtered = poi_df.copy()

            st.session_state.weak_day_instruct = None

            st.session_state.date_str_instruct = None

            st.session_state.time_range_instruct = None

            st.session_state.dur_fin_instruct = None

            st.session_state.no_stops_instruct = None

    if st.button(
            "Confirm Instructions",
            type="primary"
    ):
        if len(instructions)<0:
            st.warning("Please Provide instuctions")
        else:

            #extract_filter(user_input, poi_df, tag_df, API_URL, vector_store_poi, vector_store_tag, weak_day=None,date_str=None, time_range=None, dur_fin=None)
            suggestions=extract_filter(
                user_input=instructions,
                poi_df=st.session_state.poi_df_filtered,
                tag_df=tag_df,
                API_URL=API_URL,
                vector_store_poi=vector_store_poi,
                vector_store_tag=vector_store_tag,
                llm_base=llm_base,
                weak_day=st.session_state.weak_day_instruct,
                date_str=st.session_state.date_str_instruct,
                time_range=st.session_state.time_range_instruct,
                dur_fin= st.session_state.dur_fin_instruct,
                no_stops=st.session_state.no_stops_instruct)



            #'''
            
            st.session_state.dur_fin_instruct = suggestions["Duration"]
            st.session_state.date_str_instruct = suggestions["Date"]
            st.session_state.weak_day_instruct = suggestions["Day"]
            st.session_state.time_range_instruct = suggestions["Time"]
            st.session_state.poi_df_filtered = suggestions["POIs Filtered"]
            st.session_state.no_stops_instruct = suggestions["No Stops"]


            if len(st.session_state.poi_df_filtered)>5:
                st.session_state.poi_df_filtered=st.session_state.poi_df_filtered.iloc[0:6,:]

            if st.session_state.no_stops_instruct is None:
                st.session_state.no_stops_instruct=3
            else:
                st.session_state.no_stops_instruct = max(st.session_state.no_stops_instruct, 5)

            prepare_response="""Based on your Instructions, I Found the Following Information."""

            if len(st.session_state.poi_df_filtered)==0:
                prepare_response+="""\n\n No suitable POIs were found"""
            else:
                prepare_response+="""\n\n Desired Settings: """
                if suggestions['Is Rain']:
                    prepare_response+="Rain Filtered, "
                if suggestions['Is Family']:
                    prepare_response+="Family Friendly, "
                if suggestions['Is Setting']:
                    prepare_response+=f"{suggestions['Is Setting']} Setting"

            st.header("Header")

            st.subheader("Main information")

            st.write(prepare_response)

            st.subheader("Data Filters")

            st.dataframe(  st.session_state.poi_df_filtered , use_container_width=True)
            st.dataframe(suggestions['POIs Tag'],use_container_width=True)
            #user_input="Historic places and Museum, Thursday, 8 October, 2026, rain, indoor from 15:00 to 17:00. I have a child."

            st.subheader("Date and Time Information")

            col1_cb , col2_cb ,col3_cb , col4_cb= st.columns(4)

            with col1_cb:
                st.metric("Date",st.session_state.date_str_instruct)
            with col2_cb:
                st.metric("Day",st.session_state.weak_day_instruct.upper())
            with col3_cb:
                st.metric("Duration",f"{st.session_state.dur_fin_instruct} minutes")
            with col4_cb:
                st.metric("No Stops",f"{st.session_state.no_stops_instruct}")

            st.subheader("Plans")

            user_planning = create_plan(
                poi_df_filtered=st.session_state.poi_df_filtered,
                fixture_df=fixture_df,
                day=st.session_state.weak_day_instruct.lower()[0:3],
                duration=st.session_state.dur_fin_instruct,
                no_stops=st.session_state.no_stops_instruct,
                time_range=st.session_state.time_range_instruct
            )

            if len(user_planning["POIs"]) > 0:

                st.success(
                    f"{len(user_planning['POIs'])} plan(s) available"
                )

                for i, plan in enumerate(user_planning["POIs"]):

                    duration = user_planning["Duration"][i]
                    warnings = user_planning["Warnings"][i]

                    with st.expander(
                            f"Plan {i + 1} — {duration} min",
                            expanded=(i == 0)
                    ):

                        st.metric(
                            "Total Duration",
                            f"{duration} min"
                        )

                        st.subheader("POIs")

                        for j, poi in enumerate(plan):

                            col_poi, col_warning = st.columns([2, 3])

                            with col_poi:
                                st.write(
                                    f"**{j + 1}. {poi} (wt->{user_planning['Duration List'][i][j * 2]} vt-> {user_planning['Duration List'][i][j * 2 + 1]})**")

                            with col_warning:
                                if j < len(warnings):
                                    st.write(warnings[j])
            
            else:
                st.warning(
                    "No plan available for the selected settings"
                )

            #'''

