<template>
    <div class="file-upload">
      <h2>Upload PDF</h2>
      <div class="upload-container">
        <input type="file" @change="handleFileUpload" accept=".pdf" id="file-input" />
        <label for="file-input" class="file-input-label">Choose a file</label>
        <div v-if="selectedFile" class="file-info">
          <p>Selected file: {{ selectedFile.name }}</p>
          <button @click="uploadFile" :disabled="isUploading">Upload</button>
        </div>
        <div v-if="isUploading" class="upload-status">Uploading...</div>
        <div v-if="uploadSuccess" class="upload-status success">Upload successful!</div>
        <div v-if="uploadError" class="upload-status error">{{ uploadError }}</div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  // ... (script content remains the same) ...
  </script>
  
  <style scoped>
  .file-upload {
    height: 100%;
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
    text-align: center;
  }
  
  #file-input {
    display: none;
  }
  
  .file-input-label {
    display: inline-block;
    padding: 10px 20px;
    background-color: #4CAF50;
    color: white;
    cursor: pointer;
    border-radius: 4px;
    margin-bottom: 20px;
  }
  
  .file-info {
    margin-top: 20px;
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
    margin-top: 20px;
  }
  
  .success {
    color: green;
  }
  
  .error {
    color: red;
  }
  </style>