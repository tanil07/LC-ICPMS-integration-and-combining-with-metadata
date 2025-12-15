# LC-ICPMS-integration
Python code to integrate peak area for LC-ICPMS data
#Change the data directory to the location of the csv files for the station you want to plot
#This script will create a pdf figure for each element in the csv files in the selected directory
#Plots will have a line for each file in the directory with the element on the y-axis and the time on the x-axis
#Select the element of interest, select baseline timepoints, and select timerage of interest to integrate peak area for that range
#Integrate peak area for the calibration samples and develope calibration curve.
#Supply calibration table that contains 'r2', 'intercept', and 'slope' data
#Change the calibration filename if necessary
#Run the code that is commented at the end of integrate_LCICPMS file to calculate concentration
