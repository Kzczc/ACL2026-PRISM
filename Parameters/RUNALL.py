import requests
import json
import re

# API configuration
API_URL = "http://localhost:8000/v1"
API_KEY = "b42e0b5a3a843a17e1ad39437de13161"
MODEL_NAME = "DS32"

def call_openwebui_api(message, temperature=0.7, top_p=None):
    """Call the OpenWebUI API with specified parameters and return the response"""
    
    # API endpoint for chat completions
    endpoint = f"{API_URL}/chat/completions"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # Build payload
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ],
        "temperature": temperature,
        "max_tokens": 3200
    }
    
    # Add top_p if provided
    if top_p is not None:
        payload["top_p"] = top_p
    
    try:
        # Make the API request
        response = requests.post(endpoint, headers=headers, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')
            # Remove <think> tags and their content
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            return content
        else:
            return f"API Call Failed! Status Code: {response.status_code}, Error: {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"
    except json.JSONDecodeError as e:
        return f"JSON decode error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"



if __name__ == "__main__":
    import json
    import os
    temps = [0, 0.2, 0.4, 0.6, 0.8]
    top_ps = [0.2, 0.6, 0.8, 0.9, 0.95]
    
    for t in temps:
        for p in top_ps:
            print(f"\n{'='*80}")
            print(f"Testing with temperature={t}, top_p={p}")
            print(f"{'='*80}\n")
            
            for i in ['RE', 'KE', 'IFE', 'KM']:
                dir_path = i
                content = ""
                for file in os.listdir(dir_path):
                    if file.endswith('.md'):
                        md_path = os.path.join(dir_path, file)
                        with open(md_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        break
                
                for file in os.listdir(dir_path):
                    if file.endswith('.json'):
                        json_path = os.path.join(dir_path, file)
                        with open(json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        results = []
                        for d in data:
                            question = d['question']
                            
                            prompt = content + "\n" + question
                            print(f"prompt: {prompt}")
                            result = None
                            for attempt in range(3):
                                result = call_openwebui_api(prompt, temperature=t, top_p=p)
                                if not any(err in result for err in ["API Call Failed!", "Request failed:", "JSON decode error:", "Unexpected error:"]):
                                    break
                                print(f"Attempt {attempt + 1} failed, retrying...")
                            
                            print(f"Answer: {result}")
                            d['answer'] = result
                            results.append(d)
                        
                        output_path = os.path.join(dir_path, f'result_{t}_{p}_{file}')
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(results, f, ensure_ascii=False, indent=2)
                        print(f"Results saved to {output_path}")