import openai
import json
from flask import Flask, render_template, request, jsonify, session
import re
import os

# Set up your OpenAI API key
openai.api_key = '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'  # Replace with your actual key

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

    # Consolidated skill-level suggestion based on performance
    consolidated_prompt = f"""
    User selected the {skill_name} skill. They got {correct_count} out of 10 correct.
    Based on their performance, here are some personalized suggestions to help them improve their understanding of {skill_name}:

    - If you answered less than half of the questions correctly, it's important to revisit the foundational concepts. Focus on understanding the core principles before moving on to more advanced topics.
    - If you got around half correct, you're on the right track! Try to focus more on the areas where you missed questions. Break down complex problems and make sure you understand the reasoning behind each solution.
    - If you got a majority of questions correct, great job! However, keep practicing and solving problems regularly to ensure that you can apply the knowledge consistently.
    - Review the areas where you struggled and find alternative learning resources to gain a better understanding. Often, a different explanation can help clarify concepts that are difficult to grasp.
    - Try practicing more with interactive resources, quizzes, or real-world examples to reinforce your understanding of the topic.
    - Focus on any specific patterns in the types of questions you missed. Are there particular concepts or areas that you need to review more?
    - Don’t be discouraged by incorrect answers. Mistakes are an essential part of learning and can provide valuable insights into what you need to work on.
    - Stay consistent with your study routine and consider setting small, measurable goals to track your progress.

    Based on your score of {correct_count} out of 10, these suggestions are tailored to help you strengthen your understanding of {skill_name}. Continue practicing and refining your knowledge, and you’ll see steady improvement.
    """

    # Requesting a response from OpenAI
    consolidated_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[ 
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": consolidated_prompt}
        ],
        max_tokens=1500,
        temperature=0.7
    )

    consolidated_suggestion = consolidated_response.choices[0].message['content'].strip()

    # Convert the response into bullet points by splitting each suggestion with newlines
    suggestions_list = consolidated_suggestion.split('\n')
    
    # Filter out empty lines if any
    suggestions_list = [suggestion.strip() for suggestion in suggestions_list if suggestion.strip()]

    # Render the suggestions in bullet-point format
    return render_template('suggestions.html', correct_count=correct_count, total_questions=10, suggestions_list=suggestions_list)

if __name__ == '__main__':
    app.run(debug=True)
