<template>
  <div class="file-upload">
    <h2>Upload PDFs and Ask Context Question</h2>
    <div 
      class="upload-container"
      :class="{ 'dragging': isDragging }"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <input 
        type="file" 
        @change="handleFileSelect" 
        accept=".pdf" 
        id="file-input" 
        class="file-input"
        multiple
      />
      <label for="file-input" class="file-input-label">
        <span>Drag & Drop PDFs here or Click to Browse</span>
      </label>
    </div>
    <div v-if="isUploading" class="upload-status">
      Uploading... {{ uploadProgress.toFixed(2) }}%
      <div class="progress-bar">
        <div class="progress" :style="{ width: `${uploadProgress}%` }"></div>
      </div>
    </div>
    <div v-if="uploadSuccess" class="upload-status success">Upload successful!</div>
    <div v-if="uploadError" class="upload-status error">{{ uploadError }}</div>

    <div v-if="uploadedFiles.length > 0" class="context-question-section">
      <h3>Ask a Context Question</h3>
      <input 
        v-model="contextQuestion" 
        @keyup.enter="getContext" 
        placeholder="Enter your question..." 
        class="context-input"
      />
      <button @click="getContext" :disabled="isLoadingContext">Get Context</button>
      <div v-if="isLoadingContext" class="loading-context">Loading context...</div>
      <div v-if="contextError" class="error">{{ contextError }}</div>
      <div v-if="contexts.length > 0" class="context-results">
        <h4>Relevant Contexts:</h4>
        <div v-for="(context, index) in contexts" :key="index" class="context-item">
          <label>
            <input type="checkbox" v-model="context.selected" @change="updateSelectedContexts" />
            <strong>File: {{ context.fileName }} - Page {{ context.page }} ({{ context.token_count }} tokens):</strong>
          </label>
          <p>{{ context.content }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import axios from 'axios'

const props = defineProps<{
  selectedContexts: Array<{ fileName: string, page: string, content: string }>
}>()

const emit = defineEmits(['filesUploaded', 'contextsUpdated'])

const uploadedFiles = ref<File[]>([])
const isUploading = ref(false)
const uploadSuccess = ref(false)
const uploadError = ref('')
const isDragging = ref(false)
const contextQuestion = ref('')
const isLoadingContext = ref(false)
const contextError = ref('')
const contexts = ref<Array<{ fileName: string, page: string, content: string, token_count: number, selected: boolean }>>([])
const uploadProgress = ref(0)

const handleDragOver = (event: DragEvent) => {
  isDragging.value = true
}

const handleDragLeave = (event: DragEvent) => {
  isDragging.value = false
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files) {
    handleFiles(Array.from(files))
  }
}

const handleFileSelect = (event: Event) => {
  const files = (event.target as HTMLInputElement).files
  if (files) {
    handleFiles(Array.from(files))
  }
}

const handleFiles = (files: File[]) => {
  const pdfFiles = files.filter(file => file.type === 'application/pdf')
  if (pdfFiles.length > 0) {
    uploadedFiles.value.push(...pdfFiles)
    uploadFiles()
  } else {
    uploadError.value = 'Please select valid PDF files.'
  }
}

const removeFile = (index: number) => {
  uploadedFiles.value.splice(index, 1)
  emit('filesUploaded', uploadedFiles.value)
}

const uploadFiles = async () => {
  if (uploadedFiles.value.length === 0) return
  isUploading.value = true
  uploadSuccess.value = false
  uploadError.value = ''
  uploadProgress.value = 0

  try {
    const formData = new FormData()
    uploadedFiles.value.forEach((file, index) => {
      formData.append(`file${index}`, file)
    })

    const response = await fetch('http://localhost:5001/api/upload', {
      method: 'POST',
      body: formData,
    })

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (reader) {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.trim()) {
            const data = JSON.parse(line)
            if (data.status === 'processing') {
              uploadProgress.value = data.progress
            } else if (data.status === 'complete') {
              uploadSuccess.value = true
              emit('filesUploaded', uploadedFiles.value)
            } else if (data.error) {
              throw new Error(data.error)
            }
          }
        }
      }
    } else {
      throw new Error('Failed to get response reader')
    }
  } catch (error) {
    console.error('Upload error:', error)
    uploadError.value = 'An error occurred during upload. Please try again.'
  } finally {
    isUploading.value = false
  }
}

const getContext = async () => {
  if (!contextQuestion.value.trim()) return
  isLoadingContext.value = true
  contextError.value = ''
  contexts.value = []

  try {
    const response = await axios.post('http://localhost:5001/api/query', {
      question: contextQuestion.value,
      files: uploadedFiles.value.map(file => file.name)
    })

    if (response.status === 200) {
      contexts.value = response.data.contexts.map((ctx: any) => ({
        ...ctx,
        selected: false,
        token_count: ctx.token_count || 0 // Ensure token_count is included
      }))
    } else {
      throw new Error('Failed to get context')
    }
  } catch (error) {
    console.error('Context error:', error)
    contextError.value = 'An error occurred while fetching context. Please try again.'
  } finally {
    isLoadingContext.value = false
  }
}

const updateSelectedContexts = () => {
  const newSelectedContexts = contexts.value
    .filter(context => context.selected)
    .map(({ fileName, page, content, token_count }) => ({ fileName, page, content, token_count }))
  
  emit('contextsUpdated', newSelectedContexts)
}

// Watch for changes in contexts and update selected contexts
watch(contexts, updateSelectedContexts, { deep: true })
</script>

<style scoped>
.file-upload {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
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
  margin-bottom: 20px;
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

.context-input {
  width: 100%;
  padding: 8px;
  margin-bottom: 10px;
}

.context-results {
  margin-top: 20px;
}

.context-item {
  background-color: #f0f0f0;
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 4px;
}

.upload-status, .loading-context, .error {
  margin-top: 10px;
}

.success {
  color: green;
}

.error {
  color: red;
}

.uploaded-files-list {
  margin-top: 20px;
}

.uploaded-files-list ul {
  list-style-type: none;
  padding: 0;
}

.uploaded-files-list li {
  margin-bottom: 5px;
}

.remove-file-btn {
  margin-left: 10px;
  padding: 2px 5px;
  background-color: #ff4444;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background-color: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
  margin-top: 10px;
}

.progress {
  height: 100%;
  background-color: #4CAF50;
  transition: width 0.3s ease;
}

</style>