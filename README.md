
# Chatbot

This is a RAG based chatbot through which you can query about the Restaurants on which this model has been trained on. It lets user to query based on dietary preferences, price of item, rating of restaurant or any other specific parameters.

## Pre-requisites
Ensure you have the following installed before running the project: 
- Python 3.12.3
## Setup & Installation
- clone the repository <code>git clone https://github.com/guptautkarsh21/Nugget-Assesment</code>
- Install all dependencies using <code>pip install -r requirements.txt </code>
- Configure environment variables by entering Hugging Face API Token and Pinecone Token in rag_engine.py
-  Build the project and run <code>python app.py</code>
- Verify the Setup Check url http://localhost:5000/health-check
## Scrapped Data

Web scraping has been performed on the following 7 restaurants:
- Daryaganj
- Cafe Delhi Heights
- Magamoto
- Xero Courtyard
- KFC
- Burger King
- Taco Bell

For each restaurant, two CSV files have been generated:
1. Restaurant Information:
- name
- location
- rating
- rating count
- cuisines
- timings
- contact no.

2. Menu Information:
- Category (Starters, Main Course etc.)
- Subcategory
- Name
- Price
- Veg/ Non-Veg
- Tags (Bestseller, Gluten free etc.)
- Description
- Name of Restaurant
