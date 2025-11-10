import streamlit as st

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
if "_more_info" not in st.session_state:
    st.session_state._more_info = False
if not st.session_state.agreed:
    st.title("Your AI Footprint Calculator")
    st.markdown("""Please read the following before using the AI Footprint Calculator.
                
    Estimated completion time: 5 - 10 minutes""")
    st.markdown("""This calculator is not currently storing user inputs for analysis.""")

    st.subheader("Consent to Participate")
    with st.form("consent_form"):
        submitted = st.form_submit_button("I have read and consent to the terms above.")
    if submitted:
        st.session_state.agreed = True
        st.session_state.page = "form"
        _safe_rerun()
    st.write("If you do not consent, please close this page.")

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
if st.session_state.page == "form":
    st.title("AI Footprint Calculator")
    with st.form("AI Calc Data"):
        dem_q1 = st.selectbox('Are you a student or a staff/faculty member at Wofford College?',['Student', 'Staff/Faculty'], key = 'dem_q1')
        dem_q2 = st.number_input('How old are you?', 18, 90, key = 'dem_q2')
        q_1 = st.number_input('Typically, how many queries do you input a week into Chat-GTP?', 0, 200, value = 5, key = 'q_1')
        q_2 = st.text_input('What was your most recent query?', 'Enter query here', key = 'q_2')
        q_3=st.slider('How many times a week do you use google? *AI summary is automatically generated for any google query*',0,100, value = 5, key = 'q_3')
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
                if google_energy>1.4:
                    fridge_comp=google_energy/1.5
                    fcomp_days=round((fridge_comp*2),2)
                    results["goog_comp"]["fridge_days_equivalent"] = fcomp_days
                wgoog_energy=round((google_energy*2225),2)
                wgoog_co2=round((google_co2*2225),2)
                wgoog_water=round((google_water*2225),2)
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
  
            st.session_state.results = results
            st.session_state.page = "results"
            _safe_rerun()
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
                f'The energy produced from your weekly Chat-GPT usage is equivalent to running a fridge for {comparisons.get("fridge_days")} consecutive days.'
            )
        else:
            st.write("No comparison data available.")
            
        st.subheader("AI-powered Google searches")
        google = results.get("google", {})
        if google:
            st.write(
                f'You use an average of {google.get("g_co2_metric_tons")} grams of CO2, '
                f"{google.get('g_water_liters')} liter(s) of water, "
                f"and {google.get('g_energy_kwh')} kW of energy per week from your AI-powered Google searches."
            )
        else:
            st.write("No AI-powered Google search usage data (q_3 was 0).")
            
        st.subheader("Scaled Google search usage")
        if_all_used_goog = results.get("if_all_used_goog", {})
        if if_all_used_goog:
            st.write(
                f'If all students and staff used AI-powered Google searches the way you do, we would emit '
                f'{if_all_used_goog.get("wg_co2_metric_tons")} grams of CO2, '
                f'{if_all_used_goog.get("wg_water_liters")} liter(s) of water, '
                f'and {if_all_used_goog.get("wg_energy_kwh")} kW of energy per week.'
            )
        else:
            st.write("No scaling data available for Google searches.")
        st.subheader("Comparisons / Equivalents")
        goog_comp = results.get("goog_comp",{})
        if goog_comp:
            st.write(
                f'The energy produced from your weekly AI google searches is equivalent to running a fridge for {goog_comp.get("fridge_days_equivalent")} consecutive days.'
            )
        else:
            st.write("No comparison data available.")
            
        st.subheader("Training Costs of Chat-GPT 3")
        st.write("*These calculations come from the training of GPT-3 and GPT-4 before deployment and does not account for any further training Chat-GPT has gone through since.*")
        training_costs = results.get("training_costs", {})
        if training_costs:
            st.write(
                f'The estimated environmental cost of training GPT-4 is '
                f'{training_costs.get("training_co2")} metric ton(s) of CO2, '
                f'and {training_costs.get("training_energy_kwh")} kWh of energy.'
                f' The amount of water used to train GPT-3 was {training_costs.get("training_water")} liter(s) of water.'
            )
        else:
            st.write("No training cost data available.")
        st.subheader("Confused?")
        clicked = st.button("Click here to learn why AI harms the environment.")
        if clicked:
            st.session_state.page = "_more_info"

if st.session_state.page == "_more_info":
    st.title("Why does AI harm the environment?")
    st.header("Water Usage")
    st.markdown("""Data centers generate an enormous amount of heat and the industry standard cooling system is the usage of water. """)
    st.header("CO2 emmissions")
    st.markdown("""As the demand for AI increases exponentially, the energy grid is struggling to keep up. Renewable energy cannot provide the mass amounts of energy that data centers requires, causing a reliance on fossil fuels to fill the gap. Many AI companies have rolled back their net zero carbon emmission timelines/statements in a direct response to this increased reliance on fossil fuels.""")
    st.header("Energy Consumption")
    st.markdown("""AI is hungry. It requires massive amounts of energy to both be trained and to run. """)
