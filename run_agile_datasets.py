import ollama
import os
from tqdm import tqdm
import json
import argparse
import pandas as pd
import sys
from PIL import Image
from transformers import AutoTokenizer, CLIPTextModel, CLIPTokenizer, CLIPModel 
from torch.nn.functional import cosine_similarity
import torch
import signal
import torch.nn.functional as F
from scipy.spatial.distance import cosine
import requests

BASE_DIR = "..." # Provide the base directory of the datasets

def download_images_by_label(csv_path, no_label_name, output_dir="downloaded_images"):
    """
    Downloads images from a CSV file based on a given label.
    
    Parameters:
        csv_path (str): Path to the CSV file.
        label_name (str): The label to filter images.
        output_dir (str): Directory to save the downloaded images.
    
    Returns:
        list: A list of dictionaries containing index, image name, and local path.
    """
    # Load CSV file
    df = pd.read_csv(csv_path, on_bad_lines='skip')
    
    # Filter data based on label name
    filtered_df = df[df['label'].isin(['positive', 'negative'])]
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    image_list = {}
    
    
    for idx in tqdm(filtered_df['url'].keys(), total=len(filtered_df), desc="Downloading Images"):
        image_url = filtered_df["url"][idx]
        image_label_pn = filtered_df["label"][idx]
        if image_label_pn == 'positive':
            image_label = 'Yes'
        elif image_label_pn == 'negative':
            image_label = 'No'
            
        image_name = f"image_{idx}.jpg"
        image_path = os.path.join(output_dir, image_name)
    
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
    
            with open(image_path, "wb") as img_file:
                img_file.write(response.content)
    
            image_list[idx] = {"name": image_name, "path": image_path, "url": image_url, "label": image_label}
    
        except requests.RequestException as e:
            # print(f"Failed to download {image_url}: {e}")
            pass

        # if idx > 10:
        #     break

    return image_list





# def get_class_embeddings(prompts, tokenizer, text_encoder):
#     text_inputs = tokenizer(prompts, padding="max_length", return_tensors="pt").to(device)
#     outputs = text_encoder(**text_inputs)
#     text_embedding = outputs.pooler_output
#     return text_embedding
    
# def get_query_embedding(query_prompt, tokenizer, text_encoder):
    
#     query_input = tokenizer(query_prompt, padding="max_length", return_tensors="pt").to(device)
#     query_output = text_encoder(**query_input)
#     query_embedding = query_output.pooler_output
#     return query_embedding

def get_class_embeddings(prompts, tokenizer, text_encoder):
    text_inputs = tokenizer(prompts, padding="max_length", return_tensors="pt").to(device)
    outputs = text_encoder(**text_inputs)
    text_embedding = outputs.pooler_output
    return text_embedding
    
def get_query_embedding(query_prompt, tokenizer, text_encoder):
    
    query_input = tokenizer(query_prompt, padding="max_length", return_tensors="pt").to(device)
    query_output = text_encoder(**query_input)
    query_embedding = query_output.pooler_output
    return query_embedding

def compute_scores_clip(class_embeddings, query_embedding, prompts):
     # Compute cosine similarity scores
    similarity_scores = cosine_similarity(query_embedding, class_embeddings, dim=1)  # Shape: [37]
    
    # Find the highest matching score and corresponding item
    max_score_index = torch.argmax(similarity_scores).item()
    max_score = similarity_scores[max_score_index].item()
    best_match = prompts[max_score_index]
    
    # Print the result
   # print(f"Best match: {best_match} with a similarity score of {max_score:.4f}")
    return best_match

    
def compute_best_match(query_text, class_embeddings, class_dict, model_name):
    query_response = ollama.embed(model=model_name, input=query_text)
    query_embedding = query_response["embeddings"]
    query_embedding_tensor = torch.tensor(query_embedding[0])
    
    list_name_emb = list(class_embeddings.keys())
    current_best_score = -1.0  # Start with a low value for cosine similarity
    current_best_match = ""
    
    for class_name in list_name_emb:
        #print(f"Comparing with class: {class_name}")
        class_embeddings_tensor = torch.tensor(class_embeddings[class_name][0])
        # Compute the cosine similarity
        similarity_score = F.cosine_similarity(query_embedding_tensor.unsqueeze(0), class_embeddings_tensor.unsqueeze(0), dim=1)
        
        if similarity_score > current_best_score:
            current_best_score = similarity_score.item()  # Ensure it's a Python float for printing
            current_best_match = class_name
            #print(f"Current best match is: {current_best_match} with score: {current_best_score}")
    matched_label = class_dict[current_best_match] # integer representing class 
    matched_class_name  = current_best_match
    return matched_class_name, matched_label 

def compute_scores(class_embeddings, query_embedding, prompts, temperature=0.8):
    scores = []
    # Compute cosine similarity scores
    for class_name in class_embeddings:
        similarity_scores = cosine_similarity(torch.tensor(query_embedding), torch.tensor(class_embeddings[class_name]), dim=1)  # Shape: [37]
        similarity_scores = similarity_scores / temperature
        scores.append(similarity_scores.item())

    probabilities = F.softmax(torch.tensor(scores), dim=0)
    # Find the highest matching score and corresponding item

    max_prob_index = torch.argmax(probabilities).item()
    max_prob = probabilities[max_prob_index]
    best_match = prompts[max_prob_index]
    
    # Print the result
   # print(f"Best match: {best_match} with a similarity score of {max_score:.4f}")
    return best_match, probabilities, max_prob

def generate_context_embedding(class_names, model_name, options):
    prompt = "You are working on a difficult fine-grained image classification task, here are the only classes you can choose from"+class_names
    context_response = ollama.generate(model=model_name, prompt=prompt, options=options)
    return context_response['context']

def compute_class_embeddings(class_names_list, model_name) :
    class_embeddings = {}
    print("Computing the class embeddings --")
    for class_name in tqdm(class_names_list) :
        # print(class_name)
        response = ollama.embed(model=model_name, input=class_name)
        class_embeddings[class_name] = response["embeddings"]
    
    return class_embeddings


class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException


parser = argparse.ArgumentParser(description="Run numerous experiments with varying VLM models on the traffic sign dataset")

parser.add_argument("--model_name", type=str, required=True, help=" VLM model name")
parser.add_argument("--dataset_name", type=str, required=False, help="Dataset name")
parser.add_argument("--subset", type=str, required=True, help="train, test or validation set")
parser.add_argument("--timeout", type=int, default=100, help="time out duration to skip one sample")
parser.add_argument("--model_unloading", action="store_true", help="Enables unloading mode. Every 100 sampels it unloades the model from the GPU to avoid crashing.")


args = parser.parse_args()

#model_unloading= True


base_dir = BASE_DIR #args.base_dir #

csv_path = os.path.join(base_dir,f"{args.dataset_name}_{args.subset}_labels.csv")
dataset_download_path = f"{BASE_DIR}/downloaded_images/{args.dataset_name}_{args.subset}/"
no_label = "no image"

data = download_images_by_label(csv_path, no_label, dataset_download_path)

model_name  = args.model_name
results_dir = os.path.join(base_dir, "results")
os.makedirs(results_dir, exist_ok=True)
#dataset_name = args.dataset_name#"traffic"
subset = args.subset
results_file_name=os.path.join(results_dir,f"{args.dataset_name}-{model_name}-{subset}.json")
raw_image_info=os.path.join(results_dir,f"{args.dataset_name}-{model_name}-{subset}-raw_info.json")

print("Pulling Ollama Model...")
print(model_name)
ollama.pull(model_name)
print("Done Pulling..")
timeout_duration = args.timeout

options= {  # new
        "seed": 123,
        "temperature": 0,
        "num_ctx": 2048, # must be set, otherwise slightly random output
    }

model_id_clip  = "openai/clip-vit-large-patch14"
device="cuda" if torch.cuda.is_available() else "cpu"
print("Setting up CLIP..")

tokenizer = CLIPTokenizer.from_pretrained(model_id_clip)
text_encoder = CLIPTextModel.from_pretrained(model_id_clip).to(device)
clip_model = CLIPModel.from_pretrained(model_id_clip).to(device)


class_names_list = ["Yes", "No"]
class_dict = {class_name : i for i, class_name in enumerate(class_names_list)}
reverse_class_dict = {v: k for k, v in class_dict.items()}

# ollama.pull("mxbai-embed-large") # model for embedding class names text
# class_embeddings = compute_class_embeddings(class_names_list, model_name)
class_embeddings = get_class_embeddings(class_names_list, tokenizer, text_encoder)
# context_embedding = generate_context_embedding(class_names, model_name, options)
print("Done setting up clip...")

model_labels = {}
dataset_name_for_prompt = args.dataset_name
dataset_name_for_prompt.replace("-", " ")

prompt = f"Is this a photo of {str(dataset_name_for_prompt).replace('-', ' ')}? Answer only with Yes or No"
print(f" The prompt is === {prompt}")
count = 0

print("Begin prompting...")
text_length = 500

for key in tqdm(data.keys()):
    # print(type(key))
    count = count + 1

    image_path = data[key]["path"]

    print(f"Current count {count}")
    #if count  > 10 : 
        # break
#disp_img(image_path)

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_duration)

    try:
    
        response = ollama.generate(model=model_name, prompt=prompt, images=[image_path], options=options)
    

        model_response = response['response']
        if len(model_response) > text_length : 
            query_prompt = model_response[:text_length]
        else : 
            query_prompt = model_response
        
        query_embedding = get_query_embedding(query_prompt, tokenizer, text_encoder)
        class_name = compute_scores_clip(class_embeddings, query_embedding, class_names_list)
        class_number = class_dict[class_name]
        
        #query_response = ollama.embed(model=model_name, input=model_response)
        #query_embedding = query_response["embeddings"]
        # print(query_embedding)

        #best_match_class, best_match_label = compute_best_match(model_response, class_embeddings, class_dict,model_name)

        #best_match, probs, max_prob = compute_scores(class_embeddings, query_embedding[0], class_names_list, temperature=0.2)
        #class_label =  best_match_label #class_dict[best_match]
    
        # Initialize variables for the best match
        # best_match = None
        # best_similarity = -1  # Cosine similarity ranges from -1 to 1, so start with a very low value
        
        # # Find the best matching embedding
        # for class_name, class_embedding in class_embeddings.items():
        #     similarity = 1 - cosine(query_embedding[0], class_embedding[0])  # Cosine similarity is 1 - cosine distance
        #     if similarity > best_similarity:
        #         best_similarity = similarity
        #         best_match = class_name
        # #= get_query_embedding(model_response, tokenizer, text_encoder)
        # matched_label = best_match #compute_scores(traffic_embeedings, response_embedding, class_names_list)
        
    # print(f"{image_path} | {matched_label} | {model_response}")
        model_labels[key] = {
            "path": image_path,
            "label": class_number, # integer index representing class
            "class": class_name, # string indicating class name
            "model_response": model_response, # string coming from the model
            "query_prompt": query_prompt # actual prompt used to generate embedding
        }


    except (TimeoutException, ValueError, ollama._types.ResponseError) as e:
        print(e)
        print(f"Prompt for {image_path} took longer than {timeout_duration} seconds. Moving to the next one.")
        model_labels[key] = {
            "path": None,
            "label": None, # integer index representing class
            "class": None, # string indicating class name
            "model_response": None # string coming from the model
        }
        pass

    finally:
        signal.alarm(0)
        # model_labels[image_path] = {
        #     "label": class_label, # integer index representing class
        #     "class": best_match, # string indicating class name
        #     "model_response": model_response # string coming from the model
        # }

        

with open(results_file_name, 'w') as fp:
    json.dump(model_labels, fp, indent=4)

with open(raw_image_info, 'w') as fp:
    json.dump(data, fp, indent=4)

