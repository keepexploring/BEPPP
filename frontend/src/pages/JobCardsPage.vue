<template>
  <q-page class="q-pa-md">
    <!-- Header -->
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="text-h5">Job Cards</div>
        <div class="text-caption text-grey-7">
          Manage maintenance jobs and issues
        </div>
      </div>
      <div class="col-auto">
        <q-btn
          color="primary"
          label="New Job Card"
          icon="add"
          @click="showCreateDialog = true"
        />
      </div>
    </div>

    <!-- Filters -->
    <q-card flat bordered class="q-mb-md">
      <q-card-section class="q-py-sm">
        <div class="row q-col-gutter-md">
          <div class="col-auto">
            <q-select
              v-model="filterAssignedTo"
              :options="userOptions"
              label="Assigned To"
              clearable
              dense
              outlined
              style="min-width: 200px"
              @update:model-value="loadCards"
            />
          </div>
          <div class="col-auto">
            <q-select
              v-model="filterPriority"
              :options="['low', 'medium', 'high', 'urgent']"
              label="Priority"
              clearable
              dense
              outlined
              style="min-width: 150px"
              @update:model-value="loadCards"
            />
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- Loading State -->
    <div v-if="loading" class="text-center q-py-xl">
      <q-spinner color="primary" size="50px" />
      <div class="text-caption q-mt-md">Loading job cards...</div>
    </div>

    <!-- Kanban Board -->
    <div v-else class="kanban-board row q-col-gutter-md">
      <!-- To Do Column -->
      <div class="col-12 col-md-3">
        <q-card flat bordered class="column-card">
          <q-card-section class="bg-grey-3">
            <div class="text-subtitle1 text-weight-medium">
              To Do
              <q-badge color="grey-7" :label="getColumnCount('todo')" class="q-ml-sm" />
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section class="card-list-container">
            <div
              class="card-list"
              @dragover="allowDrop($event)"
              @drop="handleDrop($event, 'todo')"
            >
              <JobCard
                v-for="card in getColumnCards('todo')"
                :key="card.card_id"
                :card="card"
                @click="openCardDialog(card)"
                @dragstart="handleDragStart($event, card)"
                draggable="true"
              />
              <div v-if="getColumnCount('todo') === 0" class="text-center text-grey-6 q-py-md">
                No cards
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- In Progress Column -->
      <div class="col-12 col-md-3">
        <q-card flat bordered class="column-card">
          <q-card-section class="bg-blue-2">
            <div class="text-subtitle1 text-weight-medium">
              In Progress
              <q-badge color="blue" :label="getColumnCount('in_progress')" class="q-ml-sm" />
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section class="card-list-container">
            <div
              class="card-list"
              @dragover="allowDrop($event)"
              @drop="handleDrop($event, 'in_progress')"
            >
              <JobCard
                v-for="card in getColumnCards('in_progress')"
                :key="card.card_id"
                :card="card"
                @click="openCardDialog(card)"
                @dragstart="handleDragStart($event, card)"
                draggable="true"
              />
              <div v-if="getColumnCount('in_progress') === 0" class="text-center text-grey-6 q-py-md">
                No cards
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Blocked Column -->
      <div class="col-12 col-md-3">
        <q-card flat bordered class="column-card">
          <q-card-section class="bg-orange-2">
            <div class="text-subtitle1 text-weight-medium">
              Blocked
              <q-badge color="orange" :label="getColumnCount('blocked')" class="q-ml-sm" />
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section class="card-list-container">
            <div
              class="card-list"
              @dragover="allowDrop($event)"
              @drop="handleDrop($event, 'blocked')"
            >
              <JobCard
                v-for="card in getColumnCards('blocked')"
                :key="card.card_id"
                :card="card"
                @click="openCardDialog(card)"
                @dragstart="handleDragStart($event, card)"
                draggable="true"
              />
              <div v-if="getColumnCount('blocked') === 0" class="text-center text-grey-6 q-py-md">
                No cards
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Done Column -->
      <div class="col-12 col-md-3">
        <q-card flat bordered class="column-card">
          <q-card-section class="bg-green-2">
            <div class="text-subtitle1 text-weight-medium">
              Done
              <q-badge color="green" :label="getColumnCount('done')" class="q-ml-sm" />
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section class="card-list-container">
            <div
              class="card-list"
              @dragover="allowDrop($event)"
              @drop="handleDrop($event, 'done')"
            >
              <JobCard
                v-for="card in getColumnCards('done')"
                :key="card.card_id"
                :card="card"
                @click="openCardDialog(card)"
                @dragstart="handleDragStart($event, card)"
                draggable="true"
              />
              <div v-if="getColumnCount('done') === 0" class="text-center text-grey-6 q-py-md">
                No cards
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Create Card Dialog -->
    <JobCardDialog
      v-model="showCreateDialog"
      @saved="onCardSaved"
    />

    <!-- Edit Card Dialog -->
    <JobCardDialog
      v-model="showEditDialog"
      :card-id="selectedCardId"
      @saved="onCardSaved"
      @deleted="onCardDeleted"
    />
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { jobCardsAPI } from 'src/services/api'
import JobCard from 'src/components/JobCard.vue'
import JobCardDialog from 'src/components/JobCardDialog.vue'

const $q = useQuasar()

const loading = ref(false)
const cards = ref([])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const selectedCardId = ref(null)
const draggedCard = ref(null)

// Filters
const filterAssignedTo = ref(null)
const filterPriority = ref(null)
const userOptions = ref([])

onMounted(() => {
  loadCards()
})

const loadCards = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterAssignedTo.value) {
      params.assigned_to = filterAssignedTo.value.value
    }
    const response = await jobCardsAPI.list(params)
    cards.value = response.data.cards || []
  } catch (error) {
    console.error('Failed to load job cards:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load job cards',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

// Get cards for a specific column
const getColumnCards = (status) => {
  let filtered = cards.value.filter(card => card.status === status)

  // Apply priority filter
  if (filterPriority.value) {
    filtered = filtered.filter(card => card.priority === filterPriority.value)
  }

  return filtered
}

// Get count for a column
const getColumnCount = (status) => {
  return getColumnCards(status).length
}

// Open card detail dialog
const openCardDialog = (card) => {
  selectedCardId.value = card.card_id
  showEditDialog.value = true
}

// Drag and drop handlers
const handleDragStart = (event, card) => {
  draggedCard.value = card
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/html', event.target.innerHTML)
  event.target.style.opacity = '0.4'
}

const allowDrop = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

const handleDrop = async (event, newStatus) => {
  event.preventDefault()

  if (!draggedCard.value) return

  const card = draggedCard.value

  // Don't update if status hasn't changed
  if (card.status === newStatus) {
    draggedCard.value = null
    return
  }

  try {
    // Update card status via API
    await jobCardsAPI.update(card.card_id, { status: newStatus })

    // Update local state
    const cardIndex = cards.value.findIndex(c => c.card_id === card.card_id)
    if (cardIndex !== -1) {
      cards.value[cardIndex].status = newStatus
    }

    $q.notify({
      type: 'positive',
      message: 'Card moved successfully',
      position: 'top'
    })
  } catch (error) {
    console.error('Failed to update card status:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to move card',
      position: 'top'
    })
  } finally {
    draggedCard.value = null
  }
}

// Event handlers
const onCardSaved = () => {
  showCreateDialog.value = false
  showEditDialog.value = false
  selectedCardId.value = null
  loadCards()
}

const onCardDeleted = () => {
  showEditDialog.value = false
  selectedCardId.value = null
  loadCards()
}
</script>

<style scoped>
.kanban-board {
  min-height: calc(100vh - 250px);
}

.column-card {
  height: calc(100vh - 300px);
  display: flex;
  flex-direction: column;
}

.card-list-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.card-list {
  min-height: 100%;
}
</style>
