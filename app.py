import openai
import json
from flask import Flask, render_template, request, jsonify

# Set up your OpenAI API key
openai.api_key = 'your-api-key'  # Replace with your actual OpenAI API key

app = Flask(__name__)

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
    
    # Create a prompt to generate multiple-choice questions based on the user-provided skill
    analysis_prompt = f"""
    Generate a list of 5 multiple-choice questions with 4 choices each for someone looking to improve their {skill_name} skill.
    The questions should be detailed and relevant to {skill_name}, and follow this format:

    Question 1: What is the best way to learn {skill_name}?
    A) Option 1
    B) Option 2
    C) Option 3
    D) Option 4

    Question 2: How can you improve your {skill_name} skills?
    A) Option 1
    B) Option 2
    C) Option 3
    D) Option 4

    Continue this format for 5 questions.
    """
    print(analysis_prompt)
    # Use the OpenAI API to generate the questions
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Using the chat-based model
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": analysis_prompt}
        ],
        max_tokens=600  # Increase the token limit to allow more questions
    )

    # Extract the generated questions and choices from the response
    content = response['choices'][0]['message']['content'].strip().split("\n\n")
    questions = []

    for question_block in content:
        question_lines = question_block.split("\n")
        question = question_lines[0].strip()
        choices = {letter: choice.strip() for letter, choice in zip("ABCD", question_lines[1:])}
        questions.append({"question": question, "choices": choices})
    
    # Return the questions to the template
    return render_template('ask_questions.html', skill_name=skill_name, questions=enumerate(questions, 1))


@app.route('/submit_answers', methods=['POST'])
def submit_answers():
    skill_name = request.form['skill_name']
    
    # Collect all answers from the form. It assumes you name each answer field 'answer_X' (where X is the index)
    answers = [request.form[f'answer_{i}'] for i in range(1, len(request.form))]
    
    # Create a system prompt with the answers
    analysis_prompt = f"""
    User has selected {skill_name}. Here are their answers to the skill-related questions:
    {answers}

    Based on their responses, provide suggestions on areas to improve and tips to master the selected skill.
    """
    print(analysis_prompt)
    # Use the ChatCompletion API endpoint (correct method for chat-based models)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Use the chat-based model
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": analysis_prompt}
        ],
        max_tokens=200
    )
    
    # Extract suggestions from the response
    suggestions = response['choices'][0]['message']['content'].strip()
    
    return render_template('suggestions.html', suggestions=suggestions)


if __name__ == '__main__':
    app.run(debug=True)


# import boto3
# import json
# from flask import Flask, render_template, request, jsonify

# # Initialize the AWS Bedrock client
# bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')  # Change to your region

# app = Flask(__name__)

# # Function to load skill data from JSON file
# def load_skills_data():
#     try:
#         with open('skills_data.json', 'r') as file:
#             data = file.read().strip()  # Read and strip any leading/trailing whitespace
            
#             if not data:
#                 raise ValueError("The JSON file is empty.")
            
#             return json.loads(data)
    
#     except FileNotFoundError:
#         print("The file 'skills_data.json' was not found.")
#     except json.JSONDecodeError as e:
#         print(f"Error parsing JSON: {e}")
#     except ValueError as e:
#         print(e)

#     return {}  # Return an empty dictionary in case of error

# @app.route('/')
# def index():
#     skills_data = load_skills_data()
    
#     if not skills_data:
#         return "Failed to load skill data. Please check your JSON file.", 500
    
#     skills = [skill['name'] for skill in skills_data['skills']]
#     return render_template('index.html', skills=skills)

# @app.route('/ask_questions', methods=['POST'])
# def ask_questions():
#     skill_name = request.form['skill_name']
    
#     # Create a prompt to generate multiple-choice questions based on the user-provided skill
#     # Your analysis prompt formatted correctly
#     analysis_prompt = f"""
#     Generate a list of 5 multiple-choice questions with 4 choices each for someone looking to improve their {skill_name} skill.
#     The questions should be detailed and relevant to {skill_name}, and follow this format:

#     Question 1: What is the best way to learn {skill_name}?
#     A) Option 1
#     B) Option 2
#     C) Option 3
#     D) Option 4

#     Question 2: How can you improve your {skill_name} skills?
#     A) Option 1
#     B) Option 2
#     C) Option 3
#     D) Option 4

#     Continue this format for 5 questions.
#     """

#     # Construct the payload
#     request_payload = {
#         "modelId": "amazon.nova-pro-v1:0",  # Replace with your actual model ID
#         "body": {
#             "inferenceConfig": {
#                 "max_new_tokens": 500  # Adjust as needed
#             },
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": {
#                         "text": analysis_prompt  # Ensure prompt is wrapped in 'text'
#                     }
#                 }
#             ]
#         },
#         "contentType": "application/json",  # Content type should be JSON
#         "accept": "application/json"  # Expecting JSON response
#     }
    
#     # Send request to AWS Bedrock to generate questions
#     try:
#         response = bedrock_client.invoke_model(
#             modelId=request_payload['modelId'],  # Correct field name
#             body=json.dumps(request_payload['body']),  # Correctly use 'body' as a JSON string
#             contentType=request_payload['contentType'],  # Correct field for content type
#             accept=request_payload['accept']  # Correct field for accept header
#         )
        
#         result = json.loads(response['Body'].read().decode('utf-8'))
        
#         # Assuming the response returns text containing questions
#         questions_text = result.get('output', {}).get('message', {}).get('content', [])
        
#         if not questions_text:
#             return "No questions were generated. Please try again.", 500
        
#         # Parse the questions from the returned text
#         questions = parse_questions(questions_text[0])  # Passing the first element (string content)
        
#         return render_template('ask_questions.html', skill_name=skill_name, questions=questions)

#     except Exception as e:
#         return f"Error invoking AWS Bedrock model: {str(e)}", 500

# # Function to parse the returned text into structured questions
# def parse_questions(questions_text):
#     questions = []
#     question_blocks = questions_text.split("\n---\n")  # Split the text into individual questions
    
#     for block in question_blocks:
#         lines = block.strip().split("\n")
#         question_text = lines[0]  # The first line is the question
#         choices = {letter: choice.strip() for letter, choice in zip("ABCD", lines[1:])}  # Map options to A, B, C, D
#         questions.append({
#             "question": question_text,
#             "choices": choices
#         })
    
#     return questions

# @app.route('/submit_answers', methods=['POST'])
# def submit_answers():
#     skill_name = request.form['skill_name']
    
#     # Collect all answers from the form. It assumes you name each answer field 'answer_X' (where X is the index)
#     answers = [request.form[f'answer_{i}'] for i in range(1, len(request.form))]

#     # Create a system prompt with the answers
#     analysis_prompt = f"""
#     User has selected {skill_name}. Here are their answers to the skill-related questions:
#     {answers}

#     Based on their responses, provide suggestions on areas to improve and tips to master the selected skill.
#     """
    
#     # Structure the request to AWS Bedrock for answer analysis
#     request_payload = {
#         "modelId": "amazon.nova-pro-v1:0",  # Replace with your actual model ID
#         "body": {
#             "inferenceConfig": {
#                 "max_new_tokens": 200
#             },
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": {
#                         "text": analysis_prompt  # Pass the raw prompt directly as content (no "text" field)
#                     }
#                 }
#             ]
#         },
#         "contentType": "application/json",  # Correct field for content type
#         "accept": "application/json"  # Expect JSON response
#     }
    
#     # Send request to AWS Bedrock to generate suggestions
#     try:
#         response = bedrock_client.invoke_model(
#             modelId=request_payload['modelId'],
#             body=json.dumps(request_payload['body']),
#             contentType=request_payload['contentType'],
#             accept=request_payload['accept']
#         )
        
#         result = json.loads(response['Body'].read().decode('utf-8'))
        
#         # Extract suggestions from the response
#         suggestions = result.get('output', {}).get('message', {}).get('content', "No suggestions found.")
        
#         return render_template('suggestions.html', suggestions=suggestions)

#     except Exception as e:
#         return f"Error invoking AWS Bedrock model: {str(e)}", 500

# if __name__ == '__main__':
#     app.run(debug=True)