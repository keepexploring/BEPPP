import { boot } from 'quasar/wrappers'
import axios from 'axios'
import api, { setRouter } from 'src/services/api'

export default boot(({ app, router }) => {
  // for use inside Vue files (Options API) through this.$axios and this.$api
  app.config.globalProperties.$axios = axios
  app.config.globalProperties.$api = api

  // Set router in api service for 401 redirects
  setRouter(router)
})

export { axios, api }
