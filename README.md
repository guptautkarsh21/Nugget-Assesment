
# Chatbot

This is a RAG based chatbot through which you can query about the Restaurants on which this model has been trained on. It lets user to query based on dietary preferences, price of item, rating of restaurant or any other specific parameters.

## Pre-requisites
Ensure you have the following installed before running the project: 
- Python 3.12.3
## Setup & Installation
- clone the repository git clone https://github.com/guptautkarsh21/Nugget-Assesment
- Configure environment variables by entering Hugging Face API Token and Pinecone Token in rag_engine.py
-  Build the project and run app.py
- Verify the Setup Check url http://localhost:5000/health-check
## Scrapped Data

Web Scrapping has been done on 7 restaurants:
- Daryaganj
- Cafe Delhi Heights
- Magamoto
- Xero Courtyard
- KFC
- Burger King
- Taco Bell

For each restaurant two csv files has been generated:
1. About information of restaurant having following fields
- name
- location
- rating
- rating count
- cuisines
- timings
- contact no.

2. About the menu of restaurant having:
- Category (Starters, Main Course etc.)
- Subcategory
- Name
- Price
- Veg/ Non-Veg
- Tags (Bestseller, Gluten free etc.)
- Description
- Name of Restaurant
