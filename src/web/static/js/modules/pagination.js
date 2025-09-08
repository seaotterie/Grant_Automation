// Catalynx Pagination Module
// Table pagination and sorting utilities extracted from monolithic app.js

class CatalynxPagination {
    constructor() {
        this.defaultItemsPerPage = 10;
        this.maxItemsPerPage = 100;
        
        // Default pagination state
        this.defaultState = {
            currentPage: 1,
            itemsPerPage: this.defaultItemsPerPage,
            sortColumn: null,
            sortDirection: 'asc'
        };
    }
    
    /**
     * Create pagination state for a data context
     */
    createPaginationState(itemsPerPage = null) {
        return {
            ...this.defaultState,
            itemsPerPage: itemsPerPage || this.defaultItemsPerPage
        };
    }
    
    /**
     * Get paginated and sorted data
     */
    getPaginatedData(data, paginationState) {
        if (!data || !Array.isArray(data)) return [];
        
        const { currentPage, itemsPerPage, sortColumn, sortDirection } = paginationState;
        
        // Apply sorting if column is selected
        let sortedData = [...data];
        if (sortColumn) {
            sortedData.sort((a, b) => {
                let aVal = a[sortColumn];
                let bVal = b[sortColumn];
                
                // Handle different data types
                if (typeof aVal === 'string') aVal = aVal.toLowerCase();
                if (typeof bVal === 'string') bVal = bVal.toLowerCase();
                
                if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
                if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
                return 0;
            });
        }
        
        // Apply pagination
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        return sortedData.slice(startIndex, endIndex);
    }
    
    /**
     * Get total number of pages
     */
    getTotalPages(data, itemsPerPage) {
        if (!data || !Array.isArray(data)) return 1;
        return Math.ceil(data.length / itemsPerPage);
    }
    
    /**
     * Sort table by column
     */
    sortTable(paginationState, column) {
        if (paginationState.sortColumn === column) {
            paginationState.sortDirection = paginationState.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            paginationState.sortColumn = column;
            paginationState.sortDirection = 'asc';
        }
        // Reset to first page when sorting changes
        paginationState.currentPage = 1;
        return paginationState;
    }
    
    /**
     * Navigate to specific page
     */
    goToPage(paginationState, page, totalPages) {
        if (page >= 1 && page <= totalPages) {
            paginationState.currentPage = page;
        }
        return paginationState;
    }
    
    /**
     * Navigate to next page
     */
    nextPage(paginationState, data) {
        const totalPages = this.getTotalPages(data, paginationState.itemsPerPage);
        if (paginationState.currentPage < totalPages) {
            paginationState.currentPage++;
        }
        return paginationState;
    }
    
    /**
     * Navigate to previous page
     */
    prevPage(paginationState) {
        if (paginationState.currentPage > 1) {
            paginationState.currentPage--;
        }
        return paginationState;
    }
    
    /**
     * Set items per page (with validation)
     */
    setItemsPerPage(paginationState, itemsPerPage) {
        const validItemsPerPage = Math.max(1, Math.min(itemsPerPage, this.maxItemsPerPage));
        paginationState.itemsPerPage = validItemsPerPage;
        paginationState.currentPage = 1; // Reset to first page
        return paginationState;
    }
    
    /**
     * Get pagination info for UI display
     */
    getPaginationInfo(data, paginationState) {
        const totalItems = data ? data.length : 0;
        const totalPages = this.getTotalPages(data, paginationState.itemsPerPage);
        const currentPage = Math.min(paginationState.currentPage, totalPages);
        const startIndex = (currentPage - 1) * paginationState.itemsPerPage;
        const endIndex = Math.min(startIndex + paginationState.itemsPerPage, totalItems);
        
        return {
            totalItems,
            totalPages,
            currentPage,
            itemsPerPage: paginationState.itemsPerPage,
            startIndex: startIndex + 1, // 1-based for display
            endIndex,
            hasNextPage: currentPage < totalPages,
            hasPrevPage: currentPage > 1,
            isFirstPage: currentPage === 1,
            isLastPage: currentPage === totalPages
        };
    }
    
    /**
     * Generate page numbers array for pagination controls
     */
    getPageNumbers(totalPages, currentPage, maxVisiblePages = 5) {
        if (totalPages <= maxVisiblePages) {
            return Array.from({ length: totalPages }, (_, i) => i + 1);
        }
        
        const halfVisible = Math.floor(maxVisiblePages / 2);
        let startPage = Math.max(1, currentPage - halfVisible);
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
        
        // Adjust if we're near the end
        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }
        
        return Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);
    }
    
    /**
     * Search and filter data before pagination
     */
    filterData(data, searchTerm, filterFunction = null) {
        if (!data || !Array.isArray(data)) return [];
        
        let filteredData = data;
        
        // Apply search term if provided
        if (searchTerm && searchTerm.trim()) {
            const searchLower = searchTerm.toLowerCase().trim();
            filteredData = filteredData.filter(item => {
                // Search in common text fields
                const searchableFields = ['name', 'organization_name', 'title', 'description', 'ein'];
                return searchableFields.some(field => {
                    const value = item[field];
                    return value && String(value).toLowerCase().includes(searchLower);
                });
            });
        }
        
        // Apply custom filter function if provided
        if (typeof filterFunction === 'function') {
            filteredData = filteredData.filter(filterFunction);
        }
        
        return filteredData;
    }
}

// Make available globally for modular system
window.CatalynxPagination = CatalynxPagination;

// Auto-initialize if loaded standalone
if (typeof window !== 'undefined' && !window.CatalynxPagination) {
    window.CatalynxPagination = new CatalynxPagination();
    console.log('✅ CatalynxPagination module loaded');
}