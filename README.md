# mobility-electrification
2022 CUSP Capstone project repo - The Electric Commute: Envisioning 100% Electrified Mobility in New York City (TEC-NYC)
Update - June 12, 2022

Development efforts are entirely now done in the 05 and 06 directories. Do not use 01,02,03,04 for any further updates. Any updates to the models need to be done in the 05 directory, and visualization work should be done in the 06 directory.

## Final Documentation
This repo serves as the saving point and codebase of our technical work over the past 5 months. At a high level, we were tasked with developing a commuter and electricity demand model to simulate the power needs of an all-electric commute into Manhattan on a typical Fall day. This codebase documents our work to do so. Each section has a more detailed README file that clarifies specific files being used and code ran.

[Section 1](01_DataExploration_and_Engineering/)
For our first block of work, we needed to engineer the appropriate datasets required for this work. Our first data source, [IPUMS USA](https://usa.ipums.org/usa/index.shtml), is a cleaner, easier-to-use version of existing American Community Survey data as of 2019. The ACS asks a representative sample of Americans about their lives, including demographic information and commute patterns, which are relevant to us. 

Additionally, we needed to reconcile any IPUMS counts against [NYMTC's Hub Bound Travel data](https://www.nymtc.org/DATA-AND-MODELING/Transportation-Data-and-Statistics). This report and statistics provides true counts of in/out flow into Manhattan on a typical fall business day (in 2019). Because such data is aggregated,it cannot, alone, be fuel for a commuter model. But it can serve to affirm accuracy of the IPUMS sampled data. 

[Section 2](02_DataVisualization/)
This directory was used in the Spring to manipulate the data resulting from step 1 for interim, proof-of-concept visualizations. Ultimately, data was visualized in tools outside of python for client demonstrations.


[Section 3](03_CommuterModel/)
With our data ready to use, we now took on the work of developing a workable, repeatable, well-documented Commuter Model. Cleaned data was fed into notebooks that utilized our [commuter model python class](<03_CommuterModel/tranwork_flags/commuter_model.py>). This class ingested our clean data and, after a few interim steps and adjustable parameters, assigned modes of transit to each person in our dataset. This directory was where we built our first versions of this model for testing, review, and early interim visualizations.


[Section 4](04_ElectricalInfrastructureModel/)
After building a commuter model, we needed to understand the electricity demands of each possible iteration of commuter distribution by mode, by hour, and by origin. This directory features our work developing an [electric model python class](<04_ElectricalInfrastructureModel/electrical_model.py>). This file distributes electricity demand based on certain input parameters and the commuter model output it is measuring. Any two commuter model runs should have different outputs and therefore unique electricity demand profiles.


[Section 5](05_Commuter_Electric_Pipeline/)
This work is where our final development work is housed - combining efforts from steps 3 and 4, we house the latest and only versions of our models that should be used here. Then, we have notebooks showing how we ran these models concurrently to develop pickle files that would be fed into our final visualization.


[Section 6](06_Dashboard_Visualization/)
This houses our final deliverable - our interactive dashboard. THe goal of this is to show how when one changes certain input parameters about commuting patterns, the electricity demand on Manhattan's grid will adjust. This visualization is developed using plotly, and all of its code is housed here.

Link to readme within this section that explains in more detail what we have done