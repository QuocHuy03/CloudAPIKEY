// Admin Panel JavaScript

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Confirm dialogs for destructive actions
    $('.btn-danger').on('click', function(e) {
        if (!confirm('Bạn có chắc chắn muốn thực hiện hành động này?')) {
            e.preventDefault();
        }
    });

    // Form validation
    $('form').on('submit', function(e) {
        var form = $(this);
        var isValid = true;

        // Check required fields
        form.find('[required]').each(function() {
            if (!$(this).val().trim()) {
                $(this).addClass('is-invalid');
                isValid = false;
            } else {
                $(this).removeClass('is-invalid');
            }
        });

        if (!isValid) {
            e.preventDefault();
            showAlert('Vui lòng điền đầy đủ thông tin bắt buộc!', 'danger');
        }
    });

    // Remove validation classes on input
    $('input, select, textarea').on('input change', function() {
        $(this).removeClass('is-invalid');
    });
});

// Utility functions
function showAlert(message, type = 'info') {
    var alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('.container-fluid').prepend(alertHtml);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        var date = new Date(dateString);
        return date.toLocaleDateString('vi-VN');
    } catch (e) {
        return dateString;
    }
}

function formatNumber(number) {
    if (number === null || number === undefined) return 'N/A';
    return number.toLocaleString('vi-VN');
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showAlert('Đã sao chép vào clipboard!', 'success');
    }).catch(function() {
        showAlert('Không thể sao chép vào clipboard!', 'danger');
    });
}

// Table functions
function sortTable(columnIndex, tableId = 'keysTable') {
    var table = document.getElementById(tableId);
    var tbody = table.querySelector('tbody');
    var rows = Array.from(tbody.querySelectorAll('tr'));
    
    var isAscending = table.getAttribute('data-sort-direction') !== 'asc';
    
    rows.sort(function(a, b) {
        var aVal = a.cells[columnIndex].textContent.trim();
        var bVal = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as numbers
        var aNum = parseFloat(aVal);
        var bNum = parseFloat(bVal);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        
        // Sort as strings
        return isAscending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
    
    // Re-append sorted rows
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
    
    // Update sort direction
    table.setAttribute('data-sort-direction', isAscending ? 'asc' : 'desc');
}

// Search and filter functions
function searchTable(searchTerm, tableId = 'keysTable') {
    var table = document.getElementById(tableId);
    var rows = table.querySelectorAll('tbody tr');
    
    searchTerm = searchTerm.toLowerCase();
    
    rows.forEach(function(row) {
        var text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
    
    updateRowCount(tableId);
}

function filterTable(filterFunction, tableId = 'keysTable') {
    var table = document.getElementById(tableId);
    var rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(function(row) {
        if (filterFunction(row)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
    
    updateRowCount(tableId);
}

function updateRowCount(tableId = 'keysTable') {
    var table = document.getElementById(tableId);
    var visibleRows = table.querySelectorAll('tbody tr:not([style*="display: none"])');
    var countElement = document.getElementById('totalKeys');
    
    if (countElement) {
        countElement.textContent = visibleRows.length;
    }
}

// AJAX helper functions
function makeAjaxRequest(url, method = 'GET', data = null, successCallback = null, errorCallback = null) {
    var options = {
        url: url,
        method: method,
        success: function(response) {
            if (successCallback) {
                successCallback(response);
            }
        },
        error: function(xhr, status, error) {
            if (errorCallback) {
                errorCallback(xhr, status, error);
            } else {
                showAlert('Có lỗi xảy ra: ' + error, 'danger');
            }
        }
    };
    
    if (data) {
        options.data = JSON.stringify(data);
        options.contentType = 'application/json';
    }
    
    $.ajax(options);
}

// Export functions
function exportToCSV(tableId = 'keysTable', filename = 'keys.csv') {
    var table = document.getElementById(tableId);
    var rows = table.querySelectorAll('tr');
    var csv = [];
    
    rows.forEach(function(row) {
        var cells = row.querySelectorAll('th, td');
        var rowData = [];
        
        cells.forEach(function(cell) {
            var text = cell.textContent.trim();
            // Escape quotes and wrap in quotes if contains comma
            if (text.includes(',') || text.includes('"')) {
                text = '"' + text.replace(/"/g, '""') + '"';
            }
            rowData.push(text);
        });
        
        csv.push(rowData.join(','));
    });
    
    var csvContent = csv.join('\n');
    var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    var link = document.createElement('a');
    
    if (link.download !== undefined) {
        var url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Loading states
function showLoading(element) {
    var $element = $(element);
    $element.data('original-text', $element.html());
    $element.html('<i class="fas fa-spinner fa-spin me-2"></i>Đang xử lý...').prop('disabled', true);
}

function hideLoading(element) {
    var $element = $(element);
    $element.html($element.data('original-text')).prop('disabled', false);
}

// Real-time updates
function startRealTimeUpdates(interval = 30000) {
    setInterval(function() {
        // Update statistics
        makeAjaxRequest('/admin/api/stats', 'GET', null, function(response) {
            if (response.success) {
                updateStatistics(response.data);
            }
        });
    }, interval);
}

function updateStatistics(stats) {
    // Update dashboard statistics
    Object.keys(stats).forEach(function(module) {
        var moduleStats = stats[module];
        var card = $('[data-module="' + module + '"]');
        
        if (card.length) {
            card.find('.total-count').text(moduleStats.total);
            card.find('.active-count').text(moduleStats.active);
            card.find('.expired-count').text(moduleStats.expired);
            card.find('.used-up-count').text(moduleStats.used_up);
        }
    });
}

// Initialize real-time updates on dashboard
if (window.location.pathname.includes('/admin/')) {
    startRealTimeUpdates();
}