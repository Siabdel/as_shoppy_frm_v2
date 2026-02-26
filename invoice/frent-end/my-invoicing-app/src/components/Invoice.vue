<!-- src/components/Invoice.vue -->
<template>
  <div class="container mt-4">
    <h2 class="mb-4">Ajouter une facture</h2>

    <div class="form-group">
      <label for="clientSelect">Client:</label>
      <select v-model="selectedClient" id="clientSelect" class="form-control">
        <option v-for="client in clients" :key="client.id" :value="client.id">{{ client.name }}</option>
      </select>
    </div>

    <div class="form-group">
      <label for="itemSearch">Rechercher des articles:</label>
      <input v-model="itemSearch" id="itemSearch" @input="searchItems" class="form-control" />
    </div>

    <ul class="list-group mb-4">
      <li class="list-group-item" v-for="item in filteredItems" :key="item.id">
        {{ item.name }} - <button @click="addItem(item)" class="btn btn-sm btn-primary">Ajouter</button>
      </li>
    </ul>

    <h3>Articles ajoutés à la facture:</h3>
    <ul class="list-group mb-4">
      <li class="list-group-item" v-for="item in selectedItems" :key="item.id">
        {{ item.name }} - <button @click="removeItem(item)" class="btn btn-sm btn-danger">Retirer</button>
      </li>
    </ul>

    <button @click="createInvoice" class="btn btn-success">Créer la facture</button>
  </div>
</template>

<script>
// ... Le reste du script ...
</script>

<style scoped>
/* Vous pouvez également personnaliser le style ici si nécessaire */
</style>
