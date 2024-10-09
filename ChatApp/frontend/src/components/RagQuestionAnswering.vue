<!-- src/components/RagQuestionAnswering.vue -->
<template>
  <div class="rag-container">
    <h2>RAG Question Answering</h2>
    <form @submit.prevent="sendRequest">
      <div class="input-group">
        <label for="question">Question:</label>
        <input v-model="question" id="question" type="text" placeholder="Enter your question" required>
      </div>
      <div class="input-group">
        <label for="pdfFile">PDF File:</label>
        <input @change="handleFileUpload" id="pdfFile" type="file" accept=".pdf" required>
      </div>
      <button type="submit" :disabled="isLoading">Send</button>
    </form>
    <div v-if="isLoading" class="loading">Processing...</div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="response" class="response">
      <h3>Response:</h3>
      <p>{{ response }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import axios from 'axios';

const question = ref('');
const pdfFile = ref<File | null>(null);
const response = ref('');
const isLoading = ref(false);
const error = ref('');

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files) {
    pdfFile.value = target.files[0];
  }
};

const sendRequest = async () => {
  if (!question.value || !pdfFile.value) {
    error.value = 'Please provide both a question and a PDF file.';
    return;
  }

  isLoading.value = true;
  error.value = '';
  response.value = '';

  const formData = new FormData();
  formData.append('question', question.value);
  formData.append('file', pdfFile.value);

  try {
    const result = await axios.post('http://localhost:5001/api/process', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    response.value = result.data.answer;
  } catch (err) {
    console.error('Error:', err);
    if (err.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      error.value = `Server error: ${err.response.status} - ${err.response.data}`;
    } else if (err.request) {
      // The request was made but no response was received
      error.value = 'No response received from server. Please try again.';
    } else {
      // Something happened in setting up the request that triggered an Error
      error.value = `Error: ${err.message}`;
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.rag-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.input-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
}

input[type="text"],
input[type="file"] {
  width: 100%;
  padding: 8px;
  margin-bottom: 10px;
}

button {
  background-color: #4CAF50;
  color: white;
  padding: 10px 15px;
  border: none;
  cursor: pointer;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.loading,
.response,
.error {
  margin-top: 20px;
}

.error {
  color: red;
}
</style>