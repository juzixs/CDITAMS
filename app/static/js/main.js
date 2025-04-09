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

// 侧边栏功能
document.addEventListener('DOMContentLoaded', function() {
    // 保存侧边栏状态到本地存储
    function saveSidebarState(isCollapsed) {
        localStorage.setItem('sidebarCollapsed', isCollapsed);
    }

    // 从本地存储加载侧边栏状态
    function loadSidebarState() {
        const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (isCollapsed && window.innerWidth >= 992) {
            document.body.classList.add('sidebar-collapsed');
        }
    }

    // 初始加载侧边栏状态
    loadSidebarState();

    // 侧边栏切换
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function() {
            // 在小屏幕上，切换sidebar-open类
            if (window.innerWidth < 992) {
                document.body.classList.toggle('sidebar-open');
                
                // 确保sidebar-collapsed不会在小屏幕上启用
                document.body.classList.remove('sidebar-collapsed');
            } else {
                // 在大屏幕上，切换sidebar-collapsed类
                document.body.classList.toggle('sidebar-collapsed');
                
                // 保存状态到本地存储
                saveSidebarState(document.body.classList.contains('sidebar-collapsed'));
            }
        });
    }
    
    // 处理侧边栏下拉菜单
    const dropdownItems = document.querySelectorAll('.sidebar .has-submenu');
    dropdownItems.forEach(function(item) {
        item.addEventListener('click', function(e) {
            // 阻止点击事件冒泡
            e.preventDefault();
            
            // 检查侧边栏是否处于折叠状态
            const isSidebarCollapsed = document.body.classList.contains('sidebar-collapsed');
            
            // 如果侧边栏折叠，先展开侧边栏，然后再处理子菜单
            if (isSidebarCollapsed) {
                document.body.classList.remove('sidebar-collapsed');
                saveSidebarState(false);
                
                // 确保子菜单可见，延迟一点点以等待侧边栏展开动画
                setTimeout(() => {
                    const submenu = this.nextElementSibling;
                    if (submenu && submenu.classList.contains('sidebar-submenu')) {
                        submenu.classList.add('show');
                        this.classList.add('active');
                    }
                }, 50);
                
                return;
            }
            
            const submenu = this.nextElementSibling;
            if (!submenu || !submenu.classList.contains('sidebar-submenu')) return;
            
            // 已展开则关闭，否则展开
            if (submenu.classList.contains('show')) {
                submenu.classList.remove('show');
                this.classList.remove('active');
            } else {
                // 只在非折叠模式下关闭其他展开的子菜单
                document.querySelectorAll('.sidebar-submenu.show').forEach(function(el) {
                    el.classList.remove('show');
                    if (el.previousElementSibling) {
                        el.previousElementSibling.classList.remove('active');
                    }
                });
                
                submenu.classList.add('show');
                this.classList.add('active');
            }
        });
    });
    
    // 为侧边栏中的子菜单图标添加单独的展开/折叠功能
    dropdownItems.forEach(function(item) {
        // 获取菜单项中的图标元素
        const icon = item.querySelector('.fa-chevron-down');
        if (icon) {
            // 将事件监听器添加到图标本身
            icon.addEventListener('click', function(e) {
                // 防止事件冒泡，确保点击图标只执行这一个处理程序
                e.stopPropagation();
                // 阻止默认行为
                e.preventDefault();
                
                // 触发父元素的点击事件来展开/折叠子菜单
                item.click();
            });
        }
    });
    
    // 背景遮罩点击关闭侧边栏（在移动设备上）
    const backdrop = document.querySelector('.sidebar-backdrop');
    if (backdrop) {
        backdrop.addEventListener('click', function() {
            document.body.classList.remove('sidebar-open');
        });
    }
    
    // 根据窗口大小调整侧边栏
    function handleResize() {
        if (window.innerWidth < 992) {
            // 小屏幕上：清除折叠状态，准备响应式交互
            document.body.classList.remove('sidebar-collapsed');
            
            // 如果菜单打开，点击任何链接都应该关闭菜单
            if (document.body.classList.contains('sidebar-open')) {
                const navLinks = document.querySelectorAll('.sidebar .nav-link:not(.has-submenu)');
                navLinks.forEach(link => {
                    link.addEventListener('click', function() {
                        document.body.classList.remove('sidebar-open');
                    }, { once: true });
                });
            }
        } else {
            // 大屏幕上：移除开放状态，根据保存的状态设置折叠
            document.body.classList.remove('sidebar-open');
            
            // 重新加载保存的状态
            const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
            if (isCollapsed) {
                document.body.classList.add('sidebar-collapsed');
            } else {
                document.body.classList.remove('sidebar-collapsed');
            }
        }
    }
    
    // 添加窗口大小调整事件监听
    window.addEventListener('resize', handleResize);
    
    // 初始调整
    handleResize();

    // 设置当前活动菜单项
    setActiveNavItem();
});

// 设置当前活动菜单项
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    let hasActive = false;
    
    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
            
            // 如果是子菜单项，展开其父菜单
            const parent = link.closest('.sidebar-submenu');
            if (parent) {
                parent.classList.add('show');
                const parentLink = parent.previousElementSibling;
                if (parentLink && parentLink.classList.contains('has-submenu')) {
                    parentLink.classList.add('active');
                }
            }
            
            hasActive = true;
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
            hasActive = true;
        } else if (!link.classList.contains('has-submenu')) {
            // 只移除非子菜单头的active状态
            link.classList.remove('active');
        }
    });
    
    // 如果没有匹配项，则默认首页为活动状态
    if (!hasActive && currentPath === '/') {
        const homeLink = document.querySelector('.sidebar .nav-link[href="/"]');
        if (homeLink) {
            homeLink.classList.add('active');
        }
    }
}

// 添加页面内容淡入效果
document.addEventListener('DOMContentLoaded', function() {
    const contentElement = document.querySelector('.content');
    if (contentElement) {
        contentElement.style.opacity = '0';
        setTimeout(function() {
            contentElement.style.opacity = '1';
        }, 50);
    }
}); 