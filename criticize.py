from openrouter import OpenRouter
import os
import json
import time
from prompts import PHILOSOPHER_PROMPT, STUDENT_PROMPT, DEPRESSED_ANGRY_MOTHER_PROMPT, MATH_TEACHER_PROMPT, PIGEON_PROMPT, TASK_PROMPT
PROMPTS = [PHILOSOPHER_PROMPT, STUDENT_PROMPT, DEPRESSED_ANGRY_MOTHER_PROMPT, MATH_TEACHER_PROMPT, PIGEON_PROMPT]
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("Pls init OPENROUTER_API_KEY")
    exit()

# Init client
if api_key and api_key.startswith("sk-hc"):
    client = OpenRouter(api_key=api_key, server_url="https://ai.hackclub.com/proxy/v1")
else:
    client = OpenRouter(api_key=api_key)

if not os.path.exists("user_data.json"):
    name = input("What's your name, doofus? ").strip()
    age = input("How old are you, grandpa? ").strip()
    interests = input("What are your interests (assuming playing useless video games, doing nothing, and daydreaming, anyway they should be comma separated) ").strip().split(",")
    goals = input("What are your goals (assuming you don't have any, anyway they should be comma separated) ").strip().split(",")
    likes = input("What are your likings, i guess sleeping, eating, and breathing, anyway they should be comma separated ").strip().split(",")
    dislikes = input("What are your dislikings, i think everything, anyway they should be coma separated ").strip().split(",")
    job = input("Jobless right? Prove me wrong! Enter only one job, i mean i am very confident u dont have two, even so dont enter 2 cause this program might break if u have two, so pls just say sleeping ").strip()
    skills = input("What are your skills, like pls just say none ").strip().split(",")
    weaknesses = input("So jobless guy, pls enter your weaknesses like i think they are a lot and u have a lot of time, so take your time to write, and make sure they are comma separated ").strip().split(",")
    with open("user_data.json", "w") as f:
        json.dump({
            "name": name,
            "age": age,
            "interests": interests,
            "goals": goals,
            "likes": likes, 
            "dislikes": dislikes,
            "job": job,
            "skills": skills,
            "weaknesses": weaknesses,
            "journals": []
        }, f, indent=4)
    print("Your useless data is logged. I mean why did i even log them they should be put in the bin. Anyways ending this program now")

with open("user_data.json", "r") as f:
    user_data = json.load(f)

if "journals" not in user_data:
    user_data["journals"] = []

while True:
    user_input = input().strip()
    if user_input == "quit":
        print("Quitting ALREADY?? Expected from a pathetic looser")
        break
    elif user_input.startswith("goal"):
        goal = user_input[5:].strip()
        if goal == "":
            print("Goal EMPTY?? Whats the point looser")
        else:
            user_data["goals"].append(goal)
            with open("user_data.json", "w") as f:
                json.dump(user_data, f, indent=4)
            print("Added a goal, btw i dont think you'll complete it but still dont add any more goals now just waste my time later")
    elif user_input.startswith("like"):
        like = user_input[5:].strip()
        if like == "":
            print("Like nothing?? Why even bother")
        else:
            user_data["likes"].append(like)
            with open("user_data.json", "w") as f:
                json.dump(user_data, f, indent=4)
            print("Really do u like what, anyway good job i guess")
    elif user_input.startswith("dislike"):
        dislike = user_input[8:].strip()
        if dislike == "":
            print("Dislike nothing?? Why even bother")
        else:
            user_data["dislikes"].append(dislike)
            with open("user_data.json", "w") as f:
                json.dump(user_data, f, indent=4)
            print("Really do u dislike what, anyway bad job i guess")
    elif user_input.startswith("interest"):
        interest = user_input[10:].strip()
        if interest == "":
            print("Interest nothing?? Why even bother")
        else:
            user_data["interests"].append(interest)
            with open("user_data.json", "w") as f:
                json.dump(user_data, f, indent=4)
            print("Really do u interest what, anyway good job i guess")
    elif user_input.startswith("age"):
        age = user_input[4:].strip()
        if age == "":
            print("Age EMPTY?? Whats the point looser")
        else:
            user_data["age"] = age
            with open("user_data.json", "w") as f:
                json.dump(user_data, f, indent=4)
            print("Ok so it was your birthday today right loser, wasted a year watching TV, anyway sad birthday")
    elif user_input.startswith("weakness"):
        weakness = user_input[9:].strip()
        if weakness == "":
            print("Weakness EMPTY??")
        else:
            user_data["weaknesses"].append(weakness)
            with open("user_data.json", "w") as f:
                json.dump(user_data, f, indent=4)
            print("Added weakness, just another wound added to ur already wounded body, good job")
    elif user_input.startswith("name"):
        name = user_input[5:].strip()
        if name == "":
            print("Name EMPTY?? Are u god of failures?")
        else:
            user_data["name"] = name
            with open("user_data.json", "w") as f:
                json.dump(user_data, f, indent=4)
            print("Changed your name? To what, some random name? Anyway good job i guess")
    elif user_input.startswith("skills"):
        skills = user_input[7:].strip()
        if skills == "":
            print("Skills EMPTY??")
        else:
            user_data["skills"].append(skills)
            with open("user_data.json", "w") as f:
                json.dump(user_data, f, indent=4)
            print("Added skill, anyway good job i guess")
    elif user_input.startswith("job"):
        job = user_input[4:].strip()
        if job == "":
            print("Job EMPTY?? You lazy bum")
        else:
            user_data["job"] = job
            with open("user_data.json", "w") as f:
                json.dump(user_data, f, indent=4)
            print("Added job, anyway good job i guess")
    elif user_input.startswith("journal"):
        journal = user_input[8:].strip()
        if journal == "":
            print("Journal EMPTY??")
        else:
            user_data["journals"].append(journal)
            with open("user_data.json", "w") as f:
                json.dump(user_data, f, indent=4)
            print("Added journal, was it a whiny one, looser?")
    elif user_input.startswith("criticize"):
        messages = []
        for prompt in PROMPTS:
            try:
                response = client.chat.send(
                    model="google/gemma-4-31b-it:free",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": f"Here is my data: {json.dumps(user_data, indent=4)}"}
                    ],
                    stream=False
                )
            except Exception:
                response = client.chat.send(
                    model="openrouter/free",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": f"Here is my data: {json.dumps(user_data, indent=4)}"}
                    ],
                    stream=False
                )
            message = response.choices[0].message.content
            messages.append(message)
            for char in message:
                print(char, end="", flush=True)
                time.sleep(0.01)
            print("\n\n")
        try:
            task_response = client.chat.send(
                model="google/gemma-4-31b-it:free",
                messages=[
                    {"role": "system", "content": TASK_PROMPT},
                    {"role": "user", "content": f"Here is my data: {json.dumps(user_data, indent=4)}"}
                ],
                stream=False
            )
        except Exception:
            task_response = client.chat.send(
                model="openrouter/free",
                messages=[
                    {"role": "system", "content": TASK_PROMPT},
                    {"role": "user", "content": f"Here is my data: {json.dumps(user_data, indent=4)}"}
                ],
                stream=False
            )
        task = task_response.choices[0].message.content
        for char in task:
            print(char, end="", flush=True)
            time.sleep(0.01)
        print("\n\n")
        
    else:
        print("TYPE SOMETHING USEFUL. AND IF YOU ARE ANGRY ON ME, THATS RIGHT. I HATE YOU TOO")
    