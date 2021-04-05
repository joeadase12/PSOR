# US Border Patrol Basic Analysis

# To do list:
# - Make flexible parameters for analysis: (Demographic/sector/nationality)
# - Put legends on all plots
# - Change integer months to strings for graphs
# - Only need past 6 months of forecasting for graphs
# - create a ReadME file on how to get this file working from ground zero. Get anaconda, pip install, etc.

# CBP Website for reference:  
# https://www.cbp.gov/newsroom/stats/southwest-land-border-encounters

# Important:
# To get this file to work you must have the following libraries installed:
# - pandas
# - openpyxl
# - seaborn  
#   
# You must also have the excel file downloaded in the same folder as this notebook  
#   
# If you are unfamiliar with python here is a guide on pip installing:
# - https://docs.python.org/3/installing/index.html

# Importing and Formatting Data
# import the necessary libraries used in the code

import pandas as pd    # for dataframes
import openpyxl        # for reading in excel files
import seaborn as sns  # for nice graphs

# read in the data file
filename = "USBP SBO Encounters by Sector Citiz Group Demo FY13-FY21TD-FEB.xlsx"
df = pd.read_excel(filename, header=6,usecols="B:G", engine='openpyxl')
df.head()

# Switched from strings to integers for months to make calculations easier.  
# In order to get the dates to process in the right order, 1=October or the first month in the fiscal year

# months are placed into a list starting with OCT becasue it is the start of the fiscal year,
# which the data uses instead of calendar year.  The months are then mapped to digits starting
# with OCT as 1, NOV as 2, DEC as 3, and so on up to SEP as 12.  Column 'M' is added to the
# dataframe representing the numerical value of the month that was previously assigned. In the
# 'FY' column, the FY is removed from the value so it is represented soley numerically. Changing
# these values to numbers rather than letters or a mix of letters and numbers
# makes it easier to conduct the analysis on the data.
months = ['OCT','NOV','DEC','JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP']
month_map = {month:i+1 for i,month in enumerate(months)}
df["M"] = df["Month"].map(month_map)
df["FY"] = df["FY"].apply(lambda x:int(x[2:6]))

df.head()
df.tail()

# data is summed by demographic, fiscal year, and month to consolidate similar data entries into 
# one count.  This way there is one entry for each demographic for every month of each fiscal year
# instead of multiple entries with very similar information.  A new column 'Date' is added to the
# dataframe in order for the user to quickly identify the year and month.
sum_df = df.groupby(["Demographic","FY","M"]).sum().reset_index()
sum_df["Date"] = sum_df["FY"]+sum_df["M"]/100
sum_df

# ### Current Analysis
# - % Change = the (current month - previous month) / previous month
# - Predicted = averaging the % Change from the past three years
# - Error = The difference between the actual and the predicted totals

# This cell calculates the month to month percent change in data.  After we have aggregated the
# data into one entry for each month, the percent change is calculated by taking the difference
# between the current month and the previous month, then dividing by the previous month's numbers.
# A percent change column is added to the dataframe with the corresponding values.  A negative 
# percent change means the previous month's total was higher than the current month's total.
sum_df["% Change"] = 0
for row_idx, row in sum_df.iterrows():
    
    row_demographic = row["Demographic"]
    row_month = row["M"]
    row_year = row["FY"]
    
    if row_month != 1:
        previous_month = sum_df.loc[sum_df["Demographic"]==row_demographic].loc[sum_df["M"]==row_month-1].loc[sum_df["FY"]==row_year]
    else:
        previous_month = sum_df.loc[sum_df["Demographic"]==row_demographic].loc[sum_df["M"]==12].loc[sum_df["FY"]==(row_year-1)]
    
    if not previous_month.empty:
        sum_df.loc[[row_idx],["% Change"]] = round(float((row["Count"]-previous_month["Count"])/previous_month["Count"]),4)*100

# Calculations for the percent change prediction.  Calculated by averageing the previous month's
# change with the previous two year's changes.  For example, predicting Jan to Feb 2021 change
# would require averaging the previous Dec to Jan prediction with the Dec to Jan prediction from
# 2020 and 2019.  If the data does not go back far enough, only the available data is used.  The
# percent change predicted is then used to make the predicted count for the month.

# this cell will be simplified and commented on more for the future
sum_df["% Predicted"] = 0
sum_df["Count Predicted"] = 0
PAST_YEARS = 3
for row_idx, row in sum_df.iterrows():
    
    row_demographic = row["Demographic"]
    row_month = row["M"]
    row_year = row["FY"]
    
    change_average = 0
    unavailable_years = 0
    if row_month != 1:
        last_month = sum_df.loc[sum_df["Demographic"]==row_demographic].loc[sum_df["M"]==row_month-1].loc[sum_df["FY"]==(row_year)]
        for year in range(PAST_YEARS):
            year_change = sum_df.loc[sum_df["Demographic"]==row_demographic].loc[sum_df["M"]==row_month-1].loc[sum_df["FY"]==row_year-year]
            if not year_change["% Change"].empty and year_change["% Change"].item() != 0:
                change_average += year_change["% Change"].item()
            else:
                unavailable_years +=1
    else:
        last_month = sum_df.loc[sum_df["Demographic"]==row_demographic].loc[sum_df["M"]==12].loc[sum_df["FY"]==(row_year-1)]
        for year in range(PAST_YEARS):
            year_change = sum_df.loc[sum_df["Demographic"]==row_demographic].loc[sum_df["M"]==12].loc[sum_df["FY"]==(row_year-1-year)]
            if not year_change["% Change"].empty:
                change_average += year_change["% Change"].item()
            else:
                unavailable_years +=1
    if unavailable_years != 3:
        change_average /= (PAST_YEARS-unavailable_years)
    sum_df.loc[[row_idx],["% Predicted"]] = round(change_average,2)
    
    if not last_month["Count"].empty:
        sum_df.loc[[row_idx],["Count Predicted"]] = round((1+(change_average/100))*last_month["Count"].item())

# Another column is added to the dataframe for the error measurement of the predicted change.  The
# error is calculated by subtracting the predicted value from the actual value and dividing by the
# actual value.  A negative error means that the predicted value was higher than the actual value.
sum_df["Error"] = (sum_df["Count"]-sum_df["Count Predicted"])/sum_df["Count"]

# Example By hand
sum_df[sum_df['M']<=3].head(9)

# Displayed above are the first three months of 2013, 2014, 2015  
# Looking at the FMUA Demographic in 2015 lets predict Month 3 (December), using the past three years of data:  
# October to November 2015 = 11.70% change  
# October to November 2014 = 15.41% change  
# October to November 2013 = 02.88% change  
# 11.70 + 15.41 - 2.88 = 24.23/3 = 8.08 % change on average from October to November  
#   
# 1+(8.08/100) = 1.0808 (% change in decimal)  
# November 2015 count = 2415 (Most recent month)  
# 2415*1.0808 = 2610 people predicted for December  
# Actual count was 2891 which was a 9.72% error  

# Pivot Tables for each of the new values
# These are tables of specific data such as Count, % Change, etc. at a glance

# This pivot table separates the values by demographic.  The demographics are the x-axis and the
# year/month are the y-axis.
counts=sum_df.pivot(index="Date",columns="Demographic",values="Count")
counts.head()

# This pivot table shows the month to month percent change for each demographic, with the same
# axis labels as before.
percents=sum_df.pivot(index="Date",columns="Demographic",values="% Change")
percents.head()

# Here we have the predicted values in the pivot table, again same axis labels are used.
prediction=sum_df.pivot(index="Date",columns="Demographic",values="Count Predicted")
prediction.head()

# pivot table with the error values, same axis labels.
error=sum_df.pivot(index="Date",columns="Demographic",values="Error")
error.head()

# Fancy Plots
# Plots of the Counts for each Month

# this plot shows the predicted counts for each demographic, year-to-year.
sns.lineplot(data=sum_df,x="Date",y="Count Predicted",hue="Demographic")

# these graphs are the same as the previous one, the predicted counts for each month, but instead
# of all three demographics overlayed on one graph, they are separated into three different graphs
g = sns.FacetGrid(sum_df, col="Demographic")
g.map_dataframe(sns.lineplot,x="Date",y="Count Predicted")

# These graphs show the month-to-month predicted counts for the three demographics.  The darker
# lines or the more recent year's values (the darker the line, the more recent the data is).  The 
# month are represented on the x-axis by their fiscal year numerical value (OCT=1, NOV=2, etc.)
g = sns.FacetGrid(sum_df, col="Demographic") 
g.map_dataframe(sns.lineplot,x="M",y="Count Predicted",hue="FY")

# Plots of the  Percent Change each Month
# this plot shows the percent change for each demographic, year-to-year.
sns.lineplot(data=sum_df,x="Date",y="% Change",hue="Demographic")

# these graphs are the same as the previous one, the percent change for each month, but instead
# of all three demographics overlayed on one graph, they are separated into three different graphs
g = sns.FacetGrid(sum_df, col="Demographic")
g.map_dataframe(sns.lineplot,x="Date",y="% Change")

# These graphs show the month-to-month percent changes for the three demographics.  The darker
# lines or the more recent year's values (the darker the line, the more recent the data is).  The 
# month are represented on the x-axis by their fiscal year numerical value (OCT=1, NOV=2, etc.)
g = sns.FacetGrid(sum_df, col="Demographic")
g.map_dataframe(sns.lineplot,x="M",y="% Change",hue="FY")

# Different Plots of Error each Month
# this plot shows the error calculation for each demographic, year-to-year.
sns.lineplot(data=sum_df,x="Date",y="Error",hue="Demographic")

# these graphs are the same as the previous one, the error calculation for each month, but instead
# of all three demographics overlayed on one graph, they are separated into three different graphs
g = sns.FacetGrid(sum_df, col="Demographic")
g.map_dataframe(sns.lineplot,x="Date",y="Error")

# These graphs show the month-to-month error calculation for the three demographics.  The darker
# lines or the more recent year's values (the darker the line, the more recent the data is).  The 
# month are represented on the x-axis by their fiscal year numerical value (OCT=1, NOV=2, etc.)
g = sns.FacetGrid(sum_df, col="Demographic")
g.map_dataframe(sns.lineplot,x="M",y="Error",hue="FY")

# Plots of the Actual and Predicted Counts by Demographic and Year

# the following graphs show the count in blue and the predicted count in orange.  We can see how
# good the predictions were based on how close the lines are together.  The x-axis has the months
# represented by their numerical value, and the y axis has the counts.  Each row of graphs
# represents a different fiscal year, and each column represents a different demographic.
melted_df = pd.melt(sum_df, id_vars=['Demographic','FY','M'], value_vars=['Count', 'Count Predicted'])
g = sns.FacetGrid(melted_df, col="Demographic", row="FY",margin_titles=True)
g = g.map_dataframe(sns.lineplot,x="M",y="value",hue="variable")
g.add_legend()


