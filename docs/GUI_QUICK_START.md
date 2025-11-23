# GUI Quick Start - Minimal Working Example

**Get started in 5 minutes with the Catalynx-style interface**

This is a companion to the [GUI_REPLICATION_GUIDE.md](./GUI_REPLICATION_GUIDE.md) - use this to get a minimal working application running immediately.

---

## Step 1: Create Project Structure

```bash
mkdir my-app
cd my-app
mkdir -p static/{js,css,modules}
```

---

## Step 2: Create Backend (main.py)

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI(title="My App")

# API endpoint example
@app.get("/api/items")
async def get_items():
    return [
        {"id": 1, "name": "Item 1", "status": "active"},
        {"id": 2, "name": "Item 2", "status": "pending"},
        {"id": 3, "name": "Item 3", "status": "active"}
    ]

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

# Serve static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/")
async def root():
    return FileResponse(static_path / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Step 3: Create Frontend HTML (static/index.html)

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
    <link rel="stylesheet" href="/static/css/style.css">

    <style>
        [x-cloak] { display: none !important; }
    </style>

    <!-- Tailwind Configuration -->
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: {
                            primary: '#2563eb',
                            hover: '#1d4ed8'
                        }
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-gray-100 dark:bg-gray-900" x-data="appState()" x-init="init()" x-cloak>

    <!-- Notifications -->
    <div class="fixed top-4 right-4 z-50 space-y-2">
        <template x-for="notification in notifications" :key="notification.id">
            <div x-show="notification.visible"
                 x-transition:enter="transition ease-out duration-300"
                 x-transition:enter-start="opacity-0 translate-x-full"
                 x-transition:enter-end="opacity-100 translate-x-0"
                 class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 max-w-sm border-l-4"
                 :class="{
                     'border-l-green-500': notification.type === 'success',
                     'border-l-red-500': notification.type === 'error',
                     'border-l-blue-500': notification.type === 'info'
                 }">
                <div class="flex items-start justify-between">
                    <div>
                        <h4 class="font-medium text-gray-900 dark:text-white" x-text="notification.title"></h4>
                        <p class="text-sm text-gray-600 dark:text-gray-300 mt-1" x-text="notification.message"></p>
                    </div>
                    <button @click="dismissNotification(notification.id)"
                            class="ml-2 text-gray-400 hover:text-gray-600">×</button>
                </div>
            </div>
        </template>
    </div>

    <!-- Main Layout -->
    <div class="min-h-screen flex">

        <!-- Sidebar -->
        <aside class="hidden lg:block bg-gray-900 dark:bg-gray-800 text-white w-80 flex-shrink-0">
            <!-- Logo -->
            <div class="p-6 border-b border-gray-700">
                <div class="flex items-center justify-between">
                    <h1 class="text-2xl font-bold">MY APP</h1>
                    <button @click="toggleDarkMode()"
                            class="p-2 rounded-lg hover:bg-gray-700">
                        <span x-show="!darkMode">🌙</span>
                        <span x-show="darkMode">☀️</span>
                    </button>
                </div>
            </div>

            <!-- Navigation -->
            <nav class="mt-6">
                <!-- Dashboard -->
                <div class="px-2 mb-4">
                    <a href="#" @click.prevent="switchStage('dashboard')"
                       :class="{
                           'bg-blue-600 text-white shadow-lg': activeStage === 'dashboard',
                           'text-gray-300 hover:bg-gray-700 border-blue-500/30': activeStage !== 'dashboard'
                       }"
                       class="block px-6 py-8 text-2xl font-bold rounded-lg transition-all border">
                        DASHBOARD
                        <div class="text-xs font-normal opacity-80 mt-1">Overview & Metrics</div>
                    </a>
                </div>

                <!-- Items -->
                <div class="px-2 mb-4">
                    <a href="#" @click.prevent="switchStage('items')"
                       :class="{
                           'bg-purple-600 text-white shadow-lg': activeStage === 'items',
                           'text-gray-300 hover:bg-gray-700 border-purple-500/30': activeStage !== 'items'
                       }"
                       class="block px-6 py-8 text-2xl font-bold rounded-lg transition-all border">
                        ITEMS
                        <div class="text-xs font-normal opacity-80 mt-1">Manage Items</div>
                    </a>
                </div>

                <!-- Settings -->
                <div class="px-2 mb-4">
                    <a href="#" @click.prevent="switchStage('settings')"
                       :class="{
                           'bg-teal-600 text-white shadow-lg': activeStage === 'settings',
                           'text-gray-300 hover:bg-gray-700 border-teal-500/30': activeStage !== 'settings'
                       }"
                       class="block px-6 py-8 text-2xl font-bold rounded-lg transition-all border">
                        SETTINGS
                        <div class="text-xs font-normal opacity-80 mt-1">Configuration</div>
                    </a>
                </div>
            </nav>

            <!-- Footer -->
            <div class="absolute bottom-0 w-80 p-4 border-t border-gray-700">
                <div class="text-center text-xs text-gray-400">
                    <div class="font-medium">My Application</div>
                    <div class="mt-1">Version 1.0.0</div>
                </div>
            </div>
        </aside>

        <!-- Mobile Menu Button -->
        <div class="lg:hidden fixed top-4 left-4 z-50">
            <button @click="mobileMenuOpen = !mobileMenuOpen"
                    class="p-2 bg-gray-900 text-white rounded-lg">
                ☰
            </button>
        </div>

        <!-- Mobile Sidebar -->
        <aside x-show="mobileMenuOpen"
               @click.away="mobileMenuOpen = false"
               x-transition:enter="transition-transform ease-out duration-300"
               x-transition:enter-start="-translate-x-full"
               x-transition:enter-end="translate-x-0"
               class="lg:hidden fixed inset-y-0 left-0 w-80 bg-gray-900 text-white z-40">
            <!-- Same content as desktop sidebar -->
            <div class="p-6">
                <h1 class="text-2xl font-bold">MY APP</h1>
            </div>
            <!-- ... navigation items ... -->
        </aside>

        <!-- Main Content Area -->
        <main class="flex-1 overflow-auto">
            <!-- Header -->
            <header class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
                <h2 class="text-3xl font-semibold text-gray-900 dark:text-white" x-text="getStageTitle()"></h2>
                <p class="text-sm text-gray-600 dark:text-gray-300 mt-1" x-text="getStageDescription()"></p>
            </header>

            <!-- Content -->
            <div class="p-6">

                <!-- Dashboard View -->
                <div x-show="activeStage === 'dashboard'">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <!-- Stat Card 1 -->
                        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Total Items</h3>
                            <p class="text-3xl font-bold text-gray-900 dark:text-white mt-2" x-text="items.length"></p>
                        </div>

                        <!-- Stat Card 2 -->
                        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Active</h3>
                            <p class="text-3xl font-bold text-green-600 mt-2"
                               x-text="items.filter(i => i.status === 'active').length"></p>
                        </div>

                        <!-- Stat Card 3 -->
                        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Pending</h3>
                            <p class="text-3xl font-bold text-yellow-600 mt-2"
                               x-text="items.filter(i => i.status === 'pending').length"></p>
                        </div>
                    </div>
                </div>

                <!-- Items View -->
                <div x-show="activeStage === 'items'">
                    <div class="bg-white dark:bg-gray-800 rounded-lg shadow">
                        <!-- Loading State -->
                        <div x-show="loading" class="p-8 text-center">
                            <div class="spinner mx-auto mb-4"></div>
                            <p class="text-gray-600 dark:text-gray-300">Loading items...</p>
                        </div>

                        <!-- Items Table -->
                        <div x-show="!loading" class="overflow-x-auto">
                            <table class="w-full">
                                <thead class="bg-gray-50 dark:bg-gray-700">
                                    <tr>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">ID</th>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Name</th>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Status</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                                    <template x-for="item in items" :key="item.id">
                                        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                                            <td class="px-6 py-4 text-sm text-gray-900 dark:text-white" x-text="item.id"></td>
                                            <td class="px-6 py-4 text-sm text-gray-900 dark:text-white" x-text="item.name"></td>
                                            <td class="px-6 py-4">
                                                <span class="px-2 py-1 text-xs font-medium rounded-full"
                                                      :class="{
                                                          'bg-green-100 text-green-800': item.status === 'active',
                                                          'bg-yellow-100 text-yellow-800': item.status === 'pending'
                                                      }"
                                                      x-text="item.status"></span>
                                            </td>
                                        </tr>
                                    </template>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Settings View -->
                <div x-show="activeStage === 'settings'">
                    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                        <h3 class="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Appearance</h3>

                        <div class="space-y-4">
                            <label class="flex items-center">
                                <input type="checkbox"
                                       x-model="darkMode"
                                       @change="toggleDarkMode()"
                                       class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
                                <span class="ml-2 text-gray-900 dark:text-white">Dark Mode</span>
                            </label>
                        </div>
                    </div>
                </div>

            </div>
        </main>
    </div>

    <!-- Application State Script -->
    <script>
        function appState() {
            return {
                // State
                activeStage: 'dashboard',
                darkMode: false,
                mobileMenuOpen: false,
                loading: false,
                items: [],
                notifications: [],

                // Initialize
                async init() {
                    console.log('App initialized');

                    // Restore dark mode
                    const savedDarkMode = localStorage.getItem('darkMode') === 'true';
                    if (savedDarkMode) {
                        this.darkMode = true;
                        document.documentElement.classList.add('dark');
                    }

                    // Load data
                    await this.loadItems();
                },

                // Navigation
                switchStage(stage) {
                    console.log(`Switching to ${stage}`);
                    this.activeStage = stage;
                    this.mobileMenuOpen = false;

                    // Save to localStorage
                    localStorage.setItem('activeStage', stage);
                },

                getStageTitle() {
                    const titles = {
                        dashboard: 'Dashboard',
                        items: 'Items',
                        settings: 'Settings'
                    };
                    return titles[this.activeStage] || 'Welcome';
                },

                getStageDescription() {
                    const descriptions = {
                        dashboard: 'Overview of your application metrics',
                        items: 'Manage and view all items',
                        settings: 'Configure application settings'
                    };
                    return descriptions[this.activeStage] || '';
                },

                // Dark Mode
                toggleDarkMode() {
                    this.darkMode = !this.darkMode;

                    if (this.darkMode) {
                        document.documentElement.classList.add('dark');
                    } else {
                        document.documentElement.classList.remove('dark');
                    }

                    localStorage.setItem('darkMode', this.darkMode);
                },

                // API Calls
                async loadItems() {
                    this.loading = true;

                    try {
                        const response = await fetch('/api/items');
                        if (!response.ok) throw new Error('Failed to load items');

                        this.items = await response.json();
                        this.showNotification('success', 'Success', 'Items loaded successfully');
                    } catch (error) {
                        console.error('Error loading items:', error);
                        this.showNotification('error', 'Error', 'Failed to load items');
                    } finally {
                        this.loading = false;
                    }
                },

                // Notifications
                showNotification(type, title, message, duration = 5000) {
                    const id = Date.now();
                    this.notifications.push({
                        id,
                        type,
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
                }
            }
        }
    </script>
</body>
</html>
```

---

## Step 4: Create CSS (static/css/style.css)

```css
/* Custom Styles */

:root {
    --brand-primary: #2563eb;
    --brand-hover: #1d4ed8;
}

/* Loading Spinner */
.spinner {
    display: inline-block;
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid var(--brand-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Smooth Transitions */
* {
    transition-property: background-color, border-color, color;
    transition-duration: 200ms;
    transition-timing-function: ease-in-out;
}

/* Custom Scrollbar */
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

/* Fade In Animation */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in {
    animation: fadeIn 0.3s ease-in-out;
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

---

## Step 5: Install Dependencies

```bash
pip install fastapi uvicorn python-multipart
```

---

## Step 6: Run the Application

```bash
python main.py
```

Visit: http://localhost:8000

---

## What You Get

✅ **3-Stage Sidebar Navigation** (Dashboard, Items, Settings)
✅ **Dark Mode Toggle** (with localStorage persistence)
✅ **Responsive Design** (Mobile & Desktop)
✅ **Notification System** (Success, Error, Info)
✅ **API Integration** (FastAPI backend)
✅ **Loading States** (Spinner during data fetch)
✅ **Data Table** (With status badges)
✅ **Stat Cards** (Dashboard metrics)

---

## Next Steps

1. **Add more navigation items** - Duplicate the sidebar nav pattern
2. **Create new API endpoints** - Follow the `/api/items` pattern
3. **Add authentication** - See main guide for JWT example
4. **Customize colors** - Update Tailwind config and CSS variables
5. **Add charts** - Include Chart.js and create visualizations

---

## File Structure

```
my-app/
├── main.py                 # FastAPI backend
├── static/
│   ├── index.html         # Main SPA
│   └── css/
│       └── style.css      # Custom styles
└── README.md
```

---

## Customization Quick Reference

### Change Colors

**In `index.html` Tailwind config:**
```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                brand: {
                    primary: '#YOUR_COLOR',
                    hover: '#YOUR_HOVER_COLOR'
                }
            }
        }
    }
}
```

### Add Navigation Item

**In `index.html` sidebar:**
```html
<div class="px-2 mb-4">
    <a href="#" @click.prevent="switchStage('your-stage')"
       :class="{
           'bg-green-600 text-white shadow-lg': activeStage === 'your-stage',
           'text-gray-300 hover:bg-gray-700 border-green-500/30': activeStage !== 'your-stage'
       }"
       class="block px-6 py-8 text-2xl font-bold rounded-lg transition-all border">
        YOUR STAGE
        <div class="text-xs font-normal opacity-80 mt-1">Description</div>
    </a>
</div>
```

**Add content view:**
```html
<div x-show="activeStage === 'your-stage'">
    <!-- Your content here -->
</div>
```

### Add API Endpoint

**In `main.py`:**
```python
@app.get("/api/your-endpoint")
async def your_endpoint():
    return {"data": "your data"}
```

**Call from frontend:**
```javascript
async loadYourData() {
    const response = await fetch('/api/your-endpoint');
    const data = await response.json();
    console.log(data);
}
```

---

## Troubleshooting

**Issue: Alpine.js not working**
- Check browser console for errors
- Ensure `defer` attribute is on Alpine.js script tag
- Verify `x-data` is on a parent element

**Issue: Dark mode not persisting**
- Check localStorage in DevTools
- Verify `init()` method is being called
- Check `x-init="init()"` is on body element

**Issue: API calls failing**
- Verify backend is running on port 8000
- Check network tab in DevTools
- Verify endpoint URLs match backend routes

**Issue: Styling not working**
- Check Tailwind CDN is loading
- Verify class names are spelled correctly
- Check custom CSS file is linked

---

## Full Documentation

For complete details, advanced patterns, and best practices, see:
**[GUI_REPLICATION_GUIDE.md](./GUI_REPLICATION_GUIDE.md)**

---

**You now have a fully functional Catalynx-style application!** 🎉
