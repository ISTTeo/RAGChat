<template>
    <div class="file-upload">
      <h2>Upload PDF</h2>
      <input type="file" @change="handleFileUpload" accept=".pdf" />
      <div v-if="selectedFile" class="file-info">
        <p>Selected file: {{ selectedFile.name }}</p>
        <button @click="uploadFile" :disabled="isUploading">Upload</button>
      </div>
      <div v-if="isUploading" class="upload-status">Uploading...</div>
      <div v-if="uploadSuccess" class="upload-status success">Upload successful!</div>
      <div v-if="uploadError" class="upload-status error">{{ uploadError }}</div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue'
  
  const selectedFile = ref<File | null>(null)
  const isUploading = ref(false)
  const uploadSuccess = ref(false)
  const uploadError = ref('')
  
  const emit = defineEmits(['fileUploaded'])
  
  const handleFileUpload = (event: Event) => {
    const target = event.target as HTMLInputElement
    if (target.files) {
      selectedFile.value = target.files[0]
      uploadSuccess.value = false
      uploadError.value = ''
    } else {
      uploadError.value = 'Please select a valid PDF file.'
    }
  }
  
  const uploadFile = async () => {
    if (!selectedFile.value) return
    isUploading.value = true
    uploadSuccess.value = false
    uploadError.value = ''
  
    // Simulated API call
    setTimeout(() => {
      isUploading.value = false
      uploadSuccess.value = true
      emit('fileUploaded', selectedFile.value)
    }, 2000)
  }
  </script>


  <style scoped>
  .file-upload {
    padding: 20px;
    border: 1px solid #ccc;
    border-radius: 5px;
  }
  
  h2 {
    margin-top: 0;
  }
  
  input[type="file"] {
    margin-bottom: 10px;
  }
  
  .file-info {
    margin-top: 10px;
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
  
  .upload-status {
    margin-top: 10px;
  }
  
  .success {
    color: green;
  }
  
  .error {
    color: red;
  }
  </style>