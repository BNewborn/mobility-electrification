# 1 - Exploring, Cleaning and Engineering Data

This directory is no longer used for active development.

The below was written 6/20/2022

As part of our development process, we needed to clean and explore the two datasets we were using.

Notebooks [01](01_ReferenceTables.ipynb), [02](02_IPUMS_DataCleaning.ipynb), and [05](05_IPUMS_DataCleaning_Disaggregated.ipynb) are the cleaned up exploration of the IPUMS ACS data. For steps 1 and 2, we originally explored using separate cross-tab reference tables for modeling, but ultimately decided on a disaggregated, line-level dataset to use as the primary input of our commuter model. The result of this is in notebook 5. Notebooks [03](03_HBD_Reformatting_And_Checks.ipynb) and [04](04_Comparing_HBD_IPUMS.ipynb) detail our work with the Hub-Bound data report. Using this data required a fair amount of manual cleaning, given the original format of human-readable Excel files. Such exploration and comparison with our commuter data is seen in notebook 4.

Step 6 is a separate SQL step showing how we calculated centroid-to-centroid distances for our commuter inputs. We wanted to try to do street-level distances (i.e. what distance you'd see on Google Maps for driving/walking/biking),but did not have the ability to do so. Ultimately, this centroid-to-centroid (as the crow flies) distance was a good enough approximation for distance traveled.