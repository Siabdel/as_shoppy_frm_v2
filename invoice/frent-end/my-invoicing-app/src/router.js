
import Vue from 'vue'
import VueRouter from 'vue-router'
import Clients from '../components/Clients.vue'
import Invoices from '../components/Invoices.vue'
import InvoiceItems from '../components/InvoiceItems.vue'

Vue.use(VueRouter)

const routes = [
  { path: '/clients', component: Clients },
  { path: '/invoices', component: Invoices },
  { path: '/invoice-items', component: InvoiceItems }
]

const router = new VueRouter({
  routes
})

export default router
