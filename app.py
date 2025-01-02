import streamlit as st
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

DATA_FILE = 'bucket_list_data.csv'
MEDIA_DIR = Path("media")
COLUMNS = ['Task', 'Completed', 'Completion Date', 'Media', 'Caption']

MEDIA_DIR.mkdir(exist_ok=True)

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    df = pd.DataFrame(columns=COLUMNS)
    df.to_csv(DATA_FILE, index=False)
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def handle_media_upload(media_files, task_name, completion_date):
    media_paths = []
    for file in media_files:
        file_ext = Path(file.name).suffix
        safe_name = f"{task_name}_{completion_date}_{len(media_paths)}{file_ext}".replace(" ", "_")
        file_path = MEDIA_DIR / safe_name
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
        media_paths.append(str(file_path))
    return ", ".join(media_paths)

def display_media(media_str, caption=""):
    if pd.isna(media_str) or not media_str:
        return
    
    media_paths = [path.strip() for path in media_str.split(",")]
    cols = st.columns(min(3, len(media_paths)))
    
    for idx, path in enumerate(media_paths):
        if not os.path.exists(path):
            continue
        col_idx = idx % len(cols)
        with cols[col_idx]:
            suffix = Path(path).suffix.lower()
            if suffix in ['.jpg', '.png']:
                st.image(path, caption=f"Image {idx + 1}")
            elif suffix == '.mp4':
                st.video(path)

def main():
    st.set_page_config(page_title="Bucket List App", layout="wide")
    
    # Load data at startup
    if 'data' not in st.session_state:
        st.session_state.data = load_data()

    option = st.sidebar.radio("Navigation", ["View Tasks", "Add Task"], index=0)

    if option == "Add Task":
        st.title("Add New Task")
        with st.form("add_task_form"):
            task_name = st.text_input("Task Name")
            submitted = st.form_submit_button("Add Task")
            
            if submitted and task_name:
                new_task = pd.DataFrame([{
                    'Task': task_name,
                    'Completed': False,
                    'Completion Date': '',
                    'Media': '',
                    'Caption': ''
                }])
                st.session_state.data = pd.concat([st.session_state.data, new_task], ignore_index=True)
                save_data(st.session_state.data)
                st.success(f"Added: {task_name}")

    else:
        st.title("Your Bucket List")
        df = st.session_state.data
        show_completed = st.checkbox("Show completed tasks", value=True)
        
        if not show_completed:
            df = df[~df['Completed']]

        for idx, row in df.iterrows():
            with st.expander(f"{row['Task']} {'✓' if row['Completed'] else ''}", expanded=not row['Completed']):
                if not row['Completed']:
                    if st.checkbox("Mark as completed", key=f"complete_{idx}"):
                        with st.form(f"completion_form_{idx}"):
                            completion_date = st.date_input(
                                "When did you complete this?",
                                min_value=datetime.today()
                            )
                            caption = st.text_area("Add a note (optional)")
                            media_files = st.file_uploader(
                                "Add photos/videos",
                                type=["jpg", "png", "mp4"],
                                accept_multiple_files=True
                            )
                            
                            if st.form_submit_button("Save"):
                                st.session_state.data.at[idx, 'Completed'] = True
                                st.session_state.data.at[idx, 'Completion Date'] = str(completion_date)
                                st.session_state.data.at[idx, 'Caption'] = caption
                                
                                if media_files:
                                    media_paths = handle_media_upload(
                                        media_files,
                                        row['Task'],
                                        completion_date
                                    )
                                    st.session_state.data.at[idx, 'Media'] = media_paths
                                
                                save_data(st.session_state.data)
                                st.success("Updated!")
                                st.rerun()
                
                else:
                    st.write(f"**Completed:** {row['Completion Date']}")
                    if row['Caption']:
                        st.write(f"**Note:** {row['Caption']}")
                    if row['Media']:
                        st.write("**Media:**")
                        display_media(row['Media'], row['Caption'])

if __name__ == "__main__":
    main()