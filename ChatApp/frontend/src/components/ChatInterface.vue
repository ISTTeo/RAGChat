<template>
    <div class="chat-interface">
      <div class="chat-messages" ref="chatMessages">
        <div v-for="(message, index) in messages" :key="index" :class="['message', message.type]">
          {{ message.text }}
        </div>
      </div>
      <div class="chat-input">
        <input v-model="inputMessage" @keyup.enter="sendMessage" placeholder="Type your question..." />
        <button @click="sendMessage" :disabled="isLoading || !uploadedFile">
          {{ sendButtonText }}
        </button>
      </div>
      <div v-if="isLoading" class="loading">Processing...</div>
      <div v-if="error" class="error">{{ error }}</div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, computed } from 'vue'
  import axios from 'axios'
  
  const inputMessage = ref('')
  const messages = ref([])
  const isLoading = ref(false)
  const chatMessages = ref(null)
  const error = ref('')
  const selectedContexts = ref([])
  
  const props = defineProps<{
    uploadedFile: File | null
  }>()
  
  const sendButtonText = computed(() => {
    return selectedContexts.value.length > 0 ? 'Ask with context' : 'Ask without context'
  })
  
  const sendMessage = async () => {
    if (inputMessage.value.trim() === '' || !props.uploadedFile) return
    
    const userMessage = { type: 'user', text: inputMessage.value }
    messages.value.push(userMessage)
    inputMessage.value = ''
    isLoading.value = true
    error.value = ''
  
    try {
      let contexts = selectedContexts.value
  
      // Get the answer using the contexts
      const answerResponse = await axios.post('http://localhost:5001/api/answer', {
        question: userMessage.text,
        contexts: contexts
      })
  
      messages.value.push({ type: 'bot', text: answerResponse.data.answer })
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
  
  const updateSelectedContexts = (contexts) => {
    selectedContexts.value = contexts
  }
  
  defineExpose({ updateSelectedContexts })
  </script>
  

  <style scoped>
  .chat-interface {
    display: flex;
    flex-direction: column;
    height: calc(100% - 40px); /* Adjust based on your header height */
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
  </style>