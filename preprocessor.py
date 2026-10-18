import re
import pandas as pd

def preprocess(data):
    # Auto-detect the date format
    pattern_ios = r'\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}:\d{2}\]\s'
    pattern_android_24hr = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s'
    pattern_android_12hr = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s(?:am|pm|AM|PM|a\.m\.|p\.m\.)\s-\s'

    if re.search(pattern_ios, data):
        pattern = pattern_ios
        is_ios = True
    elif re.search(pattern_android_12hr, data):
        pattern = pattern_android_12hr
        is_ios = False
    else:
        pattern = pattern_android_24hr
        is_ios = False

    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)

    df = pd.DataFrame({'user_message': messages, 'message_date': dates})
    
    # Check if empty to prevent AttributeError crash
    if df.empty:
        return df

    # Ensure it's treated as a string before applying .str accessor
    df['message_date'] = df['message_date'].astype(str)

    # Clean up dates based on platform
    if is_ios:
        df['message_date'] = df['message_date'].str.replace(r'\[|\]', '', regex=True).str.strip()
    else:
        df['message_date'] = df['message_date'].str.replace(r'\s-\s$', '', regex=True).str.strip()

    # Convert to datetime safely
    df['message_date'] = pd.to_datetime(df['message_date'], dayfirst=True, errors='coerce')

    df.rename(columns={'message_date': 'date'}, inplace=True)

    # Drop any rows where datetime conversion failed
    df.dropna(subset=['date'], inplace=True)

    users = []
    messages = []
    for message in df['user_message']:
        entry = re.split(r'([\w\W]+?):\s', message)
        if entry[1:]:  # user name
            users.append(entry[1])
            messages.append(" ".join(entry[2:]))
        else:
            users.append('group_notification')
            messages.append(entry[0])

    df['user'] = users
    df['message'] = messages
    df.drop(columns=['user_message'], inplace=True)

    if df.empty:
        return df

    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    period = []
    for hour in df['hour']:
        if pd.isna(hour):
            period.append("Unknown")
            continue
        hour = int(hour)
        if hour == 23:
            period.append(str(hour) + "-" + str('00'))
        elif hour == 0:
            period.append(str('00') + "-" + str(hour + 1))
        else:
            period.append(str(hour) + "-" + str(hour + 1))

    df['period'] = period

    return df