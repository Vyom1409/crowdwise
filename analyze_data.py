import pandas as pd
import numpy as np
import time

print('Loading dataset...')
t0 = time.time()
df = pd.read_csv(r'C:\Users\LENOVO\.gemini\antigravity\scratch\crowdedness-journey-planner\data\October-Delhi.csv')
print(f'Data loaded in {time.time()-t0:.2f}s. Parsing timestamps...')

print(f'Data loaded in {time.time()-t0:.2f}s. Parsing timestamps with fast string parsing...')

df['date_str'] = df['created_at'].str[:10]
df['hour'] = df['created_at'].str[11:13].astype(int)
unique_dates = pd.Series(df['date_str'].unique())
date_to_dow = pd.to_datetime(unique_dates).dt.day_name()
date_to_dow_map = dict(zip(unique_dates, date_to_dow))
df['day_of_week'] = df['date_str'].map(date_to_dow_map)
df['is_weekend'] = df['day_of_week'].isin(['Saturday', 'Sunday'])

print('\n=== HOURLY TICKET DISTRIBUTION ===')
hourly = df.groupby('hour')['passenger_count'].agg(['count', 'sum'])
print(hourly)

print('\n=== DAY OF WEEK DISTRIBUTION ===')
dow = df.groupby('day_of_week')['passenger_count'].agg(['count', 'sum']).reindex(
    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
)
print(dow)

print('\n=== VEHICLE NUMBER STATS ===')
non_null_veh = df[df['vehicle_number'].notnull()]
print(f'Total tickets with vehicle_number: {len(non_null_veh):,} ({len(non_null_veh)/len(df)*100:.1f}%)')
print(f"Unique vehicles: {non_null_veh['vehicle_number'].nunique():,}")

print('\n=== TOP 20 ROUTES ===')
top_routes = df.groupby('route')['passenger_count'].agg(['count', 'sum']).sort_values('sum', ascending=False).head(20)
print(top_routes)

print('\n=== TRIP RECONSTRUCTION EXPERIMENT ===')
sample_veh = non_null_veh['vehicle_number'].value_counts().index[0]
sample_veh_data = non_null_veh[non_null_veh['vehicle_number'] == sample_veh].sort_values('created_at')
print(f"Top vehicle: {sample_veh} with {len(sample_veh_data)} tickets across dates")
sample_day = sample_veh_data['date_str'].value_counts().index[0]
day_tickets = sample_veh_data[sample_veh_data['date_str'] == sample_day]
print(f"Sample day {sample_day} for vehicle {sample_veh}: {len(day_tickets)} tickets")
print(day_tickets[['created_at', 'route', 'start_stop_name', 'end_stop_name', 'passenger_count']].head(10))
