// Front-end interactions for CloudShop E-Commerce
document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // Dynamic price calculation on orders page if present
    const productSelect = document.getElementById('product_id');
    const quantityInput = document.getElementById('quantity');
    if (productSelect && quantityInput) {
        const updateStockMax = () => {
            const selectedOption = productSelect.options[productSelect.selectedIndex];
            if (selectedOption && selectedOption.dataset.stock) {
                const stock = parseInt(selectedOption.dataset.stock, 10);
                quantityInput.max = stock;
            }
        };
        productSelect.addEventListener('change', updateStockMax);
    }
});

