<!-- src/components/Invoices.vue -->
<template>
  <div>
    <h1>Liste des factures</h1>
    <!-- ... Autres fonctionnalités ... -->

    <!-- Intégrer le composant Invoice -->
    <Invoice />
  </div>
</template>

<script>
import Invoice from './Invoice.vue';

export default {
  components: {
    Invoice
  },
  // ... Autres configurations ...
};
</script>
