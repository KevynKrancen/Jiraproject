from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json
from prompt import prompt_description, verification_agent

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

@app.route('/process_project', methods=['POST'])
def process_project():
    user_input = request.json.get('input', '')
    
    # First AI assistant processes the input
    first_response = chat_with_ai(prompt_description, user_input)
    
    # Verification agent reviews the first response
    verified_response = chat_with_ai(verification_agent, first_response)
    
    try:
        project_info = json.loads(verified_response)
        questions = []
        
        if not project_info.get('Project_name'):
            questions.append("What would you like to name this project?")
        
        if not project_info.get('Project_type'):
            questions.append("Where do you want to deploy this project? (e.g., web, mobile)")
        
        response = {
            "project_info": project_info,
            "questions": questions,
            "complete": len(questions) == 0
        }
        
        return jsonify(response)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid response from AI", "raw_response": verified_response}), 500

def chat_with_ai(system_prompt, user_input):
    try:
        completion = client.chat.completions.create(
            model="cognitivecomputations/dolphin-2.9-llama3-8b-gguf",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in chat_with_ai: {str(e)}")
        return "An error occurred. Please try again."

@app.route('/reset_description', methods=['POST'])
def reset_project_description():
    global project_description
    project_description = {key: None for key in project_description}
    print(f"Reset project description: {json.dumps(project_description)}")
    return jsonify({"message": "Project description has been reset.", "project_description": project_description})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)