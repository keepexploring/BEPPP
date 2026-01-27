<template>
  <q-card
    flat
    bordered
    class="job-card q-mb-sm cursor-pointer"
    :class="{ 'overdue': isOverdue }"
    @click="$emit('click')"
  >
    <q-card-section class="q-py-sm">
      <!-- Title and Priority Badge -->
      <div class="row items-center q-mb-xs">
        <div class="col">
          <div class="text-body2 text-weight-medium">{{ card.title }}</div>
        </div>
        <div class="col-auto">
          <q-badge
            :color="priorityColor"
            :label="card.priority"
            class="text-capitalize"
          />
        </div>
      </div>

      <!-- Description (truncated) -->
      <div v-if="card.description" class="text-caption text-grey-8 q-mb-sm" style="max-height: 40px; overflow: hidden;">
        {{ card.description }}
      </div>

      <!-- Linked Entity -->
      <div v-if="card.linked_entity_name" class="row items-center q-mb-xs">
        <q-icon :name="getEntityIcon()" size="xs" class="q-mr-xs" />
        <span class="text-caption">{{ card.linked_entity_name }}</span>
      </div>

      <!-- Due Date -->
      <div v-if="card.due_date" class="row items-center q-mb-xs">
        <q-icon name="event" size="xs" class="q-mr-xs" :color="isOverdue ? 'negative' : 'grey-7'" />
        <span class="text-caption" :class="{ 'text-negative': isOverdue }">
          {{ formatDate(card.due_date) }}
        </span>
        <q-badge v-if="isOverdue" color="negative" label="Overdue" class="q-ml-sm" />
      </div>

      <!-- User Information -->
      <div class="row items-center q-gutter-xs q-mb-xs">
        <!-- Assigned User -->
        <q-chip
          v-if="card.assigned_user_name"
          dense
          size="sm"
          color="blue-2"
          text-color="blue-9"
          icon="person"
        >
          <span class="text-weight-medium">{{ card.assigned_user_name }}</span>
        </q-chip>

        <!-- Creator (only show if different from assigned user) -->
        <q-chip
          v-if="card.creator_name && card.creator_name !== card.assigned_user_name"
          dense
          size="sm"
          color="grey-3"
          text-color="grey-8"
          icon="create"
        >
          <span>Created by {{ card.creator_name }}</span>
        </q-chip>
      </div>

      <!-- Activity Count -->
      <div v-if="card.activity_count > 0" class="row items-center q-mt-xs">
        <q-icon name="comment" size="xs" class="q-mr-xs text-grey-7" />
        <span class="text-caption text-grey-7">{{ card.activity_count }} {{ card.activity_count === 1 ? 'activity' : 'activities' }}</span>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup>
import { computed } from 'vue'
import { date } from 'quasar'

const props = defineProps({
  card: {
    type: Object,
    required: true
  }
})

// Priority colors
const priorityColor = computed(() => {
  const colors = {
    low: 'grey-6',
    medium: 'blue',
    high: 'orange',
    urgent: 'negative'
  }
  return colors[props.card.priority] || 'grey-6'
})

// Check if card is overdue
const isOverdue = computed(() => {
  if (!props.card.due_date) return false
  if (props.card.status === 'done') return false

  const now = new Date()
  const dueDate = new Date(props.card.due_date)
  return dueDate < now
})

// Get entity icon based on type
const getEntityIcon = () => {
  const icons = {
    battery: 'battery_charging_full',
    pue: 'power',
    user: 'person',
    rental: 'receipt'
  }
  return icons[props.card.linked_entity_type] || 'link'
}

// Format date
const formatDate = (dateString) => {
  if (!dateString) return ''
  return date.formatDate(new Date(dateString), 'MMM D, YYYY')
}
</script>

<style scoped>
.job-card {
  transition: all 0.2s;
}

.job-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.job-card.overdue {
  border-left: 4px solid #c10015;
}

.cursor-pointer {
  cursor: pointer;
}
</style>
