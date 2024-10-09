<template>
    <div class="chat-interface">
      <div class="chat-messages" ref="chatMessages">
        <div v-for="(message, index) in messages" :key="index" :class="['message', message.type]">
          {{ message.text }}
        </div>
      </div>
      <div class="chat-input">
        <input v-model="inputMessage" @keyup.enter="sendMessage" placeholder="Type your question..." />
        <button @click="sendMessage" :disabled="isLoading || !uploadedFile">Send</button>
      </div>
      <div v-if="isLoading" class="loading">Processing...</div>
      <div v-if="error" class="error">{{ error }}</div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted, watch } from 'vue'
  import axios from 'axios'
  
  const inputMessage = ref('')
  const messages = ref([])
  const isLoading = ref(false)
  const chatMessages = ref(null)
  const error = ref('')
  const uploadedFile = ref<File | null>(null)
  
  const props = defineProps<{
    uploadedFile: File | null
  }>()
  
  watch(() => props.uploadedFile, (newFile) => {
    if (newFile) {
      uploadedFile.value = newFile
      messages.value.push({ type: 'system', text: `File uploaded: ${newFile.name}. You can now ask questions about the content.` })
    }
  })
  
  const sendMessage = async () => {
    if (inputMessage.value.trim() === '' || !uploadedFile.value) return
    
    const userMessage = { type: 'user', text: inputMessage.value }
    messages.value.push(userMessage)
    inputMessage.value = ''
    isLoading.value = true
    error.value = ''
  
    const formData = new FormData()
    formData.append('question', userMessage.text)
    formData.append('file', uploadedFile.value)
  
    try {
      const result = await axios.post('http://localhost:5001/api/process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      messages.value.push({ type: 'bot', text: result.data.answer })
    } catch (err) {
      console.error('Error:', err)
      error.value = 'An error occurred while processing your request. Please try again.'
      messages.value.push({ type: 'system', text: 'Error: Unable to process your request.' })
    } finally {
      isLoading.value = false
    }
  }
  
  const scrollToBottom = () => {
    if (chatMessages.value) {
      chatMessages.value.scrollTop = chatMessages.value.scrollHeight
    }
  }
  
  watch(() => messages.value.length, scrollToBottom)
  onMounted(scrollToBottom)
  </script>
  
  <style scoped>
  .chat-interface {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 100px); /* Adjust based on your header height */
  }
  
  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    margin-bottom: 10px;
  }
  
  .message {
    margin-bottom: 10px;
    padding: 8px;
    border-radius: 5px;
    max-width: 70%;
  }
  
  .user {
    background-color: #e6f2ff;
    align-self: flex-end;
    margin-left: auto;
  }
  
  .bot {
    background-color: #f0f0f0;
    align-self: flex-start;
  }
  
  .chat-input {
    display: flex;
    padding: 10px;
  }
  
  input {
    flex: 1;
    padding: 8px;
    margin-right: 10px;
  }
  
  button {
    padding: 8px 16px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
  
  .loading, .error {
    margin-top: 10px;
    text-align: center;
  }
  
  .error {
    color: red;
  }
  
  .system {
    background-color: #f0f0f0;
    font-style: italic;
  }
  </style>