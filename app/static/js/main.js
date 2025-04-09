// 全局函数
document.addEventListener('DOMContentLoaded', function() {
    // 自动关闭警告框
    var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var alertInstance = new bootstrap.Alert(alert);
            alertInstance.close();
        }, 5000);
    });
    
    // 初始化所有工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 移动端导航栏自动折叠
    var navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    var navbarCollapse = document.querySelector('.navbar-collapse');
    var bsCollapse = navbarCollapse ? new bootstrap.Collapse(navbarCollapse, {toggle: false}) : null;
    
    navLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            if (window.innerWidth < 992 && bsCollapse) {
                bsCollapse.hide();
            }
        });
    });
}); 