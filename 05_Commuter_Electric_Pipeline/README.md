# Commuter_Electric_Pipeline
This folder houses the final

- [Commuter Model]()

- [Energy Model]()

- An [example]() of running the entire models to create commuting scenarios and calculate eletricity demand



### Reference

**Eligibility Model**

Each commute mode takes relevant individual parameters such as gender, health, and age, as well as contextual parameters, like the existence of safe biking infrastructure, to declare if an individual is eligible for each mode of transportation. These parameters apply different constraints on possible mode choices. The details and sources for this implementation can be found **[here]()**. 

To predict WFH dynamics in the post-pandemic environment, we build conditional probabilities reflecting any individual’s likeliness to WFH at their respective education, profession, and income levels. This data is obtained from the 2020/2021 US Census Household Pulse Survey. Using this survey’s answers about income, education, and WFH status, we are able to find the probability that any American adult works from home given their education status (aggregated to “not college educated” and “college educated”) and their household income (broken down into 7 buckets from $0–25k to ≥$200k). Individuals who work in the service industry or blue-collar professions are less likely to work from home compared to white-collar college educated individuals. This calculation is then be used to estimate WFH likelihood in our commuter model. The conditional probabilities can be found **[here]()**.  

**EV Technical Information**

We collect the technical characteristics of available electric modes of transportation including range (km), efficiency (kWh/km), and charging power (kW) from EV databases and manufacturers. The detailed information can be find **[here]()**. 

