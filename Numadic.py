import pandas as pd
from datetime import datetime
import os
from pytz import timezone
import math




class Numadic_vehicle_asset_report:
    def __init__(self):
        self.csv_files = { 
            'Trip-Info': r'path_of_your_file\Trip-Info.csv',
            'vehicle-trails': r'path_of_your_file/NU-raw-location-dump/EOL-dump/'
            }

    def check_csv_exists(self,file_path):
        return os.path.isfile(file_path) and file_path.endswith('.csv')


    def csv_reader_using_pandas(self,csv_file='', start_time=None, end_time=None):
        """
        Reads a CSV file and optionally filters rows based on a date range.

        Parameters:
        csv_file : Path to the CSV file.
        start_time : Start time in epoch format. Default is None.
        end_time : End time in epoch format. Default is None.

        Returns:Filtered DataFrame if date range is provided, otherwise the entire DataFrame.
        """
        try:
            if not csv_file:
                raise ValueError("The csv_file parameter must be provided.")
            
            # Read the CSV file
            df = pd.read_csv(csv_file)
            tz = timezone("Asia/Kolkata" )
            if start_time is not None and end_time is not None:
                start_time = pd.to_datetime(start_time, unit='s', utc=True).tz_convert('Asia/Kolkata')
                end_time = pd.to_datetime(end_time, unit='s', utc=True).tz_convert('Asia/Kolkata')
                print("Start time: %s, End time: %s" % (start_time, end_time))  
                if 'date_time' not in df.columns:
                    raise ValueError("The CSV file must contain a 'date_time' column.")
                
                # Convert the 'date_time' column to datetime format
                df['date_time'] = pd.to_datetime(df['date_time'], format='%Y%m%d%H%M%S').dt.tz_localize('Asia/Kolkata')
                # Filter the DataFrame based on the date range
                filtered_df = df[(df['date_time'] >= start_time) & (df['date_time'] <= end_time)]
                print(filtered_df)
                return filtered_df
            else:
                return df

        except Exception as e:
            print('Error in getting data from the %s: %s' % (csv_file, e))
            return pd.DataFrame()

    def vehicle_asset_reporter(self,start_time, end_time):
        """
        Processes based on the time range given in epoch format
        returns
        """
        try:
            dataframes = []
            num_trips_completed = {}
            csv_file = self.csv_files['Trip-Info']
            trips_completed = self.csv_reader_using_pandas(csv_file, start_time, end_time)
            if trips_completed.empty:
                raise Exception('No data in this time range %s::%s' % (start_time, end_time))
            for trips in trips_completed['vehicle_number']:
                Transporter_Name = ''
                if not Transporter_Name : Transporter_Name = trips_completed['transporter_name']
                vehicle_trail_file = os.path.join(self.csv_files['vehicle-trails'], "%s.csv" % trips)
                if self.check_csv_exists(vehicle_trail_file):
                    open_vehicle_trail = self.csv_reader_using_pandas(vehicle_trail_file)
                    if not open_vehicle_trail.empty:
                        trip_details_of_vehicle = open_vehicle_trail

                        #caliculate the trip cmpletion
                        license_plate_number = trip_details_of_vehicle.iloc[0]['lic_plate_no']
                        if license_plate_number in num_trips_completed:
                            num_trips_completed[license_plate_number] += 1
                            continue
                        else:
                            num_trips_completed[license_plate_number] = 1
                        #caliculate the distance
                        if 'lat' not in trip_details_of_vehicle.columns or 'lon' not in trip_details_of_vehicle.columns:
                            raise ValueError("The CSV file must contain 'lat' and 'lon' columns.")
                        
                        # Initialize parameters for total

                        total_distance = 0.0
                        total_osf = 0
                        total_speed = 0
                        license_plate_number = ''

                        # Iterate through the rows, calculating the distance between each pair of consecutive points
                        for index, row in trip_details_of_vehicle.iterrows():
                            if index > 0:  # Skip the first row as there's no previous row to compare
                                lat1, lon1 = trip_details_of_vehicle.loc[index - 1, ['lat', 'lon']]
                                lat2, lon2 = row['lat'], row['lon']
                                distance = self.haversine(lat1, lon1, lat2, lon2)
                                
                                if row['osf'] == True:
                                    total_osf += 1
                                    
                                total_speed += row['spd'] if not math.isnan(row['spd']) else 0
                                total_distance += distance if not math.isnan(distance) else 0

                                if not license_plate_number: license_plate_number = row['lic_plate_no']
                                print(index,row)
                        print('Total distance for vehicle %s: %.2f km,total over spees %s' % (trips, total_distance,total_osf))
                        average_speed = total_speed / len(trip_details_of_vehicle)

                        iteration_data = pd.DataFrame({
                            'License plate number': [license_plate_number],
                            'Distance': [total_distance],
                            'Number of Trips Completed': [num_trips_completed[license_plate_number]],
                            'Average Speed': [average_speed],
                            'Transporter Name': [Transporter_Name],
                            'Number of Speed Violations': [total_osf]
                        })
                        dataframes.append(iteration_data)
                    else:
                        print('No Data Available in %s' %vehicle_trail_file)
                else:
                    print('%s vehicle trail file does not exist' %vehicle_trail_file)
            if dataframes:
                result_df = pd.concat(dataframes, ignore_index=True)
                # Write the combined DataFrame to an Excel file
                self.write_to_excel(result_df)
                # result_df.to_excel('vehicle_data.xlsx', index=False)
            else:
                print("No data to write to the Excel file.")
        except Exception as e:
            print('Error in vehicle_asset_reporter: %s' % e)


    def write_to_excel(self,df, file_name='vehicle_data.xlsx'):
        """
        Takes the dataframe dumps into excel file
        """
        if not df.empty:
            df.to_excel(file_name, index=False)
        else:
            print("No data to write to the Excel file.")


    def haversine(self,lat1, lon1, lat2, lon2):
        """
        Calculate the distance between two points 
        Parameters:
        lat1, lon1: Latitude and Longitude of point 1 
        lat2, lon2: Latitude and Longitude of point 2 
        
        Returns:
        Distance between the two points in kilometers.
        """
        # Radius of the Earth in kilometers
        R = 6371.0

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Apply the Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # Distance in kilometers
        distance = R * c

        return distance


asset_reort = Numadic_vehicle_asset_report()



start_time = '1519843271'  #self.yyyymmddhhmmss_to_epoch('20180301001111')  # Example start time in epoch
end_time = '1519846932' #self.yyyymmddhhmmss_to_epoch('20180301011212')    # Example end time in epoch

asset_reort.vehicle_asset_reporter(start_time, end_time)


# def yyyymmddhhmmss_to_epoch(timestamp_str):
    
#     dt = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
#     epoch_time = int(dt.timestamp())
#     return epoch_time
