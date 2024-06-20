import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from pathlib import Path
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.stylable_container import stylable_container  #
from streamlit_gsheets import GSheetsConnection
from sklearn import metrics
import hashlib


if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ''

if 'student_name' not in st.session_state:
    st.session_state['student_name'] = ''

if 'password' not in st.session_state:
    st.session_state['password'] = ''

if 'group' not in st.session_state:
    st.session_state['group'] = ''


st.set_page_config(
        page_title='Medium Project', # agregamos el nombre de la pagina, este se ve en el browser
        page_icon='📈' # se agrega el favicon, tambien este se ve en el browser
    )


login = None
log_df_n_cols = 4
login_df_ncols = 5
config_df_ncols = 2

conn = st.connection("gsheets", type=GSheetsConnection)
users_existing_data =  conn.read(worksheet="users", usecols=list(range(login_df_ncols)), ttl=1)
users_existing_data = users_existing_data.dropna(how="all")
users_existing_data.index = users_existing_data['email']

gs_user_db = users_existing_data.T.to_dict()

configuration_parameters = conn.read(worksheet="configuration", usecols=list(range(config_df_ncols)), ttl=1)

deadline = configuration_parameters['deadline']
deadline = pd.to_datetime(deadline)

max_per_day = int(configuration_parameters['max_per_day'])

today = pd.Timestamp.today()

difference = deadline - today


days = difference.dt.days.iloc[0]
seconds = difference.dt.seconds.iloc[0]
hours = seconds // 3600
minutes = (seconds % 3600) // 60


# emojis are obtained from bootstrap icons https://icons.getbootstrap.com/
with st.sidebar:
    st.image("./savila_games_logo.png")
    selected = option_menu(
        menu_title='MEDIUM APP',
        options= ['Login','Rankings','My group Submissions','Submit Results'],
        icons=['bi bi-person-fill-lock', '123','bi bi-database','bi bi-graph-up-arrow'], menu_icon="cast"
    )

    add_vertical_space(1)

    if selected == 'Login':

        user_name = st.text_input('User email', placeholder = 'username@email.com')
        user_password =  st.text_input('Password', placeholder = '12345678',type="password")
        login = st.button("Login", type="primary")
    add_vertical_space(1)

if selected == 'Login':
   
   st.header('Welcome to your Final group project Challenge')
   st.divider()
   st.subheader(f" Time remaining: {days} days, {hours} hours and {minutes} minutes")
   st.divider()
   st.write('Please proceed to login using the left side panel')
   st.write('⚠️ Please note that access to subsequent sections is restricted to logged-in users.')
   st.divider()
   st.subheader('Rules:')
   with st.expander('Rules',expanded=True):
      st.markdown("- This app lets you submit your project calculations.")
      st.markdown("- Everyone on your team can submit their solutions")
      st.markdown(f"- The site let each team submit {max_per_day} submissions per day max ")
      st.markdown("- For each one of the parts whichever team comes up with the best result for a given part gets the top grade for that part.")
      st.markdown("- In case there is a tie. The team that submitted first the solution will get the higher grade.")  
           
                
   st.subheader('How to use the app:')
   with st.expander('How to use the app',expanded=True):
      st.markdown("- Check out the **Ranking** 🥇 tab to see where your team stands for each one of the parts.")   
      st.markdown("- Click on **My Group Submissions** 🗃️ to see the history of all the solutions that your team has submitted.")
      st.markdown("- Hit **Submit Results** 📊 to drop in a new solution.")
      st.markdown("- Every time you submit, the app checks if it's all good and pops out some feedback in case you had a bug.") 
      st.markdown("- Keep trying new things and submitting - there's no limit")          
   add_vertical_space(1)

if login:

    hash_object_user_name = hashlib.sha256()
    hash_object_user_name.update(user_name.encode())
    hashed_username = hash_object_user_name.hexdigest()

    if hashed_username not in gs_user_db.keys():
        with st.sidebar:
            st.error('Username not registered')
    else:

        hash_object_password = hashlib.sha256()
        real_password = gs_user_db[hashed_username]['password']

        hash_object_password.update(user_password.encode())
        hashed_user_password = hash_object_password.hexdigest()

        if hashed_user_password != real_password:
            with st.sidebar:
                st.error('Sorry wrong password')
        else:
            user_first_name = gs_user_db[hashed_username]['name']
            group = gs_user_db[hashed_username]['group']
            st.session_state['user_name'] = user_name
            st.session_state['student_name'] = user_first_name
            st.session_state['password'] = real_password
            st.session_state['group'] =  group
            with st.sidebar:
                st.success(f'{user_first_name} from group ({group}) succesfully log-in', icon="✅")
            

with st.sidebar:
    if st.session_state['user_name'] != '':
        st.write(f"User: {st.session_state['user_name']} ")
        st.write(f"Group: {st.session_state['group']} ")
        logout = st.button('Logout')
        if logout:
            st.session_state['user_name'] = ''
            st.session_state['password'] = ''
            st.session_state['group'] = ''
            st.session_state['student_name'] = ''
            st.rerun()
    else:
        st.write(f"User: Not logged in ")


if selected == 'Submit Results':

    st.markdown("""
        <style>
        div[data-testid="stMetric"] {
            background-color: #EEEEEE;
            border: 2px solid #CCCCCC;
            padding: 5% 5% 5% 10%;
            border-radius: 5px;
            overflow-wrap: break-word;
        }
        </style>
        """
        , unsafe_allow_html=True)

    st.header('Submit Predictions')
    st.subheader("Machine Learning Classification")
    st.divider()
    st.subheader(f" Time remaining: {days} days, {hours} hours and {minutes} minutes")
    st.divider()

    if st.session_state['user_name'] == '':
        st.warning('Please log in to be able to submit your project solution')
    else:
            
        group_log_df = conn.read(worksheet="log", usecols=list(range(log_df_n_cols)), ttl=1).dropna(how="all")
        group_log_df = group_log_df[group_log_df['group'] == st.session_state['group']]
        group_log_df['time'] = pd.to_datetime(group_log_df['time'])

        test_data = conn.read(worksheet="test_data", usecols=list(range(1)), ttl=30).dropna(how="all")
        test_data_y = test_data['y']

        n_test = len(test_data)

        current_date = pd.Timestamp.today()

        submissions_count = group_log_df[(group_log_df['time'].dt.date == current_date.date())].shape[0]

        time_diff = deadline - current_date
        time_diff = time_diff.dt.total_seconds().iloc[0]


        if time_diff <= 0:
            st.warning('Sorry you cannot longer submit anymore, the project deadline has passed')
        else:
            if submissions_count >= max_per_day:
                st.warning(f'Sorry your team has already submitted {submissions_count} times today, and this exceeds the maximun amount of submissions per day')
            else:

                user_file = st.file_uploader("Upload your predictions file",type=['csv'])
                st.caption(f"Your file must have {n_test} rows and at least one column named \'predictions\' with your model predictions")

                if user_file is not None:

                    submit_pred = st.button('submit',type="primary",key="submit_pred")

                    if submit_pred:

                        pred_df = pd.read_csv(user_file) 

                        if 'predictions' not in pred_df.columns.to_list():
                            st.error('Sorry there is no \"predictions\" column in your file', icon="🚨")
                        elif len(pred_df) != n_test:
                            st.error(f'Sorry the number of rows of your file ({len(pred_df)}) does not match the expected lenght of ({n_test})', icon="🚨")
                        else:
                            with st.spinner('Uploading solution to database'):
                                user_predictions = pred_df['predictions']

                                timestamp = datetime.datetime.now()
                                timestamp = timestamp.strftime("%d/%m/%Y, %H:%M:%S")
                                st.write(f'Submitted on: {timestamp}')                
                        
                                ACC = metrics.accuracy_score(test_data_y,user_predictions)
                                

                                F1 = metrics.f1_score(test_data_y,user_predictions)

                                cm = pd.DataFrame(metrics.confusion_matrix(test_data_y,user_predictions),
                                                columns = ["T Pred","F Pred"],index=["T Real","F Real"])

                                columns_part_2 = st.columns(3)

                                with columns_part_2[0]:
                                    st.metric("ACCURACY",f"{100*ACC:.1f} %")
                                with columns_part_2[1]:
                                    st.metric("F1-Score",f'{F1:.3f}')
                                
                                with columns_part_2[2]:
                                    st.dataframe(cm,use_container_width=True)

                                solution_dict = dict()
                                solution_dict['user'] = st.session_state['student_name']
                                solution_dict['group'] = st.session_state['group']
                                solution_dict['time'] = timestamp
                                solution_dict['score'] = ACC

                                logs_df_2 = conn.read(worksheet="log", usecols=list(range(log_df_n_cols)), ttl=1).dropna(how="all")
                                solution_2 = pd.DataFrame([solution_dict])
                                updated_log_2 = pd.concat([logs_df_2,solution_2],ignore_index=True)
                                conn.update(worksheet="log",data = updated_log_2)
                                st.success(f'Your solution was uploaded on: {timestamp}',icon="✅")
                                st.balloons()


if selected == "Rankings":
    st.header('Rankings')
    
    if st.session_state['user_name'] == '':
        st.warning('Please log in to be able to see The rankings')
    else:
        st.write('The table below shows the rankings for the project')

        rank_df = conn.read(worksheet="log", usecols=list(range(log_df_n_cols)), ttl=1).dropna(how="all")
        GROUPS = list(rank_df['group'].unique())
        default_time = pd.to_datetime('01/01/1901, 00:00:00')

        st.header("Part 4: Machine Learning Classification")
        st.divider()

        ranking_list_2 = []
        for gr in GROUPS:

            mini_df_2 = rank_df[rank_df['group'] == gr]
            if len(mini_df_2) == 0:
                row = {'group':gr,'Accuracy':0,'time':default_time}
                ranking_list_2.append(row)
                continue
            else:
                best_idx_2 = np.argmax(mini_df_2['score'])
                best_value_2 = mini_df_2.iat[best_idx_2,-1]
                best_time_2 = pd.to_datetime(mini_df_2.iat[best_idx_2,2])
                row = {'group':gr,'Accuracy':best_value_2,'time':best_time_2}
                ranking_list_2.append(row)
        ranking_df_2 = pd.DataFrame(ranking_list_2).sort_values(by = ['Accuracy','time'],ascending=[False, True])
        ranking_df_2 = ranking_df_2.reset_index(drop=True)
        ranking_df_2.iat[0,0] = ranking_df_2.iat[0,0] + "   🥇"
        ranking_df_2.iat[1,0] = ranking_df_2.iat[1,0] + "   🥈"
        ranking_df_2.iat[2,0] = ranking_df_2.iat[2,0] + "   🥉"
        st.dataframe(ranking_df_2,use_container_width=True,hide_index=True)


if selected == 'My group Submissions':
    st.header('My Group Submissions')
    
    if st.session_state['user_name'] == '':
        st.warning('Please log in to be able to see your submission history')
    else:
        st.write(f'The table below shows you the submission history of your group: **{st.session_state["group"]}**')
        group_log_df = conn.read(worksheet="log", usecols=list(range(log_df_n_cols)), ttl=1).dropna(how="all")
        group_log_df = group_log_df[group_log_df['group'] == st.session_state['group']]
        group_log_df = group_log_df[['user','time','score']]
        
       
        st.subheader('Submissions History:')
        st.dataframe(group_log_df,use_container_width=True,hide_index=True)          
