<template>
  <div id="app">
    <div class="split-layout">
      <div class="chat-section">
        <h1>RAG Question Answering</h1>
        <ChatInterface :uploadedFile="uploadedFile" />
      </div>
      <div class="file-upload-section">
        <FileUpload @fileUploaded="handleFileUpload" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ChatInterface from './components/ChatInterface.vue'
import FileUpload from './components/FileUpload.vue'

const uploadedFile = ref<File | null>(null)

const handleFileUpload = (file: File) => {
  uploadedFile.value = file
}
</script>

<style scoped>
#app {
  font-family: Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  height: 100%;
  margin: 0;
  padding: 0;
}

.split-layout {
  display: flex;
  height: 100%;
}

.chat-section, .file-upload-section {
  flex: 1;
  padding: 20px;
}

.chat-section {
  border-right: 1px solid #ccc;
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