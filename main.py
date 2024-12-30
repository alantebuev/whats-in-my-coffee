from flask import Flask, render_template, request, jsonify, abort
import pandas as pd
from difflib import get_close_matches
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will allow all domains to make requests to your Flask app

def load_drink_database():
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'BlueBottleDB.csv')
        df = pd.read_csv(csv_path)
        print("Loaded columns:", df.columns.tolist())
        
        required_columns = ['Drink name', 'Type', 'Milk Type', 'Size (oz)', 
                          'Stay/Take away', 'Calories', 'Protein', 'Sugar']
        if not all(col in df.columns for col in required_columns):
            print("Error: Missing required columns")
            print("Available columns:", df.columns.tolist())
            return None
        
        column_map = {
            'Drink name': 'drink_name',
            'Type': 'drink_type',
            'Milk Type': 'milk_type',
            'Size (oz)': 'size',
            'Stay/Take away': 'container',
            'Calories': 'calories',
            'Protein': 'protein',
            'Sugar': 'sugar'
        }
        df = df.rename(columns=column_map)
        return df
        
    except Exception as e:
        print(f"Error loading database: {e}")
        return None

def find_similar_drinks(input_drink, drinks_df):
    drink_names = drinks_df['drink_name'].tolist()
    matches = get_close_matches(input_drink.lower(), 
                              [drink.lower() for drink in drink_names], 
                              n=1, cutoff=0.6)
    return matches[0] if matches else None

def suggest_alternatives(drink_name, drinks_df):
    original = drinks_df[drinks_df['drink_name'].str.lower() == drink_name.lower()]
    if original.empty:
        return None, None
    
    original_dict = original.iloc[0].to_dict() if not original.empty else None
    
    alternatives = drinks_df[
        drinks_df['calories'] < original['calories'].iloc[0]
    ].sort_values('calories', ascending=True)
    
    alt_list = alternatives.head(3).to_dict('records') if not alternatives.empty else []
    
    return original_dict, alt_list

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        drinks_df = load_drink_database()
        if drinks_df is None:
            return render_template('index.html', error="Database error")
            
        user_drink = request.form['drink']
        matched_drink = find_similar_drinks(user_drink, drinks_df)
        
        if not matched_drink:
            return render_template('index.html', error="Drink not found")
            
        original, alternatives = suggest_alternatives(matched_drink, drinks_df)
        if original is None:
            return render_template('index.html', error="No alternatives found")
            
        return render_template('index.html', 
                             original=original, 
                             alternatives=alternatives)
    
    return render_template('index.html')

@app.route('/suggestions')
def get_suggestions():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    drinks_df = load_drink_database()
    if drinks_df is None:
        return jsonify([])
    
    # Filter drink names that contain the query substring
    suggestions = drinks_df[drinks_df['drink_name'].str.lower().str.contains(query, na=False)]['drink_name'].tolist()
    
    # Get unique suggestions and limit to top 5
    suggestions = list(dict.fromkeys(suggestions))  # Remove duplicates while preserving order
    suggestions = suggestions[:5]
    
    return jsonify(suggestions)

# Custom Error Handlers
@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    print("Starting Flask application...")
    print(f"Current working directory: {os.getcwd()}")
    app.run(debug=True)
    csv_path = os.path.join(os.path.dirname(__file__), 'BlueBottleDB.csv')
    print(csv_path)  # This will print the path Flask is using to find the CSV file