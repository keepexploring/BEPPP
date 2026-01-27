<template>
  <q-dialog v-model="showDialog" @hide="onHide" persistent>
    <q-card style="min-width: 600px; max-width: 800px">
      <q-card-section>
        <div class="text-h6">Return Feedback Survey</div>
        <div class="text-caption text-grey-7">
          Thank you for using our service! Please take a moment to share your feedback.
        </div>
      </q-card-section>

      <q-separator />

      <!-- Loading State -->
      <q-card-section v-if="loading">
        <div class="text-center q-py-lg">
          <q-spinner color="primary" size="50px" />
          <div class="text-caption q-mt-md">Loading survey questions...</div>
        </div>
      </q-card-section>

      <!-- Survey Questions -->
      <q-card-section v-else class="q-pt-md" style="max-height: 60vh; overflow-y: auto;">
        <q-form ref="surveyForm" @submit="onSubmit">
          <div v-for="(question, index) in visibleQuestions" :key="question.question_id" class="q-mb-lg">
            <!-- Question Label -->
            <div class="q-mb-sm">
              <span class="text-body1">
                {{ index + 1 }}. {{ question.question_text }}
                <span v-if="question.is_required" class="text-negative">*</span>
              </span>
              <div v-if="question.help_text" class="text-caption text-grey-7 q-mt-xs">
                {{ question.help_text }}
              </div>
            </div>

            <!-- Open Text -->
            <q-input
              v-if="question.question_type === 'open_text' && responses[question.question_id]"
              v-model="responses[question.question_id].response_value"
              type="textarea"
              outlined
              :rules="question.is_required ? [val => !!val || 'This field is required'] : []"
              rows="3"
              placeholder="Enter your response..."
              autogrow
            />

            <!-- Multiple Choice -->
            <q-option-group
              v-else-if="question.question_type === 'multiple_choice'"
              v-model="responses[question.question_id].response_value"
              :options="question.options.map(opt => ({ label: opt.option_text, value: opt.option_value }))"
              type="radio"
              :rules="question.is_required ? [val => !!val || 'Please select an option'] : []"
              @update:model-value="(val) => handleAnswerChange(question, val)"
            />

            <!-- Conditional Text Input for Multiple Choice -->
            <q-input
              v-if="question.question_type === 'multiple_choice' && shouldShowTextInput(question)"
              v-model="responses[question.question_id].response_text"
              type="textarea"
              outlined
              class="q-mt-sm"
              rows="2"
              placeholder="Please describe..."
            />

            <!-- Multiple Select -->
            <q-option-group
              v-else-if="question.question_type === 'multiple_select'"
              v-model="responses[question.question_id].response_values"
              :options="question.options.map(opt => ({ label: opt.option_text, value: opt.option_value }))"
              type="checkbox"
              :rules="question.is_required ? [val => val && val.length > 0 || 'Please select at least one option'] : []"
              @update:model-value="(val) => handleMultiSelectChange(question, val)"
            />

            <!-- Conditional Text Input for Multiple Select -->
            <q-input
              v-if="question.question_type === 'multiple_select' && shouldShowTextInputForMultiSelect(question)"
              v-model="responses[question.question_id].response_text"
              type="textarea"
              outlined
              class="q-mt-sm"
              rows="2"
              placeholder="Please describe..."
            />

            <!-- Rating -->
            <div v-else-if="question.question_type === 'rating'" class="q-mt-sm">
              <div class="row items-center q-mb-sm">
                <div class="col-auto text-caption text-grey-7 q-pr-md" style="min-width: 100px; text-align: right">
                  {{ question.rating_min_label || 'Low' }}
                </div>
                <div class="col-auto q-gutter-xs">
                  <q-btn
                    v-for="n in (question.rating_max || 10) - (question.rating_min || 1) + 1"
                    :key="n"
                    :label="String((question.rating_min || 1) + n - 1)"
                    :color="responses[question.question_id].response_value === (question.rating_min || 1) + n - 1 ? 'primary' : 'grey-4'"
                    :text-color="responses[question.question_id].response_value === (question.rating_min || 1) + n - 1 ? 'white' : 'grey-8'"
                    size="md"
                    style="min-width: 45px"
                    @click="responses[question.question_id].response_value = (question.rating_min || 1) + n - 1; handleAnswerChange(question, (question.rating_min || 1) + n - 1)"
                  />
                </div>
                <div class="col-auto text-caption text-grey-7 q-pl-md" style="min-width: 100px">
                  {{ question.rating_max_label || 'High' }}
                </div>
              </div>
              <div v-if="question.is_required && !responses[question.question_id].response_value" class="text-caption text-negative">
                Please select a rating
              </div>
            </div>

            <!-- Yes/No -->
            <q-option-group
              v-else-if="question.question_type === 'yes_no'"
              v-model="responses[question.question_id].response_value"
              :options="question.options.map(opt => ({ label: opt.option_text, value: opt.option_value }))"
              type="radio"
              inline
              :rules="question.is_required ? [val => !!val || 'Please select an option'] : []"
              @update:model-value="(val) => handleAnswerChange(question, val)"
            />
          </div>
        </q-form>
      </q-card-section>

      <q-separator />

      <!-- Actions -->
      <q-card-actions align="right" class="q-pa-md">
        <q-btn
          flat
          label="Skip Survey"
          color="grey"
          @click="onSkip"
          :disable="submitting"
        />
        <q-btn
          label="Submit Feedback"
          color="primary"
          @click="onSubmit"
          :loading="submitting"
          :disable="loading"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { surveyAPI } from 'src/services/api'
import { useQuasar } from 'quasar'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  rentalType: {
    type: String,
    required: true,
    validator: (val) => ['battery', 'pue'].includes(val)
  },
  rentalId: {
    type: [Number, null],
    required: false,
    default: null
  },
  hubId: {
    type: Number,
    required: false
  }
})

const emit = defineEmits(['update:modelValue', 'submitted', 'skipped'])

const $q = useQuasar()
const showDialog = ref(props.modelValue)
const surveyForm = ref(null)
const loading = ref(false)
const submitting = ref(false)
const questions = ref([])
const responses = ref({})

// Watch for dialog open/close
watch(() => props.modelValue, (val) => {
  showDialog.value = val
  if (val) {
    loadQuestions()
  }
})

watch(showDialog, (val) => {
  emit('update:modelValue', val)
})

// Compute visible questions based on conditional logic
const visibleQuestions = computed(() => {
  return questions.value.filter(question => {
    // If no parent question, always show
    if (!question.parent_question_id) {
      return true
    }

    // Find parent question's response
    const parentResponse = responses.value[question.parent_question_id]
    if (!parentResponse) {
      return false
    }

    // Check if parent answer matches the condition
    const parentAnswer = parentResponse.response_value || parentResponse.response_values
    if (!parentAnswer) {
      return false
    }

    // Parse the show_if_parent_answer condition (it's a JSON array)
    try {
      const conditions = JSON.parse(question.show_if_parent_answer || '[]')

      // For single values (radio buttons, yes/no)
      if (typeof parentAnswer === 'string') {
        return conditions.includes(parentAnswer)
      }

      // For multiple values (checkboxes)
      if (Array.isArray(parentAnswer)) {
        return conditions.some(condition => parentAnswer.includes(condition))
      }
    } catch (e) {
      console.error('Error parsing conditional logic:', e)
      return false
    }

    return false
  })
})

const loadQuestions = async () => {
  // Don't load if rentalId is not set yet
  if (!props.rentalId) {
    console.log('Skipping survey load - no rental ID yet')
    return
  }

  loading.value = true
  try {
    const params = {
      rental_type: props.rentalType,
      hub_id: props.hubId
    }
    console.log('Loading survey questions with params:', params)
    const response = await surveyAPI.getActiveQuestions(params)
    questions.value = response.data.questions || []
    console.log('Loaded survey questions:', questions.value.length)

    // If no questions available, automatically close dialog
    if (questions.value.length === 0) {
      console.log('No survey questions available, auto-skipping')
      showDialog.value = false
      emit('skipped')
      return
    }

    // Initialize responses object
    responses.value = {}
    questions.value.forEach(question => {
      responses.value[question.question_id] = {
        question_id: question.question_id,
        response_value: question.question_type === 'multiple_select' ? null : '',
        response_values: question.question_type === 'multiple_select' ? [] : null,
        response_text: ''
      }
    })
  } catch (error) {
    console.error('Failed to load survey questions:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load survey questions',
      position: 'top'
    })
    // Close dialog on error
    showDialog.value = false
    emit('skipped')
  } finally {
    loading.value = false
  }
}

const handleAnswerChange = (question, value) => {
  // Trigger reactivity for conditional questions
  responses.value[question.question_id].response_value = value
}

const handleMultiSelectChange = (question, values) => {
  // Trigger reactivity for conditional questions
  responses.value[question.question_id].response_values = values
}

const shouldShowTextInput = (question) => {
  const response = responses.value[question.question_id]
  if (!response || !response.response_value) return false

  // Check if the selected option has is_open_text_trigger
  const selectedOption = question.options.find(opt => opt.option_value === response.response_value)
  return selectedOption?.is_open_text_trigger || false
}

const shouldShowTextInputForMultiSelect = (question) => {
  const response = responses.value[question.question_id]
  if (!response || !response.response_values || response.response_values.length === 0) return false

  // Check if any selected option has is_open_text_trigger
  return response.response_values.some(value => {
    const option = question.options.find(opt => opt.option_value === value)
    return option?.is_open_text_trigger || false
  })
}

const onSubmit = async () => {
  // Validate form
  const isValid = await surveyForm.value.validate()
  if (!isValid) {
    $q.notify({
      type: 'warning',
      message: 'Please answer all required questions',
      position: 'top'
    })
    return
  }

  submitting.value = true
  try {
    // Filter out only answered questions and format for API
    const answeredResponses = Object.values(responses.value).filter(response => {
      return response.response_value ||
             (response.response_values && response.response_values.length > 0) ||
             response.response_text
    })

    const payload = {
      [props.rentalType === 'battery' ? 'battery_rental_id' : 'pue_rental_id']: props.rentalId,
      responses: answeredResponses
    }

    await surveyAPI.submitResponses(payload)

    $q.notify({
      type: 'positive',
      message: 'Thank you for your feedback!',
      position: 'top'
    })

    emit('submitted')
    showDialog.value = false
  } catch (error) {
    console.error('Failed to submit survey responses:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to submit survey responses',
      position: 'top'
    })
  } finally {
    submitting.value = false
  }
}

const onSkip = () => {
  emit('skipped')
  showDialog.value = false
}

const onHide = () => {
  // Reset form when dialog closes
  responses.value = {}
  questions.value = []
}
</script>
