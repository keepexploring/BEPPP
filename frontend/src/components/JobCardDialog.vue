<template>
  <q-dialog v-model="showDialog" @hide="onHide" persistent>
    <q-card style="min-width: 700px; max-width: 900px; height: 80vh; display: flex; flex-direction: column;">
      <!-- Header -->
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">{{ isEditMode ? 'Edit Job Card' : 'Create Job Card' }}</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="closeDialog" />
      </q-card-section>

      <q-separator />

      <!-- Loading State -->
      <q-card-section v-if="loading" class="flex flex-center" style="flex: 1;">
        <q-spinner color="primary" size="50px" />
      </q-card-section>

      <!-- Form Content -->
      <q-card-section v-else class="q-pt-md" style="flex: 1; overflow-y: auto;">
        <q-form ref="cardForm">
          <!-- Title -->
          <q-input
            v-model="form.title"
            label="Title"
            filled
            :rules="[val => !!val || 'Title is required']"
            class="q-mb-md"
          />

          <!-- Description -->
          <q-input
            v-model="form.description"
            label="Description"
            type="textarea"
            filled
            rows="3"
            autogrow
            class="q-mb-md"
          />

          <div class="row q-col-gutter-md q-mb-md">
            <!-- Status -->
            <div class="col-12 col-sm-6">
              <q-select
                v-model="form.status"
                :options="statusOptions"
                label="Status"
                filled
                emit-value
                map-options
              />
            </div>

            <!-- Priority -->
            <div class="col-12 col-sm-6">
              <q-select
                v-model="form.priority"
                :options="priorityOptions"
                label="Priority"
                filled
                emit-value
                map-options
              />
            </div>
          </div>

          <div class="row q-col-gutter-md q-mb-md">
            <!-- Assigned To -->
            <div class="col-12 col-sm-6">
              <q-select
                v-model="form.assigned_to"
                :options="userOptions"
                label="Assigned To"
                filled
                clearable
                emit-value
                map-options
                option-label="label"
                option-value="value"
              />
            </div>

            <!-- Due Date -->
            <div class="col-12 col-sm-6">
              <q-input
                v-model="form.due_date"
                label="Due Date"
                filled
                clearable
              >
                <template v-slot:prepend>
                  <q-icon name="event" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date v-model="form.due_date" mask="YYYY-MM-DD">
                        <div class="row items-center justify-end">
                          <q-btn v-close-popup label="Close" color="primary" flat />
                        </div>
                      </q-date>
                    </q-popup-proxy>
                  </q-icon>
                </template>
              </q-input>
            </div>
          </div>

          <!-- Linked Entity Section -->
          <div v-if="showLinkedEntity" class="q-mb-md">
            <!-- Display linked entity (Edit Mode or pre-filled in Create Mode) -->
            <div v-if="hasLinkedEntity">
              <div class="text-subtitle2 q-mb-sm text-grey-7">Linked Entity</div>
              <q-item bordered class="bg-grey-2">
                <q-item-section avatar>
                  <q-icon :name="getLinkedEntityIcon()" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ getLinkedEntityLabel() }}</q-item-label>
                  <q-item-label caption>{{ getLinkedEntityId() }}</q-item-label>
                </q-item-section>
              </q-item>
            </div>

            <!-- Search for entities (Create Mode without pre-filled entity) -->
            <div v-else-if="!isEditMode" class="row q-col-gutter-md">
              <div class="col-12 col-sm-6">
                <q-select
                  v-model="selectedBattery"
                  :options="batteryOptions"
                  label="Link Battery (optional)"
                  filled
                  clearable
                  use-input
                  input-debounce="300"
                  @filter="filterBatteries"
                  @update:model-value="onBatterySelected"
                  option-label="label"
                  option-value="value"
                  emit-value
                  map-options
                >
                  <template v-slot:prepend>
                    <q-icon name="battery_charging_full" />
                  </template>
                  <template v-slot:no-option>
                    <q-item>
                      <q-item-section class="text-grey">
                        Type to search batteries...
                      </q-item-section>
                    </q-item>
                  </template>
                </q-select>
              </div>

              <div class="col-12 col-sm-6">
                <q-select
                  v-model="selectedPUE"
                  :options="pueOptions"
                  label="Link PUE (optional)"
                  filled
                  clearable
                  use-input
                  input-debounce="300"
                  @filter="filterPUE"
                  @update:model-value="onPUESelected"
                  option-label="label"
                  option-value="value"
                  emit-value
                  map-options
                >
                  <template v-slot:prepend>
                    <q-icon name="power" />
                  </template>
                  <template v-slot:no-option>
                    <q-item>
                      <q-item-section class="text-grey">
                        Type to search PUE...
                      </q-item-section>
                    </q-item>
                  </template>
                </q-select>
              </div>
            </div>
          </div>

          <!-- Activity Timeline (Edit Mode) -->
          <div v-if="isEditMode && card" class="q-mt-lg">
            <div class="text-subtitle2 q-mb-md">Activity History</div>
            <q-timeline color="primary" layout="dense">
              <q-timeline-entry
                v-for="activity in activities"
                :key="activity.activity_id"
                :title="activity.description"
                :subtitle="formatActivityDate(activity.created_at)"
                :icon="getActivityIcon(activity.activity_type)"
              >
                <div v-if="activity.creator_name" class="text-caption text-grey-7">
                  by {{ activity.creator_name }} <span v-if="activity.created_by" class="text-grey-6">(ID: {{ activity.created_by }})</span>
                </div>
              </q-timeline-entry>
            </q-timeline>

            <!-- Add Comment -->
            <div class="q-mt-md">
              <q-input
                v-model="newComment"
                label="Add Comment"
                type="textarea"
                filled
                rows="2"
                class="q-mb-sm"
              />
              <q-btn
                label="Add Comment"
                color="primary"
                @click="addComment"
                :disable="!newComment"
              />
            </div>
          </div>
        </q-form>
      </q-card-section>

      <q-separator />

      <!-- Actions -->
      <q-card-actions align="right" class="q-pa-md">
        <q-btn
          v-if="isEditMode"
          label="Delete"
          color="negative"
          flat
          @click="confirmDelete"
        />
        <q-space />
        <q-btn label="Cancel" flat @click="closeDialog" />
        <q-btn
          label="Save"
          color="primary"
          @click="save"
          :loading="saving"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import { jobCardsAPI, batteriesAPI, pueAPI, hubsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { date } from 'quasar'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  cardId: {
    type: Number,
    default: null
  },
  linkedEntityType: {
    type: String,
    default: null
  },
  linkedEntityId: {
    type: [String, Number],
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'saved', 'deleted'])

const $q = useQuasar()
const authStore = useAuthStore()
const showDialog = ref(props.modelValue)
const cardForm = ref(null)
const loading = ref(false)
const saving = ref(false)
const card = ref(null)
const activities = ref([])
const newComment = ref('')

// Form data
const form = ref({
  title: '',
  description: '',
  status: 'todo',
  priority: 'medium',
  assigned_to: null,
  due_date: null,
  linked_entity_type: props.linkedEntityType,
  linked_battery_id: null,
  linked_pue_id: null,
  linked_user_id: null,
  linked_rental_id: null
})

// Options
const statusOptions = [
  { label: 'To Do', value: 'todo' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Blocked', value: 'blocked' },
  { label: 'Done', value: 'done' }
]

const priorityOptions = [
  { label: 'Low', value: 'low' },
  { label: 'Medium', value: 'medium' },
  { label: 'High', value: 'high' },
  { label: 'Urgent', value: 'urgent' }
]

const userOptions = ref([])
const batteryOptions = ref([])
const pueOptions = ref([])
const selectedBattery = ref(null)
const selectedPUE = ref(null)
const linkedEntityName = ref(null)

// Computed
const isEditMode = computed(() => !!props.cardId)

const hasLinkedEntity = computed(() => {
  return (
    (isEditMode.value && card.value?.linked_entity_name) ||
    (!isEditMode.value && props.linkedEntityId)
  )
})

const showLinkedEntity = computed(() => {
  // Show linked entity section in edit mode if entity exists, or in create mode always
  return isEditMode.value ? !!card.value?.linked_entity_name : true
})

// Watch dialog visibility
watch(() => props.modelValue, (val) => {
  showDialog.value = val
  if (val) {
    loadData()
  }
})

watch(showDialog, (val) => {
  emit('update:modelValue', val)
})

// Load data
const loadData = async () => {
  // Load admin users for assignment
  try {
    const usersResponse = await jobCardsAPI.getAdminUsers()
    userOptions.value = usersResponse.data.users.map(user => ({
      label: user.Name || user.username,
      value: user.user_id
    }))
  } catch (error) {
    console.error('Failed to load admin users:', error)
  }

  // If edit mode, load card details
  if (isEditMode.value) {
    loading.value = true
    try {
      const response = await jobCardsAPI.get(props.cardId)
      card.value = response.data
      activities.value = response.data.activities || []

      // Populate form
      form.value = {
        title: card.value.title,
        description: card.value.description || '',
        status: card.value.status,
        priority: card.value.priority,
        assigned_to: card.value.assigned_to,
        due_date: card.value.due_date ? card.value.due_date.split('T')[0] : null,
        linked_entity_type: card.value.linked_entity_type,
        linked_battery_id: card.value.linked_battery_id,
        linked_pue_id: card.value.linked_pue_id,
        linked_user_id: card.value.linked_user_id,
        linked_rental_id: card.value.linked_rental_id
      }
    } catch (error) {
      console.error('Failed to load card:', error)
      $q.notify({
        type: 'negative',
        message: 'Failed to load job card',
        position: 'top'
      })
    } finally {
      loading.value = false
    }
  } else {
    // Create mode - set linked entity if provided
    if (props.linkedEntityType && props.linkedEntityId) {
      form.value.linked_entity_type = props.linkedEntityType
      if (props.linkedEntityType === 'battery') {
        form.value.linked_battery_id = props.linkedEntityId
        // Load battery details for display
        try {
          const response = await batteriesAPI.get(props.linkedEntityId)
          linkedEntityName.value = response.data.short_id || response.data.battery_id
        } catch (error) {
          console.error('Failed to load battery details:', error)
        }
      } else if (props.linkedEntityType === 'pue') {
        form.value.linked_pue_id = props.linkedEntityId
        // Load PUE details for display
        try {
          const response = await pueAPI.get(props.linkedEntityId)
          linkedEntityName.value = response.data.name || `PUE #${response.data.pue_id}`
        } catch (error) {
          console.error('Failed to load PUE details:', error)
        }
      } else if (props.linkedEntityType === 'user') {
        form.value.linked_user_id = props.linkedEntityId
      } else if (props.linkedEntityType === 'rental') {
        form.value.linked_rental_id = props.linkedEntityId
      }
    }
  }
}

// Save card
const save = async () => {
  const isValid = await cardForm.value.validate()
  if (!isValid) {
    $q.notify({
      type: 'warning',
      message: 'Please fill in all required fields',
      position: 'top'
    })
    return
  }

  saving.value = true
  try {
    const payload = {
      title: form.value.title,
      description: form.value.description,
      status: form.value.status,
      priority: form.value.priority,
      assigned_to: form.value.assigned_to,
      due_date: form.value.due_date,
      linked_entity_type: form.value.linked_entity_type,
      linked_battery_id: form.value.linked_battery_id,
      linked_pue_id: form.value.linked_pue_id,
      linked_user_id: form.value.linked_user_id,
      linked_rental_id: form.value.linked_rental_id
    }

    if (isEditMode.value) {
      await jobCardsAPI.update(props.cardId, payload)
      $q.notify({
        type: 'positive',
        message: 'Job card updated successfully',
        position: 'top'
      })
    } else {
      await jobCardsAPI.create(payload)
      $q.notify({
        type: 'positive',
        message: 'Job card created successfully',
        position: 'top'
      })
    }

    emit('saved')
    closeDialog()
  } catch (error) {
    console.error('Failed to save card:', error)
    $q.notify({
      type: 'negative',
      message: `Failed to ${isEditMode.value ? 'update' : 'create'} job card`,
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

// Add comment
const addComment = async () => {
  if (!newComment.value) return

  try {
    await jobCardsAPI.addActivity(props.cardId, {
      activity_type: 'comment',
      description: newComment.value
    })

    newComment.value = ''
    loadData()  // Reload to get updated activities

    $q.notify({
      type: 'positive',
      message: 'Comment added',
      position: 'top'
    })
  } catch (error) {
    console.error('Failed to add comment:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to add comment',
      position: 'top'
    })
  }
}

// Delete card
const confirmDelete = () => {
  $q.dialog({
    title: 'Confirm Delete',
    message: 'Are you sure you want to delete this job card?',
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await jobCardsAPI.delete(props.cardId)
      $q.notify({
        type: 'positive',
        message: 'Job card deleted successfully',
        position: 'top'
      })
      emit('deleted')
      closeDialog()
    } catch (error) {
      console.error('Failed to delete card:', error)
      $q.notify({
        type: 'negative',
        message: 'Failed to delete job card',
        position: 'top'
      })
    }
  })
}

// Close dialog
const closeDialog = () => {
  showDialog.value = false
}

// Reset form on hide
const onHide = () => {
  form.value = {
    title: '',
    description: '',
    status: 'todo',
    priority: 'medium',
    assigned_to: null,
    due_date: null,
    linked_entity_type: props.linkedEntityType,
    linked_battery_id: null,
    linked_pue_id: null,
    linked_user_id: null,
    linked_rental_id: null
  }
  card.value = null
  activities.value = []
  newComment.value = ''
  selectedBattery.value = null
  selectedPUE.value = null
  linkedEntityName.value = null
  batteryOptions.value = []
  pueOptions.value = []
}

// Battery and PUE search
const filterBatteries = async (val, update) => {
  const hubId = authStore.user?.hub_id
  if (!hubId) {
    update(() => {
      batteryOptions.value = []
    })
    return
  }

  try {
    const response = await hubsAPI.getBatteries(hubId)
    update(() => {
      let batteries = response.data || []
      // Filter by search term if provided
      if (val) {
        batteries = batteries.filter(battery =>
          (battery.short_id && battery.short_id.toLowerCase().includes(val.toLowerCase())) ||
          (battery.battery_id && battery.battery_id.toLowerCase().includes(val.toLowerCase()))
        )
      }
      batteryOptions.value = batteries.map(battery => ({
        label: battery.short_id || battery.battery_id,
        value: battery.battery_id
      }))
    })
  } catch (error) {
    console.error('Failed to search batteries:', error)
    update(() => {
      batteryOptions.value = []
    })
  }
}

const filterPUE = async (val, update) => {
  const hubId = authStore.user?.hub_id
  if (!hubId) {
    update(() => {
      pueOptions.value = []
    })
    return
  }

  try {
    const response = await hubsAPI.getPUE(hubId)
    update(() => {
      let pueList = response.data || []
      // Filter by search term if provided
      if (val) {
        pueList = pueList.filter(pue =>
          (pue.name && pue.name.toLowerCase().includes(val.toLowerCase())) ||
          (pue.pue_id && pue.pue_id.toLowerCase().includes(val.toLowerCase()))
        )
      }
      pueOptions.value = pueList.map(pue => ({
        label: pue.name || `PUE #${pue.pue_id}`,
        value: pue.pue_id
      }))
    })
  } catch (error) {
    console.error('Failed to search PUE:', error)
    update(() => {
      pueOptions.value = []
    })
  }
}

const onBatterySelected = (batteryId) => {
  if (batteryId) {
    form.value.linked_entity_type = 'battery'
    form.value.linked_battery_id = batteryId
    // Clear PUE if battery is selected
    selectedPUE.value = null
    form.value.linked_pue_id = null
  } else {
    form.value.linked_entity_type = null
    form.value.linked_battery_id = null
  }
}

const onPUESelected = (pueId) => {
  if (pueId) {
    form.value.linked_entity_type = 'pue'
    form.value.linked_pue_id = pueId
    // Clear battery if PUE is selected
    selectedBattery.value = null
    form.value.linked_battery_id = null
  } else {
    form.value.linked_entity_type = null
    form.value.linked_pue_id = null
  }
}

// Linked entity helpers
const getLinkedEntityIcon = () => {
  if (isEditMode.value && card.value) {
    const icons = {
      battery: 'battery_charging_full',
      pue: 'power',
      user: 'person',
      rental: 'receipt'
    }
    return icons[card.value.linked_entity_type] || 'link'
  } else if (props.linkedEntityType) {
    const icons = {
      battery: 'battery_charging_full',
      pue: 'power',
      user: 'person',
      rental: 'receipt'
    }
    return icons[props.linkedEntityType] || 'link'
  }
  return 'link'
}

const getLinkedEntityLabel = () => {
  if (isEditMode.value && card.value) {
    return card.value.linked_entity_name || card.value.linked_entity_type
  } else if (linkedEntityName.value) {
    return linkedEntityName.value
  }
  return props.linkedEntityType
}

const getLinkedEntityId = () => {
  if (isEditMode.value && card.value) {
    return card.value.linked_battery_id || card.value.linked_pue_id || card.value.linked_user_id || card.value.linked_rental_id || ''
  } else if (props.linkedEntityId) {
    return props.linkedEntityId
  }
  return ''
}

// Helpers
const getActivityIcon = (type) => {
  const icons = {
    created: 'add_circle',
    status_changed: 'sync_alt',
    comment: 'comment',
    assigned: 'person_add',
    updated: 'edit',
    due_date_changed: 'event'
  }
  return icons[type] || 'info'
}

const formatActivityDate = (dateString) => {
  if (!dateString) return ''
  return date.formatDate(new Date(dateString), 'MMM D, YYYY h:mm A')
}
</script>

<style scoped>
</style>
