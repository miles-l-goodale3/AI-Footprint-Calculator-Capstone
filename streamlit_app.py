import streamlit as st
import pandasql as psql
import pandas as pd
import os
import json
import tempfile
import pathlib
from collections.abc import Mapping, Sequence
from streamlit_gsheets import GSheetsConnection
import re
import gspread
from google.oauth2.service_account import Credentials

def _safe_rerun():
    try:
        st.experimental_rerun()
    except Exception as e_exp:
        try:
            from streamlit.runtime.scriptrunner import RerunException
        except Exception:
            try:
                from streamlit.web.server import RerunException
            except Exception:
                RerunException = None

        if RerunException is not None:
            try:
                raise RerunException({"rerun": True})
            except TypeError:
                try:
                    raise RerunException({})
                except Exception:
                    st.stop()
        else:
            st.stop()
    
if "agreed" not in st.session_state:
    st.session_state.agreed = False
if "page" not in st.session_state:
    st.session_state.page = "consent"
if "results" not in st.session_state:
    st.session_state.results = None
if "form_inputs" not in st.session_state:
    st.session_state.form_inputs = None
if "_sheet_written" not in st.session_state:
    st.session_state._sheet_written = False

if not st.session_state.agreed:
    st.title("Your AI Footprint Calculator")
    st.markdown("""Please read the following before using the AI Footprint Calculator.
                
    Estimated completion time: 10 minutes""")
    st.subheader("Purpose of Study")
    st.markdown(
        """
    This calculator collects data from participants to then estimate the AI footprint of Wofford as a whole. In addition, participants will receive personalized insights into their AI use, which could encourage reduced use through increased awareness. Ultimately, this study will contribute to the emerging field of AI use in higher education and may support the development of a campus-wide AI policy at Wofford.
"""
    )
    st.subheader("Description of Study")
    st.markdown(
        """
        The term Artificial Intelligence (AI) refers to machine-learning models that can learn to make a prediction based on data. What most of the public is focused on today is Generative AI (Gen AI), which is a machine-learning model that is trained to create new data rather than predictions about a specific dataset.
        
        A simple example of Gen AI is autocomplete—it is trained on your speech patterns to suggest words you were already going to say. One can think of large Gen AI models like ChatGPT in a similar way: instead of being trained on your specific speech patterns, they are trained on most of the available data on the internet (Zewe, 2023). 
        
        Gen AI requires energy and water to run its data centers, resulting in a large resource footprint. Preliminary studies suggest that training ChatGPT-4 alone took between 57,045.624± MWh of energy, between 13,725± metric tons of CO2e (Ludvigsen, 2023), and for GPT-3 roughly 700,000 liters of water (McLean, 2023). The average query emits 4.32g of CO2 (Pederson, 2025). The scale at which queries are being asked and answered globally is difficult to comprehend, with between 700 and 800 million weekly users of ChatGPT. So, focusing on a local scale can help individuals at Wofford understand how our community's usage contributes to the global cost of Gen AI. 
        
        This AI footprint calculator will allow the researchers to estimate the AI footprint of the Wofford community as a whole. In addition, the researchers will conduct an analysis to identify any correlations between AI usage and age or college status (student or staff).
        """)
    st.subheader("Subject Confidentiality")
    st.markdown("""
               No identifiable personal information will be collected; the only demographic information collected will be age and whether the individual is a student or staff member. The demographic data will be used to determine if there is a correlation between age and AI usage, as well as between status at the college and AI usage. The participants’ data will not be shared in any way that could reveal their identity.
""" )
    st.subheader("Risks")
    st.markdown(""" Minimal risks are associated with this survey. There is a chance that the calculator's outcome distresses the participant. However, if this occurs, participants will have access to resources that may reduce distress on the final page of the survey (after completion). """)
    st.subheader("Consent to Participate")
    
    with st.form("consent_form"):
        submitted = st.form_submit_button("I have read and consent to the terms above.")
    if submitted:
        st.session_state.agreed = True
        st.session_state.page = "form"
    st.write("If you do not consent, please close this page.")
    st.subheader("References")
    st.markdown(""" 
Ludvigsen, Kasper. “The carbon footprint of GPT-4.” Medium, Towards Data Science Archive. 18 July 2023. https://medium.com/data-science/the-carbon-footprint-of-gpt-4 d6c676eb21ae. 
                
McLean, Sophie. “The Environmental Impact of ChatGPT: A Call for Sustainable Practices in AI Development.” Earth.org, Global Commons. 28 April 2023. https://earth.org/environmental-impact-chatgpt/.

Pederson, Cam. “The Real Carbon Cost of an AI Token.” Ditchcarbon, Ditchcarbon Ltd. 24
April 2025. https://ditchcarbon.com/blog/llm-carbon-emissions.

                
Zewe, Adam. “Explained: Generative AI.” MIT News, Massachusetts Institute of Technology. 9
November 2023. https://news.mit.edu/2023/explained-generative-ai-1109.


""")
    st.stop()

def estimate_tokens(text, method="average"):
    if not text:
        return 0.0
    word_count = len(text.split())
    char_count = len(text)
    tokens_count_word_est = word_count / 0.75
    tokens_count_char_est = char_count / 4.0

    if method == "average":
        return (tokens_count_word_est + tokens_count_char_est) / 2
    elif method == "words":
        return tokens_count_word_est
    elif method == "chars":
        return tokens_count_char_est
    elif method == "max":
        return max(tokens_count_word_est, tokens_count_char_est)
    elif method == "min":
        return min(tokens_count_word_est, tokens_count_char_est)
    else:
        raise ValueError("Invalid method. Use 'average', 'words', 'chars', 'max', or 'min'.")

def inputs_callback(dem_q1,dem_q2,q_1,q_2,q_3):    
    with open('data.csv', 'a+') as f:
        f.write(f"{dem_q1},{dem_q2},{q_1},{q_2},{q_3}\n")

if st.session_state.page == "form":
    st.title("AI Footprint Calculator")
    with st.form("AI Calc Data"):
        dem_q1 = st.selectbox('Are you a student or a staff/faculty member at Wofford College?',['Student', 'Staff/Faculty'], key = 'dem_q1')
        dem_q2 = st.number_input('How old are you?', 18, 90, key = 'dem_q2')
        q_1 = st.slider('On average how many queries do you input a week into Chat-GTP?', 0, 50, value = 5, key = 'q_1')
        q_2 = st.text_input('What was your most recent query?', 'Enter query here', key = 'q_2')
        q_3=st.slider('On average how many times a week do you use google? *AI summary is automatically generated for any google query*',0,100, value = 5, key = 'q_3')
        submit = st.form_submit_button("Submit")
    if submit:
        st.session_state.form_inputs = {
            "dem_q1": dem_q1,
            "dem_q2": dem_q2,
            "q_1": q_1,
            "q_2": q_2,
            "q_3": q_3,
        }
        try:
            q_2_tokens=estimate_tokens(q_2,method="average")
            results = {"per_week": {}, "if_all_used": {}, "comparisons": {}, "google": {}, "if_all_used_goog": {}, "goog_comp": {}, "training_costs": {}}
            if q_1>0:
                co2_per_qmt=q_2_tokens*0.03
                co2_per_week=round((co2_per_qmt*q_1),2)
                l_per_q=q_2_tokens*0.011464225161
                l_per_week=round((l_per_q*q_1),2)
                energy_per_q=int(q_2_tokens*0.771)
                energy_per_week=round((energy_per_q*q_1),2)
                results["per_week"] = {
                    "co2_metric_tons": co2_per_week,
                    "water_liters": l_per_week,
                    "energy_kwh": energy_per_week,
                }
                wai_co2=round((co2_per_week*2225),2)
                wai_water=round((l_per_week*2225),2)
                wai_energy=round((energy_per_week*2225),2)
                results["if_all_used"] = {
                    "wai_co2_metric_tons": wai_co2,
                    "wai_water_liters": wai_water,
                    "wai_energy_kwh": wai_energy,
                }
                if energy_per_week>0.0624:
                    fridge_comp=energy_per_week/0.0625
                    fcomp_days=int(fridge_comp*2)
                    results["comparisons"]["fridge_days"] = fcomp_days
            if q_3>0.99:
                google_energy=round((q_3*0.24),2)
                google_co2=round((q_3*0.03),2)
                google_water=round((q_3*0.26),2)
                results["google"] = {
                    "g_energy_kwh": google_energy,
                    "g_co2_metric_tons": google_co2,
                    "g_water_liters": google_water,
                 }
                if google_energy>0.0624:
                    fridge_comp=google_energy/0.0625
                    fcomp_days=round((fridge_comp*2),2)
                    results["goog_comp"]["fridge_days_equivalent"] = fcomp_days
                wgoog_energy=google_energy*2225
                wgoog_co2=google_co2*2225
                wgoog_water=google_water*2225
                results["if_all_used_goog"] = {
                    "wg_energy_kwh": wgoog_energy,
                    "wg_co2_metric_tons": wgoog_co2,
                    "wg_water_liters": wgoog_water,
                    }
                training_energy_kwh=57045625000/700000000
                training_co2=13725000000/700000000
                training_water=700000000/700000000
                results["training_costs"] = {
                    "training_energy_kwh": round(training_energy_kwh,2),
                    "training_co2": round(training_co2,2),
                    "training_water": round(training_water,2),
                }
            inputs_callback(dem_q1,dem_q2,q_1,q_2,q_3)
        except Exception as e:
            st.error(f"An error occurred during calculation: {e}")
            st.exception(e)
if st.session_state.page == "results":
    st.title("Your AI Footprint Results")

    results = st.session_state.get("results") or {}
    inputs = st.session_state.get("form_inputs") or {}

    if not results:
        st.info("No results available. Please fill out the form first.")
        if st.button("Go to form"):
            st.session_state.page = "form"
            _safe_rerun()
    else:
        st.subheader("Per-week estimates")
        per_week = results.get("per_week", {})
        if per_week:
            st.write(
                f'You use an average of {per_week.get("co2_metric_tons")} grams of CO2, '
                f"{per_week.get('water_liters')} mL of water, "
                f"and {per_week.get('energy_kwh')} kW of energy per week."
            )
        else:
            st.write("No per-week AI Chat-GPT usage data (q_1 was 0).")

        st.subheader("Scaled Chat-GPT Usage to all students & faculty")
        if_all_used = results.get("if_all_used", {})
        if if_all_used:
            st.write(
                f'If all students and staff used AI the way you do, we would emit '
                f'{if_all_used.get("wai_co2_metric_tons")} grams of CO2, '
                f'{if_all_used.get("wai_water_liters")} mL of water, '
                f'and {if_all_used.get("wai_energy_kwh")} kW of energy per week.'
            )
        else:
            st.write("No scaling data available.")
            
        st.subheader("Comparisons / equivalents")
        comparisons = results.get("comparisons", {})
        if comparisons:
            st.write(
                f'The energy produced from your weekly Chat-GPT usage is equivalent to running a fridge for {comparisons.get("fridge_days")} consecutive days, and'
                f' the CO2 you emit is equivalent to {comparisons.get("cars_equivalent_per_year")} passenger vehicle(s) yearly emissions.'
            )
        else:
            st.write("No comparison data available.")
            
        st.subheader("AI-powered Google searches")
        google = results.get("google", {})
        if google:
            st.write(
                f'You use an average of {google.get("g_co2_metric_tons")} grams of CO2 equivalent, '
                f"{google.get('g_water_liters')} liter(s) of water, "
                f"and {google.get('g_energy_kwh')} kWh of energy per week from your AI-powered Google searches."
            )
        else:
            st.write("No AI-powered Google search usage data (q_3 was 0).")
            
        st.subheader("Scaled Google search usage")
        if_all_used_goog = results.get("if_all_used_goog", {})
        if if_all_used_goog:
            st.write(
                f'If all students and staff used AI-powered Google searches the way you do, we would emit '
                f'{if_all_used_goog.get("wg_co2_metric_tons")} grams of CO2 equivalent, '
                f'{if_all_used_goog.get("wg_water_liters")} liter(s) of water, '
                f'and {if_all_used_goog.get("wg_energy_kwh")} kWh of energy per week.'
            )
        else:
            st.write("No scaling data available for Google searches.")
        st.subheader("Comparisons / Equivalents")
        goog_comp = results.get("goog_comp",{})
        if goog_comp:
            st.write(
                f'The energy produced from your weekly AI google searches is equivalent to {goog_comp.get("fridge_days_equivalent")}, and'
                f'the CO2 you emmit is equivalent to {goog_comp.get("car_equivalent_per_year")} passenger vehicle(s) yearly emmissions.'
            )
        else:
            st.write("No comparison data available.")
            
        st.subheader("Training Costs")
        training_costs = results.get("training_costs", {})
        if training_costs:
            st.write(
                f'The estimated environmental cost of training the AI model you used is '
                f'{training_costs.get("training_co2")} metric ton(s) of CO2, '
                f'{training_costs.get("training_water")} liter(s) of water, '
                f'and {training_costs.get("training_energy_kwh")} kWh of energy.'
            )
        else:
            st.write("No training cost data available.")