<template>
    <div 
      class="file-upload"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <h2>Upload PDF</h2>
      <div 
        class="upload-container"
        :class="{ 'dragging': isDragging }"
      >
        <input 
          type="file" 
          @change="handleFileSelect" 
          accept=".pdf" 
          id="file-input" 
          class="file-input"
        />
        <label for="file-input" class="file-input-label">
          <span v-if="!selectedFile">Drag & Drop PDF here or Click to Browse</span>
          <span v-else>{{ selectedFile.name }}</span>
        </label>
        <div v-if="isUploading" class="upload-status">Uploading...</div>
        <div v-if="uploadSuccess" class="upload-status success">Upload successful!</div>
        <div v-if="uploadError" class="upload-status error">{{ uploadError }}</div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue'
  
  const selectedFile = ref<File | null>(null)
  const isUploading = ref(false)
  const uploadSuccess = ref(false)
  const uploadError = ref('')
  const isDragging = ref(false)
  
  const emit = defineEmits(['fileUploaded'])
  
  const handleDragOver = (event: DragEvent) => {
    isDragging.value = true
  }
  
  const handleDragLeave = (event: DragEvent) => {
    isDragging.value = false
  }
  
  const handleDrop = (event: DragEvent) => {
    isDragging.value = false
    const files = event.dataTransfer?.files
    if (files && files.length > 0) {
      handleFile(files[0])
    }
  }
  
  const handleFileSelect = (event: Event) => {
    const files = (event.target as HTMLInputElement).files
    if (files && files.length > 0) {
      handleFile(files[0])
    }
  }
  
  const handleFile = (file: File) => {
    if (file.type === 'application/pdf') {
      selectedFile.value = file
      uploadFile()
    } else {
      uploadError.value = 'Please select a valid PDF file.'
    }
  }
  
  const uploadFile = async () => {
    if (!selectedFile.value) return
    isUploading.value = true
    uploadSuccess.value = false
    uploadError.value = ''
  
    try {
      // Simulated API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      uploadSuccess.value = true
      emit('fileUploaded', selectedFile.value)
    } catch (error) {
      uploadError.value = 'An error occurred during upload. Please try again.'
    } finally {
      isUploading.value = false
    }
  }
  </script>
  
  <style scoped>
  .file-upload {
    height: 90%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 20px;
    box-sizing: border-box;
  }
  
  h2 {
    margin-bottom: 20px;
  }
  
  .upload-container {
    width: 100%;
    max-width: 400px;
    height: 200px;
    border: 2px dashed #ccc;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    transition: all 0.3s ease;
  }
  
  .upload-container.dragging {
    border-color: #4CAF50;
    background-color: rgba(76, 175, 80, 0.1);
  }
  
  .file-input {
    display: none;
  }
  
  .file-input-label {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 100%;
    cursor: pointer;
    font-size: 16px;
    color: #666;
  }
  
  .upload-status {
    margin-top: 20px;
  }
  
  .success {
    color: green;
  }
  
  .error {
    color: red;
  }
  </style>