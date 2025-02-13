import openai
import json
from flask import Flask, render_template, request, jsonify, session
import re
import os

# Set up your OpenAI API key
openai.api_key = 'your-api-key'  # Replace with your actual key

app = Flask(__name__)
app.secret_key = 'chatbot-skillguru'

# Function to load skill data from JSON file
def load_skills_data():
    try:
        with open('skills_data.json', 'r') as file:
            data = file.read().strip()  # Read and strip any leading/trailing whitespace
            
            if not data:
                raise ValueError("The JSON file is empty.")
            
            return json.loads(data)
    
    except FileNotFoundError:
        print("The file 'skills_data.json' was not found.")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except ValueError as e:
        print(e)

    return {}  # Return an empty dictionary in case of error

@app.route('/')
def index():
    skills_data = load_skills_data()
    
    if not skills_data:
        return "Failed to load skill data. Please check your JSON file.", 500
    
    skills = [skill['name'] for skill in skills_data['skills']]
    return render_template('index.html', skills=skills)

@app.route('/ask_questions', methods=['POST'])
def ask_questions():
    skill_name = request.form['skill_name']

    analysis_prompt = f"""
    Generate a list of 10 multiple-choice questions with 4 choices each for {skill_name}. 
    Also, provide the correct answer for each question in this format:

    1. Question: <question text>
    A) <option 1>
    B) <option 2>
    C) <option 3>
    D) <option 4>
    Correct Answer: <A/B/C/D>

    Ensure all 10 questions are included.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": analysis_prompt}
        ],
        max_tokens=800,
        temperature=0.7
    )

    content = response.choices[0].message['content'].strip()
    question_pattern = re.findall(r'(\d+)\.\sQuestion:\s(.+?)\nA\)\s(.+?)\nB\)\s(.+?)\nC\)\s(.+?)\nD\)\s(.+?)\nCorrect Answer:\s([A-D])', content, re.DOTALL)
    questions = []
    correct_answers = {}

    for q in question_pattern:
        question_number, question_text, a, b, c, d, correct = q
        questions.append({"question": question_text, "choices": {"A": a, "B": b, "C": c, "D": d}})
        correct_answers[f'answer_{question_number}'] = correct

    while len(questions) < 10:
        missing_qn = len(questions) + 1
        questions.append({"question": f"Placeholder Question {missing_qn}", "choices": {"A": "Option 1", "B": "Option 2", "C": "Option 3", "D": "Option 4"}})

    session['correct_answers'] = correct_answers  
    return render_template('ask_questions.html', skill_name=skill_name, questions=enumerate(questions, 1))

@app.route('/submit_answers', methods=['POST'])
def submit_answers():
    skill_name = request.form['skill_name']
    user_answers = {f'answer_{i}': request.form[f'answer_{i}'] for i in range(1, 11)}

    correct_answers = session.get('correct_answers', {})

    correct_count = sum(1 for key, value in user_answers.items() if correct_answers.get(key) == value)
    
    # Collecting individual suggestions for each question
    individual_suggestions = []
    for question_num in range(1, 11):  # Ensure we're iterating over all 10 questions
        user_answer = user_answers[f'answer_{question_num}']
        correct_answer = correct_answers.get(f'answer_{question_num}')
        
        # Constructing prompt to get unique and concise feedback (max 3 lines)
        analysis_prompt = f"""
        Question {question_num}:
        The user's answer was {user_answer}, but the correct answer is {correct_answer}.
        Provide a unique and concise suggestion or explanation for improvement (maximum 3 lines, ideally 2-3 sentences).
        Keep it brief and actionable. If the answer is correct, just say "Correct answer! Well done!".
        """ 

        # Generate suggestion for each question, ensuring uniqueness and brevity
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=250,  # Increase max tokens to handle detailed suggestions for each question
            temperature=0.7
        )
        
        suggestion = response.choices[0].message['content'].strip()

        # Truncate response if it's still too long
        if len(suggestion.split('\n')) > 3:
            suggestion = '\n'.join(suggestion.split('\n')[:3])  # Limit to 3 lines

        # Append suggestion to list
        individual_suggestions.append({
            "question": f"Question {question_num}",
            "suggestion": suggestion if user_answer != correct_answer else "Correct answer! Well done!"
        })

    # Now, generate the consolidated skill-level suggestion
    consolidated_prompt = f"""
    User selected the {skill_name} skill. They got {correct_count} out of 10 correct.
    Provide a brief overall suggestion for how they can improve their understanding of {skill_name}.
    Keep it concise and actionable (maximum 3 lines).
    """

    consolidated_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": consolidated_prompt}
        ],
        max_tokens=250,  # Increase max tokens to handle a more detailed overall suggestion
        temperature=0.7
    )

    consolidated_suggestion = consolidated_response.choices[0].message['content'].strip()

    # Truncate response if needed
    if len(consolidated_suggestion.split('\n')) > 3:
        consolidated_suggestion = '\n'.join(consolidated_suggestion.split('\n')[:3])  # Limit to 3 lines

    return render_template('suggestions.html', correct_count=correct_count, total_questions=10, 
                           individual_suggestions=individual_suggestions, consolidated_suggestion=consolidated_suggestion)


if __name__ == '__main__':
    app.run(debug=True)
