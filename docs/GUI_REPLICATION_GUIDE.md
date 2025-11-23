# Catalynx GUI Architecture - Replication Guide

**Version:** 1.0
**Date:** 2025-11-23
**Purpose:** Complete guide for replicating the Catalynx web interface design, sidebar navigation, and architecture in other projects

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Architecture Overview](#architecture-overview)
4. [Project Structure](#project-structure)
5. [Quick Start Setup](#quick-start-setup)
6. [Core Design Patterns](#core-design-patterns)
7. [Sidebar Tab Navigation](#sidebar-tab-navigation)
8. [Styling System](#styling-system)
9. [State Management](#state-management)
10. [API Integration](#api-integration)
11. [Component Library](#component-library)
12. [Responsive Design](#responsive-design)
13. [Dark Mode Implementation](#dark-mode-implementation)
14. [Accessibility Features](#accessibility-features)
15. [Performance Optimizations](#performance-optimizations)
16. [Common Customizations](#common-customizations)
17. [Best Practices](#best-practices)

---

## Overview

The Catalynx web interface is a **modern, reactive Single Page Application (SPA)** built with a minimalist but powerful technology stack. The design philosophy emphasizes:

- **Zero Build Step**: No webpack, no npm build process - just load and go
- **Reactive UI**: Alpine.js for declarative, Vue-like reactivity
- **Utility-First Styling**: Tailwind CSS for rapid, consistent design
- **Progressive Enhancement**: Works without JavaScript, enhanced with it
- **Mobile-First**: Responsive design from the ground up
- **Accessible**: WCAG 2.1 AA compliant
- **Dark Mode**: Full dark mode support throughout

### Key Features

- 3-stage sidebar navigation (PROFILES → SCREENING → INTELLIGENCE)
- Real-time notifications system
- WebSocket support for live updates
- Modular JavaScript architecture
- Chart visualization (Chart.js)
- RESTful API integration
- Component-based design patterns

---

## Technology Stack

### Frontend

| Technology | Version | Purpose | CDN/Local |
|------------|---------|---------|-----------|
| **Alpine.js** | 3.x | Reactive framework (Vue-like) | CDN |
| **Tailwind CSS** | 3.x | Utility-first CSS framework | CDN |
| **Chart.js** | Latest | Data visualization | Local |
| **Vanilla JavaScript** | ES6+ | Custom modules and logic | Local |

### Backend

| Technology | Purpose |
|------------|---------|
| **FastAPI** | Python async web framework |
| **Uvicorn** | ASGI server |
| **WebSockets** | Real-time communication |
| **SQLite** | Database |
| **Pydantic** | Data validation |

### Why This Stack?

1. **Alpine.js over React/Vue**: No build step, tiny footprint (15KB), perfect for server-rendered apps
2. **Tailwind over custom CSS**: Consistency, rapid development, no naming conflicts
3. **FastAPI**: Modern Python framework with automatic API documentation, async support
4. **No bundler**: Faster development, simpler deployment, easier debugging

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (Client)                          │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Alpine.js   │  │ Tailwind CSS │  │   Chart.js   │      │
│  │  (Reactive)  │  │  (Styling)   │  │   (Charts)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Modular JavaScript Components                │   │
│  │  • state-module.js      • profiles-module.js         │   │
│  │  • screening-module.js  • intelligence-module.js     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  API Routers                          │   │
│  │  /api/profiles  /api/screening  /api/intelligence    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Services   │  │  Database    │  │  WebSocket   │      │
│  │              │  │   (SQLite)   │  │   Manager    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow

1. User interacts with UI (Alpine.js component)
2. JavaScript module handles business logic
3. API call made to FastAPI backend
4. Backend processes request, queries database
5. Response returned as JSON
6. Alpine.js reactively updates DOM
7. Tailwind classes style the updated elements

---

## Project Structure

```
your-project/
├── src/
│   └── web/
│       ├── main.py                      # FastAPI application entry point
│       ├── routers/                     # API route handlers
│       │   ├── profiles.py
│       │   ├── screening.py
│       │   └── intelligence.py
│       ├── services/                    # Business logic layer
│       ├── models/                      # Pydantic models
│       ├── static/                      # Frontend assets
│       │   ├── index.html              # Main SPA entry point
│       │   ├── style.css               # Custom CSS (Tailwind extensions)
│       │   ├── js/
│       │   │   ├── config.js           # Configuration
│       │   │   ├── api/
│       │   │   │   └── client.js       # API client utilities
│       │   │   ├── core/
│       │   │   │   ├── error-handler.js
│       │   │   │   └── catalynx-utils.js
│       │   │   ├── modules/            # Feature modules
│       │   │   │   ├── charts.js
│       │   │   │   ├── discovery-engine.js
│       │   │   │   ├── websocket.js
│       │   │   │   └── pagination.js
│       │   │   └── stores/             # State management
│       │   │       ├── ui-store.js
│       │   │       └── opportunities-store.js
│       │   ├── modules/                # Alpine.js modules
│       │   │   ├── state-module.js     # Global state
│       │   │   ├── profiles-module.js  # Profile features
│       │   │   ├── screening-module.js # Screening features
│       │   │   └── intelligence-module.js
│       │   ├── templates/              # HTML template partials
│       │   │   ├── profile-modals.html
│       │   │   └── ntee-selection-modal.html
│       │   ├── data/                   # Static data files
│       │   │   ├── ntee-codes.js
│       │   │   └── government-criteria.js
│       │   └── CatalynxLogo.png
│       └── templates/                  # Jinja2 templates (if using server-side rendering)
└── docs/                               # Documentation
    └── GUI_REPLICATION_GUIDE.md       # This file
```

### Key File Responsibilities

| File | Purpose |
|------|---------|
| `index.html` | Main HTML, Alpine.js app initialization, overall layout |
| `style.css` | Custom CSS utilities, Tailwind extensions, animations |
| `state-module.js` | Centralized state management (Alpine.js store) |
| `*-module.js` | Feature-specific logic (profiles, screening, etc.) |
| `main.py` | FastAPI app configuration, middleware, route registration |
| `routers/*.py` | API endpoint definitions grouped by feature |

---

## Quick Start Setup

### Prerequisites

- Python 3.9+
- Basic understanding of HTML, CSS, JavaScript
- Text editor or IDE

### 1. Backend Setup

```bash
# Create project directory
mkdir my-project
cd my-project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn python-multipart

# Create basic FastAPI app
```

**File: `main.py`**

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI(title="My Application")

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/")
async def root():
    """Serve the main SPA"""
    return FileResponse(static_path / "index.html")

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Frontend Setup

**File: `static/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Application</title>

    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- Alpine.js -->
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>

    <!-- Custom CSS -->
    <link rel="stylesheet" href="/static/style.css">

    <style>
        [x-cloak] { display: none !important; }
    </style>
</head>
<body class="bg-gray-100" x-data="appState()" x-cloak>

    <!-- Your app content here -->
    <div class="min-h-screen flex">
        <!-- Sidebar -->
        <aside class="w-80 bg-gray-900 text-white">
            <div class="p-4">
                <h1 class="text-2xl font-bold">My App</h1>
            </div>
            <!-- Navigation will go here -->
        </aside>

        <!-- Main content -->
        <main class="flex-1 p-6">
            <h2 class="text-3xl font-semibold">Welcome</h2>
        </main>
    </div>

    <script>
        function appState() {
            return {
                activeTab: 'home',
                darkMode: false,

                init() {
                    console.log('App initialized');
                }
            }
        }
    </script>
</body>
</html>
```

**File: `static/style.css`**

```css
/* Catalynx-inspired custom styles */

:root {
    --brand-primary: #005b95;
    --brand-primary-hover: #004580;
}

/* Smooth transitions */
* {
    transition-property: color, background-color, border-color;
    transition-duration: 200ms;
    transition-timing-function: ease-in-out;
}

/* Custom scrollbar */
.custom-scrollbar::-webkit-scrollbar {
    width: 8px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
}

/* Card hover effect */
.card-hover:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

/* Loading spinner */
.spinner {
    border: 3px solid #f3f3f3;
    border-top: 3px solid #2563eb;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```

### 3. Run the Application

```bash
python main.py
```

Visit http://localhost:8000

---

## Core Design Patterns

### 1. Alpine.js Component Pattern

Alpine.js uses `x-data` to create reactive components. Think of it as Vue.js without the build step.

**Basic Pattern:**

```html
<div x-data="componentName()">
    <!-- Component content -->
    <button @click="handleClick()">Click Me</button>
    <p x-text="message"></p>
</div>

<script>
function componentName() {
    return {
        message: 'Hello',

        handleClick() {
            this.message = 'Clicked!';
        }
    }
}
</script>
```

### 2. Modular JavaScript Architecture

Instead of one giant JavaScript file, use modules:

**File: `modules/state-module.js`**

```javascript
function stateModule() {
    return {
        // State
        activeStage: 'welcome',
        selectedProfile: null,

        // Methods
        switchStage(stage) {
            this.activeStage = stage;
            console.log(`Switched to ${stage}`);
        },

        selectProfile(profile) {
            this.selectedProfile = profile;
        }
    }
}
```

**Include in HTML:**

```html
<script src="/static/modules/state-module.js"></script>
<div x-data="stateModule()">
    <!-- Use state here -->
</div>
```

### 3. API Client Pattern

Centralize API calls for reusability:

**File: `js/api/client.js`**

```javascript
class ApiClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
    }

    async get(endpoint) {
        const response = await fetch(`${this.baseURL}${endpoint}`);
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        return await response.json();
    }

    async post(endpoint, data) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        return await response.json();
    }
}

const api = new ApiClient();
```

**Usage:**

```javascript
// In your Alpine component
async loadProfiles() {
    this.loading = true;
    try {
        this.profiles = await api.get('/profiles');
    } catch (error) {
        console.error('Failed to load profiles:', error);
    } finally {
        this.loading = false;
    }
}
```

---

## Sidebar Tab Navigation

### Design Philosophy

The Catalynx sidebar uses a **3-stage workflow navigation**:

1. **PROFILES** - Profile management (purple theme)
2. **SCREENING** - Discovery & screening (teal theme)
3. **INTELLIGENCE** - Deep analysis (blue theme)

Each stage is a large, prominent button with:
- Color-coded themes
- Active state styling
- Descriptive subtitle
- Smooth transitions

### Implementation

**HTML Structure:**

```html
<aside class="hidden lg:block bg-gray-900 text-white w-80 flex-shrink-0">
    <!-- Logo Header -->
    <div class="p-4">
        <div class="flex items-center justify-between">
            <h1 class="text-xl font-bold">
                <img src="/static/logo.png" alt="Logo" class="h-10 inline mr-3">
                <span>MY APP</span>
            </h1>

            <!-- Dark Mode Toggle -->
            <button @click="toggleDarkMode()"
                    class="p-2 rounded-lg hover:bg-gray-700">
                <span x-show="!darkMode">🌙</span>
                <span x-show="darkMode">☀️</span>
            </button>
        </div>
    </div>

    <!-- Navigation Stages -->
    <nav class="mt-6">
        <!-- Stage 1: Profiles -->
        <div class="px-2 mb-4">
            <a href="#" @click.prevent="switchStage('profiles')"
               :class="{
                   'bg-purple-600 text-white shadow-lg': activeStage === 'profiles',
                   'text-gray-300 hover:bg-gray-700 hover:text-white border-purple-500/30': activeStage !== 'profiles'
               }"
               class="block px-6 py-8 text-2xl font-bold rounded-lg transition-all border">
                PROFILES
                <div class="text-xs font-normal opacity-80 mt-1">
                    Profile Management
                </div>
            </a>
        </div>

        <!-- Stage 2: Screening -->
        <div class="px-2 mb-4">
            <a href="#" @click.prevent="switchStage('screening')"
               :class="{
                   'bg-teal-600 text-white shadow-lg': activeStage === 'screening',
                   'text-gray-300 hover:bg-gray-700 hover:text-white border-teal-500/30': activeStage !== 'screening'
               }"
               class="block px-6 py-8 text-2xl font-bold rounded-lg transition-all border">
                SCREENING
                <div class="text-xs font-normal opacity-80 mt-1">
                    Discovery & Screening
                </div>
            </a>
        </div>

        <!-- Stage 3: Intelligence -->
        <div class="px-2 mb-4">
            <a href="#" @click.prevent="switchStage('intelligence')"
               :class="{
                   'bg-blue-600 text-white shadow-lg': activeStage === 'intelligence',
                   'text-gray-300 hover:bg-gray-700 hover:text-white border-blue-500/30': activeStage !== 'intelligence'
               }"
               class="block px-6 py-8 text-2xl font-bold rounded-lg transition-all border">
                INTELLIGENCE
                <div class="text-xs font-normal opacity-80 mt-1">
                    Deep Analysis & Reports
                </div>
            </a>
        </div>

        <!-- Footer -->
        <div class="mt-auto px-2 py-4 border-t border-gray-700">
            <div class="text-center">
                <div class="text-xs text-gray-400 font-medium">My Application</div>
                <div class="text-xs text-gray-500 mt-1">Version 1.0</div>
            </div>
        </div>
    </nav>
</aside>
```

### State Management for Sidebar

```javascript
function appState() {
    return {
        activeStage: 'profiles',

        switchStage(stage) {
            console.log(`Switching to ${stage}`);
            this.activeStage = stage;

            // Optional: Save to localStorage
            localStorage.setItem('activeStage', stage);

            // Optional: Dispatch event
            this.$dispatch('stage-changed', { stage });
        },

        init() {
            // Restore from localStorage
            const saved = localStorage.getItem('activeStage');
            if (saved) {
                this.activeStage = saved;
            }
        }
    }
}
```

### Responsive Sidebar (Mobile)

For mobile devices, the sidebar should:
- Be hidden by default
- Slide in from the left when menu is opened
- Overlay the main content
- Close when clicking outside

```html
<!-- Mobile Menu Button -->
<button @click="mobileMenuOpen = !mobileMenuOpen"
        class="lg:hidden p-2">
    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 6h16M4 12h16M4 18h16"></path>
    </svg>
</button>

<!-- Mobile Sidebar Overlay -->
<div x-show="mobileMenuOpen"
     @click="mobileMenuOpen = false"
     class="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
     x-transition:enter="transition-opacity ease-out duration-300"
     x-transition:enter-start="opacity-0"
     x-transition:enter-end="opacity-100"
     x-transition:leave="transition-opacity ease-in duration-200"
     x-transition:leave-start="opacity-100"
     x-transition:leave-end="opacity-0">
</div>

<!-- Mobile Sidebar -->
<aside x-show="mobileMenuOpen"
       class="lg:hidden fixed inset-y-0 left-0 w-80 bg-gray-900 text-white z-50"
       x-transition:enter="transition-transform ease-out duration-300"
       x-transition:enter-start="-translate-x-full"
       x-transition:enter-end="translate-x-0"
       x-transition:leave="transition-transform ease-in duration-200"
       x-transition:leave-start="translate-x-0"
       x-transition:leave-end="-translate-x-full">
    <!-- Same content as desktop sidebar -->
</aside>
```

---

## Styling System

### Tailwind CSS Utility Classes

Catalynx uses Tailwind extensively. Here are the key utility patterns:

#### Layout

```html
<!-- Flexbox patterns -->
<div class="flex items-center justify-between">
<div class="flex flex-col space-y-4">
<div class="grid grid-cols-3 gap-4">

<!-- Spacing -->
<div class="p-4">        <!-- padding all sides -->
<div class="px-6 py-4">  <!-- padding x and y -->
<div class="mt-6 mb-4">  <!-- margin top and bottom -->
<div class="space-y-4">  <!-- vertical spacing between children -->
```

#### Colors

```html
<!-- Text colors -->
<p class="text-gray-600 dark:text-gray-300">
<p class="text-blue-600 hover:text-blue-700">

<!-- Background colors -->
<div class="bg-white dark:bg-gray-800">
<div class="bg-gradient-to-r from-blue-500 to-purple-600">

<!-- Border colors -->
<div class="border border-gray-200 dark:border-gray-700">
```

#### Typography

```html
<h1 class="text-3xl font-bold">
<h2 class="text-2xl font-semibold">
<p class="text-sm text-gray-600">
<span class="font-medium uppercase tracking-wide">
```

#### Interactivity

```html
<!-- Hover states -->
<button class="hover:bg-blue-700 hover:shadow-lg">

<!-- Focus states -->
<input class="focus:ring-2 focus:ring-blue-500 focus:border-transparent">

<!-- Transitions -->
<div class="transition-all duration-300 ease-in-out">
```

### Custom CSS Extensions

**File: `style.css`**

```css
/* Brand colors as CSS variables */
:root {
    --brand-primary: #005b95;
    --brand-primary-hover: #004580;
    --brand-selection-bg: #1e3a8a;
    --brand-selection-border: #1e3a8a;
}

/* Reusable component classes */
.card-base {
    @apply bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700;
}

.card-content {
    @apply card-base p-4;
}

.card-elevated {
    @apply card-base shadow-lg;
}

/* Status badges */
.status-badge {
    @apply inline-flex items-center px-2 py-1 rounded-full text-xs font-medium;
}

.status-success {
    @apply status-badge bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100;
}

.status-warning {
    @apply status-badge bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100;
}

.status-error {
    @apply status-badge bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100;
}

/* Button styles */
.btn-base {
    @apply inline-flex items-center px-4 py-2 text-sm font-medium rounded-md
           transition-colors duration-200 focus:outline-none focus:ring-2
           focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-primary {
    @apply btn-base bg-indigo-600 hover:bg-indigo-700 text-white focus:ring-indigo-500;
}

.btn-secondary {
    @apply btn-base bg-gray-600 hover:bg-gray-700 text-white focus:ring-gray-500;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-in {
    animation: fadeIn 0.3s ease-in-out;
}

/* Custom scrollbar */
.custom-scrollbar::-webkit-scrollbar {
    width: 8px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}

/* Loading spinner */
.spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #2563eb;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Progress bars */
.progress-container {
    @apply w-full bg-gray-200 rounded-full overflow-hidden;
    height: 0.5rem;
}

.progress-bar {
    @apply h-full rounded-full transition-all duration-500 ease-in-out;
    background: linear-gradient(90deg, #3b82f6, #1d4ed8);
}

/* Table hover effects */
.table-row-hover:hover {
    background-color: #f9fafb;
    transform: translateX(2px);
    transition: all 0.15s ease-in-out;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* Dark mode overrides */
.dark .table-row-hover:hover {
    background-color: #374151;
}

.dark .card-base {
    background: #1f2937;
    border-color: #374151;
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
```

---

## State Management

### Centralized State with Alpine.js

Alpine.js provides reactive state management without external libraries.

**Pattern: Global Store**

```javascript
// File: modules/state-module.js
function globalState() {
    return {
        // Navigation
        activeStage: 'welcome',
        previousStage: null,

        // User data
        currentUser: null,
        selectedProfile: null,

        // UI state
        darkMode: false,
        mobileMenuOpen: false,
        notifications: [],

        // System state
        loading: false,
        error: null,

        // Methods
        switchStage(stage) {
            this.previousStage = this.activeStage;
            this.activeStage = stage;
            this.$dispatch('stage-changed', { from: this.previousStage, to: stage });
        },

        showNotification(type, title, message, duration = 5000) {
            const id = Date.now();
            this.notifications.push({
                id,
                type,  // 'success', 'error', 'warning', 'info'
                title,
                message,
                visible: true
            });

            setTimeout(() => {
                this.dismissNotification(id);
            }, duration);
        },

        dismissNotification(id) {
            const notification = this.notifications.find(n => n.id === id);
            if (notification) {
                notification.visible = false;
                setTimeout(() => {
                    this.notifications = this.notifications.filter(n => n.id !== id);
                }, 300);
            }
        },

        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            localStorage.setItem('darkMode', this.darkMode);

            if (this.darkMode) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
        },

        init() {
            // Restore dark mode from localStorage
            const savedDarkMode = localStorage.getItem('darkMode') === 'true';
            if (savedDarkMode) {
                this.darkMode = true;
                document.documentElement.classList.add('dark');
            }

            // Restore active stage
            const savedStage = localStorage.getItem('activeStage');
            if (savedStage) {
                this.activeStage = savedStage;
            }
        }
    }
}
```

**Usage in HTML:**

```html
<body x-data="globalState()" x-init="init()">
    <!-- Notifications -->
    <div class="fixed top-4 right-4 z-50 space-y-2" x-show="notifications.length > 0">
        <template x-for="notification in notifications" :key="notification.id">
            <div x-show="notification.visible"
                 x-transition:enter="transition ease-out duration-300"
                 x-transition:enter-start="opacity-0 transform translate-x-full"
                 x-transition:enter-end="opacity-100 transform translate-x-0"
                 class="bg-white rounded-lg shadow-lg p-4"
                 :class="{
                     'border-l-4 border-l-green-500': notification.type === 'success',
                     'border-l-4 border-l-red-500': notification.type === 'error',
                     'border-l-4 border-l-yellow-500': notification.type === 'warning',
                     'border-l-4 border-l-blue-500': notification.type === 'info'
                 }">
                <div class="flex items-start justify-between">
                    <div>
                        <h4 class="font-medium" x-text="notification.title"></h4>
                        <p class="text-sm text-gray-600" x-text="notification.message"></p>
                    </div>
                    <button @click="dismissNotification(notification.id)">×</button>
                </div>
            </div>
        </template>
    </div>

    <!-- Example: Trigger notification -->
    <button @click="showNotification('success', 'Success!', 'Operation completed')">
        Test Notification
    </button>
</body>
```

### Component-Level State

For feature-specific state, create separate modules:

```javascript
// File: modules/profiles-module.js
function profilesModule() {
    return {
        profiles: [],
        selectedProfile: null,
        loading: false,
        error: null,

        async loadProfiles() {
            this.loading = true;
            this.error = null;

            try {
                const response = await fetch('/api/profiles');
                if (!response.ok) throw new Error('Failed to load profiles');
                this.profiles = await response.json();
            } catch (error) {
                this.error = error.message;
                console.error('Error loading profiles:', error);
            } finally {
                this.loading = false;
            }
        },

        selectProfile(profile) {
            this.selectedProfile = profile;
            this.$dispatch('profile-selected', profile);
        }
    }
}
```

---

## API Integration

### FastAPI Backend Structure

**File: `main.py`**

```python
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(
    title="My Application",
    description="API for my awesome app",
    version="1.0.0"
)

# CORS middleware (if frontend is on different domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Profile(BaseModel):
    id: int
    name: str
    email: str
    active: bool = True

class ProfileCreate(BaseModel):
    name: str
    email: str

# In-memory storage (replace with database)
profiles_db = []

# API Routes
@app.get("/api/profiles", response_model=List[Profile])
async def get_profiles():
    """Get all profiles"""
    return profiles_db

@app.get("/api/profiles/{profile_id}", response_model=Profile)
async def get_profile(profile_id: int):
    """Get single profile by ID"""
    profile = next((p for p in profiles_db if p.id == profile_id), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.post("/api/profiles", response_model=Profile)
async def create_profile(profile: ProfileCreate):
    """Create new profile"""
    new_id = len(profiles_db) + 1
    new_profile = Profile(id=new_id, **profile.dict())
    profiles_db.append(new_profile)
    return new_profile

@app.put("/api/profiles/{profile_id}", response_model=Profile)
async def update_profile(profile_id: int, profile: ProfileCreate):
    """Update existing profile"""
    existing = next((p for p in profiles_db if p.id == profile_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="Profile not found")

    existing.name = profile.name
    existing.email = profile.email
    return existing

@app.delete("/api/profiles/{profile_id}")
async def delete_profile(profile_id: int):
    """Delete profile"""
    global profiles_db
    profiles_db = [p for p in profiles_db if p.id != profile_id]
    return {"message": "Profile deleted"}

@app.get("/api/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "profiles_count": len(profiles_db)
    }

# Serve static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/")
async def root():
    """Serve main SPA"""
    return FileResponse(static_path / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Frontend API Client

**File: `static/js/api/client.js`**

```javascript
/**
 * API Client for backend communication
 */
class ApiClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
    }

    /**
     * Generic request handler
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({
                    detail: response.statusText
                }));
                throw new Error(error.detail || 'Request failed');
            }

            // Handle no-content responses
            if (response.status === 204) {
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const query = new URLSearchParams(params).toString();
        const url = query ? `${endpoint}?${query}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

// Create singleton instance
const api = new ApiClient();

// Convenience methods for specific resources
const profilesApi = {
    getAll: () => api.get('/profiles'),
    getOne: (id) => api.get(`/profiles/${id}`),
    create: (data) => api.post('/profiles', data),
    update: (id, data) => api.put(`/profiles/${id}`, data),
    delete: (id) => api.delete(`/profiles/${id}`)
};
```

**Usage in Alpine Component:**

```javascript
function profilesModule() {
    return {
        profiles: [],
        loading: false,
        error: null,

        async loadProfiles() {
            this.loading = true;
            this.error = null;

            try {
                this.profiles = await profilesApi.getAll();
            } catch (error) {
                this.error = error.message;
                this.showNotification('error', 'Error', error.message);
            } finally {
                this.loading = false;
            }
        },

        async createProfile(name, email) {
            try {
                const newProfile = await profilesApi.create({ name, email });
                this.profiles.push(newProfile);
                this.showNotification('success', 'Success', 'Profile created');
                return newProfile;
            } catch (error) {
                this.showNotification('error', 'Error', error.message);
                throw error;
            }
        },

        async deleteProfile(id) {
            if (!confirm('Are you sure?')) return;

            try {
                await profilesApi.delete(id);
                this.profiles = this.profiles.filter(p => p.id !== id);
                this.showNotification('success', 'Success', 'Profile deleted');
            } catch (error) {
                this.showNotification('error', 'Error', error.message);
            }
        }
    }
}
```

---

## Component Library

### Reusable UI Components

#### 1. Modal Component

```html
<!-- Modal Template -->
<template x-if="showModal">
    <div class="fixed inset-0 z-50 overflow-y-auto"
         @keydown.escape.window="showModal = false">

        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black bg-opacity-50"
             @click="showModal = false"
             x-transition:enter="transition-opacity ease-out duration-300"
             x-transition:enter-start="opacity-0"
             x-transition:enter-end="opacity-100">
        </div>

        <!-- Modal Content -->
        <div class="flex items-center justify-center min-h-screen p-4">
            <div class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full"
                 @click.stop
                 x-transition:enter="transition ease-out duration-300"
                 x-transition:enter-start="opacity-0 transform scale-95"
                 x-transition:enter-end="opacity-100 transform scale-100">

                <!-- Header -->
                <div class="flex items-center justify-between p-6 border-b dark:border-gray-700">
                    <h3 class="text-xl font-semibold" x-text="modalTitle"></h3>
                    <button @click="showModal = false"
                            class="text-gray-400 hover:text-gray-600">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>

                <!-- Body -->
                <div class="p-6">
                    <slot name="modal-content"></slot>
                </div>

                <!-- Footer -->
                <div class="flex justify-end space-x-2 p-6 border-t dark:border-gray-700">
                    <button @click="showModal = false"
                            class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">
                        Cancel
                    </button>
                    <button @click="handleModalSubmit()"
                            class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                        <span x-text="modalSubmitText || 'Submit'"></span>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
```

**Usage:**

```javascript
function myComponent() {
    return {
        showModal: false,
        modalTitle: 'Create Profile',
        modalSubmitText: 'Create',

        openModal() {
            this.showModal = true;
        },

        handleModalSubmit() {
            // Your submit logic
            this.showModal = false;
        }
    }
}
```

#### 2. Data Table Component

```html
<div class="overflow-x-auto">
    <table class="w-full">
        <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
                <template x-for="column in columns" :key="column.key">
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
                        @click="sortBy(column.key)">
                        <span x-text="column.label"></span>
                        <span x-show="sortColumn === column.key">
                            <span x-show="sortDirection === 'asc'">↑</span>
                            <span x-show="sortDirection === 'desc'">↓</span>
                        </span>
                    </th>
                </template>
            </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            <template x-for="row in sortedData" :key="row.id">
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <template x-for="column in columns" :key="column.key">
                        <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100"
                            x-text="row[column.key]">
                        </td>
                    </template>
                </tr>
            </template>
        </tbody>
    </table>
</div>
```

**JavaScript:**

```javascript
function dataTable() {
    return {
        columns: [
            { key: 'id', label: 'ID' },
            { key: 'name', label: 'Name' },
            { key: 'email', label: 'Email' }
        ],
        data: [],
        sortColumn: null,
        sortDirection: 'asc',

        get sortedData() {
            if (!this.sortColumn) return this.data;

            return [...this.data].sort((a, b) => {
                const aVal = a[this.sortColumn];
                const bVal = b[this.sortColumn];

                if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1;
                if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1;
                return 0;
            });
        },

        sortBy(column) {
            if (this.sortColumn === column) {
                this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortColumn = column;
                this.sortDirection = 'asc';
            }
        }
    }
}
```

#### 3. Loading Spinner Component

```html
<div x-show="loading"
     class="flex items-center justify-center p-8">
    <div class="spinner"></div>
    <span class="ml-3 text-gray-600">Loading...</span>
</div>
```

#### 4. Status Badge Component

```html
<span :class="{
    'status-success': status === 'active',
    'status-warning': status === 'pending',
    'status-error': status === 'inactive'
}" x-text="status"></span>
```

---

## Responsive Design

### Mobile-First Approach

Catalynx uses mobile-first responsive design with Tailwind's breakpoint system:

```
sm:  640px  (Small devices)
md:  768px  (Medium devices)
lg:  1024px (Large devices)
xl:  1280px (Extra large devices)
2xl: 1536px (2X large devices)
```

**Pattern:**

```html
<!-- Mobile: Stack vertically, Desktop: Side by side -->
<div class="flex flex-col lg:flex-row">
    <div class="w-full lg:w-1/3">Sidebar</div>
    <div class="w-full lg:w-2/3">Content</div>
</div>

<!-- Hide on mobile, show on desktop -->
<aside class="hidden lg:block">Desktop Sidebar</aside>

<!-- Show on mobile, hide on desktop -->
<button class="lg:hidden">Mobile Menu</button>

<!-- Responsive text sizes -->
<h1 class="text-2xl lg:text-4xl">Responsive Heading</h1>

<!-- Responsive padding -->
<div class="p-4 lg:p-8">Responsive Padding</div>

<!-- Responsive grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <!-- Grid items -->
</div>
```

### Key Responsive Patterns

#### 1. Collapsible Sidebar

```html
<!-- Desktop: Always visible -->
<aside class="hidden lg:block w-80 bg-gray-900">
    <!-- Desktop sidebar -->
</aside>

<!-- Mobile: Toggle -->
<aside x-show="mobileMenuOpen"
       class="lg:hidden fixed inset-y-0 left-0 w-80 bg-gray-900 z-50"
       x-transition>
    <!-- Mobile sidebar (same content) -->
</aside>

<!-- Mobile menu button -->
<button @click="mobileMenuOpen = !mobileMenuOpen"
        class="lg:hidden">
    Menu
</button>
```

#### 2. Responsive Tables

```html
<!-- Desktop: Full table -->
<div class="hidden lg:block overflow-x-auto">
    <table class="w-full">
        <!-- Table content -->
    </table>
</div>

<!-- Mobile: Cards -->
<div class="lg:hidden space-y-4">
    <template x-for="item in items" :key="item.id">
        <div class="bg-white p-4 rounded-lg shadow">
            <h3 x-text="item.name"></h3>
            <p x-text="item.email"></p>
        </div>
    </template>
</div>
```

#### 3. Responsive Navigation

```html
<!-- Desktop: Horizontal -->
<nav class="hidden lg:flex space-x-4">
    <a href="#">Link 1</a>
    <a href="#">Link 2</a>
</nav>

<!-- Mobile: Vertical -->
<nav class="lg:hidden flex flex-col space-y-2">
    <a href="#">Link 1</a>
    <a href="#">Link 2</a>
</nav>
```

---

## Dark Mode Implementation

### Setup

**1. Add dark mode class to `<html>`:**

```html
<html lang="en" class="dark">  <!-- or no class for light mode -->
```

**2. Use Tailwind's dark variant:**

```html
<div class="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
    Content adapts to dark mode
</div>
```

### Dark Mode Toggle

```javascript
function darkModeToggle() {
    return {
        darkMode: false,

        toggleDarkMode() {
            this.darkMode = !this.darkMode;

            // Update DOM
            if (this.darkMode) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }

            // Persist to localStorage
            localStorage.setItem('darkMode', this.darkMode);
        },

        init() {
            // Restore from localStorage
            const saved = localStorage.getItem('darkMode');

            if (saved !== null) {
                this.darkMode = saved === 'true';
            } else {
                // Default to system preference
                this.darkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
            }

            if (this.darkMode) {
                document.documentElement.classList.add('dark');
            }
        }
    }
}
```

**HTML:**

```html
<body x-data="darkModeToggle()" x-init="init()">
    <button @click="toggleDarkMode()"
            class="p-2 rounded-lg hover:bg-gray-700">
        <span x-show="!darkMode">🌙</span>
        <span x-show="darkMode">☀️</span>
    </button>
</body>
```

### Dark Mode Color Patterns

```css
/* Light mode (default) */
.card {
    background-color: white;
    color: #1f2937;
    border-color: #e5e7eb;
}

/* Dark mode (with dark: prefix) */
.dark .card {
    background-color: #1f2937;
    color: #f9fafb;
    border-color: #374151;
}
```

**Tailwind utility approach:**

```html
<div class="bg-white dark:bg-gray-800
            text-gray-900 dark:text-white
            border-gray-200 dark:border-gray-700">
</div>
```

---

## Accessibility Features

### WCAG 2.1 AA Compliance

#### 1. Semantic HTML

```html
<!-- Good: Semantic elements -->
<header>...</header>
<nav>...</nav>
<main>...</main>
<aside>...</aside>
<footer>...</footer>

<!-- Bad: Generic divs -->
<div class="header">...</div>
```

#### 2. ARIA Labels

```html
<!-- Buttons with icon only -->
<button aria-label="Close modal">×</button>

<!-- Navigation regions -->
<nav aria-label="Main navigation">...</nav>

<!-- Form inputs -->
<input type="text" aria-label="Search" placeholder="Search...">

<!-- Live regions for dynamic content -->
<div aria-live="polite" aria-atomic="true">
    <p x-text="statusMessage"></p>
</div>
```

#### 3. Keyboard Navigation

```html
<!-- Ensure all interactive elements are keyboard accessible -->
<button @click="handleClick()"
        @keydown.enter="handleClick()"
        @keydown.space.prevent="handleClick()">
    Click Me
</button>

<!-- Modal: Close on Escape -->
<div @keydown.escape.window="closeModal()">
    <!-- Modal content -->
</div>

<!-- Trap focus in modal -->
<div x-data="{
    trapFocus() {
        // Focus trap logic
    }
}" x-init="trapFocus()">
</div>
```

#### 4. Focus Indicators

```css
/* Visible focus indicators */
.focus-visible:focus {
    outline: 2px solid #2563eb;
    outline-offset: 2px;
}

button:focus-visible,
a:focus-visible,
input:focus-visible {
    outline: 2px solid #2563eb;
    outline-offset: 2px;
}
```

#### 5. Color Contrast

Ensure text meets WCAG AA contrast ratios:
- Normal text: 4.5:1
- Large text (18pt+): 3:1

```html
<!-- Good contrast -->
<div class="bg-white text-gray-900">High contrast text</div>

<!-- Bad contrast -->
<div class="bg-gray-200 text-gray-300">Low contrast text</div>
```

#### 6. Screen Reader Support

```html
<!-- Skip to main content link -->
<a href="#main-content"
   class="sr-only focus:not-sr-only">
    Skip to main content
</a>

<!-- Hide decorative images -->
<img src="decorative.png" alt="" role="presentation">

<!-- Screen reader only text -->
<span class="sr-only">Additional context for screen readers</span>
```

**CSS for `.sr-only`:**

```css
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
}

.sr-only.focus\:not-sr-only:focus {
    position: static;
    width: auto;
    height: auto;
    padding: inherit;
    margin: inherit;
    overflow: visible;
    clip: auto;
    white-space: normal;
}
```

#### 7. Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
```

---

## Performance Optimizations

### 1. Lazy Loading

```html
<!-- Lazy load images -->
<img src="image.jpg" loading="lazy" alt="Description">

<!-- Lazy load Alpine components -->
<div x-data="expensiveComponent()" x-init="$nextTick(() => init())">
```

### 2. Virtual Scrolling (Large Lists)

For very large lists, only render visible items:

```javascript
function virtualList() {
    return {
        allItems: [], // 10,000 items
        visibleItems: [],
        itemHeight: 50,
        containerHeight: 500,
        scrollTop: 0,

        get visibleRange() {
            const start = Math.floor(this.scrollTop / this.itemHeight);
            const count = Math.ceil(this.containerHeight / this.itemHeight);
            return { start, end: start + count };
        },

        updateVisibleItems() {
            const { start, end } = this.visibleRange;
            this.visibleItems = this.allItems.slice(start, end);
        },

        onScroll(event) {
            this.scrollTop = event.target.scrollTop;
            this.updateVisibleItems();
        }
    }
}
```

### 3. Debouncing

```javascript
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Usage
function searchComponent() {
    return {
        searchQuery: '',

        init() {
            this.$watch('searchQuery', debounce((value) => {
                this.performSearch(value);
            }, 300));
        },

        performSearch(query) {
            console.log('Searching for:', query);
        }
    }
}
```

### 4. Memoization

```javascript
function dataProcessor() {
    return {
        rawData: [],
        _processedDataCache: null,
        _cacheKey: null,

        get processedData() {
            const currentKey = JSON.stringify(this.rawData);

            // Return cached result if data hasn't changed
            if (this._cacheKey === currentKey) {
                return this._processedDataCache;
            }

            // Expensive processing
            this._processedDataCache = this.rawData.map(item => {
                // Complex transformation
                return { ...item, processed: true };
            });

            this._cacheKey = currentKey;
            return this._processedDataCache;
        }
    }
}
```

### 5. Image Optimization

```html
<!-- Responsive images -->
<img srcset="image-400.jpg 400w,
             image-800.jpg 800w,
             image-1200.jpg 1200w"
     sizes="(max-width: 768px) 400px,
            (max-width: 1024px) 800px,
            1200px"
     src="image-800.jpg"
     alt="Description"
     loading="lazy">
```

### 6. Code Splitting

Split large Alpine components into separate files:

```html
<!-- Load only when needed -->
<script>
async function loadModule(name) {
    const module = await import(`/static/modules/${name}.js`);
    return module.default;
}
</script>

<div x-data="await loadModule('expensive-component')">
```

---

## Common Customizations

### 1. Custom Color Scheme

**Update CSS variables:**

```css
:root {
    --brand-primary: #your-color;
    --brand-primary-hover: #your-hover-color;
    --brand-secondary: #your-secondary;
}
```

**Update Tailwind config:**

```html
<script>
tailwind.config = {
    theme: {
        extend: {
            colors: {
                brand: {
                    50: '#...',
                    100: '#...',
                    // ... up to 900
                    primary: '#your-color'
                }
            }
        }
    }
}
</script>
```

### 2. Custom Logo

```html
<div class="p-4">
    <h1 class="text-xl font-bold flex items-center">
        <img src="/static/your-logo.png" alt="Your App" class="h-10 mr-3">
        <span>YOUR APP NAME</span>
    </h1>
</div>
```

### 3. Custom Navigation Items

```javascript
// Define navigation structure
const navigation = [
    {
        id: 'dashboard',
        label: 'Dashboard',
        icon: '📊',
        color: 'blue',
        description: 'Overview & Metrics'
    },
    {
        id: 'users',
        label: 'Users',
        icon: '👥',
        color: 'green',
        description: 'User Management'
    },
    // Add more...
];
```

```html
<nav class="mt-6">
    <template x-for="item in navigation" :key="item.id">
        <div class="px-2 mb-4">
            <a href="#"
               @click.prevent="switchStage(item.id)"
               :class="{
                   [`bg-${item.color}-600 text-white shadow-lg`]: activeStage === item.id,
                   [`text-gray-300 hover:bg-gray-700 border-${item.color}-500/30`]: activeStage !== item.id
               }"
               class="block px-6 py-8 text-2xl font-bold rounded-lg transition-all border">
                <span x-text="item.icon + ' ' + item.label"></span>
                <div class="text-xs font-normal opacity-80 mt-1"
                     x-text="item.description"></div>
            </a>
        </div>
    </template>
</nav>
```

### 4. Add Authentication

**Backend (FastAPI):**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Verify credentials
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect credentials")

    # Create token
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Verify token and return user
    pass

@app.get("/api/protected")
async def protected_route(current_user = Depends(get_current_user)):
    return {"message": "You are authenticated", "user": current_user}
```

**Frontend:**

```javascript
// Login
async function login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch('/token', {
        method: 'POST',
        body: formData
    });

    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
}

// API client with auth
class AuthenticatedApiClient extends ApiClient {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('access_token');

        return super.request(endpoint, {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `Bearer ${token}`
            }
        });
    }
}
```

### 5. Add WebSocket Support

**Backend:**

```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
```

**Frontend:**

```javascript
function websocketComponent() {
    return {
        ws: null,
        connected: false,
        messages: [],

        connect() {
            this.ws = new WebSocket('ws://localhost:8000/ws');

            this.ws.onopen = () => {
                this.connected = true;
                console.log('WebSocket connected');
            };

            this.ws.onmessage = (event) => {
                this.messages.push(event.data);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            this.ws.onclose = () => {
                this.connected = false;
                console.log('WebSocket disconnected');
            };
        },

        send(message) {
            if (this.connected) {
                this.ws.send(message);
            }
        },

        disconnect() {
            if (this.ws) {
                this.ws.close();
            }
        }
    }
}
```

---

## Best Practices

### 1. Project Organization

```
✅ DO:
- Separate concerns (HTML structure, CSS styling, JS behavior)
- Use modular JavaScript files
- Group related API endpoints in routers
- Keep components small and focused

❌ DON'T:
- Put all code in one file
- Mix business logic with presentation
- Create god objects/components
```

### 2. Performance

```
✅ DO:
- Use Alpine's `x-cloak` to prevent FOUC
- Debounce expensive operations (search, API calls)
- Lazy load images and components
- Use CSS transforms for animations (GPU accelerated)
- Minimize API calls with caching

❌ DON'T:
- Load all data upfront
- Run expensive computations in getters
- Animate properties that trigger reflow (width, height, top, left)
```

### 3. Accessibility

```
✅ DO:
- Use semantic HTML
- Provide ARIA labels
- Ensure keyboard navigation works
- Test with screen readers
- Maintain color contrast ratios

❌ DON'T:
- Rely solely on color for information
- Trap keyboard focus permanently
- Use divs for everything
```

### 4. Security

```
✅ DO:
- Validate all user input
- Use HTTPS in production
- Sanitize data before rendering
- Implement CORS properly
- Use environment variables for secrets

❌ DON'T:
- Trust client-side data
- Expose API keys in frontend code
- Use eval() or innerHTML with user data
```

### 5. Code Quality

```
✅ DO:
- Use consistent naming conventions
- Comment complex logic
- Handle errors gracefully
- Write meaningful commit messages
- Keep functions small and focused

❌ DON'T:
- Leave console.log() in production
- Ignore errors silently
- Write cryptic variable names (x, tmp, data1)
```

### 6. Alpine.js Specific

```
✅ DO:
- Use `x-cloak` to prevent flash of unstyled content
- Use `$nextTick` for DOM-dependent operations
- Use `$watch` for reactive side effects
- Use `$dispatch` for component communication
- Use getters for computed properties

❌ DON'T:
- Mutate props directly
- Put complex logic in templates
- Forget to handle loading/error states
```

### 7. CSS/Tailwind

```
✅ DO:
- Use Tailwind utility classes
- Extract common patterns to custom CSS classes
- Use dark: prefix for dark mode
- Follow mobile-first approach
- Use spacing scale consistently

❌ DON'T:
- Fight the framework with !important
- Create one-off utility classes
- Mix CSS methodologies (BEM + utilities)
```

### 8. API Design

```
✅ DO:
- Use RESTful conventions
- Version your API (/api/v1/)
- Return consistent error formats
- Use appropriate HTTP status codes
- Document endpoints (OpenAPI/Swagger)

❌ DON'T:
- Use GET for state-changing operations
- Return 200 for errors
- Expose internal implementation details
```

---

## Additional Resources

### Official Documentation

- **Alpine.js**: https://alpinejs.dev/
- **Tailwind CSS**: https://tailwindcss.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Chart.js**: https://www.chartjs.org/

### Learning Resources

- **Alpine.js Tutorial**: https://alpinejs.dev/start-here
- **Tailwind CSS Crash Course**: https://tailwindcss.com/docs/utility-first
- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/

### Tools

- **Tailwind Play**: https://play.tailwindcss.com/ (Online playground)
- **Can I Use**: https://caniuse.com/ (Browser compatibility)
- **WAVE**: https://wave.webaim.org/ (Accessibility testing)
- **Lighthouse**: Built into Chrome DevTools (Performance & accessibility)

### Color Tools

- **Tailwind Color Palette**: https://tailwindcss.com/docs/customizing-colors
- **Coolors**: https://coolors.co/ (Color scheme generator)
- **Contrast Checker**: https://webaim.org/resources/contrastchecker/

---

## Troubleshooting

### Common Issues

#### Alpine.js not working

```
Problem: Components not initializing
Solution:
1. Check that Alpine.js is loaded (defer attribute)
2. Ensure x-data is on parent element
3. Check browser console for errors
4. Use x-init to debug initialization
```

#### Dark mode not persisting

```
Problem: Dark mode resets on page reload
Solution:
1. Check localStorage.setItem() is called
2. Check init() method restores from localStorage
3. Ensure 'dark' class is added to <html>
```

#### API calls failing

```
Problem: CORS errors or 404s
Solution:
1. Check API endpoint URL is correct
2. Verify CORS middleware is configured
3. Check network tab in DevTools
4. Verify backend server is running
```

#### Tailwind classes not working

```
Problem: Styles not applying
Solution:
1. Check class names are spelled correctly
2. Verify Tailwind CDN is loaded
3. Check for conflicting custom CSS
4. Use browser DevTools to inspect elements
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-23 | Initial documentation |

---

## Support & Contribution

For questions or contributions to this guide:

1. Review the official Catalynx project documentation
2. Check existing issues/discussions
3. Create detailed bug reports or feature requests
4. Follow code style guidelines when contributing

---

**END OF GUIDE**

This guide provides a complete foundation for replicating the Catalynx GUI architecture in your own projects. Adapt patterns as needed for your specific use case.
