// ===== NOTIFICACIONES EN TIEMPO REAL =====
class NotificationManager {
    constructor() {
        this.checkInterval = 30000; // 30 segundos
        this.notificationBell = document.querySelector('.notification-bell');
        this.notificationDropdown = document.querySelector('.dropdown-menu');
        this.init();
    }

    init() {
        if (this.notificationBell) {
            this.startChecking();
            this.setupEventListeners();
        }
    }

    startChecking() {
        setInterval(() => this.checkNotifications(), this.checkInterval);
    }

    async checkNotifications() {
        try {
            const response = await fetch(notificationApiUrl);
            const data = await response.json();
            
            if (data.new_notifications) {
                this.updateNotificationBell(true);
                this.showNotificationModal(data.notifications);
                this.updateDropdown(data.notifications);
            }
        } catch (error) {
            console.error('Error checking notifications:', error);
        }
    }

    updateNotificationBell(hasNew) {
        if (hasNew) {
            this.notificationBell.classList.add('has-new');
            const badge = this.notificationBell.querySelector('.badge');
            if (badge) {
                badge.style.display = 'inline';
            }
        }
    }

    showNotificationModal(notifications) {
        const modal = new bootstrap.Modal(document.getElementById('notificationModal'));
        const modalContent = document.getElementById('modalNotificationContent');
        
        if (notifications && notifications.length > 0) {
            const lastNotification = notifications[0];
            modalContent.textContent = lastNotification.descripcion;
        }
        
        modal.show();
    }

    updateDropdown(notifications) {
        if (!this.notificationDropdown) return;
        
        // Limpiar dropdown
        this.notificationDropdown.innerHTML = '';
        
        if (notifications && notifications.length > 0) {
            notifications.forEach(notif => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <a class="dropdown-item" href="/tikects/detalles/${notif.tikect_id}/">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-info-circle text-primary me-2"></i>
                            <div>
                                <small class="text-muted">Ahora</small>
                                <p class="mb-0">${notif.descripcion}</p>
                            </div>
                        </div>
                    </a>
                `;
                this.notificationDropdown.appendChild(li);
            });
        } else {
            this.notificationDropdown.innerHTML = `
                <li class="dropdown-item text-center text-muted">
                    <i class="fas fa-check-circle mb-2" style="font-size: 2rem;"></i>
                    <p class="mb-0">No hay notificaciones</p>
                </li>
            `;
        }
    }

    setupEventListeners() {
        // Marcar notificaciones como leídas al hacer clic
        document.addEventListener('click', (e) => {
            if (e.target.closest('.dropdown-item')) {
                this.markAsRead(e.target.closest('.dropdown-item'));
            }
        });
    }

    markAsRead(element) {
        // Aquí podrías implementar la lógica para marcar como leída
        console.log('Marcando notificación como leída');
    }
}

// ===== ANIMACIONES Y EFECTOS =====
class UIManager {
    constructor() {
        this.init();
    }

    init() {
        this.addHoverEffects();
        this.addScrollEffects();
        this.initCharts();
    }

    addHoverEffects() {
        // Efecto hover para tarjetas
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
            });
        });

        // Efecto hover para botones
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                btn.style.transform = 'translateY(-2px)';
            });
            
            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'translateY(0)';
            });
        });
    }

    addScrollEffects() {
        // Efecto de aparición al hacer scroll
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate__fadeInUp');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.animated-section').forEach(el => {
            observer.observe(el);
        });
    }

    initCharts() {
        // Inicializar gráficos con animaciones
        if (typeof Chart !== 'undefined') {
            Chart.defaults.animation.duration = 2000;
            Chart.defaults.animation.easing = 'easeInOutQuart';
        }
    }
}

// ===== VALIDACIONES DE FORMULARIOS =====
class FormValidator {
    constructor() {
        this.init();
    }

    init() {
        this.setupPasswordValidation();
        this.setupEmailValidation();
    }

    setupPasswordValidation() {
        const passwordFields = document.querySelectorAll('input[type="password"]');
        
        passwordFields.forEach(field => {
            field.addEventListener('input', (e) => {
                const password = e.target.value;
                const strength = this.checkPasswordStrength(password);
                this.updatePasswordStrengthIndicator(field, strength);
            });
        });
    }

    checkPasswordStrength(password) {
        let strength = 0;
        
        if (password.length >= 8) strength++;
        if (password.match(/[a-z]/)) strength++;
        if (password.match(/[A-Z]/)) strength++;
        if (password.match(/[0-9]/)) strength++;
        if (password.match(/[^a-zA-Z0-9]/)) strength++;
        
        return strength;
    }

    updatePasswordStrengthIndicator(field, strength) {
        let indicator = field.parentElement.querySelector('.password-strength');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'password-strength mt-2';
            field.parentElement.appendChild(indicator);
        }
        
        const strengthText = ['Muy débil', 'Débil', 'Regular', 'Buena', 'Excelente'];
        const strengthColor = ['#f72585', '#f8961e', '#f9c74f', '#43aa8b', '#4cc9f0'];
        
        indicator.innerHTML = `
            <div class="progress" style="height: 5px;">
                <div class="progress-bar" style="width: ${strength * 20}%; background-color: ${strengthColor[strength]}"></div>
            </div>
            <small class="text-muted">${strengthText[strength]}</small>
        `;
    }

    setupEmailValidation() {
        const emailFields = document.querySelectorAll('input[type="email"]');
        
        emailFields.forEach(field => {
            field.addEventListener('blur', (e) => {
                const email = e.target.value;
                if (email && !this.validateEmail(email)) {
                    this.showError(field, 'Email inválido');
                }
            });
        });
    }

    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    showError(field, message) {
        field.classList.add('is-invalid');
        
        let feedback = field.parentElement.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentElement.appendChild(feedback);
        }
        
        feedback.textContent = message;
    }
}

// ===== MANEJADOR DE LOADING =====
class LoadingManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupFormSubmissions();
    }

    setupFormSubmissions() {
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    this.showLoading(submitBtn);
                }
            });
        });
    }

    showLoading(button) {
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Procesando...
        `;
        
        // Restaurar después de un tiempo (útil para pruebas)
        setTimeout(() => {
            button.disabled = false;
            button.innerHTML = originalText;
        }, 3000);
    }
}

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', () => {
    new NotificationManager();
    new UIManager();
    new FormValidator();
    new LoadingManager();
    
    // Tooltips personalizados
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// ===== FUNCIONES UTILITARIAS =====
function formatDate(date) {
    return new Date(date).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function truncateText(text, length = 100) {
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
}

function showToast(message, type = 'success') {
    // Crear elemento toast
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Agregar al contenedor
    const container = document.getElementById('toast-container');
    if (!container) {
        const newContainer = document.createElement('div');
        newContainer.id = 'toast-container';
        newContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(newContainer);
        newContainer.appendChild(toast);
    } else {
        container.appendChild(toast);
    }
    
    // Mostrar toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}