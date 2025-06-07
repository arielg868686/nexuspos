// Funciones de utilidad
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(amount);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('es-MX', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(new Date(date));
}

// Funciones para el POS
function addToCart(productId) {
    fetch(`/api/cart/add/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartDisplay();
        } else {
            showAlert('Error al agregar producto', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al agregar producto', 'danger');
    });
}

function updateCartDisplay() {
    fetch('/api/cart')
    .then(response => response.json())
    .then(data => {
        const cartItems = document.getElementById('cart-items');
        const cartTotal = document.getElementById('cart-total');
        
        if (cartItems && cartTotal) {
            cartItems.innerHTML = data.items.map(item => `
                <div class="cart-item">
                    <span>${item.name}</span>
                    <span>${item.quantity}</span>
                    <span>${formatCurrency(item.price)}</span>
                </div>
            `).join('');
            
            cartTotal.textContent = formatCurrency(data.total);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al actualizar el carrito', 'danger');
    });
}

// Funciones para el inventario
function updateStock(productId, newStock) {
    fetch(`/api/inventory/update/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ stock: newStock })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Stock actualizado correctamente', 'success');
            location.reload();
        } else {
            showAlert('Error al actualizar stock', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al actualizar stock', 'danger');
    });
}

// Funciones de utilidad general
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers de Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}); 