// Digital Society Management - Main JavaScript

// Theme Management
class ThemeManager {
    constructor() {
        this.init();
    }
    
    init() {
        // Get saved theme or default to light
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
        
        // Setup theme toggle buttons
        const themeToggle = document.getElementById('theme-toggle');
        const mobileThemeToggle = document.getElementById('mobile-theme-toggle');
        
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
        
        if (mobileThemeToggle) {
            mobileThemeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }
    
    setTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        localStorage.setItem('theme', theme);
    }
    
    toggleTheme() {
        const isDark = document.documentElement.classList.contains('dark');
        this.setTheme(isDark ? 'light' : 'dark');
    }
}

// Mobile Navigation
class MobileNav {
    constructor() {
        this.sidebar = document.getElementById('mobile-sidebar');
        this.overlay = document.getElementById('sidebar-overlay');
        this.menuToggle = document.getElementById('menu-toggle');
        this.closeSidebar = document.getElementById('close-sidebar');
        
        this.init();
    }
    
    init() {
        if (this.menuToggle) {
            this.menuToggle.addEventListener('click', () => this.openSidebar());
        }
        
        if (this.closeSidebar) {
            this.closeSidebar.addEventListener('click', () => this.closeSidebar());
        }
        
        if (this.overlay) {
            this.overlay.addEventListener('click', () => this.closeSidebar());
        }
        
        // Close sidebar on navigation
        const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');
        mobileNavLinks.forEach(link => {
            link.addEventListener('click', () => this.closeSidebar());
        });
    }
    
    openSidebar() {
        if (this.sidebar && this.overlay) {
            this.sidebar.classList.remove('-translate-x-full');
            this.overlay.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    }
    
    closeSidebar() {
        if (this.sidebar && this.overlay) {
            this.sidebar.classList.add('-translate-x-full');
            this.overlay.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
    }
}

// Toast Notifications
class ToastManager {
    constructor() {
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.createContainer();
        }
    }
    
    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.className = 'fixed bottom-4 right-4 z-50 space-y-2';
        document.body.appendChild(this.container);
    }
    
    show(message, type = 'info', duration = 5000) {
        const toast = this.createToast(message, type);
        this.container.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.add('toast-enter-active');
        }, 10);
        
        // Auto remove
        setTimeout(() => {
            this.remove(toast);
        }, duration);
        
        return toast;
    }
    
    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast-enter max-w-sm bg-white dark:bg-slate-800 shadow-lg rounded-lg p-4 border border-slate-200 dark:border-slate-700`;
        
        const iconClasses = {
            success: 'fas fa-check-circle text-green-500',
            error: 'fas fa-exclamation-circle text-red-500',
            warning: 'fas fa-exclamation-triangle text-yellow-500',
            info: 'fas fa-info-circle text-blue-500'
        };
        
        toast.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <i class="${iconClasses[type] || iconClasses.info} mr-3"></i>
                    <span class="text-sm font-medium text-slate-900 dark:text-slate-100">${message}</span>
                </div>
                <button onclick="toastManager.remove(this.closest('.toast-enter'))" 
                        class="ml-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                    <i class="fas fa-times text-xs"></i>
                </button>
            </div>
        `;
        
        return toast;
    }
    
    remove(toast) {
        toast.classList.remove('toast-enter-active');
        toast.classList.add('toast-exit-active');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

// Loading Overlay
class LoadingManager {
    constructor() {
        this.overlay = document.getElementById('loading-overlay');
        if (!this.overlay) {
            this.createOverlay();
        }
    }
    
    createOverlay() {
        this.overlay = document.createElement('div');
        this.overlay.id = 'loading-overlay';
        this.overlay.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center hidden';
        this.overlay.innerHTML = `
            <div class="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-xl">
                <div class="flex items-center">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mr-3"></div>
                    <span class="text-lg font-medium text-slate-900 dark:text-slate-100">Loading...</span>
                </div>
            </div>
        `;
        document.body.appendChild(this.overlay);
    }
    
    show() {
        this.overlay.classList.remove('hidden');
    }
    
    hide() {
        this.overlay.classList.add('hidden');
    }
}

// Form Utilities
class FormUtils {
    static async submitForm(form, url, options = {}) {
        const formData = new FormData(form);
        const data = {};
        
        formData.forEach((value, key) => {
            data[key] = value;
        });
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
                ...options
            });
            
            return await response.json();
        } catch (error) {
            console.error('Form submission error:', error);
            throw error;
        }
    }
    
    static validateRequired(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('form-error');
                isValid = false;
            } else {
                field.classList.remove('form-error');
            }
        });
        
        return isValid;
    }
    
    static validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    static validatePhone(phone) {
        const phoneRegex = /^[0-9+\-\s()]{7,15}$/;
        return phoneRegex.test(phone);
    }
}

// Navigation Active State
class NavigationManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setActiveNavItem();
    }
    
    setActiveNavItem() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link, .mobile-nav-link');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPath.startsWith(href) && href !== '/') {
                link.classList.add('active');
            } else if (href === '/' && currentPath === '/') {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
}

// Auto-hide flash messages
class FlashMessageManager {
    constructor() {
        this.init();
    }
    
    init() {
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(message => {
            setTimeout(() => {
                this.fadeOut(message);
            }, 5000);
        });
    }
    
    fadeOut(element) {
        element.style.transition = 'opacity 0.5s ease-out';
        element.style.opacity = '0';
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }, 500);
    }
}

// Chart Utilities (if using charts)
class ChartUtils {
    static formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
    }
    
    static formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(new Date(date));
    }
}

// Global utility functions
window.showToast = function(message, type = 'info', duration = 5000) {
    return window.toastManager.show(message, type, duration);
};

window.showLoading = function() {
    window.loadingManager.show();
};

window.hideLoading = function() {
    window.loadingManager.hide();
};

window.formatCurrency = function(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
};

window.formatDate = function(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(new Date(date));
};

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize managers
    window.themeManager = new ThemeManager();
    window.mobileNav = new MobileNav();
    window.toastManager = new ToastManager();
    window.loadingManager = new LoadingManager();
    window.navigationManager = new NavigationManager();
    window.flashMessageManager = new FlashMessageManager();
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add loading states to form submissions
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.classList.add('btn-loading');
            }
        });
    });
    
    console.log('Digital Society Management System loaded successfully');
});