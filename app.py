import re, io  # Standard libraries for regex and buffer handling
import pandas as pd  # Data manipulation
import matplotlib.pyplot as plt  # Visualization
import streamlit as st  # Main UI Framework
import seaborn as sns

# LangChain & AI components
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_classic.memory import ConversationBufferMemory

# Custom utility functions from local file
from function import init_state, reset_conversation, reset_state, change_on_api_key, read_files, change_on_lan

init_state()

# 1. Page Configuration
st.set_page_config(
    page_title="InsightData: AI Analyst",
    page_icon="📊",
    layout="centered"  # 'centered' is better for chat apps, 'wide' for dashboards
)

# 2. App Header
st.title("📊 InsightData: AI-Powered Analyst")

# 3. Description & Instructions
st.markdown("""
Welcome to **InsightData**! 🚀  
Upload your **CSV** or **Excel** files and ask questions in plain English.  
This agent can analyze your data, calculate metrics, and even generate **Python code** to visualize trends.

**Supported Formats:** `.csv`, `.xlsx`
""")

with st.sidebar:
    # ==========================================
    # 1. Global Settings Section
    # ==========================================
    st.header("⚙️ App Settings")

    # API Key Input
    # Using type="password" to mask the input for security during demonstration.
    # The on_change callback ensures the session resets if the key is swapped.
    st.text_input(
        "🔑 Gemini API Key",
        type="password",
        on_change=change_on_api_key,
        key="google_api_key",
        help="Paste your Google Gemini API Key here. This is required to power the AI analyst."
    )

    # Language Selection Widget
    # This dropdown controls the language of the AI's output.
    # We use a callback (on_change) to force a re-initialization of the Agent,
    # ensuring the new language instruction is injected into the System Prompt immediately.
    chosen_language = st.selectbox(
        "🗣️ AI Response Language", 
        ["English", "Indonesian"],
        index=0,
        on_change=change_on_lan,
        help="Choose the language for the analysis results. Changing this will reboot the AI agent with the new language persona."
    )

    st.divider()

    # ==========================================
    # 2. Session Management Controls
    # ==========================================
    st.subheader("🛠️ Session Controls")

    # Clear History Button
    # Removes only the chat messages, allowing the user to keep the data loaded
    # but start a new topic of conversation.
    st.button(
        "🧹 Clear Conversation",
        on_click=reset_conversation,
        use_container_width=True,
        help="Wipe the chat history to start a fresh topic (Data remains loaded)."
    )

    # Hard Reset Button
    # Resets session data (files, chat, memory) but preserves the API Key to save user effort.
    # Marked as 'primary' (usually red/highlighted) to indicate a destructive action.
    st.button(
        "🔴 Hard Reset System",
        type="primary",
        on_click=reset_state,
        use_container_width=True,
        help="Resets uploaded files, chat history, and AI memory. Your API Key remains active."
    )

    st.divider()

    # ==========================================
    # 3. Data Ingestion Section
    # ==========================================
    st.subheader("📊 Data Source")

    # Tabs to switch between Local File Upload and URL Import
    tab_upload, tab_url = st.tabs(["📂 Upload File", "🔗 Cloud / URL"])
    
    with tab_upload:
        # File Uploader Widget
        # Accepts multiple CSV or Excel files.
        uploaded_files = st.file_uploader(
            "Drop files here",
            type=["csv", "xlsx"],
            accept_multiple_files=True,
            help="Supported formats: .csv and .xlsx"
        )

    with tab_url:
        # Text Input for Direct URLs
        # Useful for connecting to Google Sheets (must be public/published).
        uploaded_link = st.text_input(
            "Paste Data URL",
            placeholder="e.g., https://docs.google.com/...",
            help="Enter a direct link to a CSV or a public Google Sheet URL."
        )

    # ==========================================
    # 4. Status Feedback & Trigger
    # ==========================================
    
    # Status Indicator Logic
    # Provides immediate visual feedback on whether data is detected.
    if uploaded_files:
        st.success(f"📂 {len(uploaded_files)} file(s) ready to process!", icon="✅")
    elif uploaded_link:
        # Validate Google Sheets URL pattern immediately
        if re.search(r"/d/([a-zA-Z0-9-_]+)", uploaded_link):
            st.success("🔗 Valid Google Sheets URL detected!", icon="✅")
        elif uploaded_link.endswith(".csv"):
            st.success("🌐 Valid Direct CSV Link detected!", icon="✅")
        else:
            st.warning("🔗 Invalid URL format. Please ensure it contains '/d/SHEET_ID'", icon="⚠️")
    else:
        st.info("👈 Waiting for data...", icon="ℹ️")

    # Main Action Button
    # The user must click this to trigger the 'read_files' and 'create_agent' logic.
    upload_btn = st.button(
        "⚡ Initialize & Analyze",
        use_container_width=True,
        disabled=not (uploaded_files or uploaded_link), # Disable button if no data is present
        help="Process the data and wake up the AI Agent."
    )

    st.divider()

    # ==========================================
    # 5. Help & Documentation Section
    # ==========================================
    st.subheader("ℹ️ Help & Guidelines")

    # --- DATA QUALITY DISCLAIMER ---
    # Enhanced explanation to enforce "Clean Data" habits for the user.
    with st.expander("⚠️ Data Quality & Format Guide"):
        st.markdown("""
        **1. 🤖 System Auto-Cleaning**
        To prevent crashes, we automatically perform these actions on upload:
        * **Ghost Rows/Cols:** Removes rows/columns that are 100% empty.
        * **Deduplication:** Removes identical duplicate rows.

        **2. 🫵 Critical User Requirements (MUST READ)**
        To ensure the AI understands your data, your file **MUST** follow these rules:
        
        * **🚫 No Merged Cells:** Unmerge all cells. Merged headers confuse the AI.
        * **📝 Single-Row Header:** The first row must be the header. Avoid complex multi-level headers (e.g., 'Sales' -> 'Q1', 'Q2' stacked).
        * **🔢 Consistent Data Types:** Do not mix text and numbers in one column. 
            * *Good:* `1000`, `2500`
            * *Bad:* `1,000` (string), `2k` (string), `USD 500` (string).
        * **📅 Standard Date Formats:** Use standard formats like `YYYY-MM-DD` or `DD/MM/YYYY`.
        
        > **⚠️ Note:** "Garbage In, Garbage Out."  
        If the data structure is messy (e.g., heavily formatted reports meant for printing), the AI analysis will likely fail or be inaccurate.
        """)

    # --- DATA SOURCE BEHAVIOR (NEW SECTION) ---
    # Explicitly explains the "File vs URL" priority logic to avoid user confusion.
    with st.expander("🔌 Data Source Priority (File vs URL)"):
        st.markdown("""
        **1. 🥇 Priority: Local Files**
        The system prioritizes **Uploaded Files** above all else. 
        * If you have both a file in the uploader AND a URL in the text box, the Agent will **IGNORE the URL** and only analyze the file.
        
        **2. 🚫 No Merging**
        Currently, the system does **not** combine data from different sources. 
        * It is strictly **One Source at a Time** (Either Local Files OR Cloud URL).
        
        **3. 🔄 How to Switch to URL**
        If you want to analyze a Google Sheet URL, you must first **remove all uploaded files** (click the 'X' on the file widget) to force the system to look at the link.
        """)

    # --- USER GUIDE & DOCUMENTATION ---
    # These sections provide self-service support, reducing the need for external explanations.
    # Strict linear flow: API -> Language -> Load Data -> Chat.
    with st.expander("📚 How To Use"):
        st.markdown("""
        **1. 🔑 API Configuration**  
        Enter your **Google Gemini API Key** in the sidebar first. This is required to power the AI engine.
        
        **2. 🌐 Select Language**  
        Choose your preferred response language (**English** or **Indonesian**). 
        
        **3. 📂 Load Data**  
        Upload a **.csv / .xlsx** file OR paste a **Google Sheet URL**. 
        Then, click **'⚡ Initialize & Analyze'** to wake up the AI Agent.
        
        **4. 💬 Start Querying**
        Once connected, type your questions naturally in the chat (e.g., *"What is the total sales trend?"*).
        
        ---
        **💡 Pro Tip:**
        *Want to switch languages mid-conversation?* **Just change it in the sidebar!** The agent will automatically update its settings and answer your next question in the new language. No need to reconnect.
        """)

    # Expandable "FAQ" Section
    # Addresses common user concerns regarding security, data hygiene, and performance.
    with st.expander("❓ FAQ (Frequently Asked Questions)"):
        st.markdown("""
        **Q: Can this agent modify or delete my original files?**  
        A: **No.** The agent operates strictly on a **temporary in-memory copy** of your data using Pandas. It cannot access, overwrite, or delete the original Excel/CSV files on your computer.

        **Q: Is it safe/bad to upload "dirty" or uncleaned data?**  
        A: **It is not dangerous, but it reduces accuracy.** 
        * **System Safety:** We automatically remove completely empty rows/columns and duplicates to prevent system crashes.  
        * **Analysis Accuracy:** However, if a column has mixed formats (e.g., a 'Price' column containing both numbers like `500` and text like `"Five Hundred"`), the AI may fail to calculate sums or generate plots.  
        
        **Tip:** Ensure your column data types are consistent for the best results.

        **Q: Why does it take a few seconds to respond?**  
        A: Unlike standard chatbots, this is a **Reasoning Engine (ReAct)**. For every question, it performs a complex loop:  
        *Thinking* (Planning) $\\rightarrow$ *Coding* (Writing Python) $\\rightarrow$ *Observing* (Executing Code) $\\rightarrow$ *Answering*.  
        This "Thought-Action-Observation" cycle ensures the answer is based on actual calculation, not hallucination.

        **Q: Is my data sent to Google?**  
        A: To function, the Agent sends the **Metadata** (Column Names) and **Relevant Data Snippets** to the Gemini API so the model can understand the context. The data is processed transiently to generate the Python code and response.

        **Q: What happens if I change the language mid-conversation?**  
        A: The system will automatically **re-initialize** the agent to apply the new language persona. Your chat history will be preserved on screen, but the Agent's next reply will strictly follow the new language setting (English or Indonesian).
        """)

    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; font-size: 0.85rem; color: #888;">
            © 2026 <b>Silvio Christian, Joe</b><br>
            Powered by <b>Google Gemini</b> 🚀<br><br>
            <a href="https://www.linkedin.com/in/silvio-christian-joe/" target="_blank" style="text-decoration: none; margin-right: 10px;">🔗 LinkedIn</a>
            <a href="mailto:viochristian12@gmail.com" style="text-decoration: none;">📧 Email</a>
        </div>
        """, 
        unsafe_allow_html=True
    )

# ==========================================
# 6. File Processing & Logic
# ==========================================
if uploaded_files and upload_btn:
    # -----------------------------------------------------------
    # 🔥 SAFETY CHECK: MODE SWITCHING (CLOUD -> LOCAL)
    # -----------------------------------------------------------
    # Detect if the active session currently holds data from a Google Sheet.
    # Logic: If we find a "GSheet" marker in the history, the user is switching data sources.
    if any(f.startswith("GSheet_") for f in st.session_state.processed_files):
        
        # Action: Perform a "Hard Flush" on the memory.
        # This prevents cross-contamination (mixing old Cloud data with new Local files).
        st.session_state.final_df = []          # Reset the main dataframe list
        st.session_state.processed_files = []  # Reset the file tracking history

        # Feedback: Notify the user that the workspace has been auto-cleaned.
        st.toast("🔄 Mode switched! Cleared previous Google Sheet data.", icon="♻️")

    # -----------------------------------------------------------
    # FILE PROCESSING INITIALIZATION
    # -----------------------------------------------------------
    # Prepare lists to track only the new files being uploaded in this cycle.
    new_filenames = []
    files_to_process = []

    try:
        # Filter: Identification of files that have not been processed yet.
        # This prevents re-reading the same file if the user clicks the button multiple times.
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.processed_files:
                files_to_process.append(uploaded_file)

        if not files_to_process:
            # Notify user if all uploaded files are already in the system
            st.toast("All uploaded documents are already in the knowledge base.", icon="ℹ️")
        else:
            # Display a loading spinner while the system reads and validates data
            with st.spinner(f"⏳ Processing {len(files_to_process)} new document(s)..."):
                for uploaded_file in files_to_process:
                    
                    # Attempt to read the file
                    df = read_files(uploaded_file)

                    # Validation 1: Check if file format is supported or readable
                    if df is None:
                        st.warning(f"⚠️ Skipped '{uploaded_file.name}': Format not supported or file is corrupt.")
                        continue

                    # Validation 2: Check if the dataframe has 0 rows initially
                    if df.empty:
                        st.warning(f"⚠️ Skipped '{uploaded_file.name}': The file contains no data (Empty).")
                        continue

                    # -------------------------------------------------------
                    # Data Cleaning 1: Remove "Ghost" Data (Empty Structure)
                    # -------------------------------------------------------
                    # Strategy: We use how='all' to strictly remove only 100% empty rows/cols.
                    # We avoid how='any' to preserve rows that have partial data (important for AI).
                    
                    # 0. Snapshot Dimensions: Capture original size to calculate cleaned data later
                    initial_rows, initial_cols = df.shape

                    # 1. Drop Rows that are completely empty (axis=0)
                    df.dropna(how="all", axis=0, inplace=True)
                            
                    # 2. Drop Columns that are completely empty (axis=1)
                    df.dropna(how="all", axis=1, inplace=True)

                    # 3. Calculate Cleaned Data: Determine how many rows/cols were removed
                    # Logic: Original Count - Current Count = Amount Removed
                    cleaned_rows = initial_rows - df.shape[0]
                    cleaned_cols = initial_cols - df.shape[1]

                    # Feedback: Notify the user if any ghost data was removed
                    # We only show the toast if actual cleaning happened to avoid noise.
                    if cleaned_rows > 0 or cleaned_cols > 0:
                        st.toast(f"🧹 Cleaned '{virtual_filename}': Removed {cleaned_rows} empty rows & {cleaned_cols} empty cols.", icon="✨")

                    # Validation 3: Ensure the file is not empty after cleaning
                    if df.empty:
                        st.warning(f"⚠️ Skipped '{virtual_filename}': File contains only null/empty values.")
                        st.stop()

                    # -------------------------------------------------------
                    # Data Cleaning 2: Handle Redundancy (Duplicates)
                    # -------------------------------------------------------
                    # Calculate duplicate rows before dropping them to report to the user
                    duplicates_count = df.duplicated().sum()
                    
                    if duplicates_count > 0:
                        df.drop_duplicates(inplace=True)
                        st.toast(f"🧹 Removed {duplicates_count} duplicate rows from '{uploaded_file.name}'", icon="✨")

                    # If all checks pass, update the tracking list and the main dataframe
                    new_filenames.append(uploaded_file.name)
                    st.session_state.final_df.append(df)

                # Update the global session state with the new valid files
                st.session_state.processed_files.extend(new_filenames)
                
                # IMPORTANT: Remove 'agent_executor' to force a re-initialization
                # This ensures the AI Agent "learns" the new data in the next chat interaction.
                st.session_state.pop("agent_executor", None)
                
                # Final Success Message
                if new_filenames:
                    st.toast(f"✅ Successfully loaded: {', '.join(new_filenames)}", icon="🚀")

    except Exception as e:
        # ------------------------------------------
        # Smart Processing Error Handling
        # ------------------------------------------
        error_str = str(e).lower()

        # Case 1: Encoding Issues (Common with CSVs from Excel/Different OS)
        if "unicodedecodeerror" in error_str or "utf-8" in error_str:
            st.error(f"🔤 **Encoding Error.** Could not read the file. Please try saving your CSV with 'UTF-8' encoding.", icon="❌")

        # Case 2: Parsing/Format Errors (e.g., uploading an image as .csv)
        elif "tokenizing" in error_str or "parser" in error_str:
            st.error(f"📄 **Format Error.** The file structure is corrupt or invalid. Please check the file content.", icon="📉")

        # Case 3: Memory Issues (File too large for Free Tier)
        elif "memory" in error_str or "allocation" in error_str:
            st.error(f"💾 **Memory Error.** The file is too large to process in this environment. Please try a smaller file.", icon="🛑")

        # Case 4: General Errors
        else:
            st.error(f"❌ **Processing Failed.** An unexpected error occurred: {str(e)}", icon="⚠️")

elif uploaded_link and upload_btn:
    try:
        # Regex to extract the Google Sheet ID (the long alphanumeric string between /d/ and /)
        match_id = re.search(r"/d/([a-zA-Z0-9-_]+)", uploaded_link)

        if not match_id and not uploaded_link.endswith(".csv"):
            # Error handling: Stop execution if the URL is neither a Google Sheet nor a direct CSV.
            st.error("❌ Invalid URL. Please provide a valid Google Sheets link or a direct .csv link.", icon="🚫")
            st.stop()
        elif uploaded_link.endswith(".csv"):
            # Feedback: Notify user that a direct CSV link was detected.
            st.toast("🌐 Direct CSV Link detected!", icon="✅")

            export_url = uploaded_link
            filename = uploaded_link.split("/")[-1]
            
            # Hack: Use "GSheet_" prefix to trigger the session reset logic automatically.
            virtual_filename = f"GSheet_{filename}"
        else:
            # Notify user that the connection process has started
            st.toast("⏳ Connecting to Google Sheets...", icon="🔗")

            sheet_id = match_id.group(1)
            virtual_filename = f"GSheet_{sheet_id}"

            # Check if a specific Sheet GID (Grid ID) is present in the URL
            # This ensures we pull the specific tab the user is looking at, not just the first one.
            match_gid = re.search(r"[?#]gid=([0-9]+)", uploaded_link)
            
            if match_gid:
                gid = match_gid.group(1)
                # Construct export parameters for a specific tab
                params = f"format=csv&gid={gid}"
                
                # Feedback: Inform the user that a specific tab (GID) is being targeted
                st.toast(f"📑 Specific tab detected (GID: {gid}). Processing...", icon="✅")
            else:
                # Default to the first tab if no GID is found
                params = "format=csv"
                
                # Feedback: Inform the user that the default/first tab is being used
                st.toast("📑 No GID found. Processing default tab...", icon="ℹ️")

            # Construct the direct export URL
            export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?{params}"

        # Load the data directly into Pandas
        df = pd.read_csv(export_url)

        # Validation 1: Check if file format is supported or readable
        if df is None:
            st.warning(f"⚠️ Skipped '{virtual_filename}': Format not supported or file is corrupt.")
            st.stop()

        # Validation 2: Check if the dataframe has 0 rows initially
        if df.empty:
            st.warning(f"⚠️ Skipped '{virtual_filename}': The file contains no data (Empty).")
            st.stop()

        # -------------------------------------------------------
        # Data Cleaning 1: Remove "Ghost" Data (Empty Structure)
        # -------------------------------------------------------
        # Strategy: We use how='all' to strictly remove only 100% empty rows/cols.
        # We avoid how='any' to preserve rows that have partial data (important for AI).
            
        # 0. Snapshot Dimensions: Capture original size to calculate cleaned data later
        initial_rows, initial_cols = df.shape

        # 1. Drop Rows that are completely empty (axis=0)
        df.dropna(how="all", axis=0, inplace=True)
                    
        # 2. Drop Columns that are completely empty (axis=1)
        df.dropna(how="all", axis=1, inplace=True)

        # 3. Calculate Cleaned Data: Determine how many rows/cols were removed
        # Logic: Original Count - Current Count = Amount Removed
        cleaned_rows = initial_rows - df.shape[0]
        cleaned_cols = initial_cols - df.shape[1]

        # Feedback: Notify the user if any ghost data was removed
        # We only show the toast if actual cleaning happened to avoid noise.
        if cleaned_rows > 0 or cleaned_cols > 0:
            st.toast(f"🧹 Cleaned '{virtual_filename}': Removed {cleaned_rows} empty rows & {cleaned_cols} empty cols.", icon="✨")

        # Validation 3: Ensure the file is not empty after cleaning
        if df.empty:
            st.warning(f"⚠️ Skipped '{virtual_filename}': File contains only null/empty values.")
            st.stop()

        # -------------------------------------------------------
        # Data Cleaning 2: Handle Redundancy (Duplicates)
        # -------------------------------------------------------
        # Calculate duplicate rows before dropping them to report to the user
        duplicates_count = df.duplicated().sum()
                    
        if duplicates_count > 0:
            df.drop_duplicates(inplace=True)
            st.toast(f"🧹 Removed {duplicates_count} duplicate rows from '{virtual_filename}'", icon="✨")

        # -------------------------------------------------------
        # 🔥 DATA OVERWRITE: SINGLE SOURCE ENFORCEMENT
        # -------------------------------------------------------
        # Unlike multi-file uploads, URL imports operate in "Single Source" mode.
        # We strictly OVERWRITE (=) the existing session data instead of appending.

        # 1. Reset the Main Dataframe
        # We wrap the single dataframe in a list [df] to maintain type consistency 
        # (List of DataFrames) while discarding any previously loaded data.
        st.session_state.final_df = [df]

        # 2. Update Tracking History
        # We replace the tracking list with this specific Google Sheet ID.
        # This marks the session as "Cloud Mode" for future safety checks.
        st.session_state.processed_files = [virtual_filename]
            
        # IMPORTANT: Reset the agent executor so it rebuilds with the new cloud data
        st.session_state.pop("agent_executor", None)

        # Success notification
        st.toast("✅ Cloud data imported successfully!", icon="🚀")

    except Exception as e:
        # ------------------------------------------
        # Smart Import Error Handling
        # ------------------------------------------
        error_str = str(e).lower()

        # Case 1: Permission Denied (Private Sheet) - MOST COMMON
        if "403" in error_str or "forbidden" in error_str:
            st.error(
                "🔒 **Access Denied.** The Google Sheet is Private.\n"
                "**Solution:** Open the Sheet -> Click 'Share' -> Change to **'Anyone with the link'** -> Try again.", 
                icon="🚫"
            )

        # Case 2: Sheet Not Found (Deleted or Wrong ID)
        elif "404" in error_str or "not found" in error_str:
            st.error("🔍 **Sheet Not Found.** The URL is incorrect or the Sheet has been deleted.", icon="❓")

        # Case 3: Empty Data / HTML Response (Usually happens if the link redirects to a login page)
        elif "parsererror" in error_str or "no columns" in error_str:
            st.error("📄 **Format Error.** Could not read CSV data. Ensure the Sheet is not empty and is publicly accessible.", icon="📉")

        # Case 4: Network / Connection Issues
        elif "name resolution" in error_str or "connection" in error_str:
            st.error("🌐 **Connection Error.** Failed to reach Google Servers. Check your internet connection.", icon="📡")

        # Case 5: General Error
        else:
            st.error(f"❌ **Import Failed.** An unexpected error occurred: {str(e)}", icon="⚠️")

elif not (uploaded_files or uploaded_link):
    # Default State: Instructions when no data is loaded yet
    st.info(
        "👈 **Awaiting Data Source**\n\n"
        "Please upload a **CSV/Excel file** OR paste a **Google Sheets URL** in the sidebar,\n"
        "then click **'⚡ Initialize & Analyze'** to start."
    )

# ==========================================
# 7. AI Engine & Memory Initialization
# ==========================================
# Check if the user has provided the API Key in the sidebar
if st.session_state.google_api_key:
    
    # Implement Singleton Pattern:
    # Only initialize the LLM if it hasn't been created yet.
    # This prevents reloading the model on every user interaction (clicks/typing), saving resources.
    if st.session_state.llm is None:
        try: 
            # Attempt to initialize the Gemini Model
            # We use specific parameters to ensure stability.
            st.session_state.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                google_api_key=st.session_state.google_api_key,
                # Temperature set to 0.3:
                # Low temperature ensures the model is "focused" and "deterministic".
                # This is critical for data analysis agents to generate accurate Python/SQL code.
                temperature=0.3 
            )
            
            # Success Notification: Let the user know the brain is active.
            st.toast("AI Engine Online & Ready!", icon="🧠")

        except Exception as e:
            # ------------------------------------------
            # Smart Initialization Error Handling
            # ------------------------------------------
            # IMPORTANT: Reset the LLM state to None.
            # This allows the user to correct the API Key and try again without refreshing.
            st.session_state.llm = None
            
            error_str = str(e).lower()

            # Case 1: Invalid API Key / Authentication Failed
            if "api_key" in error_str or "403" in error_str or "permission denied" in error_str:
                 st.error("🔑 **Authentication Failed.** Your API Key appears to be invalid or inactive. Please check specifically for typos.", icon="🚫")

            # Case 2: Model Not Found (e.g., if 'gemini-2.5-flash' is restricted or misspelled)
            elif "not found" in error_str or "404" in error_str:
                 st.error(f"🤖 **Model Error.** The model 'gemini-2.5-flash' is not accessible with this key/region. Try using 'gemini-1.5-flash'.", icon="❓")

            # Case 3: Connection / Network Issues
            elif "connection" in error_str or "failed to connect" in error_str:
                 st.error("🌐 **Connection Error.** Failed to reach Google Servers. Please check your internet connection.", icon="📡")
            
            # Case 4: Quota Exceeded (Billing)
            elif "429" in error_str or "quota" in error_str:
                 st.error("⏳ **Quota Exceeded.** Your Google Cloud Project has run out of credits or hit a rate limit.", icon="🛑")

            # Case 5: General / Unexpected Errors
            else:
                 st.error(f"❌ **Initialization Failed.** An unexpected error occurred: {str(e)}", icon="🚨")

else:
    # Warning: Block usage until the key is provided.
    st.warning("🔑 API Key Missing. Please enter your Google API Key in the sidebar to proceed.", icon="⚠️")

# Initialize Chat Memory
# We use ConversationBufferMemory to store the history of the chat.
# This allows the Agent to remember previous questions (e.g., "Make a plot for that").
if st.session_state.agent_memory is None:
    st.session_state.agent_memory = ConversationBufferMemory(
        memory_key="chat_history", 
        return_messages=True
    )  
 
# ==========================================
# 8. Agent Logic & Prompt Engineering
# ==========================================
# Initialize the Agent Executor only if:
# 1. It doesn't exist yet (Singleton pattern).
# 2. There is actual data (final_df) to analyze.
if "agent_executor" not in st.session_state and st.session_state.final_df:
    try:
        # ------------------------------------------
        # System Prompt Definition
        # ------------------------------------------
        custom_prefix = f"""
        You are an expert Data Analyst working with pandas DataFrames.
        
        ### DATA STRUCTURE
        - The primary dataframe is named `df1`.
        - If multiple files were uploaded, they are named `df2`, `df3`, etc.
        - **IMPORTANT:** If the user's query requires data from multiple files, you MUST **merge, join, or concatenate** them first using pandas logic before analyzing.

        ### 1. LANGUAGE ENFORCEMENT (ABSOLUTE RULE)
        - **OUTPUT LANGUAGE:** You MUST respond ONLY in **{chosen_language}**.
        - **TRANSLATION:** Translate ALL your thoughts and final answers into **{chosen_language}**.
        - **INPUT HANDLING:** If the user asks in a different language (e.g., Indonesian, Spanish), you must understand their intent mentally, but **TRANSLATE your final response** into **{chosen_language}**.
        - **EXAMPLE:** If User asks "Tentang apa ini?" (Indonesian) and chosen language is "English", you MUST answer "This document is about..." (English). **DO NOT** answer in Indonesian.
        - **TONE:** Professional, helpful, and natural. Do NOT use rigid numbered lists (like "1. Answer, 2. Insight"). Instead, weave the answer, the insight, and the recommendation into **normal, cohesive paragraphs**.

        ### 2. CRITICAL: PARSING ERROR PREVENTION
        To avoid the "Invalid Format" error, you must follow this logic strictly:

        **CASE A: DATA QUERY / VISUALIZATION** (e.g., "Total?", "Plot?", "Top 5?")
        - You **MUST** use the `python_repl_ast` tool.
        - **FORMAT:**
            Thought: <Reasoning>
            Action: python_repl_ast
            Action Input: <The Python Code>
            Observation: <The Result>
            Final Answer: <Your natural explanation>
        - **CRITICAL RULE:** After receiving the `Observation:`, you **MUST** immediately start your response with `Final Answer:`. **DO NOT** write `Thought:` again. If you write `Thought:` without an `Action:`, the system will crash.
        - **IMPORTANT:** 1. NEVER paste the raw Python code inside the "Final Answer". The code is for the tool, not the user.
            2. If plotting, just create the plot object (e.g., `df.plot()`). Do NOT say "Here is the code". Just say "I have visualized the data...".

        **CASE B: GENERAL CONVERSATION** (e.g., "Hello", "Thanks", "Who are you?")
        - **DO NOT** use "Thought" or "Action".
        - Skip directly to the Final Answer.
        - **FORMAT:**
            Final Answer: <Your natural response>

        ### 3. SMART CONTEXT & DEEP ANALYSIS (UPDATED)
        - **Visuals:** If the user asks for a plot OR modifies a previous plot (e.g., "Change to top 5"), you MUST generate a new plot using matplotlib.
        - **Insights:** Always include a brief insight (why this result matters) in your Final Answer.
        
        - **🔥 DEEP DIVE LOGIC (CRITICAL):** If the user asks "Why?", "Reason?", or "Explain the trend?", you must NOT rely on general assumptions.
          1. **Investigate:** Write Python code to check correlations with other columns (e.g., Price, Rating, Discount, Date).
          2. **Prove It:** Compare averages or counts to find the *real* cause.
          3. **Example:** Don't just say "Casual is popular because it's comfy." -> Check if "Casual" has the lowest average price or highest rating in the data.

        ### 4. MEMORY
        Current Conversation History:
        {{chat_history}}
        """

        # ------------------------------------------
        # Agent Initialization
        # ------------------------------------------
        # We use the 'pandas_dataframe_agent' which is optimized for tabular data.
        st.session_state.agent_executor = create_pandas_dataframe_agent(
            llm=st.session_state.llm,
            df=st.session_state.final_df,
            allow_dangerous_code=True,       # Required to execute Python code generation
            handle_parsing_errors=True,      # Tries to recover if the LLM messes up the format
            prefix=custom_prefix,            # Injecting our custom system prompt
            agent_executor_kwargs={
                "memory": st.session_state.agent_memory,
                "handle_parsing_errors": True # Double enforcement of error handling
            }
        )

    except Exception as e:
        # ------------------------------------------
        # Smart Initialization Error Handling
        # ------------------------------------------
        error_str = str(e).lower()

        # Case 1: DataFrame Structure Issues (e.g., MultiIndex or unsupported types)
        if "dataframe" in error_str or "index" in error_str:
            st.error("📊 **Data Error.** The uploaded file has a complex structure (e.g., MultiIndex) that the Agent cannot process. Please simplify the header.", icon="📉")
        
        # Case 2: LLM Not Ready (NoneType)
        elif "llm" in error_str or "none" in error_str:
             st.error("🧠 **AI Engine Error.** The Language Model was not initialized correctly. Please check your API Key and reload.", icon="🚫")

        # Case 3: Missing Dependencies (ImportError)
        elif "module" in error_str or "import" in error_str:
             st.error("📦 **Dependency Error.** A required library is missing. Please check `requirements.txt`.", icon="📦")

        # Case 4: General Initialization Crash
        else:
             st.error(f"❌ **Agent Creation Failed.** Unexpected error: {str(e)}", icon="🚨")

# ==========================================
# 9. Chat Interface & Logic
# ==========================================
#
# ------------------------------------------
# A. Display Chat History
# ------------------------------------------
# Iterate through the stored session state messages to render previous conversation turns.
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        # Render the image first if it exists in the message dictionary
        # This ensures visual consistency (Chart -> Explanation).
        if "image" in msg:
            st.image(msg["image"])
    
            # 🔘 DOWNLOAD BUTTON
            st.download_button(
                label="📥 Download Plot",
                data=msg["image"],
                file_name="analysis_chart.png",
                mime="image/png",
                key=f"download_btn_{i}" # Unique key per message
            )
        
        # Render the text content
        st.markdown(msg["content"])

# ------------------------------------------
# B. Capture User Input
# ------------------------------------------
if prompt_text := st.chat_input("💬 Ask questions about your data..."):
    
    # Validation: Ensure data is loaded before allowing queries
    if not st.session_state.final_df:
        st.warning("⚠️ No data found! Please upload a file or URL in the sidebar first.", icon="🚫")
    
    else:
        # 1. Display and save the User's message
        st.session_state.messages.append({"role": "human", "content": prompt_text})
        st.chat_message("human").write(prompt_text)

        # 2. Generate AI Response
        with st.chat_message("ai"):
            try:
                # Initialize the Streamlit Callback Handler
                # This enables the "Thinking..." animation and shows the agent's internal thought process.
                st_callback = StreamlitCallbackHandler(st.container())

                # Execute the Agent
                response = st.session_state.agent_executor.invoke(
                    {"input": prompt_text},
                    {"callbacks": [st_callback]}
                )

                # ------------------------------------------
                # C. Check for Generated Visualizations
                # ------------------------------------------
                # plt.get_fignums() returns true if there are active matplotlib figures.
                if plt.get_fignums():
                    
                    # 1. Retrieve the active figure
                    fig = plt.gcf() 
                    
                    # 2. Display the plot immediately to the user
                    st.pyplot(fig) 

                    # 3. Save the plot to an in-memory buffer
                    # We use io.BytesIO to store the image binary data without saving to the disk.
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format="png")
                    img_buffer.seek(0) # Reset buffer position to the beginning

                    # 3.5. We provide a button so the user can save the analysis chart locally.
                    st.download_button(
                        label="📥 Download Plot",
                        data=img_buffer,
                        file_name="analysis_chart.png",
                        mime="image/png",
                        key=f"download_btn_{len(st.session_state.messages)}" # Unique key per message
                    )

                    # 4. Display the textual explanation (if any)
                    if "output" in response and len(response["output"]) > 0:
                        st.markdown(response["output"])

                    # 5. Append BOTH text and image to the session history
                    st.session_state.messages.append({
                        "role": "ai", 
                        "content": response["output"], 
                        "image": img_buffer
                    })
                    
                    # 6. Cleanup: Clear the figure to prevent "bleeding" into future plots
                    plt.clf()
                    plt.close()
                    
                else:
                    # ------------------------------------------
                    # D. Handle Text-Only Responses
                    # ------------------------------------------
                    if "output" in response and len(response["output"]) > 0:
                        st.markdown(response["output"])

                    # Append only text to history
                    st.session_state.messages.append({
                        "role": "ai", 
                        "content": response["output"]
                    })

            except Exception as e:
                # ------------------------------------------
                # E. Smart Error Handling
                # ------------------------------------------
                error_str = str(e).lower()

                # Case 1: Google API Quota Exceeded (429)
                if "429" in error_str or "quota" in error_str or "resource exhausted" in error_str:
                    st.error("⏳ **API Quota Exceeded.** You are sending requests too fast. Please wait a moment.", icon="🛑")

                # Case 2: Invalid API Key or Authentication Error (400/403)
                elif "api_key" in error_str or "403" in error_str or "permission denied" in error_str:
                    st.error("🔑 **Authentication Failed.** Please check if your Google API Key is correct/active.", icon="🚫")

                # Case 3: Model Not Found (e.g., using gemini-2.5-flash if not available)
                elif "not found" in error_str or "404" in error_str:
                    st.error("🤖 **Model Error.** The specified AI model version is not available. Try changing the model version.", icon="❓")

                # Case 4: Parsing Error (LLM Output Formatting)
                elif "parsing" in error_str or "output parser" in error_str:
                    st.error("🧩 **Parsing Error.** The AI got confused with the format. Please ask the question again specifically.", icon="😵‍💫")

                # Case 5: Python Code Execution Error (Pandas/Matplotlib issues)
                elif "nameerror" in error_str or "syntaxerror" in error_str or "keyerror" in error_str:
                     st.error(f"🐍 **Code Execution Error.** The AI tried to run invalid Python code. \nDetails: `{error_str}`", icon="📉")

                # Case 6: General / Unexpected Errors
                else:
                    st.error(f"❌ **Unexpected Error:** {str(e)}", icon="🚨")