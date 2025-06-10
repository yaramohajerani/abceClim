# Climate Economics Agent-Based Modeling based on abcEconomics

A reusable framework for adding geographical distribution, climate stress modeling, and comprehensive visualization capabilities to agent-based economic models built with abcEconomics.

abcClimateEcon is built on a fork of [abcEconomics](https://github.com/AB-CE/abce). Aside from the core climate funcationlity, this fork updates some of the deprecated functionality of abcEconomics to work with up-to-date libraries since abcEcon was archived in early 2024. In particular, the logging functionality of the original repository may face issues with newer libraries, which is now replaced with a new logging system. Anothe change to the existing funcationlity of abeEconomics is the addition of purchase optimization, such that available money is spent optimally between different categories of inputs to maximize output assuming a Cobb-Douglas production function. 

The main feature of this fork, however, is the addition of a climate risk framework that allows the analysis of propagation of regional acute and chronic climate stresses through a global supply chain network.

**Important Disclaimer: this is work in progress and is by no means finished, so you may often see temporary placeholder values for various parameters and experimental methodologies. Therefore, do not use this code for any real study or application (yet). There are no guarantees for anything in this repository whatsoever.** If you have any thoughts or would like to contribute, please [reach out](mailto:yaramohajerani@gmail.com).

For sample analyses and more information on the implemented climate framework, refer to [this post](https://open.substack.com/pub/yaramo/p/introducing-an-agent-based-modelling?r=5gzbvr&utm_campaign=post&utm_medium=web&showWelcomeOnShare=true).

## Overview

The Climate Framework provides a standardized way to:
- **Distribute agents geographically** across continents with different climate risks
- **Apply climate stress** (both acute events and chronic degradation) based on geography
- **Collect comprehensive data** about agent interactions and climate impacts
- **Generate visualizations** showing geographical networks, climate events, and economic impacts
- **Export data** for further analysis

**Key Features include:**

### 🌍 Geographical Distribution
- Automatically assigns agents to continents based on configurable rules
- Different agent types can have different geographical preferences
- Climate vulnerability is adjusted based on continental climate risk

### 🌡️ Climate Stress Modeling
- **Acute stress**: Random climate events with continent-specific probabilities
- **Chronic stress**: Gradual productivity degradation and/or overhead increase over time
- Flexible application to any agent type with production capabilities

## Getting started
Start with the 3-layer climate model `climate_3layer`, which simulates a 3-layer supply chain connected to households. Acute and chronic stresses are applied to the productivity and overhead of firms. Refer to the ReadME inside the directory for full details. 
