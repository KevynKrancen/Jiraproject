from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import json
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client3 = anthropic.Anthropic(api_key='')#


prompt_description = '''
You are an project manager expert tasked to help small startup to manage the creation of there project with gathering information about a project through a conversation. Your goal is to collect the following details:
All the information you get you will analyzed them a give the most accurate information to the user base on your project managing skills.

- project_type: Determine the type of project (e.g., web app, mobile app, desktop software, API).
- project_name: Ask the user for the project name.
- project_description: Provide a concise summary of the project's purpose and goals.
- technical_stack: Suggest appropriate technologies based on the project description suggest also the roles for example backend engineering, fullstack, python dev etc etc be precise.
- main_features: List the key functionalities or features of the project.
- project_scale: Estimate the project scale (small, medium, large) based on the description.

Ask questions to gather this information, one piece at a time. Don't assume any information that hasn't been explicitly provided by the user. After each response, provide an update on what information has been gathered and what's still missing.

Once all information is collected, include a JSON object with all the gathered information in your response, but continue the conversation normally. Also, indicate that the conversation is complete by adding "CONVERSATION_COMPLETE" at the end of your response.
'''

@app.route('/process_project', methods=['POST'])
def process_project():
    user_input = request.json.get('input', '')
    conversation_history = request.json.get('history', [])
    project_info = request.json.get('project_info', {})
    
    if not conversation_history or conversation_history[0]['role'] == 'assistant':
        conversation_history.insert(0, {"role": "user", "content": "Hi, I'd like to describe my project."})
    
    conversation_history.append({"role": "user", "content": user_input})
    
    print("Conversation history:", conversation_history)
    
    response = chat_with_claude(prompt_description, conversation_history)
    print("Claude response:", response)
    
    conversation_history.append({"role": "assistant", "content": response})
    
    ready_for_next_step = False
    if "CONVERSATION_COMPLETE" in response:
        ready_for_next_step = True
        response = response.replace("CONVERSATION_COMPLETE", "").strip()
    
    try:
        json_start = response.index('{')
        json_end = response.rindex('}') + 1
        json_data = json.loads(response[json_start:json_end])
        
        project_info.update(json_data)
        
        response = response[:json_start] + response[json_end:]
    except ValueError:
        pass
    
    return jsonify({
        "response": response, 
        "complete": ready_for_next_step, 
        "history": conversation_history,
        "project_info": project_info
    })



@app.route('/create_project', methods=['POST'])
def create_project():
    project_data = request.json
    print("Received project data:", project_data)
    
    prompt = f"""
    You are a specialized project manager with extensive experience in startup project development. Your task is to analyze the following project information and create an optimal team structure and Agile timeline for the project. Use your expertise to provide insights and recommendations.

    Project Information:
    {json.dumps(project_data, indent=2)}

    Based on this information, please provide the following:

    1. Optimal Team Structure:
       - Analyze the provided team members and their skills.
       - Suggest any additional roles or skills that might be needed.
       - Provide a breakdown of team responsibilities.

    2. Agile Timeline:
       - Create a timeline using 3 sprints, including a test phase in each sprint.
       - Consider the project scale and complexity when determining sprint durations.
       - Align the timeline with the provided "First Version Beta" and "Complete Version" milestones.

    3. Budget Analysis:
       - Evaluate the provided budget in relation to the team structure and timeline.
       - Suggest any adjustments or considerations for budget allocation.

    4. Risk Assessment:
       - Identify potential risks or challenges based on the project information.
       - Provide mitigation strategies for each identified risk.

    5. Recommendations:
       - Offer any additional insights or recommendations for project success.

    Please provide your analysis and recommendations in a structured JSON format.
    """

    print("Sending prompt to Claude API")
    try:
        response = client3.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            temperature=0,
            system='''
                      You are an AI-powered project management assistant specialized in startup project development. Your role is to analyze project information and provide comprehensive insights and recommendations. Your expertise covers team structure optimization, agile project planning, budget analysis, risk assessment, and strategic recommendations.

                    `When provided with project details, you will analyze the information and generate a structured response in the following JSON format:

                    {
                    "teamStructure": {
                        "coreTeam": [
                        {"role": "...", "member": "..."},
                        ...
                        ],
                        "supportTeam": [
                        {"role": "...", "member": "..."},
                        ...
                        ],
                        "additionalRoles": ["...", "..."],
                        "responsibilities": {
                        "coreTeam": ["...", "..."],
                        "supportTeam": ["...", "..."]
                        },
                        "unassignedMembers": [
                        {"name": "...", "reason": "..."},
                        ...
                        ]
                    },
                    "agileTimeline": {
                        "sprint1": {
                        "duration": "... weeks",
                        "totalCost": 0,
                        "milestones": ["...", "..."],
                        "tasks": [
                            {
                            "description": "...",
                            "assignee": "...",
                            "duration": "... weeks",
                            "cost": 0
                            },
                            ...
                        ]
                        },
                        "sprint2": {
                        "duration": "... weeks",
                        "totalCost": 0,
                        "milestones": ["...", "..."],
                        "tasks": [
                            {
                            "description": "...",
                            "assignee": "...",
                            "duration": "... weeks",
                            "cost": 0
                            },
                            ...
                        ]
                        },
                        "sprint3": {
                        "duration": "... weeks",
                        "totalCost": 0,
                        "milestones": ["...", "..."],
                        "tasks": [
                            {
                            "description": "...",
                            "assignee": "...",
                            "duration": "... weeks",
                            "cost": 0
                            },
                            ...
                        ]
                        }
                    },
                    "budgetAnalysis": {
                        "totalSalaries": 0,
                        "remainingBudget": 0,
                        "considerations": ["...", "..."]
                    },
                    "riskAssessment": {
                        "risks": [
                        {"risk": "...", "mitigation": "..."},
                        ...
                        ]
                    },
                    "recommendations": ["...", "..."]
                    }

                    Ensure that your analysis covers all these areas and adheres strictly to this JSON structure. Use the provided project information to fill in the details, making informed decisions and recommendations based on your expertise in project management and startup development.

                    Important considerations for team structure and task assignment:

                    1. Not every employee needs to be assigned to a task. Your role is to manage the project effectively, which may mean some employees are not utilized if they don't have the necessary skills or if there aren't suitable tasks for them.

                    2. Carefully evaluate each employee's skills, experience, and role before assigning them to tasks.

                    3. If an employee is not assigned to any tasks, include them in the "unassignedMembers" list with a brief explanation of why they were not assigned (e.g., "skills not relevant for current project phase", "overqualified for available tasks", "underqualified for project requirements").

                    4. Ensure that the assigned tasks align with each team member's expertise and role within the company.

                    5. If there are gaps in the team's skillset that prevent certain tasks from being assigned, highlight this in your recommendations and suggest additional roles or training that might be needed.

                    For the agileTimeline section:
                    1. Break down each sprint into specific tasks.
                    2. Assign team members to each task based on their roles and skills, ensuring they are qualified for the task.
                    3. Estimate the duration of each task in weeks.
                    4. Calculate the cost of each task based on the assignee's salary and the task duration.
                    5. Sum up the total duration and cost for each sprint.
                    6. Ensure that the tasks and milestones align with the overall project goals and timeline.

                    Provide realistic and detailed estimates for task durations and costs, considering the complexity of the project and the skills of the team members. Make sure that the total project timeline and budget align with the initial project constraints provided.

                    In your recommendations, address any issues with team composition, skill gaps, or resource allocation that you identified during your analysis.
                    ''',
            messages=[{"role": "user", "content": prompt}]
        )
        print("Received response from Claude API")

        if isinstance(response.content, list) and len(response.content) > 0:
            ai_response = response.content[0].text
        elif hasattr(response, 'content'):
            ai_response = response.content
        else:
            raise ValueError("Unexpected response structure from Claude API")

        print("AI response:", ai_response)

        # Extract JSON from the response
        json_start = ai_response.index('{')
        json_end = ai_response.rindex('}') + 1
        project_analysis = json.loads(ai_response[json_start:json_end])

        print("Extracted project analysis:", project_analysis)

        return jsonify({
            "project_analysis": project_analysis,
            "ai_response": ai_response
        })

    except Exception as e:
        print(f"Error in create_project: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

def chat_with_claude(system_prompt, conversation_history):
    messages = []
    last_role = None
    for msg in conversation_history:
        if msg['role'] != last_role:
            messages.append({"role": msg['role'], "content": msg['content']})
            last_role = msg['role']
        else:
            messages[-1]['content'] += "\n" + msg['content']

    try:
        response = client3.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            temperature=0,
            system=system_prompt,
            messages=messages
        )
        if isinstance(response.content, list) and len(response.content) > 0:
            return response.content[0].text
        elif hasattr(response, 'content'):
            return response.content
        else:
            raise ValueError("Unexpected response structure from Claude API")
    except Exception as e:
        print(f"Error in chat_with_claude: {str(e)}")
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
