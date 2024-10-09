<template>
  <div class="chat-interface">
    <div class="chat-container">
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
    
    <div class="context-drawer" :class="{ 'drawer-open': isDrawerOpen }">
      <button @click="toggleDrawer" class="drawer-toggle">
        {{ isDrawerOpen ? '>' : '<' }}
      </button>
      <h3>Selected Contexts</h3>
      <div v-if="selectedContexts.length === 0" class="no-contexts">
        No contexts selected
      </div>
      <div v-else class="context-list">
        <div v-for="(context, index) in selectedContexts" :key="index" class="context-item">
          <p><strong>Page {{ context.page }}:</strong></p>
          <p>{{ context.content }}</p>
          <button @click="removeContext(index)" class="remove-context">Remove</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import axios from 'axios'

const props = defineProps<{
  uploadedFile: File | null,
  selectedContexts: Array<{ page: string, content: string }>
}>()

const emit = defineEmits(['removeContext'])

const inputMessage = ref('')
const messages = ref([])
const isLoading = ref(false)
const chatMessages = ref(null)
const error = ref('')
const isDrawerOpen = ref(false)

const sendButtonText = computed(() => {
  return props.selectedContexts.length > 0 ? 'Ask with context' : 'Ask without context'
})

const sendMessage = async () => {
  if (inputMessage.value.trim() === '' || !props.uploadedFile) return
  
  const userMessage = { type: 'user', text: inputMessage.value }
  messages.value.push(userMessage)
  inputMessage.value = ''
  isLoading.value = true
  error.value = ''

  const question_to_ask = {
    question: userMessage.text,
    contexts: props.selectedContexts 
  }
  console.log(question_to_ask);
  try {
    const answerResponse = await axios.post('http://localhost:5001/api/answer', question_to_ask)
    console.log(answerResponse)
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

const removeContext = (index: number) => {
  emit('removeContext', index)
}

const toggleDrawer = () => {
  isDrawerOpen.value = !isDrawerOpen.value
}

// This method is no longer needed, but kept for backwards compatibility
const updateSelectedContexts = () => {}

defineExpose({ updateSelectedContexts })
</script>

<style scoped>
.chat-interface {
  display: flex;
  height: 100%;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
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

.context-drawer {
  width: 300px;
  height: 100%;
  background-color: #f9f9f9;
  border-left: 1px solid #ccc;
  padding: 20px;
  overflow-y: auto;
  transition: transform 0.3s ease-in-out;
  position: relative;
}

.drawer-open {
  transform: translateX(0);
}

.drawer-toggle {
  position: absolute;
  top: 10px;
  left: -30px;
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 5px 10px;
  cursor: pointer;
}

.context-list {
  margin-top: 20px;
}

.context-item {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
}

.remove-context {
  background-color: #ff4d4d;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 5px;
}

.no-contexts {
  color: #888;
  font-style: italic;
}
</style>