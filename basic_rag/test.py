from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.benchmarks import MMLU
import os, torch, datasets

#datasets.config.MAX_DURATION = 1000000  # Set a very high timeout in seconds

os.environ['CUDA_VISIBLE_DEVICES'] = str(5)

import json

def save_results_to_file(results, filename="mmlu_results.txt"):
    with open(filename, "w") as f:
        f.write(f"Overall Score: {results}\n")
        f.write(json.dumps(results, indent=4))

def remove_model_from_gpu(model):
    model.cpu()  # Move the model back to CPU
    del model  # Delete the reference to the model
    torch.cuda.empty_cache()  # Clear CUDA cache
    print("Model removed from GPU and CUDA cache cleared.")

class Phi(DeepEvalBaseLLM):
    def __init__(
        self,
        model,
        tokenizer,
        name=None
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.model_name = model.name_or_path if name is None else name

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        torch.cuda.empty_cache()  # Clear CUDA cache
        model = self.load_model()

        device = "cuda" # the device to load the model onto

        model_inputs = self.tokenizer([prompt], return_tensors="pt").to(device)

        generated_ids = model.generate(**model_inputs, max_new_tokens=100, do_sample=True)
        return self.tokenizer.batch_decode(generated_ids)[0]

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return self.model_name

############################################################################################

model_id = "microsoft/Phi-3.5-mini-instruct"
bnb_config = BitsAndBytesConfig(
        load_in_4bit=True, 
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
)

# Tokenizer initialization
model = AutoModelForCausalLM.from_pretrained(
    	model_id, 
    	torch_dtype="auto", 
    	trust_remote_code=True,
        quantization_config=bnb_config
	)

tokenizer = AutoTokenizer.from_pretrained(model_id)

phi = Phi(model=model, tokenizer=tokenizer, name="phi-3.5-mini-4b")

benchmark = MMLU()
results = benchmark.evaluate(model=phi)
print("Overall Score: ", results)

filename="phi3.5-mini-4b_quant.txt"
save_results_to_file(results, filename=filename)
print(f"Results saved to {filename}")

remove_model_from_gpu(model)
############################################################################################

model = AutoModelForCausalLM.from_pretrained('microsoft/Phi-3.5-mini-instruct')
tokenizer = AutoTokenizer.from_pretrained('microsoft/Phi-3.5-mini-instruct')

phi = Phi(model=model, tokenizer=tokenizer)

benchmark = MMLU()
results = benchmark.evaluate(model=phi)
print("Overall Score: ", results)

filename="phi3.5-mini-no_quant.txt"
save_results_to_file(results, filename=filename)
print(f"Results saved to {filename}")

remove_model_from_gpu(model)

############################################################################################

model_id = "microsoft/Phi-3.5-MoE-instruct"
bnb_config = BitsAndBytesConfig(
        load_in_4bit=True, 
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
)

# Tokenizer initialization
model = AutoModelForCausalLM.from_pretrained(
    	model_id, 
    	torch_dtype="auto", 
    	trust_remote_code=True,
        quantization_config=bnb_config
	)

tokenizer = AutoTokenizer.from_pretrained(model_id)


phi = Phi(model=model, tokenizer=tokenizer)

benchmark = MMLU()
results = benchmark.evaluate(model=phi)
print("Overall Score: ", results)

filename="phi3.5-MoE-4b_quant.txt"
save_results_to_file(results, filename=filename)
print(f"Results saved to {filename}")

remove_model_from_gpu(model)

############################################################################################

model_id = "microsoft/Phi-3-mini-instruct"
model = AutoModelForCausalLM.from_pretrained(model_id)
tokenizer = AutoTokenizer.from_pretrained(model_id)


# Tokenizer initialization
model = AutoModelForCausalLM.from_pretrained(
    	model_id, 
    	torch_dtype="auto", 
    	trust_remote_code=True,
        quantization_config=bnb_config
	)

tokenizer = AutoTokenizer.from_pretrained(model_id)


phi = Phi(model=model, tokenizer=tokenizer)

benchmark = MMLU()
results = benchmark.evaluate(model=phi)
print("Overall Score: ", results)

filename="phi3-mini-no_quant.txt"
save_results_to_file(results, filename=filename)
print(f"Results saved to {filename}")

remove_model_from_gpu(model)
