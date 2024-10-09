<template>
  <div id="app">
    <header>
      <img alt="Vue logo" class="logo" src="@/assets/logo.svg" width="125" height="125" />
      <h1>RAG Question Answering</h1>
    </header>
    <div class="content-wrapper">
      <div class="chat-section">
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
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

header {
  margin-bottom: 2rem;
}

.content-wrapper {
  display: flex;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.chat-section {
  flex: 1;
  margin-right: 20px;
}

.file-upload-section {
  width: 300px;
}

@media (max-width: 768px) {
  .content-wrapper {
    flex-direction: column;
  }

  .chat-section, .file-upload-section {
    width: 100%;
    margin-right: 0;
    margin-bottom: 20px;
  }
}
</style>