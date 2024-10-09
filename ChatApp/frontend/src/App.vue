<template>
  <div id="app">
    <div class="split-layout">
      <div class="chat-section">
        <h1>RAG Question Answering</h1>
        <ChatInterface ref="chatInterface" :uploadedFile="uploadedFile" />
      </div>
      <div class="file-upload-section">
        <FileUpload @fileUploaded="handleFileUpload" @contextsUpdated="handleContextsUpdated" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ChatInterface from './components/ChatInterface.vue'
import FileUpload from './components/FileUpload.vue'

const uploadedFile = ref<File | null>(null)
const chatInterface = ref(null)

const handleFileUpload = (file: File) => {
  uploadedFile.value = file
}

const handleContextsUpdated = (contexts) => {
  if (chatInterface.value) {
    chatInterface.value.updateSelectedContexts(contexts)
  }
}
</script>

<style>
body, html {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}

#app {
  font-family: Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
}

.split-layout {
  display: flex;
  height: 100vh; /* Adjust based on your header height */
  width: 100%;
}

.chat-section, .file-upload-section {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  height: 100%;
}

.chat-section {
  border-right: 1px solid #ccc;
}

h1 {
  margin-top: 0;
}

@media (max-width: 768px) {
  .split-layout {
    flex-direction: column;
  }
  
  .chat-section {
    border-right: none;
    border-bottom: 1px solid #ccc;
  }
}
</style>