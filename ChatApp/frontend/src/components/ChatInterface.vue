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
  // ... (script content remains the same) ...
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