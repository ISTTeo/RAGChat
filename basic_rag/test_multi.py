import os
import torch
import json
import argparse
import csv
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.benchmarks import MMLU
import torch.multiprocessing as mp

def save_results_to_file(results, filename="mmlu_results.txt"):
    with open(filename, "w") as f:
        f.write(f"Overall Score: {results}\n")
        f.write(json.dumps(results, indent=4))

def remove_model_from_gpu(model):
    model.cpu()
    del model
    torch.cuda.empty_cache()
    print("Model removed from GPU and CUDA cache cleared.")

class Phi(DeepEvalBaseLLM):
    def __init__(self, model, tokenizer, name=None):
        self.model = model
        self.tokenizer = tokenizer
        self.model_name = model.name_or_path if name is None else name

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        torch.cuda.empty_cache()
        model = self.load_model()
        device = next(model.parameters()).device
        model_inputs = self.tokenizer([prompt], return_tensors="pt").to(device)
        generated_ids = model.generate(**model_inputs, max_new_tokens=100, do_sample=True)
        return self.tokenizer.batch_decode(generated_ids)[0]

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return self.model_name

def evaluate_model(gpu_id, model_config):
    os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
    torch.cuda.set_device(0)  # Use the first (and only) GPU visible to this process
    
    model_id, quantize, name_suffix = model_config
    quantize = quantize.lower() == 'true'  # Convert string to boolean
    
    if quantize:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype="auto",
            trust_remote_code=True,
            quantization_config=bnb_config
        ).to('cuda')
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype="auto",
            trust_remote_code=True
        ).to('cuda')
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    phi = Phi(model=model, tokenizer=tokenizer, name=f"{model_id}-{name_suffix}")
    
    benchmark = MMLU()
    results = benchmark.evaluate(model=phi)
    print(f"Overall Score for {phi.get_model_name()}: {results}")
    
    filename = f"{phi.get_model_name().replace('/', '-')}_results.txt"
    save_results_to_file(results, filename=filename)
    print(f"Results saved to {filename}")
    
    remove_model_from_gpu(model)

def read_model_configs(csv_file):
    model_configs = []
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row
        for row in reader:
            model_configs.append(tuple(row))
    return model_configs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MMLU evaluations on multiple GPUs.")
    parser.add_argument("--gpus", type=int, nargs="+", required=True, help="List of GPU IDs to use")
    parser.add_argument("--config", type=str, required=True, help="Path to CSV file containing model configurations")
    args = parser.parse_args()

    #mp.set_start_method('spawn')
    
    model_configs = read_model_configs(args.config)
    
    available_gpus = args.gpus
    num_gpus = len(available_gpus)
    print(f"Using GPUs: {available_gpus}")
    print(f"Loaded {len(model_configs)} model configurations")
    
    processes = []
    for i, model_config in enumerate(model_configs):
        gpu_id = available_gpus[i % num_gpus]
        p = mp.Process(target=evaluate_model, args=(gpu_id, model_config))
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()

    print("All evaluations completed.")