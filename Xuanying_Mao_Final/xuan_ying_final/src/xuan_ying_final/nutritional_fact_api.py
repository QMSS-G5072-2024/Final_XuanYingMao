import requests
import csv
import os
from datetime import datetime
import pandas as pd
import plotly.express as px

# Main function that does most of the work
"""
nutritional_fact_api.py

This module provides functions to interact with the Edamam Nutrition API and process nutritional data.
"""
def add_food(quantity=0, unit="", ingredient="", app_id=None, app_key=None, filename=None):
    """
    Prompts the user to enter a food item and its quantity.

    Returns:
        tuple: A tuple containing the quantity and name of the food item.
    """
    json_response = query_api(quantity, unit, ingredient, app_id, app_key)
    nutrients_dict = parse_response(json_response)
    save_results(nutrients_dict, "daily_nutrition.csv")
    print(f'Successfully added {ingredient} to daily nutrition log.')

def query_api(quantity=0, unit="", ingredient="", app_id=None, app_key=None):
    """
    Queries the Edamam Nutrition API to retrieve nutritional information for a given ingredient.

    Parameters:
        quantity (float): The quantity of the ingredient.
        unit (str): The unit of the quantity (e.g., "g", "kg", "oz").
        ingredient (str): The name of the ingredient to query.
        app_id (str): Your Edamam API application ID.
        app_key (str): Your Edamam API application key.

    Returns:
        dict or str: A dictionary containing the API response data if successful,
                     or an error message string if not.
    """
    if app_id is None or app_key is None:
        return ("ERROR. API KEY and APP ID not provided. Please provide an app_id and app_key."
                " You can obtain these by signing up at https://developer.edamam.com/edamam-nutrition-api")

    query = (
        f"https://api.edamam.com/api/nutrition-data?"
        f"app_id={app_id}&app_key={app_key}&nutrition-type=cooking&ingr={quantity} {unit} {ingredient}"
    )

    try:
        response = requests.get(query)
        response.raise_for_status()
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        return f"ERROR: {e}"
    except ValueError:
        return "ERROR: Invalid response from API"

def parse_response(response):
    """
    Parses the API response to extract relevant nutritional information.

    Parameters:
        response (dict): The JSON response from the API.

    Returns:
        dict: A dictionary containing nutrients and their quantities and units.
    """
    cals = response.get('calories', None)
    total_nutrients = response.get('totalNutrients', {})

    def get_nutrient(nutrients, nutrient_key):
        """
        Helper function to extract nutrient quantity and unit.

        Parameters:
            nutrients (dict): Dictionary of nutrients from the API response.
            nutrient_key (str): The key corresponding to the desired nutrient.

        Returns:
            tuple: A tuple containing the quantity and unit of the nutrient.
        """
        nutrient_info = nutrients.get(nutrient_key, {})
        quantity = nutrient_info.get('quantity', 0)
        unit = nutrient_info.get('unit', '')
        return quantity, unit

    sugars, sugars_unit = get_nutrient(total_nutrients, 'SUGAR')
    carbs, carbs_unit = get_nutrient(total_nutrients, 'CHOCDF.net')
    fats, fats_unit = get_nutrient(total_nutrients, 'FAT')
    protein, protein_unit = get_nutrient(total_nutrients, 'PROCNT')
    fiber, fiber_unit = get_nutrient(total_nutrients, 'FIBTG')
    carbohydrates, carbs_unit = get_nutrient(total_nutrients, 'CHOCDF')
    cholesterol, cholesterol_unit = get_nutrient(total_nutrients, 'CHOLE')
    sodium, sodium_unit = get_nutrient(total_nutrients, 'NA')

    nutrients = {
        'Calories': cals,
        'Added Sugars': (sugars, sugars_unit),
        'Carbs': (carbs, carbs_unit),
        'Fats': (fats, fats_unit),
        'Protein': (protein, protein_unit),
        'Fiber': (fiber, fiber_unit),
        'Carbohydrates': (carbohydrates, carbs_unit),
        'Cholesterol': (cholesterol, cholesterol_unit),
        'Sodium': (sodium, sodium_unit)
    }
    return nutrients

def output_results(results):
    """
    Prints the nutritional results to the console.

    Parameters:
        results (dict): The dictionary containing nutritional information.
    """
    for key, value in results.items():
        print(f"{key}: {value}")

def save_results(results, filename=None):
    """
    Saves the nutritional results to a CSV file.

    Parameters:
        results (dict): The dictionary containing nutritional information.
        filename (str): The path to the CSV file where results will be saved.
    """
    headers = ['Date', 'Nutrient', 'Quantity', 'Unit']
    current_date = datetime.now().strftime('%Y-%m-%d')

    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)

        # If the file doesn't exist or is empty, write the headers
        if not file_exists or os.stat(filename).st_size == 0:
            print("File not found, writing headers...")
            writer.writerow(headers)

        for nutrient, value in results.items():
            if isinstance(value, tuple):
                quantity, unit = value
                if quantity == 0:
                    unit = 'g'
            else:
                quantity = value
                unit = "Cals"

            # Write the row with the date
            writer.writerow([current_date, nutrient, quantity, unit])

    print(f"Results have been saved to {filename}")

def read_and_process_data(filename):
    """
    Reads the CSV file and processes the data into a Pandas DataFrame.

    Parameters:
        filename (str): The path to the CSV file containing nutritional data.

    Returns:
        pandas.DataFrame: A DataFrame containing the processed data.
    """
    df = pd.read_csv(filename)

    # Ensure 'Quantity' is numeric
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')

    # Drop rows with missing 'Quantity' or 'Date'
    df = df.dropna(subset=['Quantity', 'Date'])

    return df

def plot_calories_line(filename):
    """
    Plots a line graph of total calories consumed per day.

    Parameters:
        filename (str): The path to the CSV file containing nutritional data.
    """
    df = read_and_process_data(filename)
    calories_df = df[df['Nutrient'] == 'Calories']
    calories_per_day = calories_df.groupby('Date')['Quantity'].sum().reset_index()

    # Plot the line graph for total calories per day using Plotly
    fig = px.line(
        calories_per_day,
        x='Date',
        y='Quantity',
        title='Total Calories Consumed Per Day',
        markers=True
    )
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Calories',
        xaxis_tickangle=45
    )
    fig.show()

def plot_nutritional_breakdown(filename):
    """
    Plots a stacked bar chart of nutritional breakdown per day.

    Parameters:
        filename (str): The path to the CSV file containing nutritional data.
    """
    df = read_and_process_data(filename)
    nutrients_df = df[df['Nutrient'] != 'Calories']

    # Pivot the data
    pivot_table = nutrients_df.pivot_table(
        index='Date',
        columns='Nutrient',
        values='Quantity',
        aggfunc='sum'
    ).fillna(0)

    # List of nutrients to include
    nutrients_to_plot = [
        'Protein', 'Carbohydrates', 'Fats', 'Fiber',
        'Sugars', 'Cholesterol', 'Sodium', 'Added Sugars'
    ]

    # Ensure the nutrients exist in the pivot table
    nutrients_to_plot = [
        n for n in nutrients_to_plot if n in pivot_table.columns
    ]

    # Reset index to get 'Date' as a column
    pivot_table = pivot_table.reset_index()

    # Melt the pivot table to long format for Plotly
    melted_df = pivot_table.melt(
        id_vars='Date',
        value_vars=nutrients_to_plot,
        var_name='Nutrient',
        value_name='Quantity'
    )

    # Plot the stacked bar chart using Plotly
    fig = px.bar(
        melted_df,
        x='Date',
        y='Quantity',
        color='Nutrient',
        title='Nutritional Breakdown Per Day',
        hover_data=['Nutrient', 'Quantity']
    )
    fig.update_layout(
        barmode='stack',
        xaxis_title='Date',
        yaxis_title='Quantity',
        legend_title_text='Nutrient',
        xaxis_tickangle=45
    )
    fig.show()