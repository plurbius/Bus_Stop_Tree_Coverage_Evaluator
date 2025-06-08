## Overview: This code creates a list of bus stops in Washington DC most suitable to have trees planted at them. The code uses five metrics: High ridership,  Minority Population, Elderly Population, High poverty rates, and tempurature data to calculate suitabilty. 
## The code begins by creating a buffer layer around the bus stops to layer calculate the number of trees with a 30 ft range and combining all metric data into one table. Then an MCE was created to find the most suitable sites for trees. 
## This was done by calculating the z-scores for all metrics at all bus stop points, then standardizing all of the metric z-scores into a coomon scoring system. Lastly, each metric was seperatly weighted, and a final MCE was partially weighted for all metrics. 
## Finally, with each bus stop's MCE value calculated, the data set was limited to only bus stops without trees currently, and the top 10 most suitable bus stops were listed. 
## For this code, the datasets used were: A boundary of Washinghton DC, DC bus stops, a dataset of trees in DC, a tempurarture dataset, bus ridership data, and DC demographic data, DC economc data, 

#%%
import arcpy
from arcpy.sa import *
arcpy.env.workspace = r"Project.gdb"
arcpy.env.overwriteOutput = True

##  Add temperature data to point features (Metro_Clip) by extracting temperature values from raster (Temperature_Clip). This operation creates a new point feature class with temperature data for each point.
ExtractValuesToPoints(in_point_features="Metro_Clip",
                        in_raster="Temperature_clip",
                        out_point_features="Temp_Points")
print("You have created a new point feature called 'Temp_Points'.\n")

## Creates (Metro_Buffer_30) a buffer zone of 30 feet around each temperature point. This helps in defining the area around bus stops where trees could provide meaningful shade.
arcpy.analysis.Buffer(in_features="Temp_Points",
                        out_feature_class=r"Outputs.gdb\Metro_Buffer_30",
                        buffer_distance_or_field="30 Feet")
print("You successfully created a buffer around your temperature points!\n")

## Perform spatial joins with tree data (DC_Trees_1)  and ridership data (Metrobus_Ridership_Stop_Grid)
## These join operations combine the buffer zone data with tree data and ridership data within the same geographic area.
arcpy.management.AddSpatialJoin(target_features=r"Outputs.gdb\Metro_Buffer_30",
                                join_features="DC_Trees_1",
                                match_option="INTERSECT")

arcpy.management.AddSpatialJoin(target_features=r"Outputs.gdb\Metro_Buffer_30",
                                join_features="Metrobus_Ridership_Stop_Grid",
                                match_option="INTERSECT")

print("The tree data has been joined to the ridership data!\n")

## Create a feature layer for the buffer with tree and ridership data for easier manipulation (Metro_Buffer_Trees_Ridership_LYR)

arcpy.management.MakeFeatureLayer(in_features=r"Outputs.gdb\Metro_Buffer_30",
                                    out_layer=r"Outputs.gdb\Metro_Buffer_Trees_Ridership_LYR")
## Copy the feature layer to a new feature class to preserve the data (Metro_Buffer_Trees_Ridership_LYR)

arcpy.management.CopyFeatures(in_features=r"Outputs.gdb\Metro_Buffer_Trees_Ridership_LYR",
                                out_feature_class=r"Outputs.gdb\Metro_Buffer_Trees_Ridership")
## Calculate fields for demographics and economics (percentages for minorities and elderly) by census tract ((DC_Data) The calculations are based on census data to determine the percentage of minorities and elderly people.

print("You have successfully created a new feature class called 'Metro_Buffer_Trees_Ridership!'\n")

arcpy.management.CalculateField(in_table="DC_Data",
                                field="Minority_Percent",
                                expression="((!DP05_0033E! - !DP05_0037E!) / !DP05_0033E!) * 100",
                                expression_type="PYTHON3",
                                field_type="FLOAT")

arcpy.management.CalculateField(in_table="DC_Data",
                                field="Elder_Percent",
                                expression="((!DP05_0029E!) / !DP05_0033E!) * 100",
                                expression_type="PYTHON3",
                                field_type="FLOAT")

print("The minority and elderly percentage fields have been calculated.\n")

## Spatially join demographic data (DC_Data) to the buffer with trees and ridership (Metro_Buffer_Trees_Ridership) 
## This step adds demographic data to our buffer zones, which now include tree and ridership data.


arcpy.management.AddSpatialJoin(target_features=r"Outputs.gdb\\Metro_Buffer_Trees_Ridership",
                                join_features="DC_Data",
                                match_option="INTERSECT")

## Create another feature layer for the buffer with added demographic data (Metro_Buffer_Data_LYR)

arcpy.management.MakeFeatureLayer(in_features=r"Outputs.gdb\Metro_Buffer_Trees_Ridership",
                                    out_layer=r"Outputs.gdb\Metro_Buffer_Data_LYR")

## Copy the updated feature layer to a new feature class (Metro_Buffer_Data)

arcpy.management.CopyFeatures(in_features=r"Outputs.gdb\Metro_Buffer_Data_LYR",
                                out_feature_class=r"Outputs.gdb\Metro_Buffer_Data")

print("The final feature class with all necessary and relevant data for our MCE has been created!\n")


## Calculate statistics, specifically the mean and standard deviation, for each MCE variable in the Metro_Buffer_Data layer 
## This calculates the mean and standard deviation for temperature, ridership, trees, poverty, minority percentage, and elderly percentage. 
## This first section of code creates variables for each of the fields names so that they can be used to identify relevant fields for review by the arcpy.analysis.Statistics. These statistical values were stored in STATS_TABLE

fields = arcpy.ListFields(r"Outputs.gdb\Metro_Buffer_Data")
temp = fields[79].name
rider = fields[112].name
trees = fields[83].name
poverty = fields[144].name
minority = fields[151].name
elderly = fields[152].name

arcpy.analysis.Statistics(in_table=r"Outputs.gdb\Metro_Buffer_Data",
                          out_table=r"Outputs.gdb\STATS_TABLE",
                          statistics_fields=[[temp, "MEAN"],[temp, "STD"],[rider, "MEAN"],[rider, "STD"],[trees, "MEAN"],[trees, "STD"],
                          [poverty, "MEAN"],[poverty, "STD"],[minority, "MEAN"],[minority, "STD"],[elderly, "MEAN"],[elderly, "STD"]])

print("You calculated the means and standard deviations of all the fields you need for the MCE!\n")

## Add new fields to store the calculated mean and standard deviation values

arcpy.management.AddFields(in_table=r"Outputs.gdb\Metro_Buffer_Data",
                           field_description=[["Temp_Mean", "FLOAT"], ["Temp_STD", "FLOAT"],
                                              ["Rider_Mean", "FLOAT"],["Rider_STD", "FLOAT"],
                                              ["Trees_Mean", "FLOAT"],["Trees_STD", "FLOAT"],
                                              ["Poverty_Mean", "FLOAT"],["Poverty_STD", "FLOAT"],
                                              ["Minority_Mean", "FLOAT"],["Minority_STD", "FLOAT"],
                                              ["Elderly_Mean", "FLOAT"],["Elderly_STD", "FLOAT"]])

## Store the statistical values in a list
## This extracts the statistics (mean and standard deviation) values and stores them to be used later. This is done using a search cursor nestled within a for loop to iterate through and capture relevant values in the STATS_TABLE

stats = arcpy.ListFields(r"Outputs.gdb\STATS_TABLE")
stats_values = []
for i in range(2,14):
    with arcpy.da.SearchCursor(in_table=r"Outputs.gdb\STATS_TABLE",
                           field_names=[[stats[i].name]]) as cursor:
        for row in cursor:
            stats_values.append(row)

## Flatten the list (stats_values_flat) of values so that each statistic is accessed individually.
stats_values_flat = [item[0] for item in stats_values]

## Update the Metro_Buffer_Data feature class with the new statistical values stored in the  
## This updates the fields in the main dataset with the statistics (mean and standard deviation) values. This was accomplished by using an update cursor nestle within a for loop to take the statistical values stored in stats_values_flat and append them to Metro_Buffer_Data

updated_fields = arcpy.ListFields(r"Outputs.gdb\Metro_Buffer_Data")
for i in range(155,167):
    with arcpy.da.UpdateCursor(in_table=r"Outputs.gdb\Metro_Buffer_Data",
                           field_names=[[updated_fields[i].name]]) as cursor:
        for row in cursor:
            row[0] = stats_values_flat[i - 155]
            cursor.updateRow(row)

print("You created fields for all these statistics and input them with the matching values calculated earlier.\n")

## Calculate Z-scores for each variable (temperature, ridership, poverty, minority, elderly) for each element in the dataset and create a new field to store those values
## A Z-score represents how far a value is from the mean in terms of standard deviations, providing a standard for comparison across our data set and variables. 
## This was accomplished using the calculate field tool using the following formula (Variable Value - Variable Mean)/Variable Standard Deviation

arcpy.management.CalculateField(
   in_table=r"Outputs.gdb\Metro_Buffer_Data",
   field="Temp_Z",
   expression=f"(!{temp}! - !Temp_Mean!)/!Temp_STD!",
   field_type="FLOAT")

arcpy.management.CalculateField(
    in_table=r"Outputs.gdb\Metro_Buffer_Data",
    field="Rider_Z",
    expression=f"(!{rider}! - !Rider_Mean!)/!Rider_STD!",
    field_type="FLOAT")

arcpy.management.CalculateField(
    in_table=r"Outputs.gdb\Metro_Buffer_Data",
    field="Pov_Z",
    expression=f"(!{poverty}! - !Poverty_Mean!)/!Poverty_STD!",
    field_type="FLOAT")

arcpy.management.CalculateField(
    in_table=r"Outputs.gdb\Metro_Buffer_Data",
    field="Minor_Z",
    expression=f"(!{minority}! - !Minority_Mean!)/!Minority_STD!",
    field_type="FLOAT")

arcpy.management.CalculateField(
    in_table=r"Outputs.gdb\Metro_Buffer_Data",
    field="Elder_Z",
    expression=f"(!{elderly}! - !Elderly_Mean!)/!Elderly_STD!",
    field_type="FLOAT")

print("You found the z-scores of all your important fields by subtracting the means from the record's value and then dividing by standard devation. How clever!\n")

## Reclassify Z-scores to a common scale for easier comparison in the Metro_Buffer_Data layer 
## This step assigns new values based on Z-scores to standardize them into a scale in a new field. For all of our variables, higher z scores will result in higher tree-need scale scores.

fields_of_interest = ["Temp_Z", "Rider_Z", "Pov_Z", "Minor_Z", "Elder_Z"]
for field in fields_of_interest:
    arcpy.management.CalculateField(in_table=r"Outputs.gdb\Metro_Buffer_Data",
        field=f"Scaled_{field}",
        expression=f"Reclass(!{field}!)",
        expression_type="PYTHON3",
        code_block="""def Reclass(input):
    if (input < -1.5):
        return 0.2
    if (input > -1.5 and input <= -1):
        return .3
    if (input >-1 and input <=-0.5):
        return .5
    if (input >0.5 and input <=1):
        return 0.7
    if (input > 0.5 and input <= 1):
        return 0.85
    if (input >1 and input <=1.5):
        return 1
    else: 
        return 0.1""",
        field_type="FLOAT")
    
print("Now all of the Z-scores have been reclassified so we can have a scale from 0-1, 1 being highest priority/demand and 0 being lowest.\n")
    
## Calculate the Multi-Criteria Evaluation (MCE) score for each feature in a new field in the Metro_Buffer_Data layer 
## MCE combines the scaled Z-scores to create a final score representing the tree-need of each bus stop based on our variables. 
## Each variable was given the following weight: Bus Ridership = 33%, Temperature = 33%, Levels of Poverty = 11%, Minority Population = 11%, Elderly = Population 11%


arcpy.management.CalculateField(
    in_table=r"Outputs.gdb\Metro_Buffer_Data",
    field="MCE",
    expression="(!Scaled_Rider_Z!*.033) + (!Scaled_Temp_Z!* 0.33) + (!Scaled_Minor_Z!*0.11) + (!Scaled_Elder_Z!* 0.11) + (!Scaled_Pov_Z!* 0.11)",
    expression_type="PYTHON3",
    field_type="FLOAT")

print("The final MCE values have been calculated!\n")

## Select bus locations with no trees (zero trees) for the final dataset 
## This filters the data to only include bus locations where no trees exist, based on the tree count field. A new layer, Final_Selection, is created with the final list of trees. 

arcpy.management.MakeFeatureLayer(r"Outputs.gdb\Metro_Buffer_Data",r"Outputs.gdb\Final_Selection_LYR",
                                  where_clause=f"{trees} < 1")

arcpy.management.CopyFeatures(in_features=r"Outputs.gdb\Final_Selection_LYR",
                              out_feature_class=r"Outputs.gdb\Final_Selection")

print("You have selected bus locations with 0 trees and put these records into a new shapefile entitled 'Final_Solution'. Good for you!\n")

## Find the top 10 bus stops according to MCE values by using SearchCursor to obtain values from the two needed fields: Stop and MCE value

final_fields = arcpy.ListFields(r"Outputs.gdb\Final_Selection")
top_bus_stops = []
with arcpy.da.SearchCursor(in_table=r"Outputs.gdb\Final_Selection",
                           field_names=[(final_fields[13].name), (final_fields[175]).name]) as cursor:
    for row in cursor:
        top_bus_stops.append(row)

sorted_bus_stops = sorted(top_bus_stops, key=lambda x: x[1], reverse=True)

print("According to our analysis, the following 10 bus stops are the most in need of trees being planted at the stop or nearby:\n")
for i in range(min(10, len(sorted_bus_stops))):  # Ensure we don't go beyond the available number of bus stops
    name, mce_score = sorted_bus_stops[i]
    print(f"{i+1}. {name.title()} - MCE score: {round(mce_score,3)}")
# %%
