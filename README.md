
    curl -X POST http://localhost:5000/initialize
         -H "Content-Type: application/json"      
         -d '{"model_id": "microsoft/Phi-3-mini-4k-instruct", "gpu_id": 0}'

    python rest_rag.py 
        --question "What are AI agents?" 
        --api_url http://localhost:5000 
        --num_contexts 3

