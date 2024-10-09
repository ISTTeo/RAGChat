<template>
    <div class="file-upload">
      <h2>Upload PDF and Ask Context Question</h2>
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
        />
        <label for="file-input" class="file-input-label">
          <span v-if="!selectedFile">Drag & Drop PDF here or Click to Browse</span>
          <span v-else>{{ selectedFile.name }}</span>
        </label>
      </div>
      <div v-if="isUploading" class="upload-status">Uploading...</div>
      <div v-if="uploadSuccess" class="upload-status success">Upload successful!</div>
      <div v-if="uploadError" class="upload-status error">{{ uploadError }}</div>
  
      <div v-if="uploadSuccess" class="context-question-section">
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
              <strong>Page {{ context.page }}:</strong>
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
  
  const selectedFile = ref<File | null>(null)
  const isUploading = ref(false)
  const uploadSuccess = ref(false)
  const uploadError = ref('')
  const isDragging = ref(false)
  const contextQuestion = ref('')
  const isLoadingContext = ref(false)
  const contextError = ref('')
  const contexts = ref<Array<{ page: string, content: string, selected: boolean }>>([])
  
  const emit = defineEmits(['fileUploaded', 'contextsUpdated'])
  //const hasSelectedContexts = computed(() => contexts.value.some(context => context.selected))
  
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
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const response = await axios.post('http://localhost:5001/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (response.status === 200) {
      uploadSuccess.value = true
      emit('fileUploaded', selectedFile.value)
    } else {
      throw new Error('Upload failed')
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
      question: contextQuestion.value
    })

    if (response.status === 200) {
      contexts.value = response.data.contexts.map((ctx: any) => ({
        ...ctx,
        selected: false
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
  const selectedContexts = contexts.value.filter(context => context.selected)
  emit('contextsUpdated', selectedContexts)
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
</style>
