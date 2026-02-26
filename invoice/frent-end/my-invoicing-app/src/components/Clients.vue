
// Exemple pour le composant Clients.vue
<script>
import axios from 'axios'

export default {
  data() {
    return {
      clients: [],
      // Autres données
    }
  },
  mounted() {
    this.fetchClients()
  },
  methods: {
    async fetchClients() {
      try {
        const response = await axios.get('http://127.0.0.1:8000/main_app/api/v1/clients/')
        this.clients = response.data
      } catch (error) {
        console.error('Error fetching clients:', error)
      }
    },
    // Ajoutez des méthodes pour créer, mettre à jour et supprimer des clients
  }
}
</script>
