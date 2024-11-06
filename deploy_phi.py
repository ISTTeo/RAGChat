import os
import torch
from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

app = Flask(__name__)

model = None
tokenizer = None
pipe = None
current_model_id = None
current_gpu_id = None

def load_model(model_id, gpu_id):
    global model, tokenizer, pipe, current_model_id, current_gpu_id
    
    # Check if the model is already loaded with the same configuration
    if model_id == current_model_id and gpu_id == current_gpu_id:
        return jsonify({'message': 'Model already initialized with the same configuration'})
    
    device = f'cuda:{gpu_id}' if torch.cuda.is_available() else 'cpu'
    
    # Clear CUDA cache if switching GPUs or models
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    pipe = pipeline("text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    device=device,
                    max_new_tokens=1024)
    
    current_model_id = model_id
    current_gpu_id = gpu_id

@app.route('/initialize', methods=['POST'])
def initialize():
    global model, current_model_id, current_gpu_id
    data = request.json
    model_id = data.get('model_id', 'microsoft/Phi-3-mini-4k-instruct')
    gpu_id = data.get('gpu_id', 0)

    # Check if the requested model is already loaded
    if model is not None and model_id == current_model_id and gpu_id == current_gpu_id:
        return jsonify({'message': 'Model already initialized with the same configuration'})

    os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
    
    try:
        load_model(model_id, gpu_id)
        return jsonify({'message': 'Model initialized successfully'})
    except Exception as e:
        return jsonify({'error': f'Failed to initialize model: {str(e)}'}), 500

@app.route('/generate', methods=['POST'])
def generate():
    global pipe
    if pipe is None:
        return jsonify({'error': 'Model not initialized. Call /initialize first.'}), 400
    
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    max_new_tokens = data.get('max_new_tokens', 1024)
    
    try:
        result = pipe(prompt, max_new_tokens=max_new_tokens)
        generated_text = result[0]['generated_text']
        # Parsing the response to extract only the assistant's part
        assistant_response = generated_text.split("<|assistant|>")[-1].strip()
        return jsonify({'generated_text': assistant_response})
    except Exception as e:
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)