# 3 - Developing our commuter model

This directory is no longer used for active development.

The below was written 6/20/2022

This folder houses the code and tests ran to build the first version of our commuter model.

Folder [ipums_data](ipums_data/) shows some late cleans and edits made to our input IPUMS dataset. Folder [regional_transit_system](regional_transit_system/) shows research done to better understand the existing transit networks and how each PUMA of origin can or cannot reach Manhattan on a work day. Folder [tmp_model](tmp_model/) shows another example of how we continued to visualize our data with the ultimate final visualization as our goal. Such examples, as seen in [this notebook](https://github.com/BNewborn/mobility-electrification/blob/main/03_CommuterModel/tmp_model/tmp_model.ipynb), continue to show how we presented our ideas to our client and how such visualizations evolved, even from the step prior.

Ultimately, the commuter model development efforts were done in the [tranwork_flags](tranwork_flags/) folder. In here, we asked each team member to develop functions that took in the input IPUMS commuter dataset, and gave each weighted line a 0 or 1 value as "possible to take this mode of transit". Inputs used included household income, distance to Manhattan, owns a car, age, health status, and gender. Such functions were collated and developed into a class `CommuterModel` [here](tranwork_flags/commuter_model.py), which enabled much more portability and re-usability. It also created one place for us to edit and further work. This class has since been modified in further directories, but reflects the first working version of our Commuter Model. To see this early model run in action, see [this notebook](<tranwork_flags/Test Commuter Model Class with Random Assignment.ipynb>)